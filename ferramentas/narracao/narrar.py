#!/usr/bin/env python3
"""Narração com Gemini TTS em blocos de ~1 minuto, verificada palavra por palavra.

    python ferramentas/narracao/narrar.py <canal/slug>                 # narra tudo (nova versão)
    python ferramentas/narracao/narrar.py <canal/slug> --blocos 4,9    # refaz só esses blocos
    python ferramentas/narracao/narrar.py <canal/slug> --plano         # só mostra a divisão em blocos
    python ferramentas/narracao/narrar.py <canal/slug> --voz Gacrux --modelo gemini-2.5-flash-preview-tts

Para cada bloco: gera → transcreve (Whisper) → compara com o texto. Se divergir (palavra
inventada, pulada, instrução lida, corte, silêncio, duração estranha) gera de novo, até
`verificacao.tentativas` vezes, e fica com a melhor tomada. Depois apara as pontas,
junta os blocos com pausa fixa e normaliza o volume.

Lê:   02_roteiro/roteiro_narracao_vNN.txt (humanizado; senão roteiro_vNN.txt)
      02_roteiro/direcao_vNN.json (opcional: [{"paragrafo": 1, "tom": "..."}])
Grava: 03_narracao/narracao_vNN.wav        áudio final (48 kHz, -16 LUFS)
       03_narracao/narracao_vNN.json       manifesto: blocos, palavras e frases com tempo
       03_narracao/qa_vNN.md               relatório de verificação
       03_narracao/blocos_vNN/             tomadas de cada bloco
Saída 6 = algum bloco ficou reprovado após todas as tentativas.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum.estudio import Projeto, gravar_json, ler_json, numero_versao, proxima_versao, ultima_versao  # noqa: E402
from narracao.blocos import Bloco, dividir, frases  # noqa: E402

TEMPERATURAS = [None, 0.8, 1.0, 0.6, 1.2, 0.9]


def texto_fonte(proj: Projeto, forcado: str | None) -> Path:
    if forcado:
        return proj.pasta / forcado
    pasta = proj.etapa("roteiro")
    achado = ultima_versao(pasta, "roteiro_narracao", ".txt") or ultima_versao(pasta, "roteiro", ".txt")
    if not achado:
        raise SystemExit("Nenhum roteiro_narracao_vNN.txt nem roteiro_vNN.txt em 02_roteiro/.")
    return achado


def tom_do_bloco(direcao: list[dict], bloco: Bloco) -> str:
    tom = ""
    for d in sorted(direcao, key=lambda d: d.get("paragrafo", 1)):
        if d.get("paragrafo", 1) - 1 <= bloco.primeiro_paragrafo:
            tom = d.get("tom", "")
    return tom


def ler_pcm(caminho: Path) -> tuple[bytes, int]:
    with wave.open(str(caminho), "rb") as w:
        return w.readframes(w.getnframes()), w.getframerate()


def aparar(origem: Path, destino: Path, inicio: float, fim: float) -> float:
    dados, taxa = ler_pcm(origem)
    a, b = int(inicio * taxa) * 2, int(fim * taxa) * 2
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        w.writeframes(dados[a:b])
    return (b - a) / 2 / taxa


def narrar_bloco(bloco: Bloco, pasta: Path, cfg: dict, idioma: str, ppm: int, tom: str, voz: str, modelo: str):
    from narracao.gemini import sintetizar
    from narracao.verificar import verificar

    ver = cfg.get("verificacao", {})
    n_tent = int(ver.get("tentativas", 4))
    reserva = cfg.get("modelo_reserva") or modelo
    melhor = None
    for t in range(1, n_tent + 1):
        mod = reserva if (t == n_tent and n_tent > 2) else modelo
        arq = pasta / f"bloco_{bloco.indice:03d}_t{t}.wav"
        opcoes = dict(voz=voz, direcao=cfg.get("direcao", ""), tom=tom, idioma=idioma,
                      temperatura=TEMPERATURAS[(t - 1) % len(TEMPERATURAS)])
        try:
            sintetizar(bloco.texto, arq, modelo=mod, **opcoes)
        except Exception as exc:
            if mod == reserva or getattr(exc, "code", None) not in (400, 404):
                raise
            print(f"    {mod} recusou ({getattr(exc, 'code', '')}); usando {reserva}")
            mod = reserva
            sintetizar(bloco.texto, arq, modelo=mod, **opcoes)
        r = verificar(arq, bloco.texto, idioma, ppm, ver.get("similaridade_minima", 0.93),
                      ver.get("desvio_duracao_max", 0.35))
        estado = "✔" if r.aprovado else "✖ " + "; ".join(r.problemas)
        print(f"    tomada {t} ({mod.split('-')[2] if mod.count('-') > 2 else mod}): sim {r.similaridade:.3f}, "
              f"{r.duracao:.1f}s {estado}")
        if melhor is None or r.nota > melhor[1].nota:
            melhor = (arq, r, t)
        if r.aprovado:
            break
    return melhor


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--texto", help="caminho relativo ao projeto (padrão: humanizado mais recente)")
    ap.add_argument("--blocos", help="refazer só estes blocos (ex.: 3,7) reaproveitando a versão anterior")
    ap.add_argument("--voz")
    ap.add_argument("--modelo")
    ap.add_argument("--plano", action="store_true", help="só mostra a divisão em blocos")
    args = ap.parse_args()

    proj = Projeto.abrir(args.projeto)
    canal = proj.canal
    cfg = canal.get("narracao", {})
    idioma = proj.dados.get("idioma") or canal.get("idioma", "pt-BR")
    ppm = int(canal.get("roteiro", {}).get("palavras_por_minuto", 150))
    voz = args.voz or cfg.get("voz", "Kore")
    modelo = args.modelo or cfg.get("modelo", "gemini-2.5-pro-preview-tts")

    fonte = texto_fonte(proj, args.texto)
    texto = fonte.read_text(encoding="utf-8")
    blocos = dividir(texto, ppm, int(cfg.get("bloco_segundos", 60)))
    direcao_arq = fonte.parent / f"direcao_v{numero_versao(fonte)}.json"
    direcao = ler_json(direcao_arq, []) or []

    print(f"Fonte: {proj.rel(fonte)} · {len(blocos)} blocos · voz {voz} · {modelo}")
    if args.plano:
        for b in blocos:
            print(f"  bloco {b.indice:03d}: {b.palavras} palavras (~{b.palavras / ppm * 60:.0f}s) "
                  f"tom: {tom_do_bloco(direcao, b) or '-'} | {b.texto[:70]}…")
        return

    pasta = proj.etapa("narracao")
    saida = proxima_versao(pasta, "narracao", ".wav")
    v = numero_versao(saida)
    trabalho = pasta / f"blocos_v{v}"
    trabalho.mkdir(parents=True, exist_ok=True)

    refazer = {int(x) for x in args.blocos.split(",")} if args.blocos else None
    anterior = ler_json(ultima_versao(pasta, "narracao", ".json"), None) if refazer else None
    if refazer and not anterior:
        raise SystemExit("--blocos precisa de uma versão anterior para reaproveitar.")

    pausa = int(cfg.get("pausa_bloco_ms", 450)) / 1000
    resultados = []
    for b in blocos:
        print(f"  bloco {b.indice:03d}/{len(blocos):03d} ({b.palavras} palavras)")
        reaproveitar = None
        if anterior and b.indice not in refazer:
            reaproveitar = next((x for x in anterior["blocos"] if x["indice"] == b.indice and x["texto"] == b.texto), None)
        if reaproveitar:
            src = proj.pasta / reaproveitar["arquivo"]
            dst = trabalho / src.name
            shutil.copy2(src, dst)
            info = dict(reaproveitar, arquivo=proj.rel(dst))
            info["palavras_tempo"] = reaproveitar["palavras_tempo"]
            print("    reaproveitado da versão anterior")
            resultados.append(info)
            continue
        arq, r, t = narrar_bloco(b, trabalho, cfg, idioma, ppm, tom_do_bloco(direcao, b), voz, modelo)
        ini = max(0.0, r.inicio_fala - 0.12)
        fim = min(r.duracao, r.fim_fala + 0.35) if r.fim_fala else r.duracao
        final = trabalho / f"bloco_{b.indice:03d}.wav"
        dur = aparar(arq, final, ini, fim)
        resultados.append({
            "indice": b.indice, "texto": b.texto, "primeiro_paragrafo": b.primeiro_paragrafo,
            "arquivo": proj.rel(final), "duracao": round(dur, 3), "tomadas": t,
            "similaridade": r.similaridade, "aprovado": r.aprovado, "problemas": r.problemas,
            "transcrito": r.transcrito,
            "palavras_tempo": [dict(p, inicio=round(max(0, p["inicio"] - ini), 3), fim=round(max(0, p["fim"] - ini), 3))
                               for p in r.palavras],
        })

    # Junta os blocos com silêncio fixo entre eles.
    bruto = trabalho / "_junto.wav"
    taxa = ler_pcm(proj.pasta / resultados[0]["arquivo"])[1]
    cursor = 0.0
    palavras, frases_out = [], []
    with wave.open(str(bruto), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        for i, res in enumerate(resultados):
            dados, tx = ler_pcm(proj.pasta / res["arquivo"])
            if tx != taxa:
                raise SystemExit(f"Bloco {res['indice']} com taxa {tx} ≠ {taxa}: refaça a narração inteira.")
            res["inicio"] = round(cursor, 3)
            w.writeframes(dados)
            dur = len(dados) / 2 / taxa
            res["fim"] = round(cursor + dur, 3)
            pts = res["palavras_tempo"]
            for p in pts:
                palavras.append({"texto": p["texto"], "inicio": round(cursor + p["inicio"], 3),
                                 "fim": round(cursor + p["fim"], 3), "bloco": res["indice"]})
            # frases do bloco, com tempo vindo das palavras
            k = 0
            par = res.get("primeiro_paragrafo", 0)
            for paragrafo in res["texto"].split("\n\n"):
                for f in frases(paragrafo):
                    from narracao.verificar import tokens
                    n = len(tokens(f))
                    if n == 0 or k >= len(pts):
                        continue
                    trecho = pts[k:k + n]
                    frases_out.append({"indice": len(frases_out), "texto": f, "bloco": res["indice"], "paragrafo": par,
                                       "inicio": round(cursor + trecho[0]["inicio"], 3),
                                       "fim": round(cursor + trecho[-1]["fim"], 3)})
                    k += n
                par += 1
            cursor += dur
            if i < len(resultados) - 1:
                w.writeframes(b"\x00\x00" * int(pausa * taxa))
                cursor += pausa

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(bruto), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
           "-ar", "48000", "-ac", "1", str(saida)]
    subprocess.run(cmd, check=True)
    bruto.unlink(missing_ok=True)

    reprovados = [r for r in resultados if not r.get("aprovado")]
    manifesto = {
        "versao": v, "fonte": proj.rel(fonte), "audio": proj.rel(saida), "voz": voz, "modelo": modelo,
        "idioma": idioma, "duracao": round(cursor, 3), "pausa_bloco": pausa,
        "blocos": resultados, "palavras": palavras, "frases": frases_out,
    }
    gravar_json(pasta / f"narracao_v{v}.json", manifesto)

    linhas = [f"# QA da narração v{v}", "", f"- Fonte: `{proj.rel(fonte)}`", f"- Voz: {voz} · {modelo}",
              f"- Duração: {int(cursor // 60)}min{int(cursor % 60):02d}s · {len(resultados)} blocos · "
              f"{len(reprovados)} reprovados", "", "| Bloco | Início | Duração | Tomadas | Similaridade | Situação |",
              "|---|---|---|---|---|---|"]
    for r in resultados:
        sit = "ok" if r.get("aprovado") else "⚠ " + "; ".join(r.get("problemas", []))
        linhas.append(f"| {r['indice']} | {int(r['inicio'] // 60)}:{int(r['inicio'] % 60):02d} | {r['duracao']:.1f}s | "
                      f"{r.get('tomadas', '-')} | {r.get('similaridade', 0):.3f} | {sit} |")
    if reprovados:
        linhas += ["", "## Reprovados — ouvir e decidir", ""]
        for r in reprovados:
            linhas += [f"### Bloco {r['indice']}", "", f"**Texto:** {r['texto']}", "", f"**Ouvido:** {r.get('transcrito', '')}", ""]
        linhas.append(f"Refazer: `python ferramentas/narracao/narrar.py {args.projeto} --blocos "
                      f"{','.join(str(r['indice']) for r in reprovados)}`")
    (pasta / f"qa_v{v}.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    proj.marcar("narracao", audio=proj.rel(saida), duracao=round(cursor, 1), reprovados=len(reprovados))

    print(f"\n→ {proj.rel(saida)} ({int(cursor // 60)}min{int(cursor % 60):02d}s)")
    print(f"→ {proj.rel(pasta / f'qa_v{v}.md')}")
    if reprovados:
        print(f"⚠ {len(reprovados)} bloco(s) reprovado(s): {', '.join(str(r['indice']) for r in reprovados)}")
        sys.exit(6)


if __name__ == "__main__":
    main()
