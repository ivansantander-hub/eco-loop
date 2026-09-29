"""Comandos de eco loop. Uso: python3 -m cli <comando> [opciones]   (python3 -m cli -h para la lista)

Cada comando es un módulo de esta carpeta con:
    AYUDA                una línea para la lista de comandos
    configurar(parser)   declara sus opciones
    ejecutar(args)       lo ejecuta y devuelve el código de salida
"""
COMANDOS = ["servir", "labs", "correr", "charla", "analizar", "exportar", "migrar"]
