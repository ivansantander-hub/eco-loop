"""Memoria: qué recuerda cada IA en cada turno.

    completa  toda la conversación (en Ollama la ventana de contexto se ajusta sola; ver proveedores.ventana)
    resumen   un resumen de lo antiguo (uno por IA, en segunda persona) + los últimos N mensajes literales
    ventana   solo los últimos N mensajes; el principio se olvida

Los resúmenes se guardan en ensayo["memoria"] = [[…IA A…], […IA B…]], cada uno {"hasta", "texto", "modelo", "costo"}.
Se actualizan de forma incremental cada N/2 mensajes; mientras tanto, lo posterior al último resumen va literal,
así que nunca queda un hueco entre lo resumido y lo literal.
"""
from dataclasses import dataclass

INSTRUCCION_RESUMEN = ("Eres la memoria de un participante en una conversación. Escribe un resumen fiel y conciso, en segunda "
                       "persona («dijiste…», «tu interlocutor contó…»): temas, datos concretos, acuerdos, preguntas pendientes "
                       "y el tono. No inventes nada. Máximo 200 palabras.")
TOKENS_RESUMEN = 400


@dataclass
class Recuerdo:
    desde: int = 0                 # primer mensaje que recibe literal
    resumen: str | None = None     # resumen de todo lo anterior a `desde`
    resumen_hasta: int | None = None

    def registro(self):
        """Lo que se guarda en cada mensaje: qué recordaba la IA al escribirlo."""
        r = {"desde": self.desde}
        if self.resumen_hasta:
            r["resumen_hasta"] = self.resumen_hasta
        return r


def recuerdo(ensayo, i, resumir=None, al_estado=None):
    """Qué recuerda la IA i en este turno. `resumir(pedido)` genera un resumen (lo pone el motor)."""
    mem = ensayo["config"].get("memoria") or {"tipo": "completa"}
    total, recientes = len(ensayo["mensajes"]), max(2, mem.get("recientes") or 8)
    if mem["tipo"] == "completa" or total <= recientes:
        return Recuerdo(0)
    desde = total - recientes
    if mem["tipo"] == "ventana":
        return Recuerdo(desde)
    r = resumen_hasta(ensayo, i, desde, recientes, resumir, al_estado)
    return Recuerdo(r["hasta"], r["texto"], r["hasta"])


def pedido_resumen(ensayo, i, anterior, inicio, hasta):
    quien = lambda m: "Tú" if m["autor"] == i else "Tu interlocutor"
    trozo = (f"Tu interlocutor: {ensayo['config']['semilla']}\n\n" if inicio == 0 and i == 0 else "") + \
        "\n\n".join(f"{quien(m)}: {m['texto']}" for m in ensayo["mensajes"][inicio:hasta])
    cabecera = f"Resumen anterior:\n{anterior['texto']}\n\nLo que se habló después:\n" if anterior else "Conversación:\n"
    return [{"role": "system", "content": INSTRUCCION_RESUMEN}, {"role": "user", "content": cabecera + trozo}]


def resumen_hasta(ensayo, i, desde, recientes, resumir, al_estado=None):
    ensayo.setdefault("memoria", [[], []])
    anterior = ensayo["memoria"][i][-1] if ensayo["memoria"][i] else None
    if anterior and desde - anterior["hasta"] < max(2, recientes // 2):
        return anterior
    if resumir is None:
        raise ValueError("la memoria «resumen» necesita una función para resumir")
    inicio = anterior["hasta"] if anterior else 0
    al_estado and al_estado(f"Actualizando la memoria de {ensayo['config']['ias'][i]['etiqueta']}…")
    res = resumir(pedido_resumen(ensayo, i, anterior, inicio, desde))
    nuevo = {"hasta": desde, "texto": res.texto.strip(), "modelo": ensayo["config"]["ias"][i]["modelo"], "costo": res.costo}
    ensayo["memoria"][i].append(nuevo)
    return nuevo
