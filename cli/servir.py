"""servir: arranca la web (índice, informes y bancos de pruebas)."""
import threading, webbrowser

from nucleo import config

AYUDA = "arranca la web en http://localhost:8765 (índice, informes y bancos de pruebas)"


def configurar(p):
    p.add_argument("--puerto", type=int, default=config.PUERTO)
    p.add_argument("--abrir", action="store_true", help="abre el navegador al arrancar")


def ejecutar(args):
    from web import servidor
    srv = servidor.crear(args.puerto)
    url = f"http://localhost:{srv.server_address[1]}"
    print(f"eco loop en {url} · laboratorios en {config.LABORATORIOS} · "
          f"OpenRouter {'activo' if config.clave_openrouter() else 'sin clave (.env)'} · Ctrl+C para parar", flush=True)
    if args.abrir:
        threading.Timer(0.8, webbrowser.open, [url]).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print()
    return 0
