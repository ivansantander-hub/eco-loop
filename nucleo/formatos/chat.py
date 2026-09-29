"""Formato «chat»: cada IA ve a la otra en el lugar del usuario.

    Turno de la IA A:  [system?] user: <primer mensaje>  assistant: A1  user: B1  assistant: A2 …
    Turno de la IA B:  [system?]                         user: A1  assistant: B1  user: A2 …

El primer mensaje solo lo recibe A. Con memoria «resumen», el resumen va como un mensaje system aparte.
"""


def mensajes(ensayo, i, recuerdo):
    c = ensayo["config"]
    salida = []
    if c["ias"][i].get("system"):
        salida.append({"role": "system", "content": c["ias"][i]["system"]})
    if recuerdo.resumen:
        salida.append({"role": "system", "content": "Memoria de la conversación hasta ahora (resumen de lo que hablaste "
                                                    "antes con tu interlocutor):\n" + recuerdo.resumen})
    if i == 0 and recuerdo.desde == 0:
        salida.append({"role": "user", "content": c["semilla"]})
    for m in ensayo["mensajes"][recuerdo.desde:]:
        salida.append({"role": "assistant" if m["autor"] == i else "user", "content": m["texto"]})
    return salida
