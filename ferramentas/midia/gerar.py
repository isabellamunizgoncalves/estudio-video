#!/usr/bin/env python3
"""Gera a imagem de uma cena quando nenhum banco livre tem o que ela pede.

    python ferramentas/midia/gerar.py <canal/slug> --cena c012
    python ferramentas/midia/gerar.py <canal/slug> --cenas c012,c045,c114
    python ferramentas/midia/gerar.py <canal/slug> --faltantes          # todas as cenas sem mídia
    python ferramentas/midia/gerar.py <canal/slug> --cena c012 --semente 42
    python ferramentas/midia/gerar.py <canal/slug> --cena c012 --prompt "..."   # prompt à mão

Último recurso, não atalho: busque nos acervos primeiro. Cena encenada que o acervo livre
não tem (família à mesa, gesto doméstico, retrato) é o caso de uso; foto de arquivo que
existe é sempre melhor que imagem gerada.

Modelo: FLUX.2-klein-4B (Black Forest Labs), Apache 2.0, roda nesta máquina, sem API nem
chave. As variantes `dev` e `klein-9B` do FLUX são de licença NÃO COMERCIAL e não servem
para canal monetizado — não troque o modelo sem conferir a licença.

O estilo vem do canal (`visual.md` e `canal.yaml`), nunca daqui: esta ferramenta é genérica.

Grava: 04_visual/midia/<cena>.jpg
       04_visual/creditos.json  com banco "gerado", o modelo, o prompt e a SEMENTE — a
       semente permite refazer a mesma imagem depois. Entrada gerada leva `gerado: true`,
       que a etapa de publicação usa para marcar conteúdo sintético no YouTube.
"""

from __future__ import annotations

import argparse
import gc
import sys
import time
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum.estudio import Projeto, agora, gravar_json, ler_json, ultima_versao  # noqa: E402

MODELO = "black-forest-labs/FLUX.2-klein-4B"
LICENCA_MODELO = "Apache 2.0"
LARGURA, ALTURA = 1024, 576  # 16:9, a proporção do vídeo

# Fora do estilo do canal: o que nunca deve aparecer numa imagem de cena.
NEGATIVO_BASE = ("text, letters, caption, watermark, logo, signature, frame border, "
                 "collage, split screen, deformed hands, extra fingers, distorted face")


def estilo_do_canal(canal: dict, guia: str) -> str:
    """Monta o sufixo de estilo a partir do guia visual do canal.

    Lê `visual.geracao.estilo` do canal.yaml quando existe. Sem isso, cai num estilo
    fotográfico neutro: melhor uma imagem sem personalidade que uma com a personalidade
    de outro canal.
    """
    cfg = (canal.get("visual") or {}).get("geracao") or {}
    if cfg.get("estilo"):
        return str(cfg["estilo"]).strip()
    return ("documentary photograph, natural available light, shallow depth of field, "
            "35mm film grain, no text anywhere")


def montar_prompt(cena: dict, estilo: str) -> str:
    """Descrição da cena + estilo do canal. A descrição manda; o estilo é moldura.

    Prefere `prompt_geracao` da decupagem, que é escrito EM INGLÊS e já diz o tamanho do
    plano (close, plano aberto, o que entra no quadro). A `descricao` é escrita na língua
    do projeto e serve ao diretor e ao pesquisador, não ao modelo: em português ela produz
    cena errada — «osso do peito» e «vidraça» não sobrevivem, e sem dizer que é close o
    modelo inventa um plano aberto com gente demais.
    """
    desc = (cena.get("prompt_geracao") or cena.get("descricao") or "").strip().rstrip(".")
    extra = []
    if cena.get("pb"):
        extra.append("black and white")
    if cena.get("estilo") == "moldura":
        extra.append("centered composition with room around the subject")
    else:
        # Em tela cheia o 16:9 corta topo e base no movimento de câmera.
        extra.append("the action placed in the central band of the frame")
    return f"{estilo}. {desc}. " + ", ".join(extra) + "."


def gerar(prompts: dict[str, str], sementes: dict[str, int], destino) -> dict[str, dict]:
    """Gera as imagens em duas etapas, para caber na memória.

    O codificador de texto (8 GB) e o transformer (7,8 GB) não cabem juntos em 15 GB.
    Codifica todos os prompts primeiro, libera o codificador, e só então carrega o
    transformer — que fica carregado para todas as cenas da chamada.
    """
    import torch
    from diffusers import Flux2KleinPipeline

    torch.set_num_threads(torch.get_num_threads())
    t0 = time.time()

    print(f"  carregando o codificador de texto ({len(prompts)} cena(s))…", flush=True)
    pipe = Flux2KleinPipeline.from_pretrained(MODELO, transformer=None, vae=None,
                                              dtype=torch.bfloat16)
    embeds = {}
    with torch.no_grad():
        for cena, p in prompts.items():
            e = pipe.encode_prompt(prompt=[p], device="cpu", num_images_per_prompt=1)
            embeds[cena] = e[0] if isinstance(e, tuple) else e
    del pipe
    gc.collect()
    print(f"  [{time.time() - t0:.0f}s] prompts codificados; codificador liberado", flush=True)

    pipe = Flux2KleinPipeline.from_pretrained(MODELO, text_encoder=None, tokenizer=None,
                                              dtype=torch.bfloat16)
    print(f"  [{time.time() - t0:.0f}s] gerador carregado", flush=True)

    feitas = {}
    for cena, emb in embeds.items():
        t1 = time.time()
        img = pipe(prompt_embeds=emb, height=ALTURA, width=LARGURA, num_inference_steps=4,
                   guidance_scale=4.0,
                   generator=torch.Generator("cpu").manual_seed(sementes[cena])).images[0]
        arq = destino(cena)
        arq.parent.mkdir(parents=True, exist_ok=True)
        img.convert("RGB").save(arq, "JPEG", quality=92)
        feitas[cena] = {"arquivo": arq, "segundos": round(time.time() - t1, 1)}
        print(f"  {cena}: {feitas[cena]['segundos']}s → {arq.name}", flush=True)
    del pipe
    gc.collect()
    return feitas


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--cena")
    ap.add_argument("--cenas", help="lista separada por vírgula")
    ap.add_argument("--faltantes", action="store_true",
                    help="todas as cenas que pedem mídia e ainda não têm")
    ap.add_argument("--prompt", help="prompt à mão (só com --cena)")
    ap.add_argument("--semente", type=int, help="repete uma imagem já gerada")
    ap.add_argument("--refazer", action="store_true",
                    help="gera de novo uma cena que já tem mídia")
    args = ap.parse_args()

    proj = Projeto.abrir(args.projeto)
    canal = proj.canal
    pasta = proj.etapa("visual")
    dec_arq = ultima_versao(pasta, "decupagem", ".json")
    if not dec_arq:
        raise SystemExit("Não há decupagem. Rode o diretor-visual primeiro.")
    cenas = {c["id"]: c for c in ler_json(dec_arq, {"cenas": []})["cenas"]}
    creditos = ler_json(pasta / "creditos.json", [])
    com_midia = {e["cena"] for e in creditos}

    if args.faltantes:
        alvos = [i for i, c in cenas.items() if c.get("busca") and i not in com_midia]
    elif args.cenas:
        alvos = [x.strip() for x in args.cenas.split(",") if x.strip()]
    elif args.cena:
        alvos = [args.cena]
    else:
        raise SystemExit("Use --cena, --cenas ou --faltantes.")

    if not args.refazer:
        jah = [i for i in alvos if i in com_midia]
        if jah:
            print(f"já têm mídia, puladas (use --refazer): {', '.join(jah)}")
        alvos = [i for i in alvos if i not in com_midia]
    if not alvos:
        print("Nada a gerar.")
        return
    faltam = [i for i in alvos if i not in cenas]
    if faltam:
        raise SystemExit(f"Cenas fora da decupagem: {', '.join(faltam)}")

    guia = (Path("canais") / proj.dados["canal"] / (canal.get("visual") or {}).get("guia", "visual.md"))
    estilo = estilo_do_canal(canal, guia.read_text(encoding="utf-8") if guia.exists() else "")

    prompts, sementes = {}, {}
    for i in alvos:
        prompts[i] = args.prompt if (args.prompt and len(alvos) == 1) else montar_prompt(cenas[i], estilo)
        # Semente estável por cena: a mesma cena gera a mesma imagem se nada mudar.
        # crc32, não hash(): o hash de str do Python muda a cada processo e a semente
        # precisa valer entre sessões, senão a imagem não se refaz igual.
        sementes[i] = args.semente if args.semente is not None else (zlib.crc32(i.encode()) % 100000)
        print(f"{i}: {prompts[i][:150]}")

    feitas = gerar(prompts, sementes, lambda c: pasta / "midia" / f"{c}.jpg")

    creditos = [e for e in ler_json(pasta / "creditos.json", []) if e["cena"] not in feitas]
    for cena, info in feitas.items():
        creditos.append({
            "cena": cena,
            "arquivo": proj.rel(info["arquivo"]),
            "tipo": "imagem",
            "banco": "gerado",
            "id": f"{MODELO}#{sementes[cena]}",
            "titulo": (cenas[cena].get("descricao") or "")[:120],
            "autor": None,
            "licenca": f"imagem gerada — modelo {MODELO} ({LICENCA_MODELO})",
            "licenca_url": f"https://huggingface.co/{MODELO}",
            "pagina": None,
            "atribuicao": None,
            "trecho": None,
            "baixado_em": agora(),
            "gerado": True,
            "modelo": MODELO,
            "semente": sementes[cena],
            "prompt": prompts[cena],
            "observacao": ("IMAGEM GERADA, não é documento histórico. "
                           "A publicação precisa marcar conteúdo sintético no YouTube."),
        })
    creditos.sort(key=lambda e: e["cena"])
    gravar_json(pasta / "creditos.json", creditos)
    print(f"\n{len(feitas)} imagem(ns) gerada(s) · creditos.json atualizado")
    print("Lembrete: entrada com `gerado: true` exige marcar conteúdo sintético na publicação.")


if __name__ == "__main__":
    main()
