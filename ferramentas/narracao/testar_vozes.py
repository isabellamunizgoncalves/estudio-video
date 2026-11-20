#!/usr/bin/env python3
"""Gera a mesma frase em várias vozes do Gemini para escolher a voz do canal.

    python ferramentas/narracao/testar_vozes.py --canal retrovisage
    python ferramentas/narracao/testar_vozes.py --canal retrovisage --vozes Charon,Gacrux,Algenib --texto "..."

Grava em canais/<canal>/amostras-voz/<Voz>.wav (fora do git). Depois, troque `narracao.voz` no canal.yaml.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum.estudio import CANAIS, carregar_canal  # noqa: E402
from narracao.gemini import VOZES, sintetizar  # noqa: E402

FRASES = {
    "fr": "Fermez les yeux une seconde… Vous sentez cette odeur ? C'est celle de la cuisine de votre grand-mère, un dimanche matin.",
    "pt": "Feche os olhos por um segundo… Sente esse cheiro? É a cozinha da sua avó, num domingo de manhã.",
    "en": "Close your eyes for a second… Can you smell that? It's your grandmother's kitchen, on a Sunday morning.",
    "es": "Cierra los ojos un segundo… ¿Hueles eso? Es la cocina de tu abuela, un domingo por la mañana.",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True)
    ap.add_argument("--vozes", help="lista separada por vírgula (padrão: 8 mais indicadas para narração)")
    ap.add_argument("--texto")
    args = ap.parse_args()
    canal = carregar_canal(args.canal)
    cfg = canal.get("narracao", {})
    idioma = canal.get("idioma", "pt-BR")
    texto = args.texto or FRASES.get(idioma[:2], FRASES["en"])
    vozes = args.vozes.split(",") if args.vozes else ["Charon", "Gacrux", "Algenib", "Sadaltager", "Iapetus",
                                                       "Sulafat", "Kore", "Vindemiatrix"]
    for v in vozes:
        if v not in VOZES:
            print(f"voz desconhecida: {v} (disponíveis: {', '.join(VOZES)})")
            continue
        destino = CANAIS / args.canal / "amostras-voz" / f"{v}.wav"
        sintetizar(texto, destino, voz=v, modelo=cfg.get("modelo", "gemini-2.5-pro-preview-tts"),
                   direcao=cfg.get("direcao", ""), idioma=idioma)
        print(f"→ {destino.relative_to(CANAIS.parent)}")


if __name__ == "__main__":
    main()
