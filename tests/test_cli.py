"""Los comandos de cli/, ejecutados como los ejecutaría una persona (sin red: proveedor de prueba)."""
import contextlib, io, json

from tests.ayuda import ConLaboratorio, LAB
from cli.__main__ import principal
from nucleo import ensayos, laboratorios


class Comandos(ConLaboratorio):
    def correr_cli(self, *argv):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = principal(list(argv))
        return codigo, salida.getvalue()

    def test_sin_comando_muestra_la_ayuda(self):
        codigo, salida = self.correr_cli()
        self.assertEqual(codigo, 1)
        self.assertIn("correr", salida)

    def test_labs(self):
        codigo, salida = self.correr_cli("labs")
        self.assertEqual(codigo, 0)
        self.assertIn(LAB, salida)

    def test_labs_nuevo(self):
        codigo, salida = self.correr_cli("labs", "nuevo", "91-otro", "--nombre", "Otro", "--pregunta", "¿Y si…?", "--marcos", "puro", "humana")
        self.assertEqual(codigo, 0, salida)
        lab = laboratorios.cargar("91-otro")
        self.assertEqual((lab["numero"], lab["marcos"], lab["por_defecto"]["marco"]), (91, ["puro", "humana"], "puro"))
        self.assertTrue((laboratorios.carpeta("91-otro") / "bitacora.md").exists())
        self.assertEqual(self.correr_cli("labs", "nuevo", "91-otro", "--nombre", "x", "--pregunta", "y")[0], 1)   # ya existe
        self.assertEqual(self.correr_cli("labs", "nuevo", "malo", "--nombre", "x", "--pregunta", "y")[0], 1)      # id inválido

    def test_correr_una_serie_y_analizarla(self):
        codigo, salida = self.correr_cli("correr", "--lab", LAB, "--serie", "s1", "--concurrencia", "2")
        self.assertEqual(codigo, 0, salida)
        es = ensayos.listar(LAB)
        self.assertEqual(len(es), 4)                                        # 2 marcos × 1 modelo × 2 réplicas
        self.assertEqual(sorted(e["config"]["replica"] for e in es), [1, 1, 2, 2])
        self.assertTrue(all(len(e["mensajes"]) == 4 and e["config"]["serie"] == "s1" for e in es))
        codigo, tabla = self.correr_cli("analizar", "--lab", LAB, "--serie", "s1")
        self.assertEqual(codigo, 0)
        self.assertIn("| humana |", tabla)
        self.assertEqual(self.correr_cli("analizar", "--lab", LAB, "--serie", "no-existe")[0], 1)

    def test_correr_con_varias_semillas(self):
        codigo, _ = self.correr_cli("correr", "--lab", LAB, "--marcos", "puro", "--replicas", "1",
                                    "--semillas", "Hola", "Anoche soñé que el mar se había ido.", "--serie", "s2")
        self.assertEqual(codigo, 0)
        es = ensayos.listar(LAB)
        self.assertEqual(sorted(e["config"]["semilla"] for e in es), ["Anoche soñé que el mar se había ido.", "Hola"])
        self.assertTrue(all("_s1_" in e["id"] or "_s2_" in e["id"] for e in es))

    def test_correr_con_opciones_y_parar_en_bucle(self):
        codigo, _ = self.correr_cli("correr", "--lab", LAB, "--marcos", "puro", "--modelos", "prueba:espejo", "--replicas", "1",
                                    "--turnos", "10", "--parar-en-bucle", "--memoria", "ventana", "--recientes", "4")
        self.assertEqual(codigo, 0)
        e = ensayos.listar(LAB)[0]
        self.assertEqual((len(e["mensajes"]), e["config"]["memoria"]), (3, {"tipo": "ventana", "recientes": 4}))

    def test_exportar_informe_estatico(self):
        self.correr_cli("correr", "--lab", LAB, "--replicas", "1", "--marcos", "puro")
        salida = self.base / "informe.html"
        codigo, _ = self.correr_cli("exportar", "--lab", LAB, "--salida", str(salida))
        html = salida.read_text()
        self.assertEqual(codigo, 0)
        self.assertIn("const SERVIDO = false", html)
        self.assertNotIn('src="/comun.js"', html)            # todo en un archivo
        self.assertIn("function md(", html)

    def test_migrar(self):
        viejo = ensayos.nuevo(LAB)
        viejo.pop("laboratorio"); viejo.pop("version_esquema")
        viejo["config"]["serie"] = "marcos-9"
        (self.base / "viejos").mkdir()
        (self.base / "viejos" / f"{viejo['id']}.json").write_text(json.dumps(viejo))
        (self.base / "02-mascaras" / "ensayos").mkdir(parents=True)
        (self.base / "02-mascaras" / "lab.json").write_text(json.dumps({**laboratorios.cargar(LAB), "id": "02-mascaras", "numero": 2}))
        codigo, salida = self.correr_cli("migrar", "--desde", str(self.base / "viejos"), "--sin-consultar")
        self.assertEqual(codigo, 0)
        self.assertIn("02-mascaras: 1 ensayos migrados", salida)
        self.assertEqual(ensayos.cargar(viejo["id"])["laboratorio"], "02-mascaras")
