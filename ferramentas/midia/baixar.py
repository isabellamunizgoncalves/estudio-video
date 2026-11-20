#!/usr/bin/env python3
"""Baixa o candidato escolhido para uma cena, padroniza o arquivo e registra o crédito.

    python ferramentas/midia/baixar.py <canal/slug> --cena c012 --escolha 3
    python ferramentas/midia/baixar.py <canal/slug> --cena c012 --escolha 3 --inicio 42 --duracao 15
    python ferramentas/midia/baixar.py <canal/slug> --cena c012 --arquivo ~/fotos/avo.jpg --licenca "próprio"

- Vídeo → MP4 H.264 sem som, até 1920x1080, a partir de --inicio (s), no máx. --duracao (padrão 40 s).
- Imagem → JPG até 2560 px de largura (P&B preservado como está).
- Crédito (autor, licença, página) vai para 04_visual/creditos.json. Sem licença conhecida = recusa.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum.estudio import Projeto, agora, gravar_json, ler_json  # noqa: E402
from midia.bancos import UA, resolver_archive, resolver_wikimedia  # noqa: E402


def baixar_url(url: str, destino: Path, tentativas: int = 4) -> None:
    for n in range(tentativas):
        with requests.get(url, headers=UA, stream=True, timeout=60) as r:
            if r.status_code in (429, 503) and n < tentativas - 1:
                espera = int(r.headers.get("Retry-After", 0) or 0) or 5 * 2 ** n
                print(f"  servidor pediu calma ({r.status_code}); nova tentativa em {espera}s")
                time.sleep(min(espera, 60))
                continue
            r.raise_for_status()
            with open(destino, "wb") as f:
                for parte in r.iter_content(1 << 20):
                    f.write(parte)
            return


def padronizar_video(origem: Path, destino: Path, inicio: float, duracao: float) -> None:
    filtro = "scale='min(1920,iw)':'min(1080,ih)':force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2,fps=30"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(inicio), "-i", str(origem), "-t", str(duracao),
                    "-vf", filtro, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(destino)], check=True)


def padronizar_imagem(origem: Path, destino: Path) -> None:
    from PIL import Image, ImageOps

    img = ImageOps.exif_transpose(Image.open(origem))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((2560, 2560))
    img.save(destino, quality=90)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--cena", required=True)
    ap.add_argument("--escolha", type=int, help="número na folha de contato")
    ap.add_argument("--arquivo", help="arquivo local (foto própria ou enviada)")
    ap.add_argument("--licenca", help="licença do arquivo local")
    ap.add_argument("--autor", default="")
    ap.add_argument("--inicio", type=float, default=0.0)
    ap.add_argument("--duracao", type=float, default=40.0)
    args = ap.parse_args()

    proj = Projeto.abrir(args.projeto)
    pasta = proj.etapa("visual")
    midia = pasta / "midia"
    midia.mkdir(exist_ok=True)

    if args.arquivo:
        if not args.licenca:
            raise SystemExit("Arquivo local precisa de --licenca (ex.: 'próprio', 'CC BY 4.0').")
        origem = Path(args.arquivo).expanduser()
        ext = origem.suffix.lower()
        cand = {"banco": "local", "id": origem.name, "tipo": "video" if ext in (".mp4", ".mov", ".webm", ".mkv") else "imagem",
                "titulo": origem.stem, "autor": args.autor, "licenca": args.licenca, "pagina": "",
                "atribuicao": f"{args.autor or 'Arquivo próprio'} ({args.licenca})"}
    else:
        dados = ler_json(pasta / "candidatos" / f"{args.cena}.json")
        if not dados or args.escolha is None:
            raise SystemExit("Rode buscar.py antes e passe --escolha N (ou use --arquivo).")
        cand = dados["candidatos"][args.escolha]
        if not cand.get("licenca") or cand["licenca"] == "ver página":
            print(f"⚠ licença não identificada automaticamente — confira em {cand.get('pagina')}")
            print("  Se for livre, baixe e use --arquivo com --licenca explícita.")
            sys.exit(7)
        if cand["banco"] == "archive":
            url = resolver_archive(cand["id"])
        elif cand["banco"] == "wikimedia":
            url = resolver_wikimedia(cand["id"])
        else:
            url = cand.get("download")
        if not url:
            raise SystemExit("Candidato sem arquivo para baixar.")
        tmp = Path(tempfile.mkdtemp(prefix="midia_"))
        origem = tmp / ("bruto" + (Path(url.split("?")[0]).suffix or ".bin"))
        print(f"baixando {cand['banco']} {cand['id']}…")
        baixar_url(url, origem)
        cand = dict(cand, download=url)

    if cand["tipo"] == "video":
        destino = midia / f"{args.cena}.mp4"
        padronizar_video(origem, destino, args.inicio, args.duracao)
    else:
        destino = midia / f"{args.cena}.jpg"
        padronizar_imagem(origem, destino)
    if not args.arquivo:
        shutil.rmtree(origem.parent, ignore_errors=True)

    creditos = [c for c in ler_json(pasta / "creditos.json", []) if c["cena"] != args.cena]
    creditos.append({"cena": args.cena, "arquivo": proj.rel(destino), "tipo": cand["tipo"], "banco": cand["banco"],
                     "id": cand["id"], "titulo": cand.get("titulo"), "autor": cand.get("autor"),
                     "licenca": cand.get("licenca"), "licenca_url": cand.get("licenca_url"),
                     "pagina": cand.get("pagina"), "atribuicao": cand.get("atribuicao"),
                     "trecho": {"inicio": args.inicio, "duracao": args.duracao} if cand["tipo"] == "video" else None,
                     "baixado_em": agora()})
    creditos.sort(key=lambda c: c["cena"])
    gravar_json(pasta / "creditos.json", creditos)
    print(f"→ {proj.rel(destino)} · {cand.get('licenca')} · {cand.get('atribuicao')}")


if __name__ == "__main__":
    main()
