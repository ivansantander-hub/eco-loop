"""Rutas y configuración compartidas. Todo se puede cambiar con variables de entorno."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _cargar_env():
    """Lee KEY=valor de .env (si existe) sin pisar variables ya definidas."""
    f = RAIZ / ".env"
    if f.exists():
        for linea in f.read_text().splitlines():
            if "=" in linea and not linea.lstrip().startswith("#"):
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_cargar_env()

LABORATORIOS = Path(os.environ.get("ECOLOOP_LABORATORIOS", RAIZ / "laboratorios"))
WEB = RAIZ / "web"
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OPENROUTER = "https://openrouter.ai/api/v1"
PUERTO = int(os.environ.get("PUERTO", 8765))
# Con ECOLOOP_PRUEBA=1 se habilita el proveedor falso «prueba:» (sin red, determinista).
PRUEBA = os.environ.get("ECOLOOP_PRUEBA") == "1"


def clave_openrouter():
    return os.environ.get("OPENROUTER_API_KEY", "")
