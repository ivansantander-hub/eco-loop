"""El servidor web de punta a punta, con el proveedor de prueba y un laboratorio temporal."""
import http.client, json, socket, threading, time

from tests.ayuda import ConLaboratorio, LAB
from nucleo import ensayos
from web import servidor


class Servidor(ConLaboratorio):
    def setUp(self):
        super().setUp()
        self.srv = servidor.crear(0, base=self.base)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.puerto = self.srv.server_address[1]

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        super().tearDown()

    def pedir(self, metodo, ruta, cuerpo=None):
        c = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=10)
        c.request(metodo, ruta, json.dumps(cuerpo) if cuerpo is not None else None, {"Content-Type": "application/json"})
        r = c.getresponse()
        datos = r.read().decode()
        c.close()
        return r.status, r.getheader("Content-Type"), datos

    def json(self, metodo, ruta, cuerpo=None):
        estado, _, datos = self.pedir(metodo, ruta, cuerpo)
        return estado, json.loads(datos)

    def eventos(self, datos):
        salida = []
        for bloque in datos.strip().split("\n\n"):
            lineas = dict(l.split(": ", 1) for l in bloque.split("\n"))
            salida.append((lineas["event"], json.loads(lineas["data"])))
        return salida

    # ---------- páginas ----------
    def test_paginas(self):
        for ruta, texto in [("/", "Laboratorios"), ("/comun.js", "function md("), (f"/lab/{LAB}", "Prueba · eco loop"),
                            (f"/lab/{LAB}/banco", "banco de pruebas")]:
            estado, _, datos = self.pedir("GET", ruta)
            self.assertEqual(estado, 200, ruta)
            self.assertIn(texto, datos, ruta)

    def test_informe_servido_enlaza_banco_y_comun(self):
        _, _, html = self.pedir("GET", f"/lab/{LAB}")
        self.assertIn('<script src="/comun.js"></script>', html)
        self.assertIn("const SERVIDO = true", html)
        self.assertIn("const EVIDENCIA = {", html)
        for seccion in ['id="resultados"', 'id="conclusiones"', 'id="destacados"', 'id="todos"']:
            self.assertIn(seccion, html)

    def test_api_app(self):
        estado, app = self.json("GET", "/api/app")
        self.assertEqual((estado, app["totales"]["laboratorios"], app["laboratorios"][0]["id"]), (200, 1, LAB))
        self.assertIn("conclusiones", app)

    def test_solo_rutas_conocidas(self):
        for ruta in ["/.env", "/.git/config", "/servidor.py", "/nucleo/config.py", "/laboratorios/marcos.json", "/lab/99-nada", "/api/ensayos/../../x"]:
            self.assertEqual(self.pedir("GET", ruta)[0], 404, ruta)

    # ---------- API ----------
    def test_labs_y_lab(self):
        estado, labs = self.json("GET", "/api/labs")
        self.assertEqual((estado, labs[0]["id"], labs[0]["n_ensayos"]), (200, LAB, 0))
        estado, lab = self.json("GET", f"/api/labs/{LAB}")
        self.assertEqual(set(lab["marcos_def"]), {"puro", "humana", "nombres", "personalidad"})

    def test_modelos_incluye_prueba(self):
        _, r = self.json("GET", "/api/modelos")
        self.assertIn("prueba:contador", [m["id"] for m in r["modelos"]])

    def test_crear_turno_y_actualizar(self):
        estado, e = self.json("POST", f"/api/labs/{LAB}/ensayos", {"marco": "humana", "turnos": 2})
        self.assertEqual((estado, e["config"]["marco"], e["mensajes"]), (201, "humana", []))
        estado, tipo, datos = self.pedir("POST", f"/api/ensayos/{e['id']}/turno")
        self.assertEqual((estado, tipo.split(";")[0]), (200, "text/event-stream"))
        evs = self.eventos(datos)
        nombres = [n for n, _ in evs]
        self.assertEqual((nombres[0], nombres[-1]), ("inicio", "fin"))
        self.assertIn("texto", nombres)
        self.assertEqual(evs[0][1]["candidatas"], ["hola"])
        fin = evs[-1][1]
        self.assertEqual(fin["mensaje"]["autor"], 0)
        self.assertIn("originalidad", fin["mensaje"]["medidas"])
        self.assertEqual(fin["resumen"]["turnos"], 1)
        self.assertEqual(len(ensayos.cargar(e["id"], self.base)["mensajes"]), 1)

        estado, _ = self.json("POST", f"/api/ensayos/{e['id']}", {"notas": "muy raro", "publicar": True, "turnos": 6})
        guardado = ensayos.cargar(e["id"], self.base)
        self.assertEqual((estado, guardado["notas"], guardado["publicar"], guardado["config"]["turnos"]), (200, "muy raro", True, 6))
        estado, completo = self.json("GET", f"/api/ensayos/{e['id']}")
        self.assertEqual((estado, completo["resumen"]["turnos"]), (200, 1))
        _, lista = self.json("GET", f"/api/labs/{LAB}/ensayos")
        self.assertEqual((lista[0]["id"], lista[0]["publicar"]), (e["id"], True))

    def test_errores_claros(self):
        self.assertEqual(self.json("POST", f"/api/labs/{LAB}/ensayos", {"marco": "saben_ias"})[0], 400)
        self.assertEqual(self.json("POST", "/api/ensayos/no-existe/turno")[0], 404)
        self.assertEqual(self.json("GET", "/api/ensayos/no-existe")[0], 404)
        self.assertEqual(self.json("POST", "/api/labs/99-nada/ensayos", {})[0], 404)

    def test_error_del_proveedor_llega_como_evento(self):
        _, e = self.json("POST", f"/api/labs/{LAB}/ensayos", {"modelos": ["modelo-que-no-existe", "modelo-que-no-existe"]})
        evs = self.eventos(self.pedir("POST", f"/api/ensayos/{e['id']}/turno")[2])
        self.assertEqual(evs[-1][0], "error")
        self.assertEqual(ensayos.cargar(e["id"], self.base)["mensajes"], [])

    def test_parar_a_mitad_de_turno_no_guarda(self):
        """Cerrar la conexión durante el stream (botón Parar) cancela el turno sin guardarlo."""
        _, e = self.json("POST", f"/api/labs/{LAB}/ensayos", {"modelos": ["prueba:lento", "prueba:lento"]})
        s = socket.create_connection(("127.0.0.1", self.puerto), timeout=10)
        s.sendall(f"POST /api/ensayos/{e['id']}/turno HTTP/1.1\r\nHost: x\r\nContent-Length: 0\r\n\r\n".encode())
        recibido = b""
        while b"event: texto" not in recibido:   # espera a que ya esté escribiendo
            recibido += s.recv(4096)
        s.close()
        time.sleep(0.8)           # da tiempo a que el servidor note el corte
        self.assertEqual(ensayos.cargar(e["id"], self.base)["mensajes"], [])
        estado, _, datos = self.pedir("POST", f"/api/ensayos/{e['id']}/turno")   # y el ensayo sigue usable
        self.assertEqual(self.eventos(datos)[-1][0], "fin")
