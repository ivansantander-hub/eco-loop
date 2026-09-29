"""analizar: tablas Markdown con las medidas de los ensayos de un laboratorio."""
from nucleo import ensayos, laboratorios, medidas

AYUDA = "tablas con las medidas de los ensayos de un laboratorio (o de una serie, agregada por marco y modelo)"


def configurar(p):
    p.add_argument("--lab", required=True)
    p.add_argument("--serie", help="agrega por marco y modelo (media ± desviación entre réplicas)")
    p.add_argument("filtro", nargs="?", default="", help="solo ensayos cuyo id contenga este texto")
    p.add_argument("--curvas", action="store_true", help="además, la originalidad turno a turno de cada ensayo")


def ejecutar(args):
    laboratorios.cargar(args.lab)
    filas = [medidas.resumen(e) for e in ensayos.listar(args.lab) if args.filtro in e["id"] and e["mensajes"]]
    if args.serie:
        filas = [f for f in filas if f["serie"] == args.serie]
        if not filas:
            print(f"No hay ensayos de la serie «{args.serie}» en {args.lab}.")
            return 1
        print(medidas.tabla_agregada(filas))
    else:
        print(medidas.tabla_ensayos(filas))
    if args.curvas:
        print()
        for f in filas:
            print(f["id"], "curva:", f["curva"])
    return 0
