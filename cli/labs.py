"""labs: lista los laboratorios o crea uno nuevo."""
import json

from nucleo import ensayos, laboratorios

AYUDA = "lista los laboratorios, o crea uno nuevo con «labs nuevo»"


def configurar(p):
    sub = p.add_subparsers(dest="accion")
    n = sub.add_parser("nuevo", help="crea laboratorios/<id>/ con su lab.json, bitácora y textos")
    n.add_argument("id", help="p. ej. 03-guion (número-nombre)")
    n.add_argument("--nombre", required=True)
    n.add_argument("--pregunta", required=True)
    n.add_argument("--formato", default="chat")
    n.add_argument("--marcos", nargs="+", default=["puro"])
    n.add_argument("--desde", help="copia los valores por defecto y la batería de otro laboratorio")


def ejecutar(args):
    if args.accion == "nuevo":
        return nuevo(args)
    for l in laboratorios.listar():
        es = ensayos.listar(l["id"])
        print(f"{l['id']:<16} {l['nombre']:<12} {l['estado']:<8} {len(es):>3} ensayos · formato {l['formato']} · {l['pregunta']}")
    return 0


def nuevo(args):
    import re
    from nucleo import formatos
    if not re.fullmatch(r"\d{2}-[\w-]+", args.id):
        print("El id debe ser «NN-nombre», por ejemplo 03-guion.")
        return 1
    formatos.obtener(args.formato)
    todos = laboratorios.marcos()
    desconocidos = [m for m in args.marcos if m not in todos]
    if desconocidos:
        print(f"Marcos desconocidos: {desconocidos}. Disponibles: {', '.join(todos)}")
        return 1
    carpeta = laboratorios.carpeta(args.id)
    if carpeta.exists():
        print(f"Ya existe {carpeta}")
        return 1
    base = laboratorios.cargar(args.desde) if args.desde else None
    lab = {
        "id": args.id, "numero": int(args.id[:2]), "nombre": args.nombre, "pregunta": args.pregunta,
        "estado": "abierto", "fechas": {}, "formato": args.formato, "marcos": args.marcos,
        "por_defecto": {**(base["por_defecto"] if base else {
            "modelos": ["or:openai/gpt-4o-mini", "or:openai/gpt-4o-mini"], "semilla": "Hola", "turnos": 12,
            "tokens": 600, "temperatura": 0.8, "memoria": {"tipo": "completa"}}), "marco": args.marcos[0]},
        "bateria": {**(base.get("bateria", {}) if base else {"modelos": ["or:openai/gpt-4o-mini"], "replicas": 3, "turnos": 12, "tokens": 600}),
                    "marcos": args.marcos},
    }
    (carpeta / "ensayos").mkdir(parents=True)
    (carpeta / "lab.json").write_text(json.dumps(lab, ensure_ascii=False, indent=2) + "\n")
    (carpeta / "bitacora.md").write_text(f"# Laboratorio {args.id[:2]} · {args.nombre}\n\n**Pregunta.** {args.pregunta}\n\n## Método\n\n## Resultados\n\n## Conclusiones\n")
    (carpeta / "textos.json").write_text(json.dumps({"orden": [], "fecha": "", "ensayos": {}, "metodo": [], "pie": f"eco loop · laboratorio {args.id[:2]}"},
                                                    ensure_ascii=False, indent=2) + "\n")
    print(f"Creado {carpeta}. Edita su lab.json y lanza ensayos con: python3 -m cli correr --lab {args.id}")
    return 0
