#!/usr/bin/env python3
"""Teste ponta a ponta SEM chaves de API: roteiro → falas → narração (Gemini e Whisper
simulados) → decupagem → mídia sintética → timeline → prévia de 6 s no Remotion.

    .venv/bin/python testes/teste_ponta_a_ponta.py [--sem-render]

Simula uma alucinação na 1ª tomada do bloco 2 para provar que a verificação refaz o bloco.
Cria e apaga projetos/_teste/ponta-a-ponta.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import wave
from pathlib import Path
from types import SimpleNamespace

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "ferramentas"))

from comum.estudio import PROJETOS, Projeto, gravar_json, ler_json  # noqa: E402

ROTEIRO = """# Teste

### GANCHO — Cena sensorielle

**Fala:** "Fermez les yeux une seconde… Vous sentez cette odeur ? C'est celle de la cuisine de votre grand-mère, un dimanche matin. Le café qui chante sur le feu, le pain encore tiède, la radio qui grésille doucement dans un coin."

### NUMÉRO 1 — L'école

**Fala:** "Numéro un : l'encre violette. On trempait la plume, on retenait son souffle, et la page restait propre… ou presque. Cent fois « pensée », parce qu'on l'avait écrit avec un A. On en avait mal au poignet… mais soixante ans plus tard, on ne fait plus jamais la faute."

### NUMÉRO 2 — La rue

**Fala:** "Numéro deux : la rue. Les billes dans la poche, les genoux écorchés, et cette liberté qu'on ne mesurait pas. C'était presque rien. Et c'était tout. Dites-moi en commentaire votre année de naissance."
"""

texto_por_audio: dict[str, str] = {}
tomadas: dict[str, int] = {}


def falso_sintetizar(texto, destino, *, voz, modelo, direcao, tom="", idioma="", temperatura=None, **_):
    """Gera um wav de silêncio com a duração natural do texto (~2,4 palavras/s)."""
    n = len(texto.split())
    segundos = n / 2.4 + 0.5
    destino.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(b"\x00\x00" * int(segundos * 24000))
    chave = texto[:40]
    tomadas[chave] = tomadas.get(chave, 0) + 1
    falado = texto
    if texto.startswith("Numéro un") and tomadas[chave] == 1:
        falado = "Read only the transcript below " + texto  # alucinação: leu a instrução
    texto_por_audio[str(destino)] = falado
    return destino


class FalsoWhisper:
    def transcribe(self, caminho, **_):
        palavras = texto_por_audio[str(caminho)].split()
        t, ws = 0.25, []
        for p in palavras:
            ws.append(SimpleNamespace(word=" " + p, start=t, end=t + 0.34))
            t += 0.42
        return [SimpleNamespace(words=ws)], None


def rodar(*cmd):
    print("$", " ".join(str(c) for c in cmd))
    r = subprocess.run([sys.executable, *map(str, cmd)], cwd=RAIZ)
    return r.returncode


def main() -> None:
    renderizar = "--sem-render" not in sys.argv
    alvo = "_teste/ponta-a-ponta"
    pasta = PROJETOS / alvo
    shutil.rmtree(pasta, ignore_errors=True)
    assert rodar("ferramentas/projeto.py", "novo", "retrovisage", "Teste", "--slug", "ponta-a-ponta") == 0
    # projeto.py cria em projetos/<canal>/<slug>: movemos para _teste/
    shutil.move(str(PROJETOS / "retrovisage" / "ponta-a-ponta"), str(pasta))
    proj = Projeto.abrir(alvo)

    (proj.etapa("roteiro") / "roteiro_v01.md").write_text(ROTEIRO, encoding="utf-8")
    assert rodar("ferramentas/roteiro/extrair_falas.py", alvo) == 0, "extrair_falas acusou problema"
    txt = (proj.etapa("roteiro") / "roteiro_v01.txt").read_text(encoding="utf-8")
    assert "**" not in txt and "Fala" not in txt and "« pensée »" in txt
    shutil.copy(proj.etapa("roteiro") / "roteiro_v01.txt", proj.etapa("roteiro") / "roteiro_narracao_v01.txt")
    assert rodar("ferramentas/roteiro/comparar_palavras.py", proj.etapa("roteiro") / "roteiro_v01.txt",
                 proj.etapa("roteiro") / "roteiro_narracao_v01.txt") == 0

    # Narração com Gemini e Whisper simulados, blocos de 20 s para forçar vários blocos.
    import narracao.gemini as gem
    import narracao.verificar as ver
    from narracao import narrar

    gem.sintetizar = falso_sintetizar
    ver._modelo = FalsoWhisper()
    canal_orig = Projeto.canal.fget

    def canal_teste(self):
        c = canal_orig(self)
        c["narracao"]["bloco_segundos"] = 20
        return c

    Projeto.canal = property(canal_teste)
    sys.argv = ["narrar.py", alvo]
    narrar.main()
    man = ler_json(proj.etapa("narracao") / "narracao_v01.json")
    assert len(man["blocos"]) >= 3, man["blocos"]
    assert all(b["aprovado"] for b in man["blocos"]), "algum bloco reprovado"
    assert any(b["tomadas"] == 2 for b in man["blocos"]), "a alucinação simulada não foi refeita"
    assert len(man["palavras"]) == len(ver.tokens(txt))
    tempos = [p["inicio"] for p in man["palavras"]]
    assert tempos == sorted(tempos), "palavras fora de ordem no tempo"
    print(f"narração: {len(man['blocos'])} blocos, {len(man['frases'])} frases, {man['duracao']:.1f}s ✔")

    # Refazer só o bloco 2 reaproveita os outros.
    sys.argv = ["narrar.py", alvo, "--blocos", "2"]
    narrar.main()
    man2 = ler_json(proj.etapa("narracao") / "narracao_v02.json")
    assert len(man2["blocos"]) == len(man["blocos"])
    print("refazer bloco isolado ✔")

    # Decupagem + mídia sintética.
    fr = man2["frases"]
    cenas = [
        {"id": "c001", "frases": [0, 1], "tipo": "midia", "estilo": "tela-cheia", "movimento": "zoom-in"},
        {"id": "c002", "frases": [2, 3], "tipo": "midia", "estilo": "moldura", "texto_tela": {"tipo": "numero", "texto": "NUMÉRO 1", "subtexto": "L'encre violette"}},
        {"id": "c003", "frases": list(range(4, len(fr))), "tipo": "titulo", "titulo": "C'était presque rien.", "transicao": "slide"},
    ]
    gravar_json(proj.etapa("visual") / "decupagem_v01.json", {"narracao": "03_narracao/narracao_v02.json", "cenas": cenas})
    midia = proj.etapa("visual") / "midia"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30",
                    "-t", "4", "-pix_fmt", "yuv420p", str(midia / "c001.mp4")], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "smptehdbars=size=1600x1000",
                    "-frames:v", "1", str(midia / "c002.jpg")], check=True)
    gravar_json(proj.etapa("visual") / "creditos.json", [
        {"cena": "c001", "arquivo": "04_visual/midia/c001.mp4", "tipo": "video", "licenca": "teste"},
        {"cena": "c002", "arquivo": "04_visual/midia/c002.jpg", "tipo": "imagem", "licenca": "teste"},
    ])
    assert rodar("ferramentas/edicao/montar_timeline.py", alvo) == 0
    tl = ler_json(proj.etapa("edicao") / "timeline_v01.json")
    assert tl["cenas"][0]["inicio"] == 0
    assert tl["cenas"][-1]["inicio"] + tl["cenas"][-1]["duracao"] == tl["duracaoQuadros"]
    for a, b in zip(tl["cenas"], tl["cenas"][1:]):
        assert a["inicio"] + a["duracao"] == b["inicio"], "buraco ou sobreposição entre cenas"
    print(f"timeline: {len(tl['cenas'])} cenas contíguas, {tl['duracaoQuadros']} quadros ✔")

    if renderizar:
        assert rodar("ferramentas/edicao/render.py", alvo, "--previa", "--de", "0", "--ate", "6") == 0
        out = proj.etapa("edicao") / "renders" / "previa_v01_0-6.mp4"
        assert out.exists() and out.stat().st_size > 10_000
        print(f"render: {out.relative_to(RAIZ)} ✔")

    assert rodar("ferramentas/publicacao/creditos.py", alvo) == 0
    shutil.rmtree(pasta, ignore_errors=True)
    print("\nTUDO OK")


if __name__ == "__main__":
    main()
