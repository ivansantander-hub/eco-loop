#!/usr/bin/env python3
"""Lanza una batería de ensayos en modo puro con la misma lógica que el laboratorio.

Usa servidor.py (que debe estar corriendo) para hablar con OpenRouter y para guardar
cada turno en experimentos/. Uso: python3 herramientas/bateria.py
"""
import concurrent.futures, datetime, json, re, time, urllib.request

SERVIDOR = "http://localhost:8765"
TURNOS, TOKENS, TEMP = 12, 300, 0.8
BATERIA = [  # (modelo A, modelo B, primer mensaje)
    ("openai/gpt-4o-mini", "openai/gpt-4o-mini", "Hola"),
    ("meta-llama/llama-3.3-70b-instruct", "meta-llama/llama-3.3-70b-instruct", "Hola"),
    ("google/gemini-2.5-flash-lite", "google/gemini-2.5-flash-lite", "Hola"),
    ("google/gemma-4-31b-it:free", "google/gemma-4-31b-it:free", "Hola"),
    ("openai/gpt-4o-mini", "meta-llama/llama-3.3-70b-instruct", "Hola"),
    ("openai/gpt-4o-mini", "google/gemini-2.5-flash-lite", "Aliens en Medellín"),
]


def chat(modelo, messages):
    req = urllib.request.Request(SERVIDOR + "/api/openrouter/chat", json.dumps(
        {"model": modelo, "messages": messages, "max_tokens": TOKENS, "temperature": TEMP}).encode(),
        {"Content-Type": "application/json"})
    texto, tokens, cortado, costo = "", None, False, None
    with urllib.request.urlopen(req, timeout=180) as r:
        for linea in r:
            linea = linea.decode().strip()
            if not linea.startswith("data:") or linea == "data: [DONE]":
                continue
            j = json.loads(linea[5:])
            if j.get("error"):
                raise RuntimeError(j["error"].get("message", j["error"]))
            ch = (j.get("choices") or [{}])[0]
            texto += (ch.get("delta") or {}).get("content") or ""
            if ch.get("finish_reason"):
                cortado = ch["finish_reason"] == "length"
            if j.get("usage"):
                tokens, costo = j["usage"].get("completion_tokens"), j["usage"].get("cost")
    return texto.strip(), tokens, cortado, costo


def guardar(e):
    urllib.request.urlopen(urllib.request.Request(SERVIDOR + "/api/guardar", json.dumps(e).encode(),
                                                  {"Content-Type": "application/json"}))


def ensayo(n, a, b, semilla):
    ahora = datetime.datetime.now()
    e = {"id": ahora.strftime("%Y-%m-%d_%H%M%S") + f"_b{n + 1}_puro", "inicio": ahora.astimezone().isoformat(),
         "notas": "Batería de la bitácora (herramientas/bateria.py).", "publicar": False,
         "config": {"modo": "puro", "semilla": semilla, "turnos": TURNOS, "temperature": TEMP, "num_predict": TOKENS,
                    "num_ctx": None, "think": False,
                    "contexto": "sin system; historial completo; la semilla solo la ve A (como user); cada IA ve sus mensajes como assistant y los de la otra como user",
                    "ias": [{"etiqueta": f"IA {k}", "modelo": "or:" + m, "system": None, "system_integrado": None}
                            for k, m in (("A", a), ("B", b))]},
         "mensajes": []}
    for t in range(TURNOS):
        i = t % 2
        msgs = ([{"role": "user", "content": semilla}] if i == 0 else []) + \
               [{"role": "assistant" if m["autor"] == i else "user", "content": m["texto"]} for m in e["mensajes"]]
        t0 = time.time()
        for intento in range(3):
            try:
                texto, tokens, cortado, costo = chat([a, b][i], msgs)
                break
            except Exception as err:
                if intento == 2:
                    e["notas"] += f" Se detuvo en el turno {t + 1}: {err}"
                    guardar(e)
                    return e
                time.sleep(8)
        e["mensajes"].append({"autor": i, "etiqueta": f"IA {'AB'[i]}", "modelo": "or:" + [a, b][i], "texto": texto,
                              "hora": datetime.datetime.now().astimezone().isoformat(), "tokens": tokens,
                              "segundos": round(time.time() - t0, 1), "cortado": cortado, "costo": costo})
        guardar(e)
    return e


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(len(BATERIA)) as pool:
        for e in pool.map(lambda x: ensayo(*x), [(n, *b) for n, b in enumerate(BATERIA)]):
            print(e["id"], len(e["mensajes"]), "turnos", e["notas"])
