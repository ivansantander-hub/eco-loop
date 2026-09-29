"""Proveedores de modelos detrás de una sola interfaz.

El id de un modelo dice su proveedor por el prefijo:
    "or:openai/gpt-4o-mini"          → OpenRouter
    "prueba:espejo"                  → proveedor falso para pruebas (solo con ECOLOOP_PRUEBA=1)
    "huihui_ai/qwen3-abliterated:14b" (sin prefijo) → Ollama
"""
import json, time, urllib.error, urllib.request
from dataclasses import dataclass, field

from . import config


class Cancelado(Exception):
    """El que pidió la respuesta la cortó (botón Parar, conexión cerrada…)."""


class ErrorProveedor(Exception):
    pass


@dataclass
class Resultado:
    texto: str
    tokens: int | None = None
    cortado: bool = False
    costo: float | None = None
    ctx: dict = field(default_factory=dict)   # {"estimado", "max", "usado"}: memoria usada en tokens


def estimar_tokens(messages):
    """Aproximación: ~3 caracteres por token en español."""
    return -(-sum(len(m["content"]) for m in messages) // 3)


def ventana(necesita, maximo):
    """Menor potencia de 2 (desde 8192) en la que cabe `necesita`, sin pasar de `maximo`."""
    maximo = maximo or 32768
    n = 8192
    while n < necesita and n < maximo:
        n *= 2
    return min(n, maximo)


def _post(url, cuerpo, cabeceras=None, timeout=300):
    req = urllib.request.Request(url, json.dumps(cuerpo).encode(), {"Content-Type": "application/json", **(cabeceras or {})})
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as err:
        with err:
            detalle = err.read().decode(errors="replace")
        try:
            detalle = json.loads(detalle)["error"]
            detalle = detalle.get("message", detalle) if isinstance(detalle, dict) else detalle
        except Exception:
            pass
        raise ErrorProveedor(f"{err.code}: {detalle}") from None
    except urllib.error.URLError as err:
        raise ErrorProveedor(f"sin conexión con {url.split('/api')[0]}: {err.reason}") from None


class Proveedor:
    nombre = ""

    def generar(self, modelo, messages, max_tokens, temperatura, al_texto=None, debe_parar=None) -> Resultado:
        raise NotImplementedError

    def info(self, modelo) -> dict:
        """{"system_integrado": str|None, "ctx_max": int|None}"""
        return {"system_integrado": None, "ctx_max": None}

    def listar(self) -> list:
        return []


class Ollama(Proveedor):
    nombre = "ollama"

    def __init__(self):
        self._info = {}

    def info(self, modelo):
        if modelo not in self._info:
            with _post(config.OLLAMA + "/api/show", {"model": modelo}, timeout=10) as r:
                d = json.load(r)
            ctx = next((v for k, v in (d.get("model_info") or {}).items() if k.endswith(".context_length")), None)
            self._info[modelo] = {"system_integrado": d.get("system") or None, "ctx_max": ctx}
        return self._info[modelo]

    def listar(self):
        try:
            with urllib.request.urlopen(config.OLLAMA + "/api/tags", timeout=5) as r:
                nombres = [m["name"] for m in json.load(r)["models"]]
        except Exception:
            return []
        modelos = []
        for n in nombres:
            try:
                i = self.info(n)
            except ErrorProveedor:
                i = {"system_integrado": None, "ctx_max": None}
            modelos.append({"id": n, "nombre": n, "proveedor": "ollama", "gratis": True, **i})
        return modelos

    def generar(self, modelo, messages, max_tokens, temperatura, al_texto=None, debe_parar=None):
        try:
            maximo = self.info(modelo)["ctx_max"]
        except ErrorProveedor:
            maximo = None
        ctx = {"estimado": estimar_tokens(messages) + max_tokens, "max": maximo}
        ctx["usado"] = ventana(ctx["estimado"] + 256, maximo)
        texto, res = "", Resultado("", ctx=ctx)
        with _post(config.OLLAMA + "/api/chat", {"model": modelo, "messages": messages, "stream": True, "think": False,
                   "keep_alive": "10m", "options": {"num_predict": max_tokens, "temperature": temperatura, "num_ctx": ctx["usado"]}}) as r:
            for linea in r:
                if debe_parar and debe_parar():
                    raise Cancelado()
                if not linea.strip():
                    continue
                j = json.loads(linea)
                if j.get("error"):
                    raise ErrorProveedor(j["error"])
                trozo = (j.get("message") or {}).get("content") or ""
                if trozo:
                    texto += trozo
                    al_texto and al_texto(texto)
                if j.get("done"):
                    res.tokens, res.cortado = j.get("eval_count"), j.get("done_reason") == "length"
        res.texto = texto
        return res


class OpenRouter(Proveedor):
    nombre = "openrouter"

    def __init__(self):
        self._modelos, self._t = None, 0

    def _cabeceras(self):
        return {"Authorization": f"Bearer {config.clave_openrouter()}",
                "HTTP-Referer": "https://github.com/ivansantander-hub/eco-loop", "X-Title": "eco-loop"}

    def listar(self):
        if not config.clave_openrouter():
            return []
        if self._modelos is None or time.time() - self._t > 3600:
            req = urllib.request.Request(config.OPENROUTER + "/models", headers=self._cabeceras())
            with urllib.request.urlopen(req, timeout=30) as r:
                datos = json.load(r)["data"]
            self._modelos = sorted((
                {"id": "or:" + m["id"], "nombre": m.get("name", m["id"]), "proveedor": "openrouter",
                 "gratis": m["id"].endswith(":free") or all(float(v or 0) == 0 for v in (m.get("pricing") or {}).values()),
                 "ctx_max": m.get("context_length"), "system_integrado": None}
                for m in datos if (m.get("architecture") or {}).get("output_modalities", ["text"]) == ["text"]),  # solo chat de texto
                key=lambda m: m["nombre"].lower())
            self._t = time.time()
        return self._modelos

    def info(self, modelo):
        m = next((x for x in (self._modelos or []) if x["id"] == "or:" + modelo), None)
        return {"system_integrado": None, "ctx_max": m["ctx_max"] if m else None}

    def generar(self, modelo, messages, max_tokens, temperatura, al_texto=None, debe_parar=None):
        if not config.clave_openrouter():
            raise ErrorProveedor("falta OPENROUTER_API_KEY en .env")
        res = Resultado("", ctx={"estimado": estimar_tokens(messages) + max_tokens, "max": self.info(modelo)["ctx_max"]})
        texto = ""
        with _post(config.OPENROUTER + "/chat/completions", {"model": modelo, "messages": messages, "max_tokens": max_tokens,
                   "temperature": temperatura, "stream": True, "usage": {"include": True}}, self._cabeceras()) as r:
            for linea in r:
                if debe_parar and debe_parar():
                    raise Cancelado()
                linea = linea.decode().strip()
                if not linea.startswith("data:") or linea == "data: [DONE]":   # ": OPENROUTER PROCESSING"
                    continue
                j = json.loads(linea[5:])
                if j.get("error"):
                    raise ErrorProveedor(j["error"].get("message", str(j["error"])))
                ch = (j.get("choices") or [{}])[0]
                trozo = (ch.get("delta") or {}).get("content") or ""
                if trozo:
                    texto += trozo
                    al_texto and al_texto(texto)
                if ch.get("finish_reason"):
                    res.cortado = ch["finish_reason"] == "length"
                if j.get("usage"):
                    res.tokens, res.costo = j["usage"].get("completion_tokens"), j["usage"].get("cost")
        res.texto = texto
        return res


class Prueba(Proveedor):
    """Proveedor falso y determinista para las pruebas (sin red).

    prueba:espejo   repite el último mensaje recibido (provoca bucles de copia)
    prueba:contador responde «Mensaje N de <modelo>» con N creciente (nunca repite)
    prueba:largo    responde un texto largo y lo marca como cortado
    prueba:lento    como contador, pero en trozos con pausas (para probar Parar)
    """
    nombre = "prueba"

    def __init__(self):
        self.llamadas = []

    def listar(self):
        return [{"id": f"prueba:{n}", "nombre": f"Prueba · {n}", "proveedor": "prueba", "gratis": True,
                 "ctx_max": 4096, "system_integrado": None} for n in ("espejo", "contador", "largo", "lento")]

    def info(self, modelo):
        return {"system_integrado": None, "ctx_max": 4096}

    def generar(self, modelo, messages, max_tokens, temperatura, al_texto=None, debe_parar=None):
        self.llamadas.append({"modelo": modelo, "messages": messages})
        ultimo = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if modelo == "espejo":
            texto, cortado = ultimo, False
        elif modelo == "largo":
            texto, cortado = "palabra " * max_tokens, True
        else:
            texto, cortado = f"Mensaje {len(self.llamadas)} de {modelo}: respondo a «{ultimo[:30]}».", False
        trozos = [texto[i:i + 8] for i in range(0, len(texto), 8)] or [""]
        acumulado = ""
        for t in trozos:
            if debe_parar and debe_parar():
                raise Cancelado()
            acumulado += t
            al_texto and al_texto(acumulado)
            if modelo == "lento":
                time.sleep(0.05)
        return Resultado(texto, tokens=len(texto.split()), cortado=cortado, costo=0.0,
                         ctx={"estimado": estimar_tokens(messages) + max_tokens, "max": 4096})


_REGISTRO = {"or": OpenRouter(), "": Ollama()}
if config.PRUEBA:
    _REGISTRO["prueba"] = Prueba()


def registrar(prefijo, proveedor):
    _REGISTRO[prefijo] = proveedor


def para(modelo):
    """(proveedor, id sin prefijo) para un id de modelo."""
    prefijo, _, resto = modelo.partition(":")
    if prefijo in _REGISTRO and prefijo:
        return _REGISTRO[prefijo], resto
    return _REGISTRO[""], modelo


def generar(modelo, messages, max_tokens, temperatura, al_texto=None, debe_parar=None) -> Resultado:
    proveedor, id_ = para(modelo)
    return proveedor.generar(id_, messages, max_tokens, temperatura, al_texto, debe_parar)


def info(modelo):
    proveedor, id_ = para(modelo)
    try:
        return proveedor.info(id_)
    except ErrorProveedor:
        return {"system_integrado": None, "ctx_max": None}


def listar():
    """Todos los modelos disponibles, con avisos de los proveedores que no respondieron."""
    modelos, avisos = [], []
    for prefijo, p in _REGISTRO.items():
        try:
            modelos += p.listar()
        except Exception as err:
            avisos.append(f"{p.nombre}: {err}")
    return {"modelos": modelos, "avisos": avisos}
