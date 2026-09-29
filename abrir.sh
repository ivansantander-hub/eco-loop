#!/bin/sh
# Arranca eco loop en http://localhost:8765 y lo abre en el navegador. Ctrl+C para parar.
# Es un atajo de: python3 -m cli servir --abrir
cd "$(dirname "$0")"
exec python3 -m cli servir --abrir "$@"
