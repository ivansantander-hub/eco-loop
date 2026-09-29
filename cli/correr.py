"""correr: lanza una serie de ensayos con réplicas (marcos × semillas × modelos × réplicas) en un laboratorio.

Usa el núcleo directamente: no hace falta tener el servidor en marcha. Los valores por defecto salen de la
sección «bateria» del lab.json; cualquier opción los sustituye.
"""
import concurrent.futures, datetime, itertools, re

from nucleo import ensayos, laboratorios, motor

AYUDA = "lanza una serie de ensayos con réplicas en un laboratorio (sin servidor)"


def configurar(p):
    p.add_argument("--lab", required=True, help="id del laboratorio, p. ej. 02-mascaras")
    p.add_argument("--marcos", nargs="+")
    p.add_argument("--modelos", nargs="+", help="ids de modelo; las dos IAs usan el mismo (or:openai/gpt-4o-mini, prueba:contador…)")
    p.add_argument("--replicas", type=int)
    p.add_argument("--turnos", type=int)
    p.add_argument("--tokens", type=int)
    p.add_argument("--temp", type=float)
    p.add_argument("--semilla", "--semillas", dest="semillas", nargs="+", help="uno o varios primeros mensajes")
    p.add_argument("--memoria", choices=["completa", "resumen", "ventana"])
    p.add_argument("--recientes", type=int, default=8, help="mensajes literales con memoria resumen o ventana")
    p.add_argument("--serie", help="nombre de la serie (por defecto, <lab>-<fecha>)")
    p.add_argument("--concurrencia", type=int, default=8)
    p.add_argument("--parar-en-bucle", action="store_true", help="corta un ensayo tras 2 copias exactas seguidas")


def plan(args, lab):
    b = lab.get("bateria", {})
    marcos = args.marcos or b.get("marcos") or [lab["por_defecto"]["marco"]]
    modelos = args.modelos or b.get("modelos") or [lab["por_defecto"]["modelos"][0]]
    replicas = args.replicas or b.get("replicas", 1)
    semillas = args.semillas or b.get("semillas") or [lab["por_defecto"]["semilla"]]
    return [(marco, s, semilla, modelo, r) for marco, (s, semilla), modelo, r
            in itertools.product(marcos, enumerate(semillas, 1), modelos, range(1, replicas + 1))], len(semillas)


def opciones_de(args, lab, marco, semilla, modelo, replica, serie, n_semilla=1, varias=False):
    b = lab.get("bateria", {})
    memoria = {"tipo": args.memoria, "recientes": args.recientes} if args.memoria and args.memoria != "completa" else (
        {"tipo": "completa"} if args.memoria else None)
    return {"marco": marco, "modelos": [modelo, modelo], "replica": replica, "serie": serie,
            "turnos": args.turnos or b.get("turnos"), "tokens": args.tokens or b.get("tokens"),
            "temperatura": args.temp, "semilla": semilla, "memoria": memoria,
            "sufijo": re.sub(r"[^\w-]", "", modelo.split("/")[-1].split(":")[-1])[:24] + (f"_s{n_semilla}" if varias else "") + f"_r{replica}",
            "notas": f"Serie «{serie}» (python3 -m cli correr), réplica {replica}."}


def ejecutar(args):
    lab = laboratorios.cargar(args.lab)
    serie = args.serie or f"{args.lab}-{datetime.date.today():%Y-%m-%d}"
    tareas, n_semillas = plan(args, lab)
    print(f"Serie «{serie}» en {args.lab}: {len(tareas)} ensayos", flush=True)

    def uno(tarea):
        marco, n, semilla, modelo, replica = tarea
        e = ensayos.nuevo(args.lab, opciones_de(args, lab, marco, semilla, modelo, replica, serie, n, n_semillas > 1))
        ensayos.guardar(e)
        final = motor.correr(e, parar_en_bucle=args.parar_en_bucle, reintentos=2)
        return e, final

    fallos = 0
    with concurrent.futures.ThreadPoolExecutor(args.concurrencia) as pool:
        for fut in concurrent.futures.as_completed([pool.submit(uno, t) for t in tareas]):
            e, final = fut.result()
            coste = sum(m.get("costo") or 0 for m in e["mensajes"])
            fallos += final.startswith("error")
            print(f"{e['id']}: {len(e['mensajes'])} turnos, ${coste:.4f}" + ("" if final == "fin" else f" · {final}"), flush=True)
    print(f"Listo. Resumen: python3 -m cli analizar --lab {args.lab} --serie {serie}")
    return 1 if fallos else 0
