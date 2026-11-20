#!/usr/bin/env python3
"""Extrai o texto falado do roteiro .md, mede a duração e procura problemas.

    python ferramentas/roteiro/extrair_falas.py <canal/slug> [--md 02_roteiro/roteiro_v02.md]

- Lê o roteiro_vNN.md mais recente (blocos "### TÍTULO" + "**Fala:** ...").
- Grava roteiro_vNN.txt ao lado: só as falas, um parágrafo por bloco, sem Markdown.
  Aspas retas e guillemets que envolvem a fala inteira saem; « » internas ficam.
- Mostra palavras, duração estimada (palavras_por_minuto do canal) e alertas:
  menções a comentários, @handles, carimbos de tempo, colchetes/direções de cena.
Saída 4 = há alertas graves (o roteirista precisa corrigir).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum.estudio import Projeto, ultima_versao  # noqa: E402

PROIBIDOS = [
    # menção a comentários / público que escreveu (pt, fr, en, es, de)
    r"\bcoment[aá]rios?\b", r"\bcomentou\b", r"voc[eê]s (disseram|escreveram)", r"\bli (os|seus) coment",
    r"\bcommentaires?\b", r"vous (m'avez|nous avez) (écrit|dit)", r"un(e)? (spectat|abonn)\w+ (nous|m')",
    r"\bcomments?\b(?! below)", r"you (told|wrote)", r"\bcomentarios?\b", r"\bKommentar",
    r"@\w{3,}",
    # produção dentro da fala
    r"\b\d{1,2}:\d{2}\b", r"\[[^\]]+\]", r"\((pausa|pause|música|music|b-?roll|corte)[^)]*\)",
]
# CTA pedindo para comentar é permitido; esses padrões liberam o alerta acima.
PERMITIDOS = [r"(dites|écrivez|laissez)[^.]{0,40}commentaire", r"(deixe|escreva|conte)[^.]{0,40}coment",
              r"(leave|drop|tell)[^.]{0,40}comment", r"(deja|escribe)[^.]{0,40}comentario"]


def extrair(md: str) -> list[str]:
    falas = []
    for m in re.finditer(r"\*\*Fala:\*\*\s*(.+?)(?=\n#{1,6} |\n\*\*[A-ZÀ-Ü][^*]*:\*\*|\Z)", md, re.S):
        t = m.group(1).strip()
        t = re.sub(r"\*\*|__|(?<!\w)[*_](?!\s)|(?<!\s)[*_](?!\w)", "", t)
        t = re.sub(r"\s*\n\s*\n\s*", "\n\n", t)
        t = re.sub(r"[ \t]*\n(?!\n)[ \t]*", " ", t)
        t = t.strip()
        if len(t) >= 2 and t[0] in "\"“" and t[-1] in "\"”":
            t = t[1:-1].strip()
        if t.startswith("«") and t.endswith("»") and t.count("«") == 1:
            t = t[1:-1].strip()
        t = t.replace('"', "")
        t = re.sub(r"[ \t]{2,}", " ", t)
        if t:
            falas.append(t)
    return falas


def alertas(texto: str) -> list[str]:
    achados = []
    for frase in re.split(r"(?<=[.!?…])\s+", texto):
        if any(re.search(p, frase, re.I) for p in PERMITIDOS):
            continue
        for p in PROIBIDOS:
            if re.search(p, frase, re.I):
                achados.append(frase.strip()[:160])
                break
    return achados


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--md")
    args = ap.parse_args()
    proj = Projeto.abrir(args.projeto)
    pasta = proj.etapa("roteiro")
    md = proj.pasta / args.md if args.md else ultima_versao(pasta, "roteiro", ".md")
    if not md or not md.exists():
        raise SystemExit("Nenhum roteiro_vNN.md em 02_roteiro/.")
    falas = extrair(md.read_text(encoding="utf-8"))
    if not falas:
        raise SystemExit("Nenhum bloco '**Fala:**' encontrado no roteiro.")
    texto = "\n\n".join(falas) + "\n"
    txt = md.with_suffix(".txt")
    txt.write_text(texto, encoding="utf-8")

    canal = proj.canal
    ppm = canal.get("roteiro", {}).get("palavras_por_minuto", 150)
    minimo = canal.get("roteiro", {}).get("duracao_minima_min", 0)
    palavras = len(texto.split())
    minutos = palavras / ppm
    print(f"→ {proj.rel(txt)}")
    print(f"{len(falas)} blocos · {palavras} palavras · ~{minutos:.1f} min a {ppm} palavras/min")
    if minimo and minutos < minimo:
        print(f"⚠ abaixo do mínimo do canal ({minimo} min): faltam ~{int((minimo - minutos) * ppm)} palavras")
    achados = alertas(texto)
    for a in achados:
        print(f"⚠ revisar: {a}")
    proj.marcar("roteiro", arquivo=proj.rel(txt), palavras=palavras, minutos=round(minutos, 1))
    sys.exit(4 if achados else 0)


if __name__ == "__main__":
    main()
