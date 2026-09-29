import datetime, json

from tests.ayuda import ConLaboratorio, LAB, lab_def
from nucleo import ensayos, laboratorios


class Laboratorios(ConLaboratorio):
    def test_listar_y_cargar(self):
        self.assertEqual([l["id"] for l in laboratorios.listar(self.base)], [LAB])
        self.assertEqual(laboratorios.cargar(LAB, self.base)["nombre"], "Prueba")

    def test_no_existe(self):
        with self.assertRaises(laboratorios.LaboratorioNoEncontrado):
            laboratorios.cargar("99-nada", self.base)

    def test_id_debe_coincidir_con_la_carpeta(self):
        (self.base / LAB / "lab.json").write_text(json.dumps(lab_def(id="otro")))
        with self.assertRaises(ValueError):
            laboratorios.cargar(LAB, self.base)

    def test_textos_por_defecto(self):
        self.assertEqual(laboratorios.textos(LAB, self.base)["ensayos"], {})


class Ensayos(ConLaboratorio):
    def test_nuevo_con_valores_del_laboratorio(self):
        e = ensayos.nuevo(LAB, base=self.base)
        c = e["config"]
        self.assertEqual((e["laboratorio"], e["version_esquema"], c["marco"], c["formato"]), (LAB, 2, "puro", "chat"))
        self.assertEqual((c["turnos"], c["num_predict"], c["semilla"]), (4, 50, "Hola"))
        self.assertEqual([ia["system"] for ia in c["ias"]], [None, None])

    def test_marco_humana_da_instruccion_solo_a_b(self):
        e = ensayos.nuevo(LAB, {"marco": "humana"}, base=self.base)
        a, b = e["config"]["ias"]
        self.assertIsNone(a["system"])
        self.assertTrue(b["system"].startswith("Eres una persona real"))

    def test_marco_con_nombres_y_personalidad(self):
        e = ensayos.nuevo(LAB, {"marco": "personalidad", "nombres": ["Nova", "Eco"], "personalidades": ["Curiosa.", "Irónica."]}, base=self.base)
        a, b = e["config"]["ias"]
        self.assertEqual((a["etiqueta"], b["etiqueta"]), ("Nova", "Eco"))
        self.assertEqual(a["system"], "Te llamas Nova. Estás conversando con otra IA llamada Eco. Curiosa.")

    def test_marco_no_permitido(self):
        with self.assertRaises(ValueError):
            ensayos.nuevo(LAB, {"marco": "saben_ias"}, base=self.base)

    def test_ids_no_se_pisan(self):
        ahora = datetime.datetime(2026, 9, 28, 12, 0, 0).astimezone()
        e1 = ensayos.nuevo(LAB, base=self.base, ahora=ahora)
        ensayos.guardar(e1, self.base)
        e2 = ensayos.nuevo(LAB, base=self.base, ahora=ahora)
        self.assertNotEqual(e1["id"], e2["id"])

    def test_guardar_cargar_listar_markdown(self):
        e = ensayos.nuevo(LAB, {"notas": "nota de prueba"}, base=self.base)
        f = ensayos.guardar(e, self.base)
        self.assertTrue(f.with_suffix(".md").read_text().startswith(f"# Ensayo {e['id']}"))
        self.assertEqual(ensayos.cargar(e["id"], self.base)["notas"], "nota de prueba")
        self.assertEqual(len(ensayos.listar(LAB, self.base)), 1)
        with self.assertRaises(KeyError):
            ensayos.cargar("no-existe", self.base)
        with self.assertRaises(KeyError):
            ensayos.cargar("../../etc/passwd", self.base)

    def test_normalizar_ensayo_antiguo(self):
        viejo = {"id": "2026-09-27_024004_personalidad", "inicio": "x", "mensajes": [],
                 "config": {"modo": "personalidad", "semilla": "?", "num_predict": 120, "temperature": 0.8,
                            "ias": [{"etiqueta": "Nova", "modelo": "prueba:contador",
                                     "system": "Te llamas Nova. Estás conversando con otra IA llamada Eco. "},
                                    {"etiqueta": "Eco", "modelo": "prueba:contador", "system": "Te llamas Eco. Estás conversando con otra IA llamada Nova."}]}}
        n = ensayos.normalizar(viejo, LAB)
        self.assertEqual((n["config"]["marco"], n["config"]["formato"], n["config"]["memoria"]), ("nombres", "chat", {"tipo": "completa"}))
        self.assertEqual((n["laboratorio"], n["version_esquema"], n["publicar"]), (LAB, 2, False))
        self.assertIn("system_integrado", n["config"]["ias"][0])

    def test_migrar_no_borra_ni_repite(self):
        origen = self.base / "viejos"
        origen.mkdir()
        viejo = ensayos.nuevo(LAB, base=self.base)
        viejo.pop("laboratorio"); viejo.pop("version_esquema"); viejo["config"].pop("marco")
        (origen / f"{viejo['id']}.json").write_text(json.dumps(viejo))
        hechos, omitidos = ensayos.migrar(origen, lambda e: LAB, self.base)
        self.assertEqual((hechos, omitidos), ({LAB: [viejo["id"]]}, []))
        self.assertTrue((origen / f"{viejo['id']}.json").exists())
        self.assertEqual(ensayos.migrar(origen, lambda e: LAB, self.base), ({}, [viejo["id"]]))
