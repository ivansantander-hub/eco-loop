"""Punto de entrada: python3 -m cli <comando> …"""
import argparse, importlib, sys

from . import COMANDOS


def principal(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m cli", description="eco loop: laboratorios de conversación entre IAs.")
    sub = p.add_subparsers(dest="comando", metavar="comando")
    modulos = {}
    for nombre in COMANDOS:
        m = importlib.import_module(f"cli.{nombre}")
        modulos[nombre] = m
        m.configurar(sub.add_parser(nombre, help=m.AYUDA, description=m.AYUDA))
    args = p.parse_args(argv)
    if not args.comando:
        p.print_help()
        return 1
    return modulos[args.comando].ejecutar(args) or 0


if __name__ == "__main__":
    sys.exit(principal())
