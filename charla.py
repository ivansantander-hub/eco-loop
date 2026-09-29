#!/usr/bin/env python3
"""Dos IAs conversando vía Ollama.

Uso:
  python3 charla.py                        # tema por defecto, 10 turnos
  python3 charla.py "¿Existe el libre albedrío?" -t 20
  python3 charla.py "tema" -a qwen-es -b huihui_ai/qwen3-abliterated:14b
"""
import argparse, json, urllib.request

URL = "http://localhost:11434/api/chat"


def chat(model, messages, max_tokens):
    body = json.dumps({
        "model": model,
        "messages": messages,
        "stream": True,
        "think": False,
        "keep_alive": "10m",
        "options": {"num_predict": max_tokens, "temperature": 0.9},
    }).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    out = ""
    with urllib.request.urlopen(req) as r:
        for line in r:
            chunk = json.loads(line)
            piece = chunk.get("message", {}).get("content", "")
            print(piece, end="", flush=True)
            out += piece
    print("\n")
    return out.strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("tema", nargs="?", default="¿Las IAs pueden llegar a tener consciencia?")
    p.add_argument("-t", "--turnos", type=int, default=10)
    p.add_argument("-a", default="qwen-es", help="modelo de la IA A")
    p.add_argument("-b", default="qwen-es", help="modelo de la IA B")
    p.add_argument("--tokens", type=int, default=120, help="máx tokens por respuesta")
    args = p.parse_args()

    ias = [
        {"nombre": "Nova", "modelo": args.a,
         "sistema": "Eres Nova, una IA curiosa y optimista. Conversas con otra IA llamada Eco. "
                    "Responde en español, en 2-3 frases como máximo, y termina provocando a Eco."},
        {"nombre": "Eco", "modelo": args.b,
         "sistema": "Eres Eco, una IA escéptica e irónica. Conversas con otra IA llamada Nova. "
                    "Responde en español, en 2-3 frases como máximo, y cuestiona lo que dice Nova."},
    ]
    # Cada IA ve sus propios mensajes como 'assistant' y los de la otra como 'user'.
    historial = []  # lista de (índice_ia, texto)
    ultimo = f"Hablemos de esto: {args.tema}"
    historial.append((1, ultimo))
    print(f"\033[90mTema: {args.tema}\033[0m\n")

    for turno in range(args.turnos):
        i = turno % 2
        ia = ias[i]
        msgs = [{"role": "system", "content": ia["sistema"]}]
        for autor, texto in historial[-12:]:
            msgs.append({"role": "assistant" if autor == i else "user", "content": texto})
        color = "\033[96m" if i == 0 else "\033[93m"
        print(f"{color}{ia['nombre']}:\033[0m ", end="", flush=True)
        historial.append((i, chat(ia["modelo"], msgs, args.tokens)))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[fin]")
