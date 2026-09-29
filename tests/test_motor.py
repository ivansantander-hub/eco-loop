from tests.ayuda import ConLaboratorio, LAB
from nucleo import ensayos, motor, proveedores


class Falla(proveedores.Proveedor):
    """Falla las primeras `n` llamadas y luego responde."""
    nombre = "falla"

    def __init__(self, n):
        self.n = n

    def generar(self, modelo, messages, max_tokens, temperatura, al_texto=None, debe_parar=None):
        self.n -= 1
        if self.n >= 0:
            raise proveedores.ErrorProveedor("503: saturado")
        return proveedores.Resultado("por fin respondo", tokens=3)


class Motor(ConLaboratorio):
    def nuevo(self, **opciones):
        e = ensayos.nuevo(LAB, opciones, base=self.base)
        ensayos.guardar(e, self.base)
        return e

    def test_un_turno_se_guarda_con_su_registro(self):
        e = self.nuevo()
        vistos = []
        m = motor.turno(e, al_texto=vistos.append, base=self.base)
        self.assertEqual((m["autor"], m["etiqueta"], m["memoria"]["desde"]), (0, "IA A", 0))
        self.assertTrue(vistos and vistos[-1] == m["texto"])            # llegó en trozos, acumulado
        self.assertEqual(len(ensayos.cargar(e["id"], self.base)["mensajes"]), 1)

    def test_los_mensajes_que_recibe_cada_ia(self):
        e = self.nuevo(marco="humana")
        motor.correr(e, base=self.base)
        llamadas = self.prueba.llamadas
        self.assertEqual(llamadas[0]["messages"], [{"role": "user", "content": "Hola"}])   # A: sin instrucción + semilla
        self.assertEqual(llamadas[1]["messages"][0]["role"], "system")                     # B: la «humana»
        self.assertEqual([m["role"] for m in llamadas[3]["messages"]], ["system", "user", "assistant", "user"])

    def test_correr_hasta_el_final(self):
        e = self.nuevo()
        self.assertEqual(motor.correr(e, base=self.base), "fin")
        self.assertEqual(len(e["mensajes"]), 4)

    def test_parar_en_bucle(self):
        e = self.nuevo(modelos=["prueba:espejo", "prueba:espejo"], turnos=10)
        self.assertEqual(motor.correr(e, parar_en_bucle=True, base=self.base), "bucle")
        self.assertEqual(len(e["mensajes"]), 3)

    def test_cancelar_no_guarda_nada(self):
        e = self.nuevo(modelos=["prueba:lento", "prueba:lento"])
        with self.assertRaises(proveedores.Cancelado):
            motor.turno(e, debe_parar=lambda: True, base=self.base)
        self.assertEqual(ensayos.cargar(e["id"], self.base)["mensajes"], [])

    def test_memoria_resumen_genera_resumenes(self):
        e = self.nuevo(turnos=10, memoria={"tipo": "resumen", "recientes": 4})
        motor.correr(e, base=self.base)
        guardado = ensayos.cargar(e["id"], self.base)
        self.assertTrue(guardado["memoria"][0] and guardado["memoria"][1])
        self.assertTrue(any(m["memoria"].get("resumen_hasta") for m in guardado["mensajes"]))

    def test_reintenta_y_luego_anota_el_error(self):
        proveedores.registrar("falla", Falla(1))
        e = self.nuevo(modelos=["falla:x", "falla:x"], turnos=1)
        self.assertEqual(motor.correr(e, reintentos=1, espera=0, base=self.base), "fin")
        proveedores.registrar("falla", Falla(5))
        e = self.nuevo(modelos=["falla:x", "falla:x"], turnos=1)
        self.assertTrue(motor.correr(e, reintentos=1, espera=0, base=self.base).startswith("error"))
        self.assertIn("503", ensayos.cargar(e["id"], self.base)["notas"])
