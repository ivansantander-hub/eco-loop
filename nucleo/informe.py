"""Páginas de resultados: la evidencia de cada laboratorio y el resumen general de la app.

Laboratorio (web/informe.html):
  - evidencia(): cifras, resultados agregados por marco y por marco × modelo, todos los ensayos y la bitácora.
  - datos(): los ensayos destacados, con las medidas de cada mensaje (para leerlos y reproducirlos).
    Qué ensayos se destacan: los marcados «En el informe» (publicar); si no hay, los de `orden` en textos.json;
    si tampoco existen (p. ej. en un clon del repo), todos los que haya.
App (web/portada.html, vía /api/app): app() con las cifras de todos los laboratorios y las conclusiones generales.
"""
import json, re, statistics
from collections import defaultdict

from . import config, ensayos, laboratorios, medidas

REPO = "https://github.com/ivansantander-hub/eco-loop/blob/main"


def valido(e):
    """Un ensayo cuenta si tiene al menos un mensaje con texto (se descartan los de respuestas vacías)."""
    return any(m["texto"].strip() for m in e["mensajes"])


def elegir(lab_id, base=None):
    todos = {e["id"]: e for e in ensayos.listar(lab_id, base) if valido(e)}
    marcados = [i for i, e in todos.items() if e.get("publicar")]
    por_defecto = [i for i in laboratorios.textos(lab_id, base).get("orden", []) if i in todos]
    return [todos[i] for i in (marcados or por_defecto or sorted(todos))]


def datos(lab_id, base=None):
    """Ensayos destacados, con las medidas de cada mensaje ya calculadas."""
    salida = []
    for e in elegir(lab_id, base):
        e = json.loads(json.dumps(e))
        for k, m in enumerate(e["mensajes"]):
            m["medidas"] = medidas.del_mensaje(e, k)
            m.pop("hora", None)
        e.pop("memoria", None)
        salida.append(e)
    return salida


# ---------- evidencia ----------
def _media(valores):
    v = [x for x in valores if x is not None]
    return round(statistics.mean(v), 1) if v else None


def _sd(valores):
    v = [x for x in valores if x is not None]
    return round(statistics.stdev(v), 1) if len(v) > 1 else None


def agregar(filas):
    """Medias de un grupo de ensayos (réplicas): lo que se dibuja en la página de resultados."""
    turnos = sum(f["turnos"] for f in filas)
    ambas = lambda campo: [statistics.mean([x for x in f[campo].values() if x is not None]) if any(
        x is not None for x in f[campo].values()) else None for f in filas]
    return {
        "ensayos": len(filas), "turnos": turnos,
        "originalidad": _media(f["orig_media"] for f in filas), "originalidad_sd": _sd(f["orig_media"] for f in filas),
        "originalidad_final": _media(f["orig_final"] for f in filas),
        "bucle": round(100 * sum(f["bucle"] for f in filas) / len(filas)), "con_bucle": sum(f["bucle"] for f in filas),
        "asistente": _media(ambas("asistente")),
        "asistente_ab": [_media(f["asistente"]["A"] for f in filas), _media(f["asistente"]["B"] for f in filas)],
        "se_dice_ia": _media(ambas("se_dice_ia")),
        "se_dice_ia_ab": [_media(f["se_dice_ia"]["A"] for f in filas), _media(f["se_dice_ia"]["B"] for f in filas)],
        "cortados": round(100 * sum(f["cortados"] for f in filas) / turnos) if turnos else 0,
        "coste": round(sum(f["coste"] for f in filas), 4),
    }


def _enlaces_web(md, lab_id):
    """Los enlaces relativos de una bitácora apuntan a archivos del repo: en la web, a su página o a GitHub."""
    def cambiar(m):
        texto, url = m.group(1), m.group(2)
        if re.match(r"https?://|/|#", url):
            return m.group(0)
        otro = re.fullmatch(r"\.\./([\w-]+)/bitacora\.md", url)
        if otro:
            return f"[{texto}](/lab/{otro.group(1)})"
        destino = re.sub(r"(^|/)\./", r"\1", f"laboratorios/{lab_id}/{url}")
        while "/../" in destino:
            destino = re.sub(r"[^/]+/\.\./", "", destino, count=1)
        return f"[{texto}]({REPO}/{destino})"
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", cambiar, md)


def secciones(md):
    """{título de sección ##: contenido} de un Markdown."""
    partes, actual = {}, None
    for linea in md.splitlines():
        if linea.startswith("## "):
            actual = linea[3:].strip()
            partes[actual] = []
        elif actual:
            partes[actual].append(linea)
    return {k: "\n".join(v).strip() for k, v in partes.items()}


def evidencia(lab_id, base=None):
    lab = laboratorios.cargar(lab_id, base)
    marcos = laboratorios.marcos(base)
    todos = [e for e in ensayos.listar(lab_id, base) if e["mensajes"]]
    es = [e for e in todos if valido(e)]
    filas = [medidas.resumen(e) for e in es]
    destacados = {e["id"] for e in elegir(lab_id, base)}
    orden = lab["marcos"] + sorted({f["marco"] for f in filas} - set(lab["marcos"]))

    por_marco = defaultdict(list)
    por_marco_modelo = defaultdict(list)
    for f in filas:
        por_marco[f["marco"]].append(f)
        por_marco_modelo[(f["marco"], f["modelos"])].append(f)

    nombre = lambda k: marcos.get(k, {}).get("nombre", k)
    ruta = laboratorios.carpeta(lab_id, base) / "bitacora.md"
    bitacora = _enlaces_web(ruta.read_text(), lab_id) if ruta.exists() else ""
    partes = secciones(bitacora)
    modelos = sorted({m for f in filas for m in f["modelos"].replace(" ×2", "").split(" vs ") if m.strip()})
    return {
        "totales": {"ensayos": len(filas), "mensajes": sum(f["turnos"] for f in filas), "modelos": modelos,
                    "coste": round(sum(f["coste"] for f in filas), 4), "series": sorted({f["serie"] for f in filas if f["serie"]}),
                    "originalidad": _media(f["orig_media"] for f in filas),
                    "bucle": round(100 * sum(f["bucle"] for f in filas) / len(filas)) if filas else 0,
                    "descartados": len(todos) - len(es)},
        "por_marco": [{"marco": k, "nombre": nombre(k), "ayuda": marcos.get(k, {}).get("ayuda", ""), **agregar(por_marco[k])}
                      for k in orden if por_marco[k]],
        "por_marco_modelo": [{"marco": k, "nombre": nombre(k), "modelos": mod, **agregar(rs)}
                             for (k, mod), rs in sorted(por_marco_modelo.items(), key=lambda x: (orden.index(x[0][0]), x[0][1]))],
        "ensayos": [{"id": f["id"], "marco": f["marco"], "nombre_marco": nombre(f["marco"]), "modelos": f["modelos"],
                     "semilla": f["semilla"], "turnos": f["turnos"], "originalidad": f["orig_media"], "bucle": f["bucle"],
                     "copias": f["copias"], "casi_copias": f["casi_copias"], "cortados": f["cortados"], "coste": f["coste"],
                     "serie": f["serie"], "replica": f["replica"], "destacado": f["id"] in destacados,
                     "de_fabrica": f["de_fabrica"]} for f in filas],
        "conclusiones": partes.get("Conclusiones", ""),
        "bitacora": bitacora,
    }


def app(base=None):
    """Cifras de todos los laboratorios y las conclusiones generales (del README) para la portada."""
    labs, total = [], {"laboratorios": 0, "ensayos": 0, "mensajes": 0, "coste": 0.0, "modelos": set()}
    for lab in laboratorios.listar(base):
        es = [e for e in ensayos.listar(lab["id"], base) if e["mensajes"] and valido(e)]
        filas = [medidas.resumen(e) for e in es]
        mods = {m for f in filas for m in f["modelos"].replace(" ×2", "").split(" vs ") if m.strip()}
        resumen = {"ensayos": len(filas), "mensajes": sum(f["turnos"] for f in filas),
                   "coste": round(sum(f["coste"] for f in filas), 4), "modelos": sorted(mods),
                   "bucle": round(100 * sum(f["bucle"] for f in filas) / len(filas)) if filas else 0,
                   "marcos": len({f["marco"] for f in filas})}
        labs.append({**lab, "resumen": resumen})
        total["laboratorios"] += 1
        total["ensayos"] += resumen["ensayos"]
        total["mensajes"] += resumen["mensajes"]
        total["coste"] += resumen["coste"]
        total["modelos"] |= mods
    total["coste"] = round(total["coste"], 4)
    total["modelos"] = sorted(total["modelos"])
    readme = (config.RAIZ / "README.md").read_text() if (config.RAIZ / "README.md").exists() else ""
    conclusiones = secciones(readme).get("Conclusiones hasta ahora", "")
    proximos = ""
    if "**Próximos" in conclusiones:
        conclusiones, proximos = conclusiones.split("**Próximos", 1)
        proximos = "**Próximos" + proximos.split("\n---")[0]
    limpiar = lambda md: re.sub(r"\[([^\]]+)\]\((laboratorios/([\w-]+)/bitacora\.md)\)", r"[\1](/lab/\3)", md).strip()
    return {"totales": total, "laboratorios": labs, "conclusiones": limpiar(conclusiones), "proximos": limpiar(proximos)}


def html(lab_id, servido=True, base=None):
    """HTML de la página del laboratorio. Servido: carga /comun.js y enlaza al banco. Estático: todo en un archivo."""
    lab = laboratorios.cargar(lab_id, base)
    textos = {**laboratorios.textos(lab_id, base),
              "marcos": {k: m["nombre"] for k, m in laboratorios.marcos(base).items()}}
    js = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    comun = '<script src="/comun.js"></script>' if servido else f"<script>\n{(config.WEB / 'comun.js').read_text()}\n</script>"
    return ((config.WEB / "informe.html").read_text()
            .replace("__TITULO__", f"{lab['nombre']} · eco loop")
            .replace("<!-- __COMUN__ -->", comun)
            .replace("__DATOS__", js(datos(lab_id, base)))
            .replace("__EVIDENCIA__", js(evidencia(lab_id, base)))
            .replace("__TEXTOS__", js(textos))
            .replace("__LAB__", js(lab))
            .replace("__SERVIDO__", "true" if servido else "false"))
