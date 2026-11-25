"""Provedor de voz: Gemini TTS (Google AI Studio).

Vozes pré-prontas (todas multilíngues; o idioma vem do texto):
Zephyr (clara), Puck (animada), Charon (informativa), Kore (firme), Fenrir (empolgada),
Leda (jovem), Orus (firme), Aoede (leve), Callirrhoe (tranquila), Autonoe (clara),
Enceladus (sussurrada), Iapetus (clara), Umbriel (tranquila), Algieba (suave),
Despina (suave), Erinome (clara), Algenib (rouca), Rasalgethi (informativa),
Laomedeia (animada), Achernar (macia), Alnilam (firme), Schedar (equilibrada),
Gacrux (madura), Pulcherrima (direta), Achird (amigável), Zubenelgenubi (casual),
Vindemiatrix (gentil), Sadachbia (viva), Sadaltager (conhecedora), Sulafat (calorosa).
"""

from __future__ import annotations

import os
import re
import time
import wave
from pathlib import Path

# Gênero conforme a tabela "Voice options" da documentação do Gemini TTS
# (cloud.google.com/text-to-speech/docs/gemini-tts). O Google não publica descrição de timbre,
# então não há adjetivo aqui: a escolha da voz de um canal é sempre feita de ouvido.
GENERO_VOZ = {
    "Zephyr": "f", "Puck": "m", "Charon": "m", "Kore": "f", "Fenrir": "m",
    "Leda": "f", "Orus": "m", "Aoede": "f", "Callirrhoe": "f", "Autonoe": "f",
    "Enceladus": "m", "Iapetus": "m", "Umbriel": "m", "Algieba": "m", "Despina": "f",
    "Erinome": "f", "Algenib": "m", "Rasalgethi": "m", "Laomedeia": "f", "Achernar": "f",
    "Alnilam": "m", "Schedar": "m", "Gacrux": "f", "Pulcherrima": "f", "Achird": "m",
    "Zubenelgenubi": "m", "Vindemiatrix": "f", "Sadachbia": "m", "Sadaltager": "m", "Sulafat": "f",
}

VOZES = list(GENERO_VOZ)


def vozes_por_genero(genero: str) -> list[str]:
    """Vozes de um gênero ('m', 'f') ou todas ('t')."""
    g = (genero or "t").lower()[0]
    return VOZES if g == "t" else [v for v, x in GENERO_VOZ.items() if x == g]

_cliente = None


def cliente():
    global _cliente
    if _cliente is None:
        from google import genai
        from google.genai import types

        chave = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not chave:
            raise SystemExit("Falta GEMINI_API_KEY no .env (crie em https://aistudio.google.com/apikey).")
        _cliente = genai.Client(api_key=chave, http_options=types.HttpOptions(api_version="v1beta"))
    return _cliente


def montar_prompt(texto: str, direcao: str, tom: str = "", idioma: str = "") -> str:
    """Prompt no formato recomendado para o Gemini TTS: perfil + notas do diretor + transcrição.

    A transcrição vem por último e é marcada como a ÚNICA coisa a ser lida, para o modelo
    não ler as instruções em voz alta nem improvisar.
    """
    notas = [direcao.strip()]
    if tom:
        notas.append(f"Émotion de ce passage / emotion of this passage: {tom}.")
    notas.append("Read ONLY the transcript below, word for word, from the first word to the last. "
                 "Do not add, skip, repeat or translate anything. Do not read these notes aloud. "
                 "Respect punctuation: commas are short breaths, ellipses are hesitations, "
                 "blank lines are longer pauses.")
    if idioma:
        notas.append(f"Language/accent: {idioma}.")
    return "### DIRECTOR'S NOTES\n" + "\n".join(notas) + "\n\n### TRANSCRIPT\n" + texto.strip()


def sintetizar(texto: str, destino: Path, *, voz: str, modelo: str, direcao: str, tom: str = "",
               idioma: str = "", temperatura: float | None = None, tentativas_api: int = 5) -> Path:
    """Gera um .wav (PCM 16 bits mono) com o texto. Repete em erro de rede/cota com espera crescente."""
    from google.genai import types

    config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        temperature=temperatura,
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voz))
        ),
    )
    prompt = montar_prompt(texto, direcao, tom, idioma)
    erro = None
    for n in range(tentativas_api):
        try:
            resp = cliente().models.generate_content(model=modelo, contents=prompt, config=config)
            parte = resp.candidates[0].content.parts[0].inline_data
            taxa = int(m.group(1)) if (m := re.search(r"rate=(\d+)", parte.mime_type or "")) else 24000
            destino.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(destino), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(taxa)
                w.writeframes(parte.data)
            return destino
        except Exception as exc:  # rede, cota (429), 500, resposta sem áudio
            codigo = getattr(exc, "code", None)
            if isinstance(codigo, int) and 400 <= codigo < 500 and codigo != 429:
                raise  # chave inválida, modelo inexistente, texto recusado: repetir não adianta
            erro = exc
            espera = min(90, 6 * 2 ** n)
            print(f"    Gemini: {type(exc).__name__}: {str(exc)[:140]} — nova tentativa em {espera}s")
            time.sleep(espera)
    raise RuntimeError(f"Gemini TTS falhou {tentativas_api}x: {erro}")
