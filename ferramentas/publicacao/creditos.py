#!/usr/bin/env python3
"""Gera capítulos (das cartelas de título) e créditos de mídia para a descrição do YouTube.

    python ferramentas/publicacao/creditos.py <canal/slug>

Grava 06_publicacao/capitulos.txt e 06_publicacao/creditos.txt.
O YouTube exige o 1º capítulo em 0:00 e no mínimo 3 capítulos de 10 s ou mais.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum.estudio import Projeto, ler_json, ultima_versao  # noqa: E402

ROTULOS = {"fr": ("Introduction", "Images et vidéos : "), "en": ("Intro", "Images and footage: "),
           "es": ("Introducción", "Imágenes y vídeos: "), "pt": ("Introdução", "Imagens e vídeos: ")}
SEM_ATRIBUICAO = {"Pexels License", "Pixabay Content License", "CC0", "Domínio público", "próprio", "teste"}


def hms(s: float) -> str:
    s = int(s)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("projeto")
    args = ap.parse_args()
    proj = Projeto.abrir(args.projeto)
    tl = ler_json(ultima_versao(proj.etapa("edicao"), "timeline", ".json"))
    if not tl:
        raise SystemExit("Sem timeline.")
    fps = tl["fps"]
    intro, rotulo_bancos = ROTULOS.get(proj.dados.get("idioma", "pt")[:2], ROTULOS["en"])
    caps = [(c["inicio"] / fps, " · ".join(x for x in (c.get("subtitulo"), c.get("titulo")) if x))
            for c in tl["cenas"] if c["tipo"] == "titulo" and c.get("titulo")]
    if not caps or caps[0][0] > 0.5:
        caps.insert(0, (0, intro))
    caps = [caps[0]] + [c for a, c in zip(caps, caps[1:]) if c[0] - a[0] >= 10]
    pasta = proj.etapa("publicacao")
    (pasta / "capitulos.txt").write_text("\n".join(f"{hms(t)} {nome}" for t, nome in caps) + "\n", encoding="utf-8")

    creditos = ler_json(proj.etapa("visual") / "creditos.json", [])
    usados = {c.get("src") for c in tl["cenas"]} | {k.get("src") for c in tl["cenas"] for k in (c.get("camadas") or [])}
    linhas, vistos = [], set()
    for c in creditos:
        if c["arquivo"] not in usados or c.get("licenca") in SEM_ATRIBUICAO:
            continue
        chave = (c.get("banco"), c.get("id"))
        if chave in vistos:
            continue
        vistos.add(chave)
        linhas.append(f"• {c.get('atribuicao') or c.get('autor')} — {c.get('pagina') or ''}".strip(" —"))
    bancos = sorted({c.get("banco") for c in creditos if c["arquivo"] in usados})
    texto = "\n".join(linhas) if linhas else "(nenhuma mídia exige atribuição)"
    if any(bancos):
        texto += "\n\n" + rotulo_bancos + ", ".join(b for b in bancos if b)
    texto += "\n"
    (pasta / "creditos.txt").write_text(texto, encoding="utf-8")
    print(f"{len(caps)} capítulos, {len(linhas)} créditos com atribuição → {proj.rel(pasta)}/")
    if len(caps) < 3:
        print("⚠ menos de 3 capítulos: o YouTube não mostra capítulos (acrescente cartelas de título).")


if __name__ == "__main__":
    main()
