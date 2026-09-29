"""migrar: pasa los ensayos de la estructura antigua (experimentos/) a sus laboratorios. No borra nada.

Regla: los de una serie «marcos-*» van a 02-mascaras; el resto, a 01-espejos. Los ya migrados se omiten.
"""
from nucleo import config, ensayos

AYUDA = "copia los ensayos antiguos de experimentos/ a su laboratorio (no borra los originales)"


def asignar(e):
    return "02-mascaras" if (e["config"].get("serie") or "").startswith("marcos-") else "01-espejos"


def configurar(p):
    p.add_argument("--desde", default=str(config.RAIZ / "experimentos"))
    p.add_argument("--sin-consultar", action="store_true", help="no preguntar a Ollama por las instrucciones de fábrica que falten")


def ejecutar(args):
    hechos, omitidos = ensayos.migrar(args.desde, asignar, consultar_modelos=not args.sin_consultar)
    for lab, ids in hechos.items():
        print(f"{lab}: {len(ids)} ensayos migrados")
    if omitidos:
        print(f"{len(omitidos)} omitidos (ya estaban migrados)")
    if not hechos and not omitidos:
        print(f"No hay ensayos en {args.desde}")
    return 0
