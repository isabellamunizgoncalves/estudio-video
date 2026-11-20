#!/usr/bin/env python3
"""Junta narração + decupagem + mídia + tema do canal num timeline.json para o Remotion.

    python ferramentas/edicao/montar_timeline.py <canal/slug>

Lê:   03_narracao/narracao_vNN.json (frases com tempo)
      04_visual/decupagem_vNN.json  (cenas → frases)
      04_visual/creditos.json       (cena → arquivo)
      04_visual/musica/*            (trilhas) e canais/<canal>/tema.json
Grava: 05_edicao/timeline_vNN.json  (tudo em quadros; caminhos relativos ao projeto)

Cada cena começa no início da sua 1ª frase e vai até o início da cena seguinte, então
imagem e voz ficam sempre sincronizadas, sem buraco. A 1ª cena começa no quadro 0.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum.estudio import Projeto, gravar_json, ler_json, proxima_versao, ultima_versao  # noqa: E402

FIM_EXTRA_S = 2.0  # respiro depois da última palavra


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--permitir-faltas", action="store_true", help="cena sem mídia vira cartela de cor (rascunho)")
    args = ap.parse_args()

    proj = Projeto.abrir(args.projeto)
    canal = proj.canal
    fmt = canal.get("formato", {})
    fps = int(fmt.get("fps", 30))
    tema = canal["_tema"]

    nar_arq = ultima_versao(proj.etapa("narracao"), "narracao", ".json")
    dec_arq = ultima_versao(proj.etapa("visual"), "decupagem", ".json")
    if not nar_arq or not dec_arq:
        raise SystemExit("Faltam narracao_vNN.json e/ou decupagem_vNN.json.")
    nar, dec = ler_json(nar_arq), ler_json(dec_arq)
    frases = nar["frases"]
    creditos = {c["cena"]: c for c in ler_json(proj.etapa("visual") / "creditos.json", [])}

    q = lambda s: int(round(s * fps))  # noqa: E731
    total = q(nar["duracao"] + FIM_EXTRA_S)

    cenas_dec = dec["cenas"]
    inicios = []
    for c in cenas_dec:
        idx = c.get("frases") or []
        if "inicio" in c:
            inicios.append(float(c["inicio"]))
        elif idx:
            inicios.append(frases[min(idx)]["inicio"])
        else:
            raise SystemExit(f"Cena {c['id']} sem 'frases' nem 'inicio'.")
    if any(b < a for a, b in zip(inicios, inicios[1:])):
        raise SystemExit("Cenas fora de ordem na decupagem (os inícios precisam crescer).")
    inicios[0] = 0.0

    faltas, cenas = [], []
    for i, c in enumerate(cenas_dec):
        ini = q(inicios[i])
        fim = q(inicios[i + 1]) if i + 1 < len(cenas_dec) else total
        tipo = c.get("tipo", "midia")
        cena = {
            "id": c["id"], "inicio": ini, "duracao": max(1, fim - ini), "tipo": tipo,
            "estilo": c.get("estilo", "tela-cheia"), "movimento": c.get("movimento", "zoom-in"),
            "transicao": c.get("transicao", tema.get("movimento", {}).get("transicao", "fade")),
            "pb": bool(c.get("pb", False)), "fundo": c.get("fundo"),
            "textoTela": c.get("texto_tela"), "titulo": c.get("titulo"), "subtitulo": c.get("subtitulo"),
            "camadas": [dict(k, src=creditos[k["cena"]]["arquivo"]) if k.get("cena") in creditos else k
                        for k in (c.get("camadas") or [])] or None,
        }
        if tipo == "midia":
            cred = creditos.get(c["id"])
            if cred:
                cena["src"] = cred["arquivo"]
                cena["midiaTipo"] = cred["tipo"]
            else:
                faltas.append(c["id"])
                cena["tipo"] = "cartela"
                cena["falta"] = True
        cenas.append(cena)

    if faltas and not args.permitir_faltas:
        raise SystemExit(f"Cenas sem mídia: {', '.join(faltas)} (rode buscar/baixar ou use --permitir-faltas).")

    # Logo do canal e trilhas vão para 05_edicao/assets/ (o Remotion só enxerga a pasta do projeto).
    assets = proj.etapa("edicao") / "assets"
    assets.mkdir(exist_ok=True)
    logo = ""
    if tema.get("logo"):
        src = Path(canal["_pasta"]) / tema["logo"]
        if src.exists():
            shutil.copy2(src, assets / src.name)
            logo = proj.rel(assets / src.name)

    musica = []
    vol_db = canal.get("musica", {}).get("volume_sob_voz_db", -22)
    for m in dec.get("musica", []):
        ids = [c["id"] for c in cenas]
        de = cenas[ids.index(m["de_cena"])]["inicio"] if m.get("de_cena") in ids else 0
        ate = cenas[ids.index(m["ate_cena"])] if m.get("ate_cena") in ids else None
        fim = (ate["inicio"] + ate["duracao"]) if ate else total
        musica.append({"src": m["arquivo"], "inicio": de, "duracao": fim - de,
                       "volume": round(10 ** (m.get("volume_db", vol_db) / 20), 4),
                       "inicioNoArquivo": q(m.get("inicio_no_arquivo", 0))})
    if not musica:
        trilhas = sorted(p for p in (proj.etapa("visual") / "musica").glob("*") if p.suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg"))
        if trilhas:
            musica.append({"src": proj.rel(trilhas[0]), "inicio": 0, "duracao": total,
                           "volume": round(10 ** (vol_db / 20), 4), "inicioNoArquivo": 0, "loop": True})

    legendas = []
    if canal.get("visual", {}).get("legendas") or tema.get("legendas", {}).get("ativas"):
        for f in frases:
            legendas.append({"inicio": q(f["inicio"]), "fim": q(f["fim"]) + 3, "texto": f["texto"]})

    timeline = {
        "canal": proj.dados["canal"], "slug": proj.dados["slug"], "titulo": proj.dados.get("tema", ""),
        "fps": fps, "largura": int(fmt.get("largura", 1920)), "altura": int(fmt.get("altura", 1080)),
        "duracaoQuadros": total, "tema": tema, "logo": logo,
        "audio": {"narracao": nar["audio"], "musica": musica, "sfx": dec.get("sfx", [])},
        "cenas": cenas, "legendas": legendas,
        "fontes": {"narracao": proj.rel(nar_arq), "decupagem": proj.rel(dec_arq)},
    }
    saida = proxima_versao(proj.etapa("edicao"), "timeline", ".json")
    gravar_json(saida, timeline)
    proj.marcar("timeline", arquivo=proj.rel(saida), cenas=len(cenas), faltas=faltas)
    print(f"→ {proj.rel(saida)} · {len(cenas)} cenas · {total / fps / 60:.1f} min" + (f" · {len(faltas)} sem mídia" if faltas else ""))


if __name__ == "__main__":
    main()
