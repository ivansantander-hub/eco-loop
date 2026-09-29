import unittest

from tests.ayuda import ensayo_de
from nucleo import memoria, proveedores
from nucleo.formatos import chat, obtener


def roles(msgs):
    return [m["role"] for m in msgs]


class FormatoChat(unittest.TestCase):
    def test_turno_de_a_incluye_la_semilla(self):
        e = ensayo_de(["a1", "b1"])
        msgs = chat.mensajes(e, 0, memoria.Recuerdo(0))
        self.assertEqual(msgs, [{"role": "user", "content": "Hola"}, {"role": "assistant", "content": "a1"},
                                {"role": "user", "content": "b1"}])

    def test_turno_de_b_no_ve_la_semilla(self):
        e = ensayo_de(["a1", "b1", "a2"])
        self.assertEqual(roles(chat.mensajes(e, 1, memoria.Recuerdo(0))), ["user", "assistant", "user"])

    def test_system_del_marco_va_primero(self):
        e = ensayo_de(["a1"])
        e["config"]["ias"][1]["system"] = "Eres una persona real"
        msgs = chat.mensajes(e, 1, memoria.Recuerdo(0))
        self.assertEqual(msgs[0], {"role": "system", "content": "Eres una persona real"})

    def test_resumen_como_system_y_sin_semilla(self):
        e = ensayo_de(["a1", "b1", "a2", "b2"])
        msgs = chat.mensajes(e, 0, memoria.Recuerdo(2, "hablasteis de perros", 2))
        self.assertEqual(roles(msgs), ["system", "assistant", "user"])
        self.assertIn("hablasteis de perros", msgs[0]["content"])

    def test_formato_desconocido(self):
        with self.assertRaises(ValueError):
            obtener("teatro")


class Memoria(unittest.TestCase):
    def falso_resumir(self):
        llamadas = []

        def resumir(pedido):
            llamadas.append(pedido)
            return proveedores.Resultado(f"resumen {len(llamadas)}", costo=0.001)
        return resumir, llamadas

    def test_completa_recuerda_todo(self):
        e = ensayo_de([f"m{k}" for k in range(20)])
        self.assertEqual(memoria.recuerdo(e, 0).desde, 0)

    def test_ventana_olvida_el_principio(self):
        e = ensayo_de([f"m{k}" for k in range(10)], memoria={"tipo": "ventana", "recientes": 4})
        r = memoria.recuerdo(e, 0)
        self.assertEqual((r.desde, r.resumen), (6, None))
        self.assertEqual(roles(chat.mensajes(e, 0, r))[0], "assistant")   # sin la semilla

    def test_no_resume_mientras_cabe(self):
        e = ensayo_de(["a", "b", "c"], memoria={"tipo": "resumen", "recientes": 4})
        resumir, llamadas = self.falso_resumir()
        self.assertEqual(memoria.recuerdo(e, 1, resumir).desde, 0)
        self.assertEqual(llamadas, [])

    def test_resumen_incremental_sin_huecos(self):
        e = ensayo_de([f"m{k}" for k in range(9)], memoria={"tipo": "resumen", "recientes": 4})
        resumir, llamadas = self.falso_resumir()
        r = memoria.recuerdo(e, 1, resumir)                       # 9 mensajes: resume 0–4, literal 5–8
        self.assertEqual((r.desde, r.resumen, r.resumen_hasta), (5, "resumen 1", 5))
        e["mensajes"].append({"autor": 1, "texto": "m9"})
        r = memoria.recuerdo(e, 1, resumir)                       # 10: todavía no toca actualizar → literal desde 5
        self.assertEqual((r.desde, len(llamadas)), (5, 1))
        e["mensajes"] += [{"autor": 0, "texto": "m10"}, {"autor": 1, "texto": "m11"}]
        r = memoria.recuerdo(e, 1, resumir)                       # 12: actualiza de forma incremental hasta 8
        self.assertEqual((r.desde, len(llamadas)), (8, 2))
        self.assertIn("Resumen anterior:\nresumen 1", llamadas[1][1]["content"])
        self.assertEqual([x["hasta"] for x in e["memoria"][1]], [5, 8])

    def test_resumen_en_segunda_persona_desde_su_punto_de_vista(self):
        e = ensayo_de(["hola soy A", "hola soy B"])
        pedido = memoria.pedido_resumen(e, 1, None, 0, 2)
        self.assertIn("Tu interlocutor: hola soy A", pedido[1]["content"])
        self.assertIn("Tú: hola soy B", pedido[1]["content"])
        self.assertNotIn("Hola", pedido[1]["content"].split("\n")[1])   # B nunca vio la semilla

    def test_resumen_sin_funcion_falla_claro(self):
        e = ensayo_de([f"m{k}" for k in range(9)], memoria={"tipo": "resumen", "recientes": 4})
        with self.assertRaises(ValueError):
            memoria.recuerdo(e, 0)

    def test_registro(self):
        self.assertEqual(memoria.Recuerdo(5, "x", 5).registro(), {"desde": 5, "resumen_hasta": 5})
        self.assertEqual(memoria.Recuerdo(0).registro(), {"desde": 0})
