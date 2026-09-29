#!/usr/bin/env python3
"""Sirve la UI y guarda los experimentos en ./experimentos (JSON + Markdown)."""
import json, re
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

RAIZ = Path(__file__).parent
EXP = RAIZ / "experimentos"
EXP.mkdir(exist_ok=True)
PUERTO = 8765


def a_markdown(e):
    c = e["config"]
    l = [f"# Experimento {e['id']}", "",
         f"- **Modo:** {c['modo']}",
         f"- **Inicio:** {e['inicio']}",
         f"- **Mensaje inicial (semilla):** {c['semilla']!r}",
         f"- **Parámetros:** temperature={c['temperature']}, num_predict={c['num_predict']}, "
         f"num_ctx={c['num_ctx']}, think={c['think']}, contexto={c['contexto']}", ""]
    for ia in c["ias"]:
        l.append(f"- **{ia['etiqueta']}** · modelo `{ia['modelo']}` · system prompt: "
                 + (f"\n  > {ia['system']}" if ia["system"] else "_ninguno_"))
        if ia.get("system_integrado"):
            l.append(f"  - system prompt de fábrica del modelo"
                     + (" (sustituido por el anterior)" if ia["system"] else " **(aplicado)**")
                     + f":\n    > {ia['system_integrado']}")
    if e.get("notas"):
        l += ["", "## Notas", "", e["notas"]]
    l += ["", "## Conversación", ""]
    for m in e["mensajes"]:
        extra = f" _({m['tokens']} tok, {m['segundos']} s)_" if m.get("tokens") else ""
        l += [f"**{m['etiqueta']}**{extra}:", "", m["texto"], ""]
    return "\n".join(l)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(RAIZ), **k)

    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/api/experimentos":
            lista = []
            for f in sorted(EXP.glob("*.json"), reverse=True):
                e = json.loads(f.read_text())
                lista.append({"id": e["id"], "modo": e["config"]["modo"], "semilla": e["config"]["semilla"],
                              "publicar": e.get("publicar", False),
                              "mensajes": [{"autor": m["autor"], "texto": m["texto"]} for m in e["mensajes"]]})
            return self._json(lista)
        m = re.fullmatch(r"/api/experimentos/([\w-]+)", self.path)
        if m:
            f = EXP / f"{m[1]}.json"
            return self._json(json.loads(f.read_text())) if f.exists() else self._json({}, 404)
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/guardar":
            return self._json({}, 404)
        e = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if not re.fullmatch(r"[\w-]+", e.get("id", "")):
            return self._json({"error": "id inválido"}, 400)
        (EXP / f"{e['id']}.json").write_text(json.dumps(e, ensure_ascii=False, indent=2))
        (EXP / f"{e['id']}.md").write_text(a_markdown(e))
        self._json({"ok": True})


if __name__ == "__main__":
    print(f"UI en http://localhost:{PUERTO} · experimentos en {EXP}")
    ThreadingHTTPServer(("127.0.0.1", PUERTO), Handler).serve_forever()
