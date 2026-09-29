#!/usr/bin/env python3
"""Resume los ensayos de experimentos/ en una tabla Markdown.

Usa las mismas medidas que el laboratorio (index.html). Uso:
    python3 herramientas/analizar.py              # todos
    python3 herramientas/analizar.py 2026-09-28   # solo los ids que contengan ese texto
La carpeta se puede cambiar con la variable EXPERIMENTOS=/ruta/a/experimentos.
"""
import difflib, json, os, re, sys
from pathlib import Path

EXP = Path(os.environ.get("EXPERIMENTOS", Path(__file__).resolve().parent.parent / "experimentos"))
VACIAS = set(("a al algo algún alguna ante antes aquí así aun aunque cada como con contra cual cuando de del desde donde dos e el ella ellas ello ellos en entre era eres es esa esas ese eso esos esta está están estas este esto estos estoy fue ha han has hay he la las le les lo los más me mi mí mis muy nada ni no nos o os otra otro para pero poco por porque qué que quien se sea ser si sí sin sino sobre son soy su sus tal también te ti tan tu tú tus un una uno unos unas y ya yo the and you i to of").split())


def contenido(texto):
    """Palabras con contenido, normalizadas igual que en el laboratorio."""
    palabras = (re.sub(r"[^\w]", "", w.lower()) for w in texto.split())
    return [w for w in palabras if len(w) > 2 and w not in VACIAS]


def originalidad(texto, previo):
    previas, propias = set(contenido(previo)), contenido(texto)
    return round(100 * sum(w not in previas for w in propias) / len(propias)) if propias else None


def modelo_corto(m):
    return ("☁ " if m.startswith("or:") else "") + m.removeprefix("or:").split("/")[-1]


def resumen(e):
    c, ms = e["config"], e["mensajes"]
    textos = [m["texto"] for m in ms]
    orig = [originalidad(t, c["semilla"] if k == 0 else textos[k - 1]) for k, t in enumerate(textos)]
    copias = [k + 1 for k in range(1, len(textos)) if textos[k] == textos[k - 1]]
    casi = [k + 1 for k in range(1, len(textos))
            if textos[k] != textos[k - 1] and difflib.SequenceMatcher(None, textos[k], textos[k - 1]).ratio() >= .9]
    validos = [o for o in orig if o is not None]
    ultimos = [o for o in orig[-4:] if o is not None]
    modelos = [modelo_corto(i["modelo"]) for i in c["ias"]]
    de_fabrica = any(not i.get("system") and i.get("system_integrado") for i in c["ias"])
    return {
        "id": e["id"], "modo": c["modo"] + (" · prompt de fábrica" if de_fabrica else ""),
        "modelos": modelos[0] + " ×2" if modelos[0] == modelos[1] else " vs ".join(modelos),
        "semilla": c["semilla"], "turnos": len(ms),
        "orig_media": round(sum(validos) / len(validos)) if validos else None,
        "orig_final": round(sum(ultimos) / len(ultimos)) if ultimos else None,
        "primera_copia": copias[0] if copias else None, "copias": len(copias), "casi_copias": len(casi),
        "cortados": sum(bool(m.get("cortado")) for m in ms),
        "coste": sum(m.get("costo") or 0 for m in ms),
        "curva": orig,
    }


def tabla(filas):
    lineas = ["| Ensayo | Modelos | Modo | Primer mensaje | Turnos | Originalidad media | Últimos 4 | 1ª copia exacta | Copias / casi copias | Cortados | Coste |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in filas:
        lineas.append(
            f"| `{r['id']}` | {r['modelos']} | {r['modo']} | «{r['semilla']}» | {r['turnos']} | {r['orig_media']}% | "
            f"{r['orig_final']}% | {'turno ' + str(r['primera_copia']) if r['primera_copia'] else '—'} | "
            f"{r['copias']} / {r['casi_copias']} | {r['cortados']} | {'$%.4f' % r['coste'] if r['coste'] else '—'} |")
    return "\n".join(lineas)


if __name__ == "__main__":
    filtro = sys.argv[1] if len(sys.argv) > 1 else ""
    filas = [resumen(json.loads(f.read_text())) for f in sorted(EXP.glob("*.json")) if filtro in f.stem]
    filas = [f for f in filas if f["turnos"]]
    print(tabla(filas))
    print()
    for f in filas:
        print(f["id"], "curva:", f["curva"])
