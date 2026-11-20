#!/usr/bin/env bash
# Uso: ./scripts/status.sh [canal/slug]   (sem argumento: lista os vídeos)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
if [ $# -eq 0 ]; then "$PY" ferramentas/projeto.py listar; else "$PY" ferramentas/projeto.py status "$1"; fi
