#!/usr/bin/env python3
"""Resume los ensayos de experimentos/ en tablas Markdown.

Usa las mismas medidas que el laboratorio. Uso:
    python3 herramientas/analizar.py                  # tabla de todos los ensayos
    python3 herramientas/analizar.py 2026-09-28       # solo los ids que contengan ese texto
    python3 herramientas/analizar.py --serie marcos-1 # tabla agregada por marco y modelo (réplicas)
La carpeta se puede cambiar con la variable EXPERIMENTOS=/ruta/a/experimentos.
"""
import argparse, difflib, json, os, re, statistics
from collections import defaultdict
from pathlib import Path

EXP = Path(os.environ.get("EXPERIMENTOS", Path(__file__).resolve().parent.parent / "experimentos"))
VACIAS = set(("a al algo algún alguna ante antes aquí así aun aunque cada como con contra cual cuando de del desde donde dos e el ella ellas ello ellos en entre era eres es esa esas ese eso esos esta está están estas este esto estos estoy fue ha han has hay he la las le les lo los más me mi mí mis muy nada ni no nos o os otra otro para pero poco por porque qué que quien se sea ser si sí sin sino sobre son soy su sus tal también te ti tan tu tú tus un una uno unos unas y ya yo the and you i to of").split())

# Señales de rol (español e inglés). Son aproximadas: detectan frases típicas, no intenciones.
ASISTENTE = re.compile(r"(en qu[eé]|c[oó]mo) (m[aá]s )?(te |le )?puedo ayudar|puedo ayudarte|estoy aqu[ií] para (ayudar|lo que|asistir)"
                       r"|how (can|may) i (help|assist)|what can i (help|do for you)", re.I)
SE_DICE_IA = re.compile(r"\b(soy|somos|como|siendo) (una |un |dos |unas |unos )?(ias?|inteligencias? artificial(es)?|modelos? de lenguaje|asistentes? virtual(es)?|chatbots?|programas?|máquinas?)\b"
                        r"|\b(nosotr[oa]s,? (las |los )?(ias?|inteligencias|modelos))|\bentre (dos )?(ias|inteligencias artificiales|modelos)\b"
                        r"|\bno tengo (cuerpo|emociones|sentimientos|experiencias personales|recuerdos personales|conciencia)"
                        r"|\b(i('| a)m|we('| a)re) (an? )?(ai|ais|artificial intelligences?|language models?)\b|\bas (an )?ais?\b", re.I)
SE_DICE_HUMANA = re.compile(r"\bsoy (un |una )?(humano|humana|persona real)\b|\bno soy (una |un )?(ia|m[aá]quina|robot|bot)\b"
                            r"|\bi('| a)m (a )?(human|real person)\b", re.I)


def contenido(texto):
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
    copias = [k + 1 for k in range(1, len(textos)) if textos[k] and textos[k] == textos[k - 1]]
    casi = [k + 1 for k in range(1, len(textos))
            if textos[k] != textos[k - 1] and difflib.SequenceMatcher(None, textos[k], textos[k - 1]).ratio() >= .9]
    validos = [o for o in orig if o is not None]
    ultimos = [o for o in orig[-4:] if o is not None]
    modelos = [modelo_corto(i["modelo"]) for i in c["ias"]]
    de_fabrica = any(not i.get("system") and i.get("system_integrado") for i in c["ias"])
    por_ia = {k: [m["texto"] for m in ms if m["autor"] == i] for i, k in enumerate("AB")}
    tasa = lambda patron, k: round(100 * sum(bool(patron.search(t)) for t in por_ia[k]) / len(por_ia[k])) if por_ia[k] else None
    return {
        "id": e["id"], "serie": c.get("serie"), "marco": c.get("marco") or c["modo"], "replica": c.get("replica"),
        "modo": c["modo"] + (" · prompt de fábrica" if de_fabrica else ""),
        "modelos": modelos[0] + " ×2" if modelos[0] == modelos[1] else " vs ".join(modelos),
        "semilla": c["semilla"], "turnos": len(ms),
        "orig_media": round(sum(validos) / len(validos)) if validos else None,
        "orig_final": round(sum(ultimos) / len(ultimos)) if ultimos else None,
        "primera_copia": copias[0] if copias else None, "copias": len(copias), "casi_copias": len(casi),
        "bucle": bool(copias or casi),
        "asistente": {k: tasa(ASISTENTE, k) for k in "AB"},
        "se_dice_ia": {k: tasa(SE_DICE_IA, k) for k in "AB"},
        "se_dice_humana": {k: sum(bool(SE_DICE_HUMANA.search(t)) for t in por_ia[k]) for k in "AB"},
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


def media_sd(valores):
    v = [x for x in valores if x is not None]
    if not v:
        return "—"
    return f"{statistics.mean(v):.0f}" + (f" ± {statistics.stdev(v):.0f}" if len(v) > 1 else "")


def tabla_agregada(filas):
    """Una fila por (marco, modelo): media ± desviación entre réplicas."""
    grupos = defaultdict(list)
    for r in filas:
        grupos[(r["marco"], r["modelos"])].append(r)
    lineas = ["| Marco | Modelos | Réplicas | Originalidad % | Últimos 4 % | Réplicas con bucle | Habla como asistente % (A / B) | Se dice IA % (A / B) | Se dice humana (A / B) | Coste medio |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for (marco, modelos), rs in sorted(grupos.items()):
        prom = lambda campo, k: media_sd([r[campo][k] for r in rs])
        lineas.append(
            f"| {marco} | {modelos} | {len(rs)} | {media_sd([r['orig_media'] for r in rs])} | {media_sd([r['orig_final'] for r in rs])} | "
            f"{sum(r['bucle'] for r in rs)} de {len(rs)} | {prom('asistente', 'A')} / {prom('asistente', 'B')} | "
            f"{prom('se_dice_ia', 'A')} / {prom('se_dice_ia', 'B')} | "
            f"{sum(r['se_dice_humana']['A'] for r in rs)} / {sum(r['se_dice_humana']['B'] for r in rs)} | "
            f"${statistics.mean(r['coste'] for r in rs):.4f} |")
    return "\n".join(lineas)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("filtro", nargs="?", default="", help="solo ensayos cuyo id contenga este texto")
    p.add_argument("--serie", help="agrega por marco y modelo los ensayos de esta serie")
    a = p.parse_args()
    filas = [resumen(json.loads(f.read_text())) for f in sorted(EXP.glob("*.json")) if a.filtro in f.stem]
    filas = [f for f in filas if f["turnos"]]
    if a.serie:
        filas = [f for f in filas if f["serie"] == a.serie]
        print(tabla_agregada(filas))
    else:
        print(tabla(filas))
        print()
        for f in filas:
            print(f["id"], "curva:", f["curva"])
