"""Utilidades comunes de las pruebas: laboratorios temporales y el proveedor falso «prueba:»."""
import json, os, shutil, tempfile, unittest
from pathlib import Path

os.environ["ECOLOOP_PRUEBA"] = "1"

from nucleo import config, proveedores  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
LAB = "90-prueba"


def lab_def(**cambios):
    lab = {
        "id": LAB, "numero": 90, "nombre": "Prueba", "pregunta": "¿Funciona todo?", "estado": "abierto",
        "formato": "chat", "marcos": ["puro", "humana", "nombres", "personalidad"],
        "por_defecto": {"marco": "puro", "modelos": ["prueba:contador", "prueba:contador"], "semilla": "Hola",
                        "turnos": 4, "tokens": 50, "temperatura": 0.8, "memoria": {"tipo": "completa"}},
        "bateria": {"marcos": ["puro", "humana"], "modelos": ["prueba:contador"], "replicas": 2, "turnos": 4, "tokens": 50},
    }
    lab.update(cambios)
    return lab


class ConLaboratorio(unittest.TestCase):
    """Cada prueba trabaja en una carpeta temporal con marcos.json y un laboratorio «90-prueba»."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="ecoloop-"))
        shutil.copy(RAIZ / "laboratorios" / "marcos.json", self.base / "marcos.json")
        (self.base / LAB / "ensayos").mkdir(parents=True)
        (self.base / LAB / "lab.json").write_text(json.dumps(lab_def(), ensure_ascii=False))
        self.prueba = proveedores.Prueba()
        proveedores.registrar("prueba", self.prueba)
        self._laboratorios = config.LABORATORIOS
        config.LABORATORIOS = self.base   # los comandos usan la carpeta por defecto

    def tearDown(self):
        config.LABORATORIOS = self._laboratorios
        shutil.rmtree(self.base, ignore_errors=True)


def mensaje(autor, texto, **extra):
    return {"autor": autor, "etiqueta": f"IA {'AB'[autor]}", "modelo": "prueba:contador", "texto": texto, **extra}


def ensayo_de(textos, semilla="Hola", **config_extra):
    """Un ensayo mínimo en memoria con esos mensajes (alternando A y B)."""
    return {"id": "e", "laboratorio": LAB, "mensajes": [mensaje(k % 2, t) for k, t in enumerate(textos)],
            "config": {"semilla": semilla, "modo": "puro", "marco": "puro", "num_predict": 50, "temperature": 0.8,
                       "turnos": len(textos), "memoria": {"tipo": "completa"},
                       "ias": [{"etiqueta": "IA A", "modelo": "prueba:contador", "system": None, "system_integrado": None},
                               {"etiqueta": "IA B", "modelo": "prueba:contador", "system": None, "system_integrado": None}],
                       **config_extra}}
