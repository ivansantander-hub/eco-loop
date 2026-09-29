"""Medidas de una conversación. Es la única implementación: la web recibe los valores ya calculados."""
import difflib, re, statistics
from collections import defaultdict

VACIAS = set(("a al algo algún alguna ante antes aquí así aun aunque cada como con contra cual cuando de del desde donde "
              "dos e el ella ellas ello ellos en entre era eres es esa esas ese eso esos esta está están estas este esto "
              "estos estoy fue ha han has hay he la las le les lo los más me mi mí mis muy nada ni no nos o os otra otro "
              "para pero poco por porque qué que quien se sea ser si sí sin sino sobre son soy su sus tal también te ti "
              "tan tu tú tus un una uno unos unas y ya yo the and you i to of").split())

# Señales de rol (español e inglés). Son aproximadas: detectan frases típicas, no intenciones.
ASISTENTE = re.compile(r"(en qu[eé]|c[oó]mo) (m[aá]s )?(te |le )?puedo ayudar|puedo ayudarte|estoy aqu[ií] para (ayudar|lo que|asistir)"
                       r"|how (can|may) i (help|assist)|what can i (help|do for you)", re.I)
SE_DICE_IA = re.compile(r"\b(soy|somos|como|siendo) (una |un |dos |unas |unos )?(ias?|inteligencias? artificial(es)?|modelos? de lenguaje|asistentes? virtual(es)?|chatbots?|programas?|máquinas?)\b"
                        r"|\b(nosotr[oa]s,? (las |los )?(ias?|inteligencias|modelos))|\bentre (dos )?(ias|inteligencias artificiales|modelos)\b"
                        r"|\bno tengo (cuerpo|emociones|sentimientos|experiencias personales|recuerdos personales|conciencia)"
                        r"|\b(i('| a)m|we('| a)re) (an? )?(ai|ais|artificial intelligences?|language models?)\b|\bas (an )?ais?\b", re.I)
SE_DICE_HUMANA = re.compile(r"\bsoy (un |una )?(humano|humana|persona real)\b|\bno soy (una |un )?(ia|m[aá]quina|robot|bot)\b"
                            r"|\bi('| a)m (a )?(human|real person)\b", re.I)
DEGENERADO = re.compile(r"(^|\s)(\S{1,20})(\s+\2){15,}")
# Adulación: elogios del tipo «¡Excelente…!», «¡Qué buena pregunta!».
ADULACION = re.compile(r"¡\s*(excelente|fant[aá]stic|magn[ií]fic|genial|maravillos|impecable|brillante|estupend|incre[ií]ble|perfecto|me encanta)"
                       r"|¡\s*qu[eé] (buena|gran|hermos|lind|interesante|bonit|maravillos|fascinante|profund)"
                       r"|\b(qu[eé]|muy) (buena|excelente|interesante|fascinante) (pregunta|reflexi[oó]n|idea|observaci[oó]n|punto)"
                       r"|\b(excellent|fantastic|wonderful|brilliant|great) (question|point|idea|insight)|what a (great|wonderful|fascinating)", re.I)
# Pedir algo como lo haría un usuario (para detectar quién «cede» y deja de ser asistente).
PIDE = re.compile(r"\bme gustar[ií]a (que me|saber|aprender|hablar de|conocer|pedirte)|¿(me )?(podr[ií]as|puedes) (ayudarme|recomendarme|explicarme|contarme|darme|sugerirme)"
                  r"|\bnecesito (ayuda|que|un|una|consejo)|\bquiero (saber|aprender|que me)|\btengo (una duda|una pregunta|curiosidad)"
                  r"|\bestoy (buscando|pensando en|intentando|investigando)|\b(recomi[eé]ndame|ay[uú]dame|expl[ií]came|cu[eé]ntame)"
                  r"|\bi('d| would) like (to know|to learn|to ask|to talk about|you to|some|a recommendation|help|advice)"
                  r"|\bcan you (help me|recommend|explain|tell me)|\bi need (help|advice|a)|\bi'm (looking for|trying to)", re.I)
# Para la cesión, «ofrecer ayuda» es algo más amplio que ASISTENTE (que no se toca, para no cambiar esa medida).
OFRECE = re.compile(ASISTENTE.pattern + r"|\bi'?m here to (help|assist)|\bhere to help|\bestoy (aqu[ií] )?para (servirte|ayudarte)", re.I)
_EN = set("the and you are is to of that it for with this what have your be can will about i'm it's don't".split())
_ES = set("el la los las que de y es en un una por para con no se lo como más pero sus qué está muy también".split())


def norm(palabra):
    """Minúsculas y solo letras y números (igual que `norm` en web/comun.js)."""
    return re.sub(r"[\W_]", "", palabra.lower())


def contenido(texto):
    """Palabras con contenido: más de 2 letras y sin palabras vacías."""
    return [w for w in (norm(p) for p in texto.split()) if len(w) > 2 and w not in VACIAS]


def previo(ensayo, k):
    """Lo que la otra IA dijo justo antes del mensaje k (para el primero, el primer mensaje del ensayo)."""
    return ensayo["config"]["semilla"] if k == 0 else ensayo["mensajes"][k - 1]["texto"]


def originalidad(texto, anterior):
    """% de palabras con contenido de `texto` que no estaban en `anterior`. None si no tiene ninguna."""
    previas, propias = set(contenido(anterior)), contenido(texto)
    return round(100 * sum(w not in previas for w in propias) / len(propias)) if propias else None


def copiadas(texto, anterior):
    """Palabras (normalizadas) de `texto` que venían de `anterior`: la web las pinta con el color de la otra IA."""
    previas = set(contenido(anterior))
    return sorted({w for w in contenido(texto) if w in previas})


def banderas(ensayo, k):
    """Alertas de un mensaje: [{"tipo", "texto"}]."""
    ms, m = ensayo["mensajes"], ensayo["mensajes"][k]
    c, f = ensayo["config"], []
    if k > 0 and m["texto"] and m["texto"] == ms[k - 1]["texto"]:
        f.append({"tipo": "copia", "texto": f"copia exacta del turno {k:02d}"})
    elif k > 1 and m["texto"] and m["texto"] == ms[k - 2]["texto"]:
        f.append({"tipo": "repite", "texto": "repite su propio mensaje anterior"})
    if not m["texto"].strip():
        f.append({"tipo": "vacio", "texto": "respuesta vacía: revisa que el modelo exista y responda"})
    d = DEGENERADO.search(m["texto"])
    if d:
        f.append({"tipo": "degenerado", "texto": f"texto degenerado: repite «{d.group(2)}» en cadena"})
    if m.get("cortado"):
        f.append({"tipo": "corte", "texto": f"cortado al llegar a {c['num_predict']} tokens"})
    etiqueta = m.get("etiqueta", "")
    if etiqueta and not re.fullmatch(r"IA [AB]", etiqueta) and re.search(rf"\b{re.escape(etiqueta)}\b", m["texto"]):
        f.append({"tipo": "nombre", "texto": f"se llama a sí misma «{etiqueta}»"})
    mem = m.get("memoria") or {}
    ctx = mem.get("ctx") or {}
    if ctx.get("max") and ctx.get("estimado", 0) > ctx["max"]:
        f.append({"tipo": "desborde", "texto": f"la conversación ya no cabía en su memoria (≈{ctx['estimado']} de {ctx['max']} tokens): "
                                               "olvidó el principio. Usa «Resumen + recientes»"})
    if mem.get("resumen_hasta"):
        f.append({"tipo": "memoria", "texto": f"recordaba un resumen de los mensajes 1–{mem['resumen_hasta']} y el resto literal"})
    elif mem.get("desde"):
        f.append({"tipo": "memoria", "texto": f"solo recordaba desde el mensaje {mem['desde'] + 1}"})
    return f


def del_mensaje(ensayo, k):
    """Todo lo que la web necesita de un mensaje ya calculado."""
    texto, ant = ensayo["mensajes"][k]["texto"], previo(ensayo, k)
    return {"originalidad": originalidad(texto, ant), "copiadas": copiadas(texto, ant), "banderas": banderas(ensayo, k)}


def copias_seguidas(ensayo):
    """Cuántas copias exactas seguidas hay al final (para «parar si entran en bucle»)."""
    ms, n = ensayo["mensajes"], 0
    for k in range(len(ms) - 1, 0, -1):
        if ms[k]["texto"] and ms[k]["texto"] == ms[k - 1]["texto"]:
            n += 1
        else:
            break
    return n


def modelo_corto(m):
    """«or:openai/gpt-4o-mini» → «☁ gpt-4o-mini»; «huihui_ai/qwen3-abliterated:14b» → «qwen3-abliterated:14b»."""
    if m.startswith("or:"):
        return "☁ " + m[3:].split("/")[-1]
    return m.split("/")[-1]


def en_ingles(texto):
    """True si el mensaje está escrito sobre todo en inglés (se cuentan palabras funcionales de cada idioma)."""
    palabras = [p.lower().strip("¿?¡!.,;:«»\"'()*") for p in texto.split()]
    en, es = sum(p in _EN for p in palabras), sum(p in _ES for p in palabras)
    return en >= 3 and en > es


def cesion(ensayo):
    """Primer turno en que una IA deja de ofrecer ayuda y pide algo, como haría un usuario.

    {"quien": "A" | "B", "turno": k (1-indexado)}, o None si nadie cede. Es una heurística: cuenta un mensaje
    que pide algo (PIDE) sin ofrecer ayuda (OFRECE). Detecta frases, no intenciones.
    """
    for k, m in enumerate(ensayo["mensajes"]):
        if PIDE.search(m["texto"]) and not OFRECE.search(m["texto"]):
            return {"quien": "AB"[m["autor"]], "turno": k + 1}
    return None


def resumen(e):
    """Medidas de un ensayo completo (para tablas, el informe y la tira de ensayos)."""
    c, ms = e["config"], e["mensajes"]
    textos = [m["texto"] for m in ms]
    orig = [originalidad(t, previo(e, k)) for k, t in enumerate(textos)]
    copias = [k + 1 for k in range(1, len(textos)) if textos[k] and textos[k] == textos[k - 1]]
    casi = [k + 1 for k in range(1, len(textos))
            if textos[k] != textos[k - 1] and difflib.SequenceMatcher(None, textos[k], textos[k - 1]).ratio() >= .9]
    validos = [o for o in orig if o is not None]
    ultimos = [o for o in orig[-4:] if o is not None]
    modelos = [modelo_corto(i["modelo"]) for i in c["ias"]]
    por_ia = {k: [m["texto"] for m in ms if m["autor"] == i] for i, k in enumerate("AB")}
    tasa = lambda patron, k: round(100 * sum(bool(patron.search(t)) for t in por_ia[k]) / len(por_ia[k])) if por_ia[k] else None
    return {
        "id": e["id"], "laboratorio": e.get("laboratorio"), "serie": c.get("serie"), "replica": c.get("replica"),
        "marco": c.get("marco") or c["modo"],
        "de_fabrica": any(not i.get("system") and i.get("system_integrado") for i in c["ias"]),
        "modelos": modelos[0] + " ×2" if modelos[0] == modelos[1] else " vs ".join(modelos),
        "semilla": c["semilla"], "turnos": len(ms), "curva": orig,
        "orig_media": round(sum(validos) / len(validos)) if validos else None,
        "orig_final": round(sum(ultimos) / len(ultimos)) if ultimos else None,
        "primera_copia": copias[0] if copias else None, "copias": len(copias), "casi_copias": len(casi),
        "bucle": bool(copias or casi),
        "en_bucle": len(ultimos) == 4 and all((o or 0) <= 5 for o in orig[-4:]),
        "asistente": {k: tasa(ASISTENTE, k) for k in "AB"},
        "se_dice_ia": {k: tasa(SE_DICE_IA, k) for k in "AB"},
        "se_dice_humana": {k: sum(bool(SE_DICE_HUMANA.search(t)) for t in por_ia[k]) for k in "AB"},
        "adulacion": {k: tasa(ADULACION, k) for k in "AB"},
        "ingles": {k: round(100 * sum(en_ingles(t) for t in por_ia[k]) / len(por_ia[k])) if por_ia[k] else None for k in "AB"},
        "cesion": cesion(e),
        "cortados": sum(bool(m.get("cortado")) for m in ms),
        "coste": sum(m.get("costo") or 0 for m in ms),
    }


def media_sd(valores):
    v = [x for x in valores if x is not None]
    if not v:
        return "—"
    return f"{statistics.mean(v):.0f}" + (f" ± {statistics.stdev(v):.0f}" if len(v) > 1 else "")


def tabla_ensayos(filas):
    lineas = ["| Ensayo | Modelos | Marco | Primer mensaje | Turnos | Originalidad media | Últimos 4 | 1ª copia exacta | Copias / casi copias | Cortados | Coste |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in filas:
        lineas.append(
            f"| `{r['id']}` | {r['modelos']} | {r['marco']}{' · prompt de fábrica' if r['de_fabrica'] else ''} | «{r['semilla']}» | "
            f"{r['turnos']} | {r['orig_media']}% | {r['orig_final']}% | {'turno ' + str(r['primera_copia']) if r['primera_copia'] else '—'} | "
            f"{r['copias']} / {r['casi_copias']} | {r['cortados']} | {'$%.4f' % r['coste'] if r['coste'] else '—'} |")
    return "\n".join(lineas)


def tabla_agregada(filas, por=("marco", "modelos")):
    """Una fila por grupo (por defecto marco y modelos): media ± desviación entre réplicas.

    `por` son campos de resumen(); con por=("marco",) se juntan todos los modelos de cada marco.
    """
    grupos = defaultdict(list)
    for r in filas:
        grupos[tuple(r[c] for c in por)].append(r)
    cab = " | ".join(c.capitalize() for c in por)
    lineas = [f"| {cab} | Ensayos | Originalidad % | Últimos 4 % | Con bucle | Habla como asistente % (A / B) | Se dice IA % (A / B) | "
              "Adulación % (A / B) | En inglés % | Cede el rol | Cortados % | Coste medio |",
              "|" + "---|" * (len(por) + 11)]
    for clave, rs in sorted(grupos.items(), key=lambda kv: [str(x) for x in kv[0]]):
        prom = lambda campo, k: media_sd([r[campo][k] for r in rs])
        ceden = [r["cesion"] for r in rs if r.get("cesion")]
        turnos = sum(r["turnos"] for r in rs)
        ingles = media_sd([statistics.mean([v for v in r["ingles"].values() if v is not None] or [0]) for r in rs])
        lineas.append(
            f"| {' | '.join(str(x) for x in clave)} | {len(rs)} | {media_sd([r['orig_media'] for r in rs])} | {media_sd([r['orig_final'] for r in rs])} | "
            f"{sum(r['bucle'] for r in rs)} de {len(rs)} | {prom('asistente', 'A')} / {prom('asistente', 'B')} | "
            f"{prom('se_dice_ia', 'A')} / {prom('se_dice_ia', 'B')} | {prom('adulacion', 'A')} / {prom('adulacion', 'B')} | {ingles} | "
            f"{len(ceden)} de {len(rs)}" + (f" (turno {statistics.mean(c['turno'] for c in ceden):.1f})" if ceden else "") + " | "
            f"{round(100 * sum(r['cortados'] for r in rs) / turnos) if turnos else 0} | ${statistics.mean(r['coste'] for r in rs):.4f} |")
    return "\n".join(lineas)
