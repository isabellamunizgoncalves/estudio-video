#!/usr/bin/env python3
"""Busca candidatos de imagem/vídeo para as cenas da decupagem e monta uma folha de contato.

    python ferramentas/midia/buscar.py <canal/slug> --todas                  # todas as cenas sem mídia
    python ferramentas/midia/buscar.py <canal/slug> --cena c012              # usa a busca da decupagem
    python ferramentas/midia/buscar.py <canal/slug> --cena c012 --q "1960s kitchen" --q "cuisine années 60" --tipo video

Grava 04_visual/candidatos/<cena>.json e 04_visual/candidatos/<cena>.jpg (folha de contato
numerada: abra a imagem para escolher). Depois: baixar.py --cena c012 --escolha N
"""

from __future__ import annotations

import argparse
import io
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum.estudio import Projeto, gravar_json, ler_json, ultima_versao  # noqa: E402
from midia.bancos import BANCOS, UA  # noqa: E402


def buscar(consultas: list[str], tipo: str, bancos: list[str], por_banco: int) -> list[dict]:
    tarefas = [(b, q) for q in consultas for b in bancos if b in BANCOS]
    vistos, out = set(), []

    def rodar(par):
        b, q = par
        try:
            return [dict(c, consulta=q) for c in BANCOS[b](q, tipo, por_banco)]
        except Exception as exc:
            print(f"  {b} «{q}»: {type(exc).__name__} {str(exc)[:100]}", file=sys.stderr)
            return []

    with ThreadPoolExecutor(max_workers=6) as ex:
        for lista in ex.map(rodar, tarefas):
            for c in lista:
                chave = (c["banco"], c["id"])
                if chave not in vistos:
                    vistos.add(chave)
                    out.append(c)
    # vídeos primeiro quando pedido vídeo; depois maior resolução
    out.sort(key=lambda c: (c["tipo"] != ("video" if tipo == "video" else c["tipo"]), -(c.get("largura") or 0)))
    return out


def folha_de_contato(cands: list[dict], destino: Path, colunas: int = 4) -> None:
    from PIL import Image, ImageDraw, ImageFont

    w, h = 400, 225
    linhas = (len(cands) + colunas - 1) // colunas
    folha = Image.new("RGB", (colunas * w, linhas * (h + 34)), "#111")
    d = ImageDraw.Draw(folha)
    try:
        fonte = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    except OSError:
        fonte = ImageFont.load_default()

    def baixar(c):
        try:
            r = requests.get(c["previa"], headers=UA, timeout=20)
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content)).convert("RGB")
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=8) as ex:
        imgs = list(ex.map(baixar, cands))
    for i, (c, img) in enumerate(zip(cands, imgs)):
        x, y = (i % colunas) * w, (i // colunas) * (h + 34)
        if img:
            img.thumbnail((w, h))
            folha.paste(img, (x + (w - img.width) // 2, y + (h - img.height) // 2))
        rot = f"{i}  {'▶' if c['tipo'] == 'video' else '■'} {c['banco']} {c.get('largura') or '?'}px"
        if c.get("duracao"):
            rot += f" {int(float(c['duracao']))}s"
        d.rectangle([x, y + h, x + w, y + h + 34], fill="#222")
        d.text((x + 8, y + h + 7), rot, fill="#fff", font=fonte)
    destino.parent.mkdir(parents=True, exist_ok=True)
    folha.save(destino, quality=82)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--cena")
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--q", action="append", help="consulta (pode repetir)")
    ap.add_argument("--tipo", choices=["video", "imagem", "qualquer"])
    ap.add_argument("--bancos", help="ex.: archive,wikimedia")
    ap.add_argument("--por-banco", type=int, default=4)
    args = ap.parse_args()

    proj = Projeto.abrir(args.projeto)
    canal = proj.canal
    pasta = proj.etapa("visual")
    dec_arq = ultima_versao(pasta, "decupagem", ".json")
    dec = ler_json(dec_arq, {"cenas": []}) if dec_arq else {"cenas": []}
    creditos = {c["cena"]: c for c in ler_json(pasta / "creditos.json", [])}
    bancos_padrao = canal.get("visual", {}).get("bancos", list(BANCOS))

    if args.todas:
        alvos = [c for c in dec["cenas"] if c.get("busca") and c["id"] not in creditos]
    elif args.cena:
        alvos = [next((c for c in dec["cenas"] if c["id"] == args.cena), {"id": args.cena})]
    else:
        raise SystemExit("Use --cena <id> ou --todas.")

    for cena in alvos:
        busca = dict(cena.get("busca") or {})
        consultas = args.q or busca.get("consultas") or []
        if not consultas:
            print(f"{cena['id']}: sem consultas (passe --q)")
            continue
        tipo = args.tipo or busca.get("tipo", "qualquer")
        bancos = args.bancos.split(",") if args.bancos else busca.get("bancos") or bancos_padrao
        cands = buscar(consultas, tipo, bancos, args.por_banco)[:24]
        gravar_json(pasta / "candidatos" / f"{cena['id']}.json", {"cena": cena["id"], "consultas": consultas,
                                                                  "tipo": tipo, "candidatos": cands})
        if cands:
            folha_de_contato(cands, pasta / "candidatos" / f"{cena['id']}.jpg")
        print(f"{cena['id']}: {len(cands)} candidatos → {proj.rel(pasta / 'candidatos' / (cena['id'] + '.jpg')) if cands else '-'}")
        for i, c in enumerate(cands[:12]):
            print(f"   {i:>2} {c['tipo']:<6} {c['banco']:<9} {str(c.get('largura') or '?'):>5}px "
                  f"{(c.get('licenca') or '')[:22]:<22} {(c.get('titulo') or '')[:60]}")


if __name__ == "__main__":
    main()
