#!/bin/sh
# Arranca eco loop en localhost:8765 (informe en / y laboratorio en /laboratorio) y lo abre en el navegador.
# Ctrl+C para parar.
cd "$(dirname "$0")"
(sleep 1 && open http://localhost:8765) &
python3 servidor.py
