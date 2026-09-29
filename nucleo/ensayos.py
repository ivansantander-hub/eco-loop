"""Ensayos: crear, guardar, cargar, listar y migrar.

Un ensayo es un JSON en laboratorios/<lab>/ensayos/<id>.json (más un .md para leerlo). Se reescribe
después de cada turno. `version_esquema` permite migrar ensayos antiguos sin perder nada.
"""
import datetime, json, re
from pathlib import Path

from . import config, laboratorios, proveedores

VERSION_ESQUEMA = 2
ID_VALIDO = re.compile(r"[\w-]+")


def carpeta(lab_id, base=None):
    d = laboratorios.carpeta(lab_id, base) / "ensayos"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _instruccion(plantilla, yo, otra, personalidad):
    if not plantilla:
        return None
    return plantilla.replace("{yo}", yo).replace("{otra}", otra).replace("{personalidad}", personalidad or "").strip()


def nuevo(lab_id, opciones=None, base=None, ahora=None):
    """Crea un ensayo (sin mensajes) a partir de los valores por defecto del laboratorio y `opciones`.

    opciones: marco, modelos [A, B], semilla, turnos, tokens, temperatura, memoria {tipo, recientes},
              nombres [A, B], personalidades [A, B], serie, replica, notas, sufijo
    """
    lab = laboratorios.cargar(lab_id, base)
    o = {**lab["por_defecto"], **{k: v for k, v in (opciones or {}).items() if v is not None}}
    marco_id = o["marco"]
    if marco_id not in lab["marcos"]:
        raise ValueError(f"el marco «{marco_id}» no está permitido en {lab_id} (permitidos: {', '.join(lab['marcos'])})")
    marco = laboratorios.marcos(base)[marco_id]
    modelos = o["modelos"] if isinstance(o["modelos"], list) else [o["modelos"]] * 2
    nombres = o.get("nombres") or ["Nova", "Eco"]
    personalidades = o.get("personalidades") or ["", ""]
    ias = []
    for i, k in enumerate("AB"):
        info = proveedores.info(modelos[i])
        ias.append({
            "etiqueta": nombres[i] if marco.get("usa_nombres") else f"IA {k}",
            "modelo": modelos[i],
            "system": _instruccion(marco[k], nombres[i], nombres[1 - i], personalidades[i]),
            "system_integrado": info["system_integrado"],
        })
    memoria = o.get("memoria") or {"tipo": "completa"}
    if memoria.get("tipo") not in ("completa", "resumen", "ventana"):
        raise ValueError(f"memoria desconocida: {memoria}")
    ahora = ahora or datetime.datetime.now().astimezone()
    base_id = f"{ahora:%Y-%m-%d_%H%M%S}_{marco_id}" + (f"_{o['sufijo']}" if o.get("sufijo") else "")
    base_id = re.sub(r"[^\w-]", "", base_id)
    id_, n = base_id, 2
    while (carpeta(lab_id, base) / f"{id_}.json").exists():
        id_, n = f"{base_id}-{n}", n + 1
    return {
        "id": id_, "laboratorio": lab_id, "version_esquema": VERSION_ESQUEMA,
        "inicio": ahora.isoformat(), "notas": o.get("notas", ""), "publicar": False,
        "config": {
            "formato": lab["formato"], "modo": marco_id, "marco": marco_id,
            "serie": o.get("serie"), "replica": o.get("replica"),
            "semilla": o["semilla"], "turnos": int(o["turnos"]), "temperature": float(o["temperatura"]),
            "num_predict": int(o["tokens"]), "num_ctx": "auto", "think": False, "memoria": memoria,
            "contexto": "la semilla solo la ve A (como user); cada IA ve sus mensajes como assistant y los de la otra "
                        "como user; lo que recuerda depende de «memoria»; si no hay system, Ollama aplica el integrado",
            "ias": ias,
        },
        "mensajes": [],
    }


def ruta(e, base=None):
    return carpeta(e["laboratorio"], base) / f"{e['id']}.json"


def guardar(e, base=None):
    if not ID_VALIDO.fullmatch(e.get("id", "")):
        raise ValueError(f"id inválido: {e.get('id')!r}")
    f = ruta(e, base)
    f.write_text(json.dumps(e, ensure_ascii=False, indent=2))
    f.with_suffix(".md").write_text(a_markdown(e))
    return f


def listar(lab_id, base=None):
    return [json.loads(f.read_text()) for f in sorted(carpeta(lab_id, base).glob("*.json"))]


def cargar(ensayo_id, base=None):
    """Busca el ensayo en todos los laboratorios."""
    if not ID_VALIDO.fullmatch(ensayo_id):
        raise KeyError(ensayo_id)
    for lab in laboratorios.listar(base):
        f = laboratorios.carpeta(lab["id"], base) / "ensayos" / f"{ensayo_id}.json"
        if f.exists():
            return json.loads(f.read_text())
    raise KeyError(ensayo_id)


def normalizar(e, lab_id, consultar_modelos=True):
    """Pone un ensayo antiguo (sin versión) al día con el esquema actual, sin tocar sus mensajes.

    Los primeros ensayos no registraban la instrucción de fábrica del modelo: si falta y `consultar_modelos`,
    se pregunta al proveedor (Ollama) para no perder ese dato.
    """
    e = json.loads(json.dumps(e))
    c = e["config"]
    if "marco" not in c:
        solo_nombres = c["modo"] == "personalidad" and not re.sub(
            r"^Te llamas [^.]*\. Estás conversando con otra IA llamada [^.]*\.", "", c["ias"][0].get("system") or "").strip()
        c["marco"] = "nombres" if solo_nombres else c["modo"]
    c.setdefault("formato", "chat")
    c.setdefault("memoria", {"tipo": "completa"})
    for ia in c["ias"]:
        if "system_integrado" not in ia:
            ia["system_integrado"] = proveedores.info(ia["modelo"])["system_integrado"] if consultar_modelos and ia["modelo"] else None
    e.setdefault("publicar", False)
    e.setdefault("notas", "")
    e["laboratorio"] = lab_id
    e["version_esquema"] = VERSION_ESQUEMA
    return e


def migrar(origen, asignar, base=None, consultar_modelos=True):
    """Copia los ensayos de la carpeta `origen` (formato antiguo) a su laboratorio. No borra los originales.

    asignar(ensayo) -> id del laboratorio, o None para dejarlo fuera.
    Devuelve {lab_id: [ids]} y la lista de ids omitidos (ya existían o sin laboratorio).
    """
    hechos, omitidos = {}, []
    for f in sorted(Path(origen).glob("*.json")):
        e = json.loads(f.read_text())
        lab_id = asignar(e)
        if not lab_id or (carpeta(lab_id, base) / f.name).exists():
            omitidos.append(e["id"])
            continue
        guardar(normalizar(e, lab_id, consultar_modelos), base)
        hechos.setdefault(lab_id, []).append(e["id"])
    return hechos, omitidos


def a_markdown(e):
    c = e["config"]
    mem = c.get("memoria") or {"tipo": "completa"}
    l = [f"# Ensayo {e['id']}", "",
         f"- **Laboratorio:** {e.get('laboratorio')}",
         f"- **Marco:** {c.get('marco') or c['modo']} · **formato:** {c.get('formato', 'chat')}",
         f"- **Inicio:** {e['inicio']}",
         f"- **Primer mensaje (semilla):** {c['semilla']!r}",
         f"- **Parámetros:** temperatura={c['temperature']}, máx. tokens={c['num_predict']}, memoria={mem.get('tipo')}"
         + (f" ({mem.get('recientes')} recientes)" if mem.get("recientes") else ""), ""]
    if c.get("serie"):
        l.insert(3, f"- **Serie:** {c['serie']} · réplica {c.get('replica')}")
    for ia in c["ias"]:
        l.append(f"- **{ia['etiqueta']}** · modelo `{ia['modelo']}` · instrucción: "
                 + (f"\n  > {ia['system']}" if ia.get("system") else "_ninguna_"))
        if ia.get("system_integrado"):
            l.append("  - instrucción de fábrica del modelo" + (" (sustituida por la anterior)" if ia.get("system") else " **(aplicada)**")
                     + f":\n    > {ia['system_integrado']}")
    if e.get("notas"):
        l += ["", "## Notas", "", e["notas"]]
    l += ["", "## Conversación", ""]
    for m in e["mensajes"]:
        extra = f" _({m['tokens']} tok, {m['segundos']} s)_" if m.get("tokens") else ""
        l += [f"**{m['etiqueta']}**{extra}:", "", m["texto"], ""]
    return "\n".join(l)
