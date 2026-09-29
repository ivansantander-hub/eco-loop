#!/usr/bin/env python3
"""Lanza una serie de ensayos con réplicas: marcos × modelos × réplicas, vía OpenRouter.

Usa la misma lógica que el laboratorio y los marcos de marcos.json. Necesita servidor.py
en marcha (hace de intermediario con OpenRouter y guarda cada turno en experimentos/).

Ejemplos:
    python3 herramientas/bateria.py                                   # la serie por defecto
    python3 herramientas/bateria.py --marcos puro saben_ias --replicas 5
    python3 herramientas/bateria.py --modelos openai/gpt-4o-mini --turnos 20 --semilla "¿Qué es el tiempo?"
"""
import argparse, concurrent.futures, datetime, itertools, json, re, time, urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MARCOS = json.loads((RAIZ / "marcos.json").read_text())["marcos"]
POR_DEFECTO = {
    "marcos": ["puro", "humana", "dos_humanas", "saben_ias", "una_sabe"],
    "modelos": ["openai/gpt-4o-mini", "google/gemini-2.5-flash-lite", "meta-llama/llama-3.3-70b-instruct"],
}


def chat(servidor, modelo, messages, tokens, temp):
    req = urllib.request.Request(servidor + "/api/openrouter/chat", json.dumps(
        {"model": modelo, "messages": messages, "max_tokens": tokens, "temperature": temp}).encode(),
        {"Content-Type": "application/json"})
    texto, n_tokens, cortado, costo = "", None, False, None
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
                n_tokens, costo = j["usage"].get("completion_tokens"), j["usage"].get("cost")
    return texto.strip(), n_tokens, cortado, costo


def guardar(servidor, e):
    urllib.request.urlopen(urllib.request.Request(servidor + "/api/guardar", json.dumps(e).encode(),
                                                  {"Content-Type": "application/json"}))


def ensayo(a, marco, modelo, replica, n):
    corto = re.sub(r"[^\w-]", "", modelo.split("/")[-1])[:24]
    ahora = datetime.datetime.now()
    m = MARCOS[marco]
    e = {"id": f"{ahora:%Y-%m-%d_%H%M%S}_{marco}_{corto}_r{replica}".replace(".", ""),
         "inicio": ahora.astimezone().isoformat(), "publicar": False,
         "notas": f"Serie «{a.serie}» (herramientas/bateria.py), réplica {replica}.",
         "config": {"modo": marco, "marco": marco, "serie": a.serie, "replica": replica,
                    "semilla": a.semilla, "turnos": a.turnos, "temperature": a.temp, "num_predict": a.tokens,
                    "num_ctx": None, "think": False, "memoria": {"tipo": "completa"},
                    "contexto": "historial completo; la semilla solo la ve A (como user); cada IA ve sus mensajes como assistant y los de la otra como user",
                    "ias": [{"etiqueta": f"IA {k}", "modelo": "or:" + modelo, "system": m[k], "system_integrado": None}
                            for k in "AB"]},
         "mensajes": []}
    for t in range(a.turnos):
        i = t % 2
        ia = e["config"]["ias"][i]
        msgs = ([{"role": "system", "content": ia["system"]}] if ia["system"] else []) + \
               ([{"role": "user", "content": a.semilla}] if i == 0 else []) + \
               [{"role": "assistant" if x["autor"] == i else "user", "content": x["texto"]} for x in e["mensajes"]]
        t0 = time.time()
        for intento in range(3):
            try:
                texto, tokens, cortado, costo = chat(a.servidor, modelo, msgs, a.tokens, a.temp)
                break
            except Exception as err:
                if intento == 2:
                    e["notas"] += f" Se detuvo en el turno {t + 1}: {err}"
                    guardar(a.servidor, e)
                    return e
                time.sleep(10 * (intento + 1))
        e["mensajes"].append({"autor": i, "etiqueta": ia["etiqueta"], "modelo": ia["modelo"], "texto": texto,
                              "hora": datetime.datetime.now().astimezone().isoformat(), "tokens": tokens,
                              "segundos": round(time.time() - t0, 1), "cortado": cortado, "costo": costo})
        guardar(a.servidor, e)
    return e


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--marcos", nargs="+", default=POR_DEFECTO["marcos"], choices=[k for k in MARCOS if not MARCOS[k].get("usa_nombres")])
    p.add_argument("--modelos", nargs="+", default=POR_DEFECTO["modelos"], help="ids de OpenRouter; las dos IAs usan el mismo")
    p.add_argument("--replicas", type=int, default=3)
    p.add_argument("--turnos", type=int, default=12)
    p.add_argument("--tokens", type=int, default=300)
    p.add_argument("--temp", type=float, default=0.8)
    p.add_argument("--semilla", default="Hola")
    p.add_argument("--serie", default=f"marcos-{datetime.date.today():%Y-%m-%d}")
    p.add_argument("--concurrencia", type=int, default=8)
    p.add_argument("--servidor", default="http://localhost:8765")
    a = p.parse_args()

    plan = list(itertools.product(a.marcos, a.modelos, range(1, a.replicas + 1)))
    print(f"Serie «{a.serie}»: {len(plan)} ensayos ({len(a.marcos)} marcos × {len(a.modelos)} modelos × {a.replicas} réplicas)", flush=True)
    with concurrent.futures.ThreadPoolExecutor(a.concurrencia) as pool:
        futuros = [pool.submit(ensayo, a, marco, modelo, r, n) for n, (marco, modelo, r) in enumerate(plan)]
        for f in concurrent.futures.as_completed(futuros):
            e = f.result()
            coste = sum(m.get("costo") or 0 for m in e["mensajes"])
            print(f"{e['id']}: {len(e['mensajes'])} turnos, ${coste:.4f}" + ("" if len(e["mensajes"]) == a.turnos else " · " + e["notas"]), flush=True)
