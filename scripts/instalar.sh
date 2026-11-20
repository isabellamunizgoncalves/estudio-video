#!/usr/bin/env bash
# Prepara o estúdio numa máquina nova: Python (.venv), Remotion (node_modules) e .env.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v ffmpeg >/dev/null || { echo "Instale o ffmpeg (ex.: sudo apt install ffmpeg / brew install ffmpeg)"; exit 1; }
command -v node >/dev/null || { echo "Instale o Node.js 18+ (https://nodejs.org)"; exit 1; }
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
(cd estudio-remotion && npm install --no-audit --no-fund)
[ -f .env ] || { cp .env.exemplo .env; echo "Criei o .env: preencha GEMINI_API_KEY (e as outras chaves se tiver)."; }
echo "Pronto. Teste: .venv/bin/python testes/teste_ponta_a_ponta.py"
