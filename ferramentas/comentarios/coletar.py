#!/usr/bin/env python3
"""Coleta metadados, comentários e transcrição de um vídeo do YouTube.

    python ferramentas/comentarios/coletar.py <canal/slug> [--url URL] [--max 500]

Ordem de tentativa: YouTube Data API v3 (se YOUTUBE_API_KEY existir) → yt-dlp.
Grava em 01_pesquisa/:
    comentarios.json  dados brutos (sem nomes de autores: privacidade e para não serem citados)
    contexto.md       leitura humana para o agente analista (comentários por relevância)

Saída 3 = nada coletado: peça a Isabella que cole os comentários em 01_pesquisa/comentarios-colados.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum.estudio import Projeto, agora, gravar_json  # noqa: E402


def id_do_video(url: str) -> str:
    for padrao in (r"youtu\.be/([\w-]{11})", r"(?:v=|/v/|embed/|live/|shorts/)([\w-]{11})"):
        m = re.search(padrao, url)
        if m:
            return m.group(1)
    if re.fullmatch(r"[\w-]{11}", url):
        return url
    raise SystemExit(f"Não reconheci o ID do vídeo em: {url}")


# ---------------------------------------------------------------- YouTube Data API
def via_api(video_id: str, maximo: int) -> tuple[dict, list[dict]] | None:
    chave = os.environ.get("YOUTUBE_API_KEY")
    if not chave:
        return None
    import requests

    base = "https://www.googleapis.com/youtube/v3"
    r = requests.get(f"{base}/videos", params={"part": "snippet,statistics,contentDetails", "id": video_id, "key": chave}, timeout=20)
    r.raise_for_status()
    itens = r.json().get("items", [])
    if not itens:
        return None
    sn, st = itens[0]["snippet"], itens[0].get("statistics", {})
    info = {
        "id": video_id, "titulo": sn.get("title"), "canal": sn.get("channelTitle"),
        "descricao": sn.get("description", ""), "publicado_em": sn.get("publishedAt"),
        "visualizacoes": int(st.get("viewCount", 0)), "curtidas": int(st.get("likeCount", 0)),
        "total_comentarios": int(st.get("commentCount", 0)), "idioma": sn.get("defaultAudioLanguage"),
    }
    comentarios: list[dict] = []
    token = None
    while len(comentarios) < maximo:
        r = requests.get(f"{base}/commentThreads", params={
            "part": "snippet,replies", "videoId": video_id, "order": "relevance", "maxResults": 100,
            "textFormat": "plainText", "pageToken": token, "key": chave}, timeout=20)
        if r.status_code == 403:
            break  # comentários desativados
        r.raise_for_status()
        dados = r.json()
        for item in dados.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            comentarios.append({"texto": top.get("textDisplay", ""), "curtidas": top.get("likeCount", 0),
                                "respostas": item["snippet"].get("totalReplyCount", 0), "data": top.get("publishedAt", "")[:10]})
            for resp in (item.get("replies") or {}).get("comments", [])[:5]:
                s = resp["snippet"]
                comentarios.append({"texto": s.get("textDisplay", ""), "curtidas": s.get("likeCount", 0),
                                    "respostas": 0, "data": s.get("publishedAt", "")[:10], "resposta": True})
        token = dados.get("nextPageToken")
        if not token:
            break
    return info, comentarios[:maximo]


# ---------------------------------------------------------------- yt-dlp
def via_ytdlp(url: str, maximo: int) -> tuple[dict, list[dict]] | None:
    cmd = [shutil.which("yt-dlp")] if shutil.which("yt-dlp") else [sys.executable, "-m", "yt_dlp"]
    cmd += ["--write-comments", "--dump-single-json", "--skip-download", "--no-playlist", "--no-warnings",
            "--extractor-args", f"youtube:comment_sort=top;max_comments={maximo},all,100", url]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"yt-dlp falhou: {exc}", file=sys.stderr)
        return None
    if r.returncode != 0 or not r.stdout.strip():
        print(f"yt-dlp falhou: {(r.stderr or '').strip().splitlines()[-1:]}", file=sys.stderr)
        return None
    d = json.loads(r.stdout)
    info = {
        "id": d.get("id"), "titulo": d.get("title"), "canal": d.get("channel") or d.get("uploader"),
        "descricao": d.get("description", ""), "publicado_em": d.get("upload_date"),
        "visualizacoes": d.get("view_count") or 0, "curtidas": d.get("like_count") or 0,
        "total_comentarios": d.get("comment_count") or 0, "duracao_s": d.get("duration"), "idioma": d.get("language"),
    }
    comentarios = [{"texto": c.get("text", ""), "curtidas": c.get("like_count") or 0,
                    "respostas": 0, "resposta": c.get("parent", "root") != "root"}
                   for c in d.get("comments") or []]
    return info, comentarios


def transcricao(video_id: str, idiomas: list[str]) -> list[dict]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        t = YouTubeTranscriptApi().fetch(video_id, languages=idiomas + ["en", "fr", "pt", "es"])
        return [{"inicio": s.start, "texto": s.text} for s in t]
    except Exception as exc:  # muitos tipos de erro específicos
        print(f"Transcrição indisponível: {type(exc).__name__}", file=sys.stderr)
        return []


def montar_md(info: dict, comentarios: list[dict], trans: list[dict], url: str) -> str:
    L = [f"# Contexto: {info.get('titulo')}", "",
         f"- URL: {url}", f"- Canal: {info.get('canal')}",
         f"- Visualizações: {info.get('visualizacoes'):,}".replace(",", "."),
         f"- Curtidas: {info.get('curtidas'):,}".replace(",", "."),
         f"- Comentários no vídeo: {info.get('total_comentarios')} | nesta amostra: {len(comentarios)}",
         f"- Coletado em: {agora()}", ""]
    if info.get("descricao"):
        L += ["## Descrição", "", info["descricao"][:3000], ""]
    L += ["## Comentários (mais relevantes primeiro — USO INTERNO, nunca citar no roteiro)", ""]
    for i, c in enumerate(comentarios, 1):
        texto = " ".join(c["texto"].split())
        if not texto:
            continue
        extra = f" · {c['respostas']} respostas" if c.get("respostas") else ""
        tipo = " · resposta" if c.get("resposta") else ""
        L.append(f"{i}. [{c['curtidas']} curtidas{extra}{tipo}] {texto[:1200]}")
    L += ["", "## Transcrição", ""]
    if trans:
        bloco, marca = [], 0.0
        for s in trans:
            if s["inicio"] - marca >= 60 and bloco:
                L.append(f"**[{int(marca)//60:02d}:{int(marca)%60:02d}]** " + " ".join(bloco))
                bloco, marca = [], s["inicio"]
            bloco.append(s["texto"].replace("\n", " "))
        if bloco:
            L.append(f"**[{int(marca)//60:02d}:{int(marca)%60:02d}]** " + " ".join(bloco))
    else:
        L.append("Não disponível.")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto", help="canal/slug")
    ap.add_argument("--url", help="padrão: link_referencia do projeto.json")
    ap.add_argument("--max", type=int, default=500)
    args = ap.parse_args()

    proj = Projeto.abrir(args.projeto)
    url = args.url or proj.dados.get("link_referencia")
    if not url:
        raise SystemExit("Sem link do vídeo de referência (use --url).")
    vid = id_do_video(url)

    resultado = None
    try:
        resultado = via_api(vid, args.max)
    except Exception as exc:
        print(f"YouTube API falhou: {exc}", file=sys.stderr)
    fonte = "youtube-api"
    if not resultado:
        resultado, fonte = via_ytdlp(url, args.max), "yt-dlp"
    if not resultado:
        print("Nada coletado. Peça os comentários colados em 01_pesquisa/comentarios-colados.md", file=sys.stderr)
        sys.exit(3)

    info, comentarios = resultado
    comentarios = [c for c in comentarios if c["texto"].strip()]
    comentarios.sort(key=lambda c: (c["curtidas"], c.get("respostas", 0)), reverse=True)
    idioma = proj.dados.get("idioma", "fr").split("-")[0]
    trans = transcricao(vid, [idioma])

    pasta = proj.etapa("pesquisa")
    gravar_json(pasta / "comentarios.json", {"fonte": fonte, "url": url, "info": info,
                                             "comentarios": comentarios, "transcricao": trans})
    (pasta / "contexto.md").write_text(montar_md(info, comentarios, trans, url), encoding="utf-8")
    proj.marcar("coleta", fonte=fonte, comentarios=len(comentarios), transcricao=bool(trans))
    aviso = "  (amostra pequena: análise preliminar)" if len(comentarios) < 20 else ""
    print(f"OK: {len(comentarios)} comentários via {fonte}, transcrição: {'sim' if trans else 'não'}{aviso}")
    print(f"→ {proj.rel(pasta / 'contexto.md')}")


if __name__ == "__main__":
    main()
