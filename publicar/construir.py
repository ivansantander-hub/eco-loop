#!/usr/bin/env python3
"""Arma el informe de eco loop a partir de plantilla.html, textos.json y los ensayos de experimentos/.

servidor.py lo usa para servir el informe en vivo en «/». Como comando, exporta una copia
estática (sin enlace al laboratorio, que necesita el servidor):

    python3 publicar/construir.py      # crea publicar/eco-loop.html
"""
import json, urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
EXPERIMENTOS = AQUI.parent / "experimentos"


def elegir_ensayos(carpeta=EXPERIMENTOS):
    """Los marcados como «En la página pública»; si no hay, los de textos.json; si tampoco, todos."""
    ensayos = {f.stem: json.loads(f.read_text()) for f in sorted(carpeta.glob("*.json"))}
    ensayos = {i: e for i, e in ensayos.items() if e.get("mensajes")}
    marcados = [i for i, e in ensayos.items() if e.get("publicar")]
    por_defecto = [i for i in json.loads((AQUI / "textos.json").read_text())["orden"] if i in ensayos]
    return [ensayos[i] for i in (marcados or por_defecto or list(ensayos))]


def system_de_fabrica(modelo):
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            "http://localhost:11434/api/show", json.dumps({"model": modelo}).encode()), timeout=3)
        return json.load(r).get("system")
    except Exception:
        return None


def generar_html(carpeta=EXPERIMENTOS, con_laboratorio=False):
    datos = elegir_ensayos(carpeta)
    for e in datos:
        for ia in e["config"]["ias"]:
            # Los primeros ensayos se guardaron antes de registrar este campo: se completa desde Ollama.
            if "system_integrado" not in ia:
                ia["system_integrado"] = system_de_fabrica(ia["modelo"])
        for m in e["mensajes"]:  # solo lo que la página necesita
            m.pop("hora", None)
    textos = json.loads((AQUI / "textos.json").read_text())
    marcos = json.loads((AQUI.parent / "marcos.json").read_text())["marcos"]
    textos["marcos"] = {k: m["nombre"] for k, m in marcos.items()}  # nombres legibles de cada marco
    js = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    return ((AQUI / "plantilla.html").read_text()
            .replace("__DATOS__", js(datos))
            .replace("__TEXTOS__", js(textos))
            .replace("__CON_LABORATORIO__", "true" if con_laboratorio else "false"))


if __name__ == "__main__":
    html = generar_html()
    (AQUI / "eco-loop.html").write_text(html)
    print("ok", len(html) // 1024, "KB → publicar/eco-loop.html")
