import unittest

from tests.ayuda import ensayo_de
from nucleo import medidas


class Palabras(unittest.TestCase):
    def test_norm_quita_puntuacion_y_mayusculas(self):
        self.assertEqual(medidas.norm("¡Hola!"), "hola")
        self.assertEqual(medidas.norm("**Estudios**"), "estudios")
        self.assertEqual(medidas.norm("día_2"), "día2")

    def test_contenido_quita_palabras_vacias_y_cortas(self):
        self.assertEqual(medidas.contenido("La casa de mi abuela es muy bonita"), ["casa", "abuela", "bonita"])


class Originalidad(unittest.TestCase):
    def test_todo_nuevo(self):
        self.assertEqual(medidas.originalidad("perro gato ratón", "Hola"), 100)

    def test_copia_total(self):
        self.assertEqual(medidas.originalidad("perro gato", "el perro y el gato"), 0)

    def test_mitad(self):
        self.assertEqual(medidas.originalidad("perro gato ratón queso", "perro y gato"), 50)

    def test_sin_contenido(self):
        self.assertIsNone(medidas.originalidad("sí, y tú", "Hola"))

    def test_copiadas(self):
        self.assertEqual(medidas.copiadas("Me gusta tu perro y tu gato", "¿Tienes perro?"), ["perro"])


class Banderas(unittest.TestCase):
    def tipos(self, e, k):
        return [b["tipo"] for b in medidas.banderas(e, k)]

    def test_copia_exacta_y_repeticion_propia(self):
        e = ensayo_de(["Hola a todos", "Hola a todos", "otra cosa", "Hola a todos", "otra cosa"])
        self.assertIn("copia", self.tipos(e, 1))
        self.assertIn("repite", self.tipos(e, 4))

    def test_vacio_degenerado_corte(self):
        e = ensayo_de(["", "A " * 30, "bien"])
        e["mensajes"][2]["cortado"] = True
        self.assertIn("vacio", self.tipos(e, 0))
        self.assertIn("degenerado", self.tipos(e, 1))
        self.assertIn("corte", self.tipos(e, 2))

    def test_se_llama_a_si_misma_solo_con_nombres(self):
        e = ensayo_de(["Hola, soy Nova y tú eres Nova", "Soy IA B"])
        e["mensajes"][0]["etiqueta"] = "Nova"
        self.assertIn("nombre", self.tipos(e, 0))
        self.assertNotIn("nombre", self.tipos(e, 1))   # «IA B» no es un nombre propio

    def test_memoria_y_desborde(self):
        e = ensayo_de(["uno", "dos"])
        e["mensajes"][1]["memoria"] = {"desde": 0, "resumen_hasta": 1, "ctx": {"estimado": 9000, "max": 8192}}
        self.assertEqual(set(self.tipos(e, 1)) & {"memoria", "desborde"}, {"memoria", "desborde"})

    def test_copias_seguidas(self):
        self.assertEqual(medidas.copias_seguidas(ensayo_de(["a b c", "x y z", "x y z", "x y z"])), 2)


class Resumen(unittest.TestCase):
    def test_resumen_de_un_bucle(self):
        r = medidas.resumen(ensayo_de(["¿En qué puedo ayudarte hoy?", "¿En qué puedo ayudarte hoy?"]))
        self.assertTrue(r["bucle"])
        self.assertEqual(r["copias"], 1)
        self.assertEqual(r["asistente"], {"A": 100, "B": 100})

    def test_se_dice_ia_en_plural(self):
        r = medidas.resumen(ensayo_de(["Como inteligencias artificiales, podemos colaborar", "Somos IAs"]))
        self.assertEqual(r["se_dice_ia"], {"A": 100, "B": 100})

    def test_tablas(self):
        filas = [medidas.resumen(ensayo_de(["perro", "gato"]))]
        self.assertIn("| `e` |", medidas.tabla_ensayos(filas))
        self.assertIn("| puro |", medidas.tabla_agregada(filas))

    def test_modelo_corto(self):
        self.assertEqual(medidas.modelo_corto("or:openai/gpt-4o-mini"), "☁ gpt-4o-mini")
        self.assertEqual(medidas.modelo_corto("huihui_ai/qwen3-abliterated:14b"), "qwen3-abliterated:14b")
