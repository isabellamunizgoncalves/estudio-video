#!/usr/bin/env bash
# Uso: ./scripts/novo-video.sh <canal> "<tema>" [link-do-youtube] [idioma]
set -euo pipefail
cd "$(dirname "$0")/.."
[ $# -ge 2 ] || { echo "Uso: $0 <canal> \"<tema>\" [link] [idioma]"; exit 1; }
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
args=(novo "$1" "$2")
[ -n "${3:-}" ] && args+=(--link "$3")
[ -n "${4:-}" ] && args+=(--idioma "$4")
"$PY" ferramentas/projeto.py "${args[@]}"
