"""Informe de un laboratorio: web/informe.html relleno con sus ensayos, textos y medidas.

Qué ensayos entran: los marcados «En el informe» (publicar); si no hay, los de `orden` en textos.json;
si tampoco existen (p. ej. en un clon del repo), todos los que haya.
"""
import json

from . import config, ensayos, laboratorios, medidas


def elegir(lab_id, base=None):
    todos = {e["id"]: e for e in ensayos.listar(lab_id, base) if e["mensajes"]}
    marcados = [i for i, e in todos.items() if e.get("publicar")]
    por_defecto = [i for i in laboratorios.textos(lab_id, base).get("orden", []) if i in todos]
    return [todos[i] for i in (marcados or por_defecto or sorted(todos))]


def datos(lab_id, base=None):
    """Ensayos elegidos, con las medidas de cada mensaje ya calculadas."""
    salida = []
    for e in elegir(lab_id, base):
        e = json.loads(json.dumps(e))
        for k, m in enumerate(e["mensajes"]):
            m["medidas"] = medidas.del_mensaje(e, k)
            m.pop("hora", None)
        e.pop("memoria", None)
        salida.append(e)
    return salida


def html(lab_id, servido=True, base=None):
    """HTML del informe. Servido: carga /comun.js y enlaza al banco. Estático: todo en un archivo."""
    lab = laboratorios.cargar(lab_id, base)
    textos = {**laboratorios.textos(lab_id, base),
              "marcos": {k: m["nombre"] for k, m in laboratorios.marcos(base).items()}}
    js = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    comun = '<script src="/comun.js"></script>' if servido else f"<script>\n{(config.WEB / 'comun.js').read_text()}\n</script>"
    return ((config.WEB / "informe.html").read_text()
            .replace("__TITULO__", f"{lab['nombre']} · eco loop")
            .replace("<!-- __COMUN__ -->", comun)
            .replace("__DATOS__", js(datos(lab_id, base)))
            .replace("__TEXTOS__", js(textos))
            .replace("__LAB__", js(lab))
            .replace("__SERVIDO__", "true" if servido else "false"))
