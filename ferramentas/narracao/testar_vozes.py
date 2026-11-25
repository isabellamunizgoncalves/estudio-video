#!/usr/bin/env python3
"""Gera a mesma frase em várias vozes do Gemini para escolher a voz do canal.

    python ferramentas/narracao/testar_vozes.py --canal retrovisage --perfil masculina
    python ferramentas/narracao/testar_vozes.py --canal retrovisage --vozes Charon,Algenib --texto "..."
    python ferramentas/narracao/testar_vozes.py --canal retrovisage --perfil feminina --todas

Grava em canais/<canal>/amostras-voz/<Voz>.wav (fora do git). Depois, troque `narracao.voz` no canal.yaml.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum.estudio import CANAIS, carregar_canal  # noqa: E402
from narracao.gemini import GENERO_VOZ, VOZES, sintetizar, vozes_por_genero  # noqa: E402

FRASES = {
    "fr": "Fermez les yeux une seconde… Vous sentez cette odeur ? C'est celle de la cuisine de votre grand-mère, un dimanche matin.",
    "pt": "Feche os olhos por um segundo… Sente esse cheiro? É a cozinha da sua avó, num domingo de manhã.",
    "en": "Close your eyes for a second… Can you smell that? It's your grandmother's kitchen, on a Sunday morning.",
    "es": "Cierra los ojos un segundo… ¿Hueles eso? Es la cocina de tu abuela, un domingo por la mañana.",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", required=True)
    ap.add_argument("--vozes", help="lista separada por vírgula (vence o --perfil)")
    ap.add_argument("--perfil", choices=["masculina", "feminina", "todas"], default="masculina",
                    help="gênero das vozes a testar (padrão: masculina)")
    ap.add_argument("--todas", action="store_true",
                    help="testa todas as vozes do perfil, não só a seleção curta")
    ap.add_argument("--texto")
    ap.add_argument("--modelo", help="padrão: narracao.modelo do canal, com queda para o modelo_reserva")
    args = ap.parse_args()
    canal = carregar_canal(args.canal)
    cfg = canal.get("narracao", {})
    idioma = canal.get("idioma", "pt-BR")
    texto = args.texto or FRASES.get(idioma[:2], FRASES["en"])
    # Seleção curta por gênero: o Google não publica timbre, então são 8 para Isabella ouvir
    # e escolher, sem gastar uma requisição por cada uma das 30.
    curtas = {
        "masculina": ["Charon", "Algenib", "Rasalgethi", "Iapetus", "Sadaltager", "Schedar", "Alnilam", "Achird"],
        "feminina": ["Gacrux", "Sulafat", "Vindemiatrix", "Kore", "Achernar", "Erinome", "Autonoe", "Despina"],
    }
    if args.vozes:
        vozes = args.vozes.split(",")
    elif args.todas:
        vozes = vozes_por_genero({"masculina": "m", "feminina": "f", "todas": "t"}[args.perfil])
    else:
        vozes = curtas.get(args.perfil) or vozes_por_genero("t")
    print(f"Canal {args.canal} · perfil {args.perfil} · {len(vozes)} vozes · {idioma}")
    modelo = args.modelo or cfg.get("modelo", "gemini-2.5-pro-preview-tts")
    reserva = cfg.get("modelo_reserva")
    feitas, falhas = 0, []
    for v in vozes:
        if v not in VOZES:
            print(f"voz desconhecida: {v} (disponíveis: {', '.join(VOZES)})")
            continue
        destino = CANAIS / args.canal / "amostras-voz" / f"{v}.wav"
        if destino.exists():
            print(f"= {destino.relative_to(CANAIS.parent)} já existe, pulando")
            feitas += 1
            continue
        opcoes = dict(voz=v, direcao=cfg.get("direcao", ""), idioma=idioma)
        try:
            sintetizar(texto, destino, modelo=modelo, **opcoes)
        except Exception as exc:
            # O modelo preferido do canal pode não existir no plano da conta (o pro tem limite
            # zero no gratuito): tenta o reserva antes de desistir desta voz.
            if not reserva or reserva == modelo:
                print(f"✖ {v}: {type(exc).__name__}: {str(exc)[:120]}")
                falhas.append(v)
                continue
            print(f"  {modelo} não atendeu; tentando {reserva}")
            try:
                sintetizar(texto, destino, modelo=reserva, **opcoes)
            except Exception as exc2:
                print(f"✖ {v}: {type(exc2).__name__}: {str(exc2)[:120]}")
                falhas.append(v)
                continue
        feitas += 1
        print(f"→ {destino.relative_to(CANAIS.parent)}  ({'masculina' if GENERO_VOZ.get(v) == 'm' else 'feminina'})")

    print(f"\n{feitas} de {len(vozes)} amostras em canais/{args.canal}/amostras-voz/")
    if falhas:
        print(f"faltaram: {', '.join(falhas)} — rode de novo depois (as prontas são puladas)")


if __name__ == "__main__":
    main()
