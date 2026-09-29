"""Laboratorios: cada uno es una carpeta en laboratorios/<id>/ con su definición y sus datos.

    laboratorios/<id>/lab.json       pregunta, formato, qué se puede variar y valores por defecto
    laboratorios/<id>/bitacora.md    su bitácora
    laboratorios/<id>/textos.json    títulos y textos de su informe
    laboratorios/<id>/ensayos/       sus ensayos (JSON + Markdown)
    laboratorios/marcos.json         marcos de conversación compartidos por todos
"""
import json
from pathlib import Path

from . import config

CAMPOS = ("id", "numero", "nombre", "pregunta", "estado", "formato", "marcos", "por_defecto")


class LaboratorioNoEncontrado(KeyError):
    pass


def carpeta(lab_id, base=None):
    return Path(base or config.LABORATORIOS) / lab_id


def marcos(base=None):
    return json.loads((Path(base or config.LABORATORIOS) / "marcos.json").read_text())["marcos"]


def cargar(lab_id, base=None):
    f = carpeta(lab_id, base) / "lab.json"
    if not f.exists():
        raise LaboratorioNoEncontrado(lab_id)
    lab = json.loads(f.read_text())
    faltan = [c for c in CAMPOS if c not in lab]
    if faltan:
        raise ValueError(f"{f}: faltan los campos {faltan}")
    if lab["id"] != lab_id:
        raise ValueError(f"{f}: el id «{lab['id']}» no coincide con la carpeta «{lab_id}»")
    return lab


def listar(base=None):
    base = Path(base or config.LABORATORIOS)
    labs = [cargar(d.name, base) for d in sorted(base.iterdir()) if (d / "lab.json").exists()]
    return sorted(labs, key=lambda l: l["numero"])


def textos(lab_id, base=None):
    f = carpeta(lab_id, base) / "textos.json"
    return json.loads(f.read_text()) if f.exists() else {"orden": [], "ensayos": {}, "metodo": [], "pie": ""}
