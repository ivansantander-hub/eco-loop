#!/usr/bin/env python3
"""Genera 'eco-loop.html' a partir de plantilla.html, textos.json y ../experimentos/*.json."""
import json, urllib.request
from pathlib import Path

AQUI = Path(__file__).parent
# Entran los ensayos marcados como "publicar" en el laboratorio; si no hay ninguno, el orden de textos.json.
marcados = sorted(f.stem for f in (AQUI.parent / "experimentos").glob("*.json")
                  if json.loads(f.read_text()).get("publicar"))
ids = marcados or json.loads((AQUI / "textos.json").read_text())["orden"]
ids = [i for i in ids if (AQUI.parent / "experimentos" / f"{i}.json").exists()]  # solo los que hay en este equipo
datos = [json.loads((AQUI.parent / "experimentos" / f"{i}.json").read_text()) for i in ids]
def system_de_fabrica(modelo):
    r = urllib.request.urlopen(urllib.request.Request("http://localhost:11434/api/show",
                               json.dumps({"model": modelo}).encode()))
    return json.load(r).get("system")

for e in datos:
    for ia in e["config"]["ias"]:
        # Los primeros experimentos se guardaron antes de registrar este campo: se completa desde Ollama.
        if "system_integrado" not in ia:
            ia["system_integrado"] = system_de_fabrica(ia["modelo"])
    for m in e["mensajes"]:  # solo lo que la página necesita
        m.pop("hora", None)
textos = json.loads((AQUI / "textos.json").read_text())
html = (AQUI / "plantilla.html").read_text()
js = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
html = html.replace("__DATOS__", js(datos)).replace("__TEXTOS__", js(textos))
(AQUI / "eco-loop.html").write_text(html)
print("ok", len(html) // 1024, "KB")
