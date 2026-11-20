#!/usr/bin/env python3
"""Cria e inspeciona vídeos (projetos) do estúdio.

    python ferramentas/projeto.py novo retrovisage "20 souvenirs des années 60" \
        --link "https://youtu.be/XXXX" --idioma fr-FR
    python ferramentas/projeto.py status retrovisage/20-souvenirs-des-annees-60
    python ferramentas/projeto.py listar [--canal retrovisage]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum.estudio import (ETAPAS, PROJETOS, Projeto, agora, carregar_canal, gravar_json,  # noqa: E402
                           slugificar, ultima_versao)

# O que prova que cada etapa terminou (pasta, prefixo, extensão).
ENTREGAS = [
    ("pesquisa", "01_pesquisa", "mapa-emocional", ".md"),
    ("roteiro", "02_roteiro", "roteiro", ".md"),
    ("humanizacao", "02_roteiro", "roteiro_narracao", ".txt"),
    ("narracao", "03_narracao", "narracao", ".wav"),
    ("decupagem", "04_visual", "decupagem", ".json"),
    ("midia", "04_visual", "creditos", ".json"),
    ("timeline", "05_edicao", "timeline", ".json"),
    ("render", "05_edicao/renders", "video", ".mp4"),
    ("publicacao", "06_publicacao", "publicacao", ".md"),
]


def novo(args) -> None:
    canal = carregar_canal(args.canal)
    slug = args.slug or slugificar(args.tema)
    pasta = PROJETOS / args.canal / slug
    if (pasta / "projeto.json").exists():
        print(f"Já existe: {pasta.relative_to(PROJETOS.parent)}")
        return
    for sub in ETAPAS.values():
        (pasta / sub).mkdir(parents=True, exist_ok=True)
    (pasta / "04_visual" / "midia").mkdir(exist_ok=True)
    (pasta / "04_visual" / "musica").mkdir(exist_ok=True)
    (pasta / "05_edicao" / "renders").mkdir(exist_ok=True)
    gravar_json(pasta / "projeto.json", {
        "canal": args.canal,
        "slug": slug,
        "tema": args.tema,
        "link_referencia": args.link or "",
        "idioma": args.idioma or canal.get("idioma", "pt-BR"),
        "criado_em": agora(),
        "etapas": {},
    })
    print(f"Projeto criado: {pasta.relative_to(PROJETOS.parent)}")


def status(args) -> None:
    proj = Projeto.abrir(args.alvo)
    d = proj.dados
    print(f"# {d['canal']}/{d['slug']} — {d['tema']}")
    print(f"idioma: {d['idioma']}   referência: {d.get('link_referencia') or '-'}\n")
    proxima = None
    for nome, sub, prefixo, ext in ENTREGAS:
        pasta = proj.pasta / sub
        achado = ultima_versao(pasta, prefixo, ext) if pasta.exists() else None
        if achado is None and nome == "roteiro" and pasta.exists():
            achado = ultima_versao(pasta, "roteiro", ".txt")  # roteiro próprio, sem .md
        if achado is None and (pasta / f"{prefixo}{ext}").exists():
            achado = pasta / f"{prefixo}{ext}"
        marca = "✔" if achado else "·"
        print(f"  {marca} {nome:<12} {proj.rel(achado) if achado else ''}")
        if not achado and proxima is None:
            proxima = nome
    print(f"\nPróxima etapa: {proxima or 'nenhuma — vídeo pronto'}")


def listar(args) -> None:
    base = PROJETOS / args.canal if args.canal else PROJETOS
    for pj in sorted(base.rglob("projeto.json")):
        print(pj.parent.relative_to(PROJETOS).as_posix())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("novo")
    a.add_argument("canal")
    a.add_argument("tema")
    a.add_argument("--link")
    a.add_argument("--idioma")
    a.add_argument("--slug")
    a.set_defaults(f=novo)
    b = sub.add_parser("status")
    b.add_argument("alvo", help="canal/slug")
    b.set_defaults(f=status)
    c = sub.add_parser("listar")
    c.add_argument("--canal")
    c.set_defaults(f=listar)
    args = ap.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
