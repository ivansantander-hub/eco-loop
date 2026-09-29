"""Formatos: cómo se convierten el ensayo y el recuerdo de una IA en los mensajes que recibe el modelo.

Cada formato es un módulo con una función:

    mensajes(ensayo, i, recuerdo) -> list[{"role", "content"}]

donde `i` es la IA que habla (0 = A, 1 = B) y `recuerdo` es lo que le toca recordar (ver nucleo.memoria).
Para un experimento nuevo (guion, moderador…) basta con añadir aquí un módulo y registrarlo.
"""
from . import chat

FORMATOS = {"chat": chat}


def obtener(nombre):
    try:
        return FORMATOS[nombre]
    except KeyError:
        raise ValueError(f"formato desconocido: {nombre!r} (disponibles: {', '.join(FORMATOS)})") from None
