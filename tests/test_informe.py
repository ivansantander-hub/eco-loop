"""La evidencia de cada laboratorio y el resumen general de la app (nucleo/informe.py)."""
from tests.ayuda import ConLaboratorio, LAB
from nucleo import ensayos, informe, motor


class Evidencia(ConLaboratorio):
    def correr(self, **opciones):
        e = ensayos.nuevo(LAB, opciones, base=self.base)
        motor.correr(e, base=self.base)
        return e

    def test_agregados_por_marco(self):
        self.correr(marco="puro", modelos=["prueba:espejo", "prueba:espejo"], turnos=4)    # bucle seguro
        self.correr(marco="puro", turnos=1)      # un solo mensaje: no puede haber bucle
        self.correr(marco="humana", turnos=4)
        ev = informe.evidencia(LAB, self.base)
        self.assertEqual(ev["totales"]["ensayos"], 3)
        self.assertEqual([m["marco"] for m in ev["por_marco"]], ["puro", "humana"])          # en el orden del lab.json
        puro = ev["por_marco"][0]
        self.assertEqual((puro["ensayos"], puro["con_bucle"], puro["bucle"]), (2, 1, 50))
        self.assertEqual(puro["nombre"], "Puro")
        self.assertEqual(len(ev["ensayos"]), 3)
        self.assertTrue(all("destacado" in e for e in ev["ensayos"]))

    def test_descarta_ensayos_vacios(self):
        self.correr(turnos=2)
        vacio = ensayos.nuevo(LAB, base=self.base)
        vacio["mensajes"] = [{"autor": 0, "etiqueta": "IA A", "modelo": "", "texto": ""}]
        ensayos.guardar(vacio, self.base)
        ev = informe.evidencia(LAB, self.base)
        self.assertEqual((ev["totales"]["ensayos"], ev["totales"]["descartados"]), (1, 1))
        self.assertNotIn("", ev["totales"]["modelos"])

    def test_bitacora_conclusiones_y_enlaces(self):
        (self.base / LAB / "bitacora.md").write_text(
            "# Lab\n\nVer [lab.json](lab.json) y el [otro](../01-espejos/bitacora.md).\n\n"
            "## Conclusiones\n\n1. **Primera.**\n2. Segunda.\n\n## Anexo\n\nNada.\n")
        ev = informe.evidencia(LAB, self.base)
        self.assertEqual(ev["conclusiones"], "1. **Primera.**\n2. Segunda.")
        self.assertIn(f"[lab.json]({informe.REPO}/laboratorios/{LAB}/lab.json)", ev["bitacora"])
        self.assertIn("[otro](/lab/01-espejos)", ev["bitacora"])

    def test_sin_ensayos(self):
        ev = informe.evidencia(LAB, self.base)
        self.assertEqual((ev["totales"]["ensayos"], ev["por_marco"], ev["conclusiones"]), (0, [], ""))

    def test_app(self):
        self.correr(turnos=2)
        a = informe.app(self.base)
        self.assertEqual((a["totales"]["laboratorios"], a["totales"]["ensayos"], a["totales"]["mensajes"]), (1, 1, 2))
        self.assertEqual(a["laboratorios"][0]["resumen"]["ensayos"], 1)
        self.assertIn("**", a["conclusiones"])                           # del README real
        self.assertNotIn("](laboratorios/", a["conclusiones"])           # enlaces pasados a la web
