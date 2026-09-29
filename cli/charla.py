"""charla: una conversación en la terminal, en vivo, guardada en el laboratorio."""
import sys

from nucleo import ensayos, laboratorios, motor

AYUDA = "una conversación en la terminal, en vivo (se guarda en el laboratorio)"
COLORES = ["\033[96m", "\033[93m"]


def configurar(p):
    p.add_argument("semilla", nargs="?", help="primer mensaje (por defecto, el del laboratorio)")
    p.add_argument("--lab", required=True)
    p.add_argument("--marco")
    p.add_argument("--modelo", help="el mismo modelo para las dos IAs")
    p.add_argument("--modelos", nargs=2, metavar=("A", "B"))
    p.add_argument("-t", "--turnos", type=int)
    p.add_argument("--tokens", type=int)
    p.add_argument("--temp", type=float)
    p.add_argument("--memoria", choices=["completa", "resumen", "ventana"])
    p.add_argument("--recientes", type=int, default=8)


def ejecutar(args):
    laboratorios.cargar(args.lab)
    memoria = {"tipo": args.memoria, "recientes": args.recientes} if args.memoria else None
    e = ensayos.nuevo(args.lab, {"semilla": args.semilla, "marco": args.marco, "turnos": args.turnos, "tokens": args.tokens,
                                 "temperatura": args.temp, "memoria": memoria,
                                 "modelos": args.modelos or ([args.modelo] * 2 if args.modelo else None),
                                 "notas": "Conversación desde la terminal (python3 -m cli charla)."})
    ensayos.guardar(e)
    print(f"\033[90m{e['id']} · primer mensaje: {e['config']['semilla']!r} · Ctrl+C para parar\033[0m\n")
    escrito = {"n": 0}

    def al_texto(texto):
        sys.stdout.write(texto[escrito["n"]:])
        sys.stdout.flush()
        escrito["n"] = len(texto)

    try:
        while len(e["mensajes"]) < e["config"]["turnos"]:
            i = len(e["mensajes"]) % 2
            print(f"{COLORES[i]}{e['config']['ias'][i]['etiqueta']}:\033[0m ", end="", flush=True)
            escrito["n"] = 0
            motor.turno(e, al_texto=al_texto, al_estado=lambda t: print(f"\033[90m[{t}]\033[0m", end=" ", flush=True))
            print("\n")
    except KeyboardInterrupt:
        print("\n[parado; el turno a medias no se guarda]")
    print(f"Guardado en laboratorios/{args.lab}/ensayos/{e['id']}.json")
    return 0
