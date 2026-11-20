#!/usr/bin/env python3
"""Renderiza o timeline do projeto com o Remotion.

    python ferramentas/edicao/render.py <canal/slug> --previa            # 960x540, rápido, para revisar
    python ferramentas/edicao/render.py <canal/slug> --previa --de 120 --ate 180   # só um trecho (segundos)
    python ferramentas/edicao/render.py <canal/slug>                     # final 1080p
    python ferramentas/edicao/render.py <canal/slug> --studio            # abre o Remotion Studio no projeto

Grava 05_edicao/renders/previa_vNN.mp4 ou video_vNN.mp4 (NN = versão do timeline).
Chrome próprio: exporte REMOTION_CHROME=/caminho/do/chrome (senão o Remotion baixa o dele).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum.estudio import RAIZ, Projeto, ler_json, numero_versao, ultima_versao  # noqa: E402

REMOTION = RAIZ / "estudio-remotion"


def duracao_midia(caminho: Path, fps: int) -> int | None:
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(caminho)],
                           capture_output=True, text=True, timeout=30)
        return int(float(r.stdout.strip()) * fps)
    except (ValueError, OSError, subprocess.TimeoutExpired):
        return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--timeline", help="caminho relativo ao projeto (padrão: o mais recente)")
    ap.add_argument("--previa", action="store_true")
    ap.add_argument("--de", type=float, help="segundo inicial")
    ap.add_argument("--ate", type=float, help="segundo final")
    ap.add_argument("--studio", action="store_true")
    ap.add_argument("--concorrencia", default=os.environ.get("REMOTION_CONCORRENCIA", "50%"))
    args = ap.parse_args()

    proj = Projeto.abrir(args.projeto)
    tl_arq = proj.pasta / args.timeline if args.timeline else ultima_versao(proj.etapa("edicao"), "timeline", ".json")
    if not tl_arq or not tl_arq.exists():
        raise SystemExit("Nenhum timeline_vNN.json (rode montar_timeline.py).")
    tl = ler_json(tl_arq)

    # duração real de cada vídeo (para repetir em loop se for mais curto que a cena)
    for c in tl["cenas"]:
        if c.get("src") and c.get("midiaTipo") == "video":
            c["midiaDuracao"] = duracao_midia(proj.pasta / c["src"], tl["fps"])

    if not (REMOTION / "node_modules").exists():
        subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=REMOTION, check=True)

    props = Path(tempfile.mkstemp(prefix="props_", suffix=".json")[1])
    props.write_text(json.dumps({"timeline": tl}, ensure_ascii=False), encoding="utf-8")

    base = ["--props", str(props), "--public-dir", str(proj.pasta)]
    if os.environ.get("REMOTION_CHROME"):
        base += ["--browser-executable", os.environ["REMOTION_CHROME"]]
    if args.studio:
        subprocess.run(["npx", "remotion", "studio", "src/index.ts", *base], cwd=REMOTION)
        return

    v = numero_versao(tl_arq)
    nome = f"{'previa' if args.previa else 'video'}_v{v}"
    if args.de is not None or args.ate is not None:
        nome += f"_{int(args.de or 0)}-{int(args.ate) if args.ate is not None else 'fim'}"
    saida = proj.etapa("edicao") / "renders" / f"{nome}.mp4"
    saida.parent.mkdir(exist_ok=True)

    cmd = ["npx", "remotion", "render", "src/index.ts", "Video", str(saida), *base, "--concurrency", str(args.concorrencia)]
    if args.previa:
        cmd += ["--scale", "0.5", "--crf", "28"]
    if args.de is not None or args.ate is not None:
        a = int((args.de or 0) * tl["fps"])
        b = int(args.ate * tl["fps"]) if args.ate is not None else tl["duracaoQuadros"] - 1
        cmd += ["--frames", f"{a}-{min(b, tl['duracaoQuadros'] - 1)}"]
    print(" ".join(cmd[:6]), "…")
    r = subprocess.run(cmd, cwd=REMOTION)
    props.unlink(missing_ok=True)
    if r.returncode != 0:
        sys.exit(r.returncode)
    proj.marcar("render", arquivo=proj.rel(saida), previa=args.previa)
    print(f"→ {proj.rel(saida)}")


if __name__ == "__main__":
    main()
