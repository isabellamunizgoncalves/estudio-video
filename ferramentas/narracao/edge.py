#!/usr/bin/env python3
"""Narração pelo Edge TTS (vozes neurais da Microsoft), sem chave e sem cota.

Ressalvas conhecidas, registradas aqui para quem mexer nisso depois:
- O endpoint é o do "Ler em voz alta" do navegador Edge, não uma API licenciada. Pode mudar
  ou bloquear sem aviso, e usar em conteúdo monetizado contraria os termos da Microsoft.
- Não aceita direção de atuação: só ritmo (`ritmo`) e tom (`tom_hz`). O `narracao.direcao` e
  o tom por parágrafo do `direcao_vNN.json` NÃO chegam na voz — ao contrário do Gemini.
- A síntese é determinística: o mesmo texto devolve sempre o mesmo áudio. Repetir uma tomada
  reprovada não muda nada, então `DETERMINISTICO` avisa o narrador a não gastar tentativas.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import tempfile
from pathlib import Path

DETERMINISTICO = True
TAXA = 24000  # igual à do Gemini, para a montagem não precisar reamostrar


def _proxy() -> str | None:
    for k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        if os.environ.get(k):
            return os.environ[k]
    return None


def vozes(idioma: str = "") -> list[tuple[str, str]]:
    """[(nome, genero)] das vozes do Edge, filtradas pelo idioma (ex.: 'fr-FR' ou 'fr')."""
    import edge_tts

    todas = asyncio.run(edge_tts.list_voices(proxy=_proxy()))
    pre = (idioma or "").replace("_", "-").lower()
    saida = []
    for v in todas:
        nome = v.get("ShortName", "")
        if pre and not nome.lower().startswith(pre):
            continue
        saida.append((nome, "m" if v.get("Gender") == "Male" else "f"))
    return sorted(saida)


def sintetizar(texto: str, destino: Path, *, voz: str, idioma: str = "", ritmo: str = "",
               tom_hz: str = "", tentativas_api: int = 5, **_ignorados) -> Path:
    """Gera um .wav PCM 16 bits mono. `ritmo`/`tom_hz` no formato do Edge: '-15%', '-2Hz'."""
    import edge_tts

    extra = {}
    if ritmo:
        extra["rate"] = ritmo
    if tom_hz:
        extra["pitch"] = tom_hz

    destino.parent.mkdir(parents=True, exist_ok=True)
    erro = None
    for n in range(tentativas_api):
        try:
            with tempfile.TemporaryDirectory() as tmp:
                bruto = Path(tmp) / "bruto.mp3"
                com = edge_tts.Communicate(texto, voz, proxy=_proxy(), **extra)
                asyncio.run(com.save(str(bruto)))
                if not bruto.exists() or bruto.stat().st_size < 1024:
                    raise RuntimeError("Edge devolveu áudio vazio")
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bruto),
                                "-ac", "1", "-ar", str(TAXA), "-c:a", "pcm_s16le", str(destino)],
                               check=True)
            return destino
        except Exception as exc:
            erro = exc
            espera = min(60, 5 * 2 ** n)
            print(f"    Edge: {type(exc).__name__}: {str(exc)[:140]} — nova tentativa em {espera}s")
            __import__("time").sleep(espera)
    raise RuntimeError(f"Edge TTS falhou {tentativas_api}x: {erro}")
