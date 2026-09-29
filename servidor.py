#!/usr/bin/env python3
"""Sirve la UI, guarda los experimentos en ./experimentos (JSON + Markdown)
y hace de intermediario con OpenRouter para que la clave nunca llegue al navegador."""
import json, os, re, time, urllib.error, urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

RAIZ = Path(__file__).parent
EXP = RAIZ / "experimentos"
EXP.mkdir(exist_ok=True)
PUERTO = 8765
OPENROUTER = "https://openrouter.ai/api/v1"


def cargar_env():
    """Lee KEY=valor de .env (si existe) sin pisar variables ya definidas."""
    f = RAIZ / ".env"
    if f.exists():
        for linea in f.read_text().splitlines():
            if "=" in linea and not linea.lstrip().startswith("#"):
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


cargar_env()
CLAVE_OR = os.environ.get("OPENROUTER_API_KEY", "")
_cache_modelos = {"t": 0, "datos": None}


def pedir_openrouter(ruta, cuerpo=None):
    req = urllib.request.Request(OPENROUTER + ruta, data=json.dumps(cuerpo).encode() if cuerpo else None, headers={
        "Authorization": f"Bearer {CLAVE_OR}", "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ivansantander-hub/eco-loop", "X-Title": "eco-loop"})
    return urllib.request.urlopen(req, timeout=120)


def a_markdown(e):
    c = e["config"]
    l = [f"# Experimento {e['id']}", "",
         f"- **Modo:** {c['modo']}",
         f"- **Inicio:** {e['inicio']}",
         f"- **Mensaje inicial (semilla):** {c['semilla']!r}",
         f"- **Parámetros:** temperature={c['temperature']}, num_predict={c['num_predict']}, "
         f"num_ctx={c['num_ctx']}, think={c['think']}, contexto={c['contexto']}", ""]
    for ia in c["ias"]:
        l.append(f"- **{ia['etiqueta']}** · modelo `{ia['modelo']}` · system prompt: "
                 + (f"\n  > {ia['system']}" if ia["system"] else "_ninguno_"))
        if ia.get("system_integrado"):
            l.append(f"  - system prompt de fábrica del modelo"
                     + (" (sustituido por el anterior)" if ia["system"] else " **(aplicado)**")
                     + f":\n    > {ia['system_integrado']}")
    if e.get("notas"):
        l += ["", "## Notas", "", e["notas"]]
    l += ["", "## Conversación", ""]
    for m in e["mensajes"]:
        extra = f" _({m['tokens']} tok, {m['segundos']} s)_" if m.get("tokens") else ""
        l += [f"**{m['etiqueta']}**{extra}:", "", m["texto"], ""]
    return "\n".join(l)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(RAIZ), **k)

    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        # Nunca servir archivos ocultos (.env con la clave, .git, …)
        if any(parte.startswith(".") for parte in self.path.split("?")[0].split("/")):
            return self._json({"error": "no encontrado"}, 404)
        if self.path == "/api/openrouter/modelos":
            return self._modelos_openrouter()
        if self.path == "/api/experimentos":
            lista = []
            for f in sorted(EXP.glob("*.json"), reverse=True):
                e = json.loads(f.read_text())
                lista.append({"id": e["id"], "modo": e["config"]["modo"], "semilla": e["config"]["semilla"],
                              "publicar": e.get("publicar", False),
                              "mensajes": [{"autor": m["autor"], "texto": m["texto"]} for m in e["mensajes"]]})
            return self._json(lista)
        m = re.fullmatch(r"/api/experimentos/([\w-]+)", self.path)
        if m:
            f = EXP / f"{m[1]}.json"
            return self._json(json.loads(f.read_text())) if f.exists() else self._json({}, 404)
        super().do_GET()

    def _modelos_openrouter(self):
        if not CLAVE_OR:
            return self._json({"activo": False, "modelos": []})
        if not _cache_modelos["datos"] or time.time() - _cache_modelos["t"] > 3600:
            try:
                with pedir_openrouter("/models") as r:
                    datos = json.load(r)["data"]
            except Exception as err:
                return self._json({"activo": True, "error": str(err), "modelos": []}, 502)
            _cache_modelos.update(t=time.time(), datos=sorted(
                ({"id": m["id"], "nombre": m.get("name", m["id"]),
                  "gratis": m["id"].endswith(":free") or all(float(v or 0) == 0 for v in (m.get("pricing") or {}).values())}
                 for m in datos if (m.get("architecture") or {}).get("output_modalities", ["text"]) == ["text"]),  # solo modelos de chat de texto
                key=lambda m: m["nombre"].lower()))
        self._json({"activo": True, "modelos": _cache_modelos["datos"]})

    def _chat_openrouter(self, cuerpo):
        """Reenvía el chat a OpenRouter y devuelve su stream SSE tal cual."""
        if not CLAVE_OR:
            return self._json({"error": "Falta OPENROUTER_API_KEY en .env"}, 400)
        pedido = {k: cuerpo[k] for k in ("model", "messages", "max_tokens", "temperature") if k in cuerpo}
        pedido.update(stream=True, usage={"include": True})
        try:
            r = pedir_openrouter("/chat/completions", pedido)
        except urllib.error.HTTPError as err:
            detalle = err.read().decode(errors="replace")
            try:
                detalle = json.loads(detalle)["error"]["message"]
            except Exception:
                pass
            return self._json({"error": f"OpenRouter {err.code}: {detalle}"}, 502)
        except Exception as err:
            return self._json({"error": f"OpenRouter: {err}"}, 502)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        try:
            with r:
                for linea in r:          # si el navegador corta (Parar), la escritura falla y se cierra OpenRouter
                    self.wfile.write(linea)
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        if self.path == "/api/openrouter/chat":
            return self._chat_openrouter(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        if self.path != "/api/guardar":
            return self._json({}, 404)
        e = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if not re.fullmatch(r"[\w-]+", e.get("id", "")):
            return self._json({"error": "id inválido"}, 400)
        (EXP / f"{e['id']}.json").write_text(json.dumps(e, ensure_ascii=False, indent=2))
        (EXP / f"{e['id']}.md").write_text(a_markdown(e))
        self._json({"ok": True})


if __name__ == "__main__":
    print(f"UI en http://localhost:{PUERTO} · experimentos en {EXP} · OpenRouter {'activo' if CLAVE_OR else 'sin clave (.env)'}")
    ThreadingHTTPServer(("127.0.0.1", PUERTO), Handler).serve_forever()
