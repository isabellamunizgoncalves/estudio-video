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


def _numero_fr(n: int) -> str:
    """Número por extenso em francês (0–100), já sem hífen."""
    u = ["zero", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix",
         "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix sept", "dix huit", "dix neuf"]
    dez = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante"}
    if n < 20:
        return u[n]
    if n == 100:
        return "cent"
    if n < 70:
        d, r = divmod(n, 10)
        return dez[d] if r == 0 else (f"{dez[d]} et un" if r == 1 else f"{dez[d]} {u[r]}")
    if n < 80:
        return "soixante et onze" if n == 71 else f"soixante {u[n - 60]}"
    return "quatre vingts" if n == 80 else f"quatre vingt {u[n - 80]}"


_NUMEROS = {str(n): _numero_fr(n) for n in range(0, 101)}


# O Whisper inventa estas frases em áudio silencioso: são legendas e vinhetas que ele
# aprendeu no treino, não som que exista na narração. Deixá-las entrar infla a transcrição
# e derruba a nota de um áudio correto. Não é regra de canal: é defeito conhecido do modelo.
ALUCINACOES = [
    r"\bsous\s*titr\w*\s+(?:r\w*alis\w*|par)\b.*",
    r"\bsous\s*titr\w*\s+(?:de\s+)?la\s+communaut\w*\b.*",
    r"\bamara\s+org\b.*",
    r"\bsous\s*titrage\s+(?:soci\w*|st)\b.*",
    r"\bmerci\s+d\s*avoir\s+regard\w*\b.*",
    r"\babonnez\s+vous\b.*",
    r"\bthanks?\s+for\s+watching\b.*",
    r"\bsubtitles?\s+by\b.*",
    r"\blegendas?\s+(?:pela|por)\b.*",
]
_fonetizador: dict = {}
_cache_fonema: dict[tuple[str, str], str] = {}


def _backend(idioma: str):
    """Backend do espeak para o idioma, ou None se não der para fonetizar aqui."""
    lang = (idioma or "").replace("_", "-").lower() or "fr-fr"
    if lang in _fonetizador:
        return _fonetizador[lang]
    try:
        import espeakng_loader
        from phonemizer.backend import EspeakBackend
        from phonemizer.backend.espeak.wrapper import EspeakWrapper

        EspeakWrapper.set_library(espeakng_loader.get_library_path())
        EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
        try:
            b = EspeakBackend(lang, with_stress=False)
        except RuntimeError:
            b = EspeakBackend(lang.split("-")[0], with_stress=False)
    except Exception as exc:  # sem espeak: cai para a comparação por letra
        print(f"    (sem fonética para {lang}: {type(exc).__name__}; comparando por letra)")
        b = None
    _fonetizador[lang] = b
    return b


def fonetizar(pedacos: list[str], idioma: str) -> list[str]:
    """Som de cada pedaço. Em francês o plural e o feminino são mudos («tomate» e «tomates»
    soam igual) e há muitos homófonos («vert»/«ver», «pâte»/«patte»): comparar letra a letra
    reprova narração boa. Sem espeak, devolve os próprios pedaços."""
    b = _backend(idioma)
    if b is None:
        return pedacos
    lang = (idioma or "fr-fr").replace("_", "-").lower()
    faltam = [p for p in dict.fromkeys(pedacos) if (lang, p) not in _cache_fonema]
    if faltam:
        try:
            for palavra, som in zip(faltam, b.phonemize(faltam, strip=True)):
                # Tira marca de vogal longa e de ênfase: «pâte» /paːt/ e «patte» /pat/ são
                # o mesmo som para o nosso fim, e o espeak alonga de forma inconsistente.
                limpo = som.replace(" ", "").replace("ː", "").replace("ˈ", "").replace("ˌ", "")
                _cache_fonema[(lang, palavra)] = limpo or palavra
        except Exception:
            return pedacos
    return [_cache_fonema.get((lang, p), p) for p in pedacos]


def subtokens(palavra: str, *, acentos: bool = False) -> list[str]:
    """Pedaços comparáveis de uma palavra, iguais nos dois lados da comparação.

    O Whisper devolve a elisão partida («qu'on» → «qu'» + «on»), parte o hífen
    («pot-au-feu» → «pot» + «au» + «feu») e escreve número em dígito («vingt-cinq» → «25»),
    enquanto o roteiro traz a forma escrita. Sem igualar isso, um francês bem narrado perde
    cerca de 11% de similaridade sem nenhum erro de narração.
    """
    bruto = palavra.lower().replace("\u2019", "'")
    if not acentos:
        bruto = unicodedata.normalize("NFKD", bruto)
        bruto = "".join(c for c in bruto if not unicodedata.combining(c))
    partes: list[str] = []
    for pedaco in re.split(r"[^\w']+", bruto, flags=re.UNICODE):
        for q in pedaco.split("'"):
            q = q.strip("'")
            if not q:
                continue
            partes.extend(_NUMEROS[q].split() if q.isdigit() and q in _NUMEROS else [q])
    return partes


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
    alucinacao_whisper: str = ""   # frase que o Whisper inventou e foi tirada da comparação

    @property
    def aprovado(self) -> bool:
        return not self.problemas

    @property
    def nota(self) -> float:
        return self.similaridade - 0.05 * len(self.problemas)


def _tirar_alucinacao(ouvidas: list, texto: str = ""):
    """Remove das palavras ouvidas as frases que o Whisper inventa. Devolve (palavras, texto tirado).

    O Whisper fatia a palavra de formas imprevisíveis («Sous» + «-titres»), então a busca é
    feita num texto normalizado (minúsculas, hífen e pontuação viram espaço) com o começo de
    cada palavra anotado, para o corte cair na palavra certa.
    """
    if not ouvidas:
        return ouvidas, ""
    partes, inicios = [], []
    for w in ouvidas:
        limpo = re.sub(r"[^\w]+", " ", w.word.lower()).strip()
        limpo = re.sub(r"\s+", " ", limpo)
        if not limpo:
            inicios.append(None)
            continue
        inicios.append(sum(len(x) + 1 for x in partes))
        partes.append(limpo)
    ouvido = " ".join(partes)

    # Uma frase que ESTÁ no roteiro nunca é alucinação: o CTA de um canal pode ser
    # exatamente uma das frases que o Whisper inventa («abonnez-vous…»). Sem esta
    # checagem, o filtro cortaria a despedida real e acusaria final truncado.
    roteiro = re.sub(r"[^\w]+", " ", (texto or "").lower()).strip()
    roteiro = re.sub(r"\s+", " ", roteiro)

    primeiro = len(ouvido)
    for padrao in ALUCINACOES:
        for m in re.finditer(padrao, ouvido):
            trecho = m.group(0).split()
            if trecho and roteiro and " ".join(trecho[:4]) in roteiro:
                continue  # está no roteiro: é fala de verdade
            primeiro = min(primeiro, m.start())
    if primeiro >= len(ouvido):
        return ouvidas, ""

    corte = len(ouvidas)
    for i, ini in enumerate(inicios):
        if ini is not None and ini >= primeiro:
            corte = i
            break
    return ouvidas[:corte], " ".join(w.word.strip() for w in ouvidas[corte:])


def verificar(audio: Path, texto: str, idioma: str, palavras_por_minuto: int,
              similaridade_minima: float = 0.93, desvio_max: float = 0.35,
              silencio_max: float = 2.8) -> Resultado:
    lang = idioma.split("-")[0].lower()
    # Decodifica via ffmpeg (faster-whisper 1.2.1 é incompatível com av 19 na leitura de arquivo).
    import subprocess
    import numpy as np
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-f", "f32le", "-ac", "1",
                          "-ar", "16000", "-"], capture_output=True, check=True).stdout
    sinal = np.frombuffer(pcm, dtype=np.float32)
    segs, _ = whisper().transcribe(sinal, language=lang, word_timestamps=True, beam_size=5,
                                   vad_filter=False, condition_on_previous_text=False)
    ouvidas = [w for s in segs for w in (s.words or [])]
    ouvidas, alucinado = _tirar_alucinacao(ouvidas, texto)
    orig = tokens(texto)
    # Compara em subtokens (elisão, hífen e número já igualados); a_map/b_map levam
    # cada subtoken de volta à palavra original, para o tempo por palavra não se perder.
    a: list[str] = []
    a_map: list[int] = []
    for i, t in enumerate(orig):
        for st in subtokens(t, acentos=True):
            a.append(st)
            a_map.append(i)
    b: list[str] = []
    b_map: list[int] = []
    for j, w in enumerate(ouvidas):
        for st in subtokens(w.word, acentos=True):
            b.append(st)
            b_map.append(j)
    # Compara o SOM, não a letra. Guarda a escrita para as mensagens de problema.
    a_escrito, b_escrito = a, b
    a, b = fonetizar(a, idioma), fonetizar(b, idioma)

    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    # Cobertura do ROTEIRO (quanto do texto foi realmente falado), e não a proporção
    # simétrica do difflib: palavra a mais na transcrição derrubava a nota de narração
    # correta. Sobra de fala é acusada à parte, pelas checagens de invenção.
    casadas = sum(x.size for x in sm.get_matching_blocks())
    sim = (casadas / len(a)) if a else 0.0
    dur = duracao_wav(audio)
    esperada = len(orig) / palavras_por_minuto * 60
    r = Resultado(similaridade=round(sim, 4), duracao=round(dur, 2), duracao_esperada=round(esperada, 2),
                  transcrito=" ".join(w.word.strip() for w in ouvidas),
                  alucinacao_whisper=alucinado)

    if sim < similaridade_minima:
        r.problemas.append(f"texto diverge (similaridade {sim:.2f} < {similaridade_minima})")
    if esperada and abs(dur - esperada) / esperada > desvio_max:
        r.problemas.append(f"duração {dur:.1f}s fora do esperado (~{esperada:.1f}s)")

    # Inserções longas no começo = instrução lida em voz alta; faltas no fim = corte.
    ops = sm.get_opcodes()
    # No início o limite é baixo (2 subtokens de SOBRA, não de tamanho): uma fórmula curta
    # lida a mais — «Fermez les yeux», 3 subtokens — passava sob o limite antigo de 4 e a
    # nota não acusava, porque a similaridade mede cobertura do roteiro e ignora inserção.
    # Mede-se a sobra para que trocar palavra por palavra (replace 2↔2) não vire alarme.
    if ops and ops[0][0] in ("insert", "replace") and (ops[0][4] - ops[0][3]) - (ops[0][2] - ops[0][1]) >= 2:
        r.problemas.append(f"fala extra no início: «{' '.join(b_escrito[ops[0][3]:ops[0][4]][:12])}»")
    if ops and ops[-1][0] in ("delete", "replace") and (ops[-1][2] - ops[-1][1]) >= 3:
        r.problemas.append(f"final cortado: faltou «{' '.join(a_escrito[ops[-1][1]:ops[-1][2]][:12])}»")
    if ops and ops[-1][0] in ("insert", "replace") and (ops[-1][4] - ops[-1][3]) - (ops[-1][2] - ops[-1][1]) >= 4:
        r.problemas.append(f"fala extra no final: «{' '.join(b_escrito[ops[-1][3]:ops[-1][4]][:12])}»")
    for op, i1, i2, j1, j2 in ops[1:-1]:
        if op in ("insert", "replace") and (j2 - j1) - (i2 - i1) >= 4:
            r.problemas.append(f"trecho inventado: «{' '.join(b_escrito[j1:j2][:12])}»")
        if op in ("delete", "replace") and (i2 - i1) - (j2 - j1) >= 4:
            r.problemas.append(f"trecho pulado: «{' '.join(a_escrito[i1:i2][:12])}»")

    for w1, w2 in zip(ouvidas, ouvidas[1:]):
        if w2.start - w1.end > silencio_max:
            r.problemas.append(f"silêncio de {w2.start - w1.end:.1f}s em {w1.end:.1f}s")
            break

    # Tempo de cada palavra do texto original (interpolado onde não houve casamento).
    tempos: list[tuple[float, float] | None] = [None] * len(orig)
    for bloco in sm.get_matching_blocks():
        for k in range(bloco.size):
            w = ouvidas[b_map[bloco.b + k]]
            i = a_map[bloco.a + k]
            ini, fim_w = float(w.start), float(w.end)
            tempos[i] = (ini, fim_w) if tempos[i] is None else (min(tempos[i][0], ini), max(tempos[i][1], fim_w))
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
