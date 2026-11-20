"""Divide o roteiro humanizado em blocos de ~N segundos, sem cortar frase nem parágrafo à toa.

Regras:
- A unidade é o parágrafo (linha em branco = pausa longa do humanizador).
- Um bloco junta parágrafos até chegar perto de `segundos` (pela velocidade do canal).
- Parágrafo maior que o bloco é quebrado em frases; frase nunca é cortada.
- Blocos curtos demais no fim (< 35% do alvo) são unidos ao anterior.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Bloco:
    indice: int
    paragrafos: list[str] = field(default_factory=list)
    primeiro_paragrafo: int = 0  # índice global do 1º parágrafo (para a direção de voz)

    @property
    def texto(self) -> str:
        return "\n\n".join(self.paragrafos)

    @property
    def palavras(self) -> int:
        return len(self.texto.split())


def paragrafos(texto: str) -> list[str]:
    return [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]


def frases(paragrafo: str) -> list[str]:
    partes = re.split(r"(?<=[.!?…])\s+(?=[«\"“A-ZÀ-ÖØ-Þ0-9¿¡])", paragrafo)
    return [p.strip() for p in partes if p.strip()]


def dividir(texto: str, palavras_por_minuto: int, segundos: int = 60) -> list[Bloco]:
    alvo = max(25, int(palavras_por_minuto * segundos / 60))
    teto = int(alvo * 1.25)
    unidades: list[tuple[int, str]] = []  # (índice do parágrafo, texto)
    for i, p in enumerate(paragrafos(texto)):
        if len(p.split()) <= teto:
            unidades.append((i, p))
            continue
        atual: list[str] = []
        for f in frases(p):
            if atual and len(" ".join(atual + [f]).split()) > alvo:
                unidades.append((i, " ".join(atual)))
                atual = []
            atual.append(f)
        if atual:
            unidades.append((i, " ".join(atual)))

    blocos: list[Bloco] = []
    atual = Bloco(indice=1)
    for i, u in unidades:
        n_atual, n_u = atual.palavras, len(u.split())
        if atual.paragrafos and (n_atual + n_u > teto or (n_atual >= alvo * 0.8 and n_atual + n_u > alvo)):
            blocos.append(atual)
            atual = Bloco(indice=len(blocos) + 1)
        if not atual.paragrafos:
            atual.primeiro_paragrafo = i
        atual.paragrafos.append(u)
    if atual.paragrafos:
        blocos.append(atual)

    if len(blocos) > 1 and blocos[-1].palavras < alvo * 0.35:
        ultimo = blocos.pop()
        blocos[-1].paragrafos.extend(ultimo.paragrafos)
    return blocos
