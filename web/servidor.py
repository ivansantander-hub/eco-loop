"""Servidor web de eco loop. Solo muestra y controla: toda la lógica está en nucleo/.

Páginas
    /                          índice de laboratorios (web/portada.html)
    /lab/<id>                  evidencia del laboratorio: resultados, conclusiones y ensayos (nucleo.informe)
    /lab/<id>/banco            banco de pruebas (web/banco.html)
    /comun.js                  código de pantalla compartido
API (JSON)
    GET  /api/app                      cifras de todos los laboratorios y conclusiones generales (para la portada)
    GET  /api/labs                     laboratorios con un resumen de sus ensayos
    GET  /api/labs/<id>                un laboratorio y sus marcos
    GET  /api/labs/<id>/ensayos        sus ensayos, resumidos (para la tira del banco)
    POST /api/labs/<id>/ensayos        crea un ensayo (cuerpo: opciones de nucleo.ensayos.nuevo)
    GET  /api/ensayos/<id>             un ensayo completo, con las medidas de cada mensaje
    POST /api/ensayos/<id>             cambia notas, publicar o turnos
    POST /api/ensayos/<id>/turno       genera el siguiente turno en streaming (SSE): inicio, estado, texto, fin, error
    GET  /api/modelos                  modelos de todos los proveedores
Solo se sirven estas rutas: nada de archivos sueltos (así .env nunca sale).
"""
import json, re, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from nucleo import config, ensayos, informe, laboratorios, medidas, motor, proveedores

PAGINAS = {"portada": config.WEB / "portada.html", "banco": config.WEB / "banco.html"}
_bloqueos, _bloqueo_global = {}, threading.Lock()


def _bloqueo(ensayo_id):
    with _bloqueo_global:
        return _bloqueos.setdefault(ensayo_id, threading.Lock())


def ensayo_para_web(e):
    """El ensayo con las medidas de cada mensaje y el resumen."""
    e = json.loads(json.dumps(e))
    for k, m in enumerate(e["mensajes"]):
        m["medidas"] = medidas.del_mensaje(e, k)
    e["resumen"] = medidas.resumen(e)
    return e


def resumen_corto(e):
    r = medidas.resumen(e)
    return {"id": e["id"], "marco": r["marco"], "semilla": r["semilla"], "turnos": r["turnos"], "curva": r["curva"],
            "autores": [m["autor"] for m in e["mensajes"]], "en_bucle": r["en_bucle"], "publicar": e.get("publicar", False),
            "serie": r["serie"], "replica": r["replica"], "modelos": r["modelos"]}


class Manejador(BaseHTTPRequestHandler):
    base = None   # carpeta de laboratorios (None = config.LABORATORIOS); las pruebas usan una temporal

    def log_message(self, *a):
        pass

    # ---------- respuestas ----------
    def _enviar(self, codigo, tipo, cuerpo):
        b = cuerpo.encode() if isinstance(cuerpo, str) else cuerpo
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(b)

    def _json(self, obj, codigo=200):
        self._enviar(codigo, "application/json; charset=utf-8", json.dumps(obj, ensure_ascii=False))

    def _error(self, codigo, texto):
        self._json({"error": texto}, codigo)

    def _cuerpo(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    # ---------- GET ----------
    def do_GET(self):
        ruta = urlparse(self.path).path.rstrip("/") or "/"
        try:
            if ruta == "/":
                return self._enviar(200, "text/html; charset=utf-8", PAGINAS["portada"].read_text())
            if ruta == "/comun.js":
                return self._enviar(200, "text/javascript; charset=utf-8", (config.WEB / "comun.js").read_text())
            if m := re.fullmatch(r"/lab/([\w-]+)", ruta):
                return self._enviar(200, "text/html; charset=utf-8", informe.html(m[1], servido=True, base=self.base))
            if m := re.fullmatch(r"/lab/([\w-]+)/banco", ruta):
                laboratorios.cargar(m[1], self.base)
                return self._enviar(200, "text/html; charset=utf-8", PAGINAS["banco"].read_text())
            if ruta == "/api/app":
                return self._json(informe.app(self.base))
            if ruta == "/api/labs":
                return self._json([self._lab_con_resumen(l) for l in laboratorios.listar(self.base)])
            if m := re.fullmatch(r"/api/labs/([\w-]+)", ruta):
                lab = laboratorios.cargar(m[1], self.base)
                todos = laboratorios.marcos(self.base)
                return self._json({**lab, "marcos_def": {k: todos[k] for k in lab["marcos"]}})
            if m := re.fullmatch(r"/api/labs/([\w-]+)/ensayos", ruta):
                laboratorios.cargar(m[1], self.base)
                return self._json([resumen_corto(e) for e in ensayos.listar(m[1], self.base)])
            if m := re.fullmatch(r"/api/ensayos/([\w-]+)", ruta):
                return self._json(ensayo_para_web(ensayos.cargar(m[1], self.base)))
            if ruta == "/api/modelos":
                return self._json(proveedores.listar())
        except (laboratorios.LaboratorioNoEncontrado, KeyError) as err:
            return self._error(404, f"no existe: {err}")
        self._error(404, "no encontrado")

    def _lab_con_resumen(self, lab):
        es = ensayos.listar(lab["id"], self.base)
        return {**lab, "n_ensayos": len(es), "n_mensajes": sum(len(e["mensajes"]) for e in es),
                "coste": round(sum(m.get("costo") or 0 for e in es for m in e["mensajes"]), 4),
                "ultimo": max((e["inicio"] for e in es), default=None)}

    # ---------- POST ----------
    def do_POST(self):
        ruta = urlparse(self.path).path.rstrip("/")
        try:
            if m := re.fullmatch(r"/api/labs/([\w-]+)/ensayos", ruta):
                e = ensayos.nuevo(m[1], self._cuerpo(), self.base)
                ensayos.guardar(e, self.base)
                return self._json(ensayo_para_web(e), 201)
            if m := re.fullmatch(r"/api/ensayos/([\w-]+)/turno", ruta):
                return self._turno(m[1])
            if m := re.fullmatch(r"/api/ensayos/([\w-]+)", ruta):
                return self._actualizar(m[1], self._cuerpo())
        except (laboratorios.LaboratorioNoEncontrado, KeyError) as err:
            return self._error(404, f"no existe: {err}")
        except ValueError as err:
            return self._error(400, str(err))
        self._error(404, "no encontrado")

    def _actualizar(self, ensayo_id, cambios):
        with _bloqueo(ensayo_id):
            e = ensayos.cargar(ensayo_id, self.base)
            if "notas" in cambios:
                e["notas"] = str(cambios["notas"])
            if "publicar" in cambios:
                e["publicar"] = bool(cambios["publicar"])
            if "turnos" in cambios:
                e["config"]["turnos"] = max(1, int(cambios["turnos"]))
            ensayos.guardar(e, self.base)
        return self._json({"ok": True, "id": ensayo_id})

    def _turno(self, ensayo_id):
        """Un turno en streaming. Si el navegador corta la conexión (Parar), se cancela y no se guarda nada."""
        candado = _bloqueo(ensayo_id)
        if not candado.acquire(blocking=False):
            return self._error(409, "ese ensayo ya está generando un turno")
        try:
            e = ensayos.cargar(ensayo_id, self.base)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            cortado = {"si": False}

            def enviar(evento, datos):
                try:
                    self.wfile.write(f"event: {evento}\ndata: {json.dumps(datos, ensure_ascii=False)}\n\n".encode())
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    cortado["si"] = True
                    raise proveedores.Cancelado()

            k = len(e["mensajes"])
            enviar("inicio", {"turno": k + 1, "autor": k % 2, "etiqueta": e["config"]["ias"][k % 2]["etiqueta"],
                              "candidatas": sorted(set(medidas.contenido(medidas.previo(e, k))))})
            try:
                motor.turno(e, al_texto=lambda t: enviar("texto", {"texto": t}), debe_parar=lambda: cortado["si"],
                            al_estado=lambda t: enviar("estado", {"texto": t}), base=self.base)
            except proveedores.Cancelado:
                return
            except Exception as err:
                return enviar("error", {"error": str(err)})
            web = ensayo_para_web(e)
            enviar("fin", {"mensaje": web["mensajes"][-1], "resumen": web["resumen"], "memoria": e.get("memoria")})
        except proveedores.Cancelado:
            pass
        finally:
            candado.release()


def crear(puerto=None, base=None, host="127.0.0.1"):
    """Crea el servidor (sin arrancarlo). puerto=0 elige uno libre (lo usan las pruebas)."""
    manejador = type("ManejadorEcoLoop", (Manejador,), {"base": base})
    return ThreadingHTTPServer((host, config.PUERTO if puerto is None else puerto), manejador)
