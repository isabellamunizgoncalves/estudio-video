"""Verificação anti-alucinação: transcreve o áudio com Whisper e compara com o texto.

Detecta: palavras trocadas/puladas/inventadas, instrução lida em voz alta, corte no fim,
silêncio longo no meio, duração fora do esperado. Também devolve o tempo de cada palavra
do TEXTO ORIGINAL (alinhado), usado depois pela edição.
"""

from __future__ import annotations

import difflib
import os
import re
import unicodedata
import wave
from dataclasses import dataclass, field
from pathlib import Path

_modelo = None


def whisper():
    global _modelo
    if _modelo is None:
        from faster_whisper import WhisperModel

        nome = os.environ.get("WHISPER_MODELO", "small")
        _modelo = WhisperModel(nome, device="auto", compute_type="int8")
    return _modelo


def normalizar(palavra: str) -> str:
    p = unicodedata.normalize("NFKD", palavra.lower().replace("’", "'"))
    p = "".join(c for c in p if not unicodedata.combining(c))
    return re.sub(r"[^\w']", "", p).strip("'")


def tokens(texto: str) -> list[str]:
    """Palavras do texto como aparecem (com pontuação colada), para alinhar e exibir."""
    return [t for t in re.findall(r"\S+", texto) if normalizar(t)]


def duracao_wav(caminho: Path) -> float:
    with wave.open(str(caminho), "rb") as w:
        return w.getnframes() / w.getframerate()


@dataclass
class Resultado:
    similaridade: float
    duracao: float
    duracao_esperada: float
    problemas: list[str] = field(default_factory=list)
    palavras: list[dict] = field(default_factory=list)   # [{texto, inicio, fim}] do TEXTO ORIGINAL
    inicio_fala: float = 0.0
    fim_fala: float = 0.0
    transcrito: str = ""

    @property
    def aprovado(self) -> bool:
        return not self.problemas

    @property
    def nota(self) -> float:
        return self.similaridade - 0.05 * len(self.problemas)


def verificar(audio: Path, texto: str, idioma: str, palavras_por_minuto: int,
              similaridade_minima: float = 0.93, desvio_max: float = 0.35) -> Resultado:
    lang = idioma.split("-")[0].lower()
    segs, _ = whisper().transcribe(str(audio), language=lang, word_timestamps=True, beam_size=5,
                                   vad_filter=False, condition_on_previous_text=False)
    ouvidas = [w for s in segs for w in (s.words or [])]
    orig = tokens(texto)
    a = [normalizar(t) for t in orig]
    b = [normalizar(w.word) for w in ouvidas]
    b_idx = [i for i, x in enumerate(b) if x]
    b = [b[i] for i in b_idx]
    ouvidas = [ouvidas[i] for i in b_idx]

    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    sim = sm.ratio() if a else 0.0
    dur = duracao_wav(audio)
    esperada = len(a) / palavras_por_minuto * 60
    r = Resultado(similaridade=round(sim, 4), duracao=round(dur, 2), duracao_esperada=round(esperada, 2),
                  transcrito=" ".join(w.word.strip() for w in ouvidas))

    if sim < similaridade_minima:
        r.problemas.append(f"texto diverge (similaridade {sim:.2f} < {similaridade_minima})")
    if esperada and abs(dur - esperada) / esperada > desvio_max:
        r.problemas.append(f"duração {dur:.1f}s fora do esperado (~{esperada:.1f}s)")

    # Inserções longas no começo = instrução lida em voz alta; faltas no fim = corte.
    ops = sm.get_opcodes()
    if ops and ops[0][0] in ("insert", "replace") and (ops[0][4] - ops[0][3]) >= 4:
        r.problemas.append(f"fala extra no início: «{' '.join(b[ops[0][3]:ops[0][4]][:12])}»")
    if ops and ops[-1][0] in ("delete", "replace") and (ops[-1][2] - ops[-1][1]) >= 3:
        r.problemas.append(f"final cortado: faltou «{' '.join(a[ops[-1][1]:ops[-1][2]][:12])}»")
    for op, i1, i2, j1, j2 in ops[1:-1]:
        if op in ("insert", "replace") and (j2 - j1) - (i2 - i1) >= 4:
            r.problemas.append(f"trecho inventado: «{' '.join(b[j1:j2][:12])}»")
        if op in ("delete", "replace") and (i2 - i1) - (j2 - j1) >= 4:
            r.problemas.append(f"trecho pulado: «{' '.join(a[i1:i2][:12])}»")

    for w1, w2 in zip(ouvidas, ouvidas[1:]):
        if w2.start - w1.end > 2.8:
            r.problemas.append(f"silêncio de {w2.start - w1.end:.1f}s em {w1.end:.1f}s")
            break

    # Tempo de cada palavra do texto original (interpolado onde não houve casamento).
    tempos: list[tuple[float, float] | None] = [None] * len(a)
    for bloco in sm.get_matching_blocks():
        for k in range(bloco.size):
            w = ouvidas[bloco.b + k]
            tempos[bloco.a + k] = (float(w.start), float(w.end))
    if ouvidas:
        r.inicio_fala = float(ouvidas[0].start)
        r.fim_fala = float(ouvidas[-1].end)
    _interpolar(tempos, r.inicio_fala, r.fim_fala or dur)
    r.palavras = [{"texto": t, "inicio": round(s, 3), "fim": round(e, 3)} for t, (s, e) in zip(orig, tempos)]
    return r


def _interpolar(tempos: list, inicio: float, fim: float) -> None:
    n = len(tempos)
    i = 0
    while i < n:
        if tempos[i] is not None:
            i += 1
            continue
        j = i
        while j < n and tempos[j] is None:
            j += 1
        t0 = tempos[i - 1][1] if i > 0 else inicio
        t1 = tempos[j][0] if j < n else fim
        passo = max(0.0, t1 - t0) / (j - i)
        for k in range(i, j):
            tempos[k] = (t0 + passo * (k - i), t0 + passo * (k - i + 1))
        i = j
