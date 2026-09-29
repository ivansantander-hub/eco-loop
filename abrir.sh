#!/bin/sh
# Sirve la UI en localhost:8765, guarda experimentos y la abre en el navegador. Ctrl+C para parar.
cd "$(dirname "$0")"
(sleep 1 && open http://localhost:8765) &
python3 servidor.py
