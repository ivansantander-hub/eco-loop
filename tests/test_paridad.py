"""Paridad con la implementación anterior, sobre los ensayos reales de este equipo.

Se salta si no hay ensayos migrados (p. ej. en un clon del repo, que solo trae los de ejemplo).
- El formato «chat» arma, turno a turno, exactamente los mismos mensajes que el laboratorio y la batería antiguos.
- Si está la versión anterior de analizar.py (variable ECOLOOP_ANALIZAR_ANTIGUO), las medidas coinciden.
"""
import importlib.util, os, unittest
from pathlib import Path

import tests.ayuda  # noqa: F401
from nucleo import config, ensayos, laboratorios, medidas, memoria
from nucleo.formatos import chat

REALES = [e for l in (laboratorios.listar() if (config.LABORATORIOS / "marcos.json").exists() else [])
          for e in ensayos.listar(l["id"]) if e["mensajes"]]


def mensajes_antiguos(e, k):
    """Cómo armaban los mensajes el laboratorio y bateria.py antes de la reestructuración (memoria completa)."""
    i, ia = k % 2, e["config"]["ias"][k % 2]
    return ([{"role": "system", "content": ia["system"]}] if ia.get("system") else []) + \
           ([{"role": "user", "content": e["config"]["semilla"]}] if i == 0 else []) + \
           [{"role": "assistant" if m["autor"] == i else "user", "content": m["texto"]} for m in e["mensajes"][:k]]


@unittest.skipUnless(len(REALES) > 5, "no hay ensayos reales migrados en este equipo")
class Paridad(unittest.TestCase):
    def test_formato_chat_igual_que_antes(self):
        comparados = 0
        for e in REALES:
            if (e["config"].get("memoria") or {}).get("tipo", "completa") != "completa":
                continue
            for k in range(len(e["mensajes"])):
                corto = {**e, "mensajes": e["mensajes"][:k]}
                self.assertEqual(chat.mensajes(corto, k % 2, memoria.Recuerdo(0)), mensajes_antiguos(e, k), f"{e['id']} turno {k + 1}")
                comparados += 1
        self.assertGreater(comparados, 100)

    @unittest.skipUnless(os.environ.get("ECOLOOP_ANALIZAR_ANTIGUO"), "sin la versión anterior de analizar.py")
    def test_medidas_iguales_que_antes(self):
        spec = importlib.util.spec_from_file_location("analizar_antiguo", os.environ["ECOLOOP_ANALIZAR_ANTIGUO"])
        antiguo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(antiguo)
        campos = ["orig_media", "orig_final", "primera_copia", "copias", "casi_copias", "bucle", "asistente", "se_dice_ia",
                  "se_dice_humana", "cortados", "curva"]
        for e in REALES:
            nuevo, viejo = medidas.resumen(e), antiguo.resumen(e)
            for c in campos:
                self.assertEqual(nuevo[c], viejo[c], f"{e['id']}: {c}")
            self.assertAlmostEqual(nuevo["coste"], viejo["coste"], places=9)
