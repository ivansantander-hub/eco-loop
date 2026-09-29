"""Ollama y OpenRouter contra un servidor local que imita sus respuestas en streaming (sin red ni coste)."""
import json, os, threading, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import tests.ayuda  # noqa: F401  (activa el proveedor de prueba)
from nucleo import config, proveedores


class Imitador(BaseHTTPRequestHandler):
    pedidos = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == "/api/tags":
            return self._json({"models": [{"name": "qwen-falso:1b"}]})
        if self.path == "/api/v1/models":
            return self._json({"data": [
                {"id": "openai/falso", "name": "Falso", "context_length": 128000, "pricing": {"prompt": "0.1"},
                 "architecture": {"output_modalities": ["text"]}},
                {"id": "musica/falsa:free", "name": "Música", "pricing": {}, "architecture": {"output_modalities": ["audio", "text"]}},
            ]})
        self.send_error(404)

    def do_POST(self):
        cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Imitador.pedidos.append((self.path, cuerpo, dict(self.headers)))
        if self.path == "/api/show":
            return self._json({"system": "Eres un asistente de fábrica.", "model_info": {"qwen.context_length": 40960}})
        if self.path == "/api/chat":
            self.send_response(200); self.end_headers()
            for t in ["Hola", ", ¿qué", " tal?"]:
                self.wfile.write((json.dumps({"message": {"content": t}, "done": False}) + "\n").encode())
            self.wfile.write((json.dumps({"message": {"content": ""}, "done": True, "eval_count": 3, "done_reason": "length"}) + "\n").encode())
            return
        if self.path == "/api/v1/chat/completions":
            if cuerpo["model"] == "roto/modelo":
                return self._json({"error": {"message": "modelo inválido"}}, 400)
            self.send_response(200); self.end_headers()
            eventos = [": OPENROUTER PROCESSING",
                       "data: " + json.dumps({"choices": [{"delta": {"content": "Buenas"}}]}),
                       "data: " + json.dumps({"choices": [{"delta": {"content": " tardes"}, "finish_reason": "stop"}]}),
                       "data: " + json.dumps({"choices": [], "usage": {"completion_tokens": 2, "cost": 0.0000123}}),
                       "data: [DONE]"]
            for ev in eventos:
                self.wfile.write((ev + "\n\n").encode())
            return
        self.send_error(404)

    def _json(self, obj, codigo=200):
        b = json.dumps(obj).encode()
        self.send_response(codigo); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)


class Proveedores(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), Imitador)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        cls._ollama, cls._or = config.OLLAMA, config.OPENROUTER
        config.OLLAMA, config.OPENROUTER = url, url + "/api/v1"
        os.environ["OPENROUTER_API_KEY"] = "sk-or-prueba"
        proveedores.registrar("", proveedores.Ollama())
        proveedores.registrar("or", proveedores.OpenRouter())

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        config.OLLAMA, config.OPENROUTER = cls._ollama, cls._or
        os.environ.pop("OPENROUTER_API_KEY", None)

    def setUp(self):
        Imitador.pedidos.clear()

    def test_ollama_stream_y_ventana_automatica(self):
        trozos = []
        r = proveedores.generar("qwen-falso:1b", [{"role": "user", "content": "x" * 30000}], 300, 0.8, al_texto=trozos.append)
        self.assertEqual((r.texto, r.tokens, r.cortado), ("Hola, ¿qué tal?", 3, True))
        self.assertEqual(trozos, ["Hola", "Hola, ¿qué", "Hola, ¿qué tal?"])
        opciones = next(c for p, c, _ in Imitador.pedidos if p == "/api/chat")["options"]
        self.assertEqual(opciones["num_ctx"], 16384)               # ~10k tokens → ventana de 16k (máx. del modelo 40k)
        self.assertEqual(r.ctx["max"], 40960)

    def test_ollama_info_y_lista(self):
        self.assertEqual(proveedores.info("qwen-falso:1b")["system_integrado"], "Eres un asistente de fábrica.")
        ids = [m["id"] for m in proveedores.listar()["modelos"]]
        self.assertIn("qwen-falso:1b", ids)

    def test_openrouter_stream_coste_y_clave(self):
        r = proveedores.generar("or:openai/falso", [{"role": "user", "content": "Hola"}], 50, 0.8)
        self.assertEqual((r.texto, r.tokens, r.costo, r.cortado), ("Buenas tardes", 2, 0.0000123, False))
        _, cuerpo, cabeceras = Imitador.pedidos[-1]
        self.assertEqual((cuerpo["model"], cuerpo["stream"], cuerpo["usage"]), ("openai/falso", True, {"include": True}))
        self.assertEqual(cabeceras["Authorization"], "Bearer sk-or-prueba")

    def test_openrouter_error_claro(self):
        with self.assertRaises(proveedores.ErrorProveedor) as ctx:
            proveedores.generar("or:roto/modelo", [{"role": "user", "content": "Hola"}], 50, 0.8)
        self.assertIn("modelo inválido", str(ctx.exception))

    def test_openrouter_solo_modelos_de_texto(self):
        modelos = [m for m in proveedores.listar()["modelos"] if m["proveedor"] == "openrouter"]
        self.assertEqual([m["id"] for m in modelos], ["or:openai/falso"])
        self.assertEqual(modelos[0]["ctx_max"], 128000)

    def test_cancelar_corta_el_stream(self):
        with self.assertRaises(proveedores.Cancelado):
            proveedores.generar("qwen-falso:1b", [{"role": "user", "content": "Hola"}], 50, 0.8, debe_parar=lambda: True)


class Utilidades(unittest.TestCase):
    def test_ventana(self):
        self.assertEqual([proveedores.ventana(n, 40960) for n in (3000, 12000, 50000)], [8192, 16384, 40960])
        self.assertEqual(proveedores.ventana(100000, None), 32768)

    def test_prefijos(self):
        self.assertEqual(proveedores.para("or:openai/x")[1], "openai/x")
        self.assertEqual(proveedores.para("huihui_ai/qwen3:14b")[1], "huihui_ai/qwen3:14b")   # «huihui_ai» no es un prefijo
        self.assertEqual(proveedores.para("prueba:espejo")[1], "espejo")
