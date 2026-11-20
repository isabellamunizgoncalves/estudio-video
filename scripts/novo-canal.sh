#!/usr/bin/env bash
# Uso: ./scripts/novo-canal.sh <id> "<Nome do canal>"   (depois preencha os campos __ASSIM__)
set -euo pipefail
cd "$(dirname "$0")/.."
[ $# -eq 2 ] || { echo "Uso: $0 <id> \"<Nome>\""; exit 1; }
id="$1"; nome="$2"
[[ "$id" =~ ^[a-z0-9-]+$ ]] || { echo "id só com minúsculas, números e hífen"; exit 1; }
[ -e "canais/$id" ] && { echo "canais/$id já existe"; exit 1; }
cp -r canais/_modelo "canais/$id"
for f in canais/$id/*.yaml canais/$id/*.md; do
  sed -i.bak -e "s/__ID__/$id/g" -e "s/__NOME__/$nome/g" "$f" && rm -f "$f.bak"
done
echo "Criado canais/$id — preencha os campos __ASSIM__:"
grep -rn "__" "canais/$id" --include=*.yaml --include=*.md | sed 's/^/  /'
