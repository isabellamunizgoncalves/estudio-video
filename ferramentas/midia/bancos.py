"""Busca em bancos de imagens e vídeos com licença livre. Todos devolvem o mesmo formato:

{banco, id, tipo: "video"|"imagem", titulo, pagina, download, previa, largura, altura,
 duracao, autor, licenca, licenca_url, atribuicao, ano}

Bancos:
- pexels     fotos e vídeos modernos, Pexels License (sem atribuição obrigatória)      PEXELS_API_KEY
- pixabay    fotos, ilustrações e vídeos, Pixabay Content License                       PIXABAY_API_KEY
- wikimedia  arquivo histórico, fotos e vídeos, CC/domínio público (atribuição varia)   sem chave
- openverse  agrega Flickr, museus etc., só licenças que permitem uso comercial          sem chave
- archive    Internet Archive (filmes de arquivo, Prelinger…), licença por item         sem chave
"""

from __future__ import annotations

import html
import os
import re

import requests

UA = {"User-Agent": "estudio-video/1.0 (ferramenta de producao de video)"}
TEMPO = 25


def _limpar(t: str | None) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", t or "")).strip()


# ------------------------------------------------------------------ Pexels
def pexels(q: str, tipo: str, n: int) -> list[dict]:
    chave = os.environ.get("PEXELS_API_KEY")
    if not chave:
        return []
    h = {**UA, "Authorization": chave}
    out = []
    if tipo in ("video", "qualquer"):
        r = requests.get("https://api.pexels.com/videos/search", headers=h, timeout=TEMPO,
                         params={"query": q, "per_page": n, "orientation": "landscape", "size": "medium"})
        r.raise_for_status()
        for v in r.json().get("videos", []):
            arqs = sorted([f for f in v.get("video_files", []) if f.get("width") and f["width"] <= 1920],
                          key=lambda f: f["width"], reverse=True)
            if not arqs:
                continue
            out.append({"banco": "pexels", "id": str(v["id"]), "tipo": "video", "titulo": v.get("url", "").rstrip("/").split("/")[-1],
                        "pagina": v.get("url"), "download": arqs[0]["link"], "previa": v.get("image"),
                        "largura": arqs[0]["width"], "altura": arqs[0]["height"], "duracao": v.get("duration"),
                        "autor": (v.get("user") or {}).get("name"), "licenca": "Pexels License",
                        "licenca_url": "https://www.pexels.com/license/", "atribuicao": f"Vídeo: {(v.get('user') or {}).get('name')} / Pexels"})
    if tipo in ("imagem", "qualquer"):
        r = requests.get("https://api.pexels.com/v1/search", headers=h, timeout=TEMPO,
                         params={"query": q, "per_page": n, "orientation": "landscape"})
        r.raise_for_status()
        for f in r.json().get("photos", []):
            out.append({"banco": "pexels", "id": str(f["id"]), "tipo": "imagem", "titulo": f.get("alt"),
                        "pagina": f.get("url"), "download": f["src"]["original"], "previa": f["src"]["medium"],
                        "largura": f.get("width"), "altura": f.get("height"), "autor": f.get("photographer"),
                        "licenca": "Pexels License", "licenca_url": "https://www.pexels.com/license/",
                        "atribuicao": f"Foto: {f.get('photographer')} / Pexels"})
    return out


# ------------------------------------------------------------------ Pixabay
def pixabay(q: str, tipo: str, n: int) -> list[dict]:
    chave = os.environ.get("PIXABAY_API_KEY", "")
    out = []
    base = {"key": chave, "q": q[:100], "per_page": max(3, n), "safesearch": "true"}
    lic = {"licenca": "Pixabay Content License", "licenca_url": "https://pixabay.com/service/license-summary/"}
    if tipo in ("video", "qualquer"):
        r = requests.get("https://pixabay.com/api/videos/", params=base, headers=UA, timeout=TEMPO)
        if r.ok:
            for v in r.json().get("hits", []):
                vs = v.get("videos", {})
                arq = vs.get("large") if (vs.get("large") or {}).get("url") else vs.get("medium", {})
                if not arq.get("url"):
                    continue
                out.append({"banco": "pixabay", "id": str(v["id"]), "tipo": "video", "titulo": v.get("tags"),
                            "pagina": v.get("pageURL"), "download": arq["url"], "previa": arq.get("thumbnail"),
                            "largura": arq.get("width"), "altura": arq.get("height"), "duracao": v.get("duration"),
                            "autor": v.get("user"), **lic, "atribuicao": f"Vídeo: {v.get('user')} / Pixabay"})
    if tipo in ("imagem", "qualquer"):
        r = requests.get("https://pixabay.com/api/", params={**base, "orientation": "horizontal"}, headers=UA, timeout=TEMPO)
        if r.ok:
            for f in r.json().get("hits", []):
                out.append({"banco": "pixabay", "id": str(f["id"]), "tipo": "imagem", "titulo": f.get("tags"),
                            "pagina": f.get("pageURL"), "download": f.get("largeImageURL"), "previa": f.get("webformatURL"),
                            "largura": f.get("imageWidth"), "altura": f.get("imageHeight"), "autor": f.get("user"),
                            **lic, "atribuicao": f"Imagem: {f.get('user')} / Pixabay"})
    return out


# ------------------------------------------------------------------ Wikimedia Commons
def wikimedia(q: str, tipo: str, n: int) -> list[dict]:
    filtro = {"imagem": "filetype:bitmap", "video": "filetype:video", "qualquer": "filetype:bitmap|video"}[tipo]
    r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=TEMPO, params={
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{q} {filtro}",
        "gsrnamespace": 6, "gsrlimit": n, "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": 640})
    r.raise_for_status()
    out = []
    for p in (r.json().get("query") or {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        mime = ii.get("mime", "")
        if not (mime.startswith("image/") or mime.startswith("video/")) or mime == "image/svg+xml":
            continue
        meta = ii.get("extmetadata", {})
        g = lambda k: _limpar((meta.get(k) or {}).get("value"))  # noqa: E731
        licenca = g("LicenseShortName") or "ver página"
        autor = g("Artist") or g("Credit")
        out.append({"banco": "wikimedia", "id": str(p.get("pageid")), "tipo": "video" if mime.startswith("video/") else "imagem",
                    "titulo": p.get("title", "").replace("File:", ""), "pagina": ii.get("descriptionurl"),
                    "download": ii.get("url"), "previa": ii.get("thumburl"), "largura": ii.get("width"),
                    "altura": ii.get("height"), "duracao": ii.get("duration"), "autor": autor, "licenca": licenca,
                    "licenca_url": g("LicenseUrl"), "ano": g("DateTimeOriginal")[:4],
                    "atribuicao": f"{autor or 'Autor desconhecido'}, {licenca}, via Wikimedia Commons"})
    return out


# ------------------------------------------------------------------ Openverse
def openverse(q: str, tipo: str, n: int) -> list[dict]:
    if tipo == "video":
        return []
    r = requests.get("https://api.openverse.org/v1/images/", headers=UA, timeout=TEMPO,
                     params={"q": q, "page_size": n, "license_type": "commercial,modification", "aspect_ratio": "wide,square"})
    if not r.ok:
        return []
    out = []
    for f in r.json().get("results", []):
        lic = f"CC {f.get('license', '').upper()} {f.get('license_version') or ''}".strip()
        if f.get("license") in ("cc0", "pdm"):
            lic = "Domínio público" if f["license"] == "pdm" else "CC0"
        out.append({"banco": "openverse", "id": f.get("id"), "tipo": "imagem", "titulo": f.get("title"),
                    "pagina": f.get("foreign_landing_url"), "download": f.get("url"), "previa": f.get("thumbnail"),
                    "largura": f.get("width"), "altura": f.get("height"), "autor": f.get("creator"),
                    "licenca": lic, "licenca_url": f.get("license_url"), "atribuicao": f.get("attribution")})
    return out


# ------------------------------------------------------------------ Internet Archive
def archive(q: str, tipo: str, n: int) -> list[dict]:
    if tipo == "imagem":
        return []
    r = requests.get("https://archive.org/advancedsearch.php", headers=UA, timeout=TEMPO, params={
        "q": f"({q}) AND mediatype:(movies) AND licenseurl:*", "fl[]": ["identifier", "title", "licenseurl", "creator", "year"],
        "rows": n, "output": "json", "sort[]": "downloads desc"})
    if not r.ok:
        return []
    out = []
    for d in r.json().get("response", {}).get("docs", []):
        ident = d["identifier"]
        licurl = d.get("licenseurl") or ""
        lic = "Domínio público" if ("publicdomain" in licurl or "mark" in licurl) else ("CC " + licurl.rstrip("/").split("/")[-2].upper() if "creativecommons" in licurl else "ver página")
        criador = d.get("creator") if isinstance(d.get("creator"), str) else ", ".join(d.get("creator") or [])
        out.append({"banco": "archive", "id": ident, "tipo": "video", "titulo": d.get("title"),
                    "pagina": f"https://archive.org/details/{ident}", "download": None,  # resolvido no download
                    "previa": f"https://archive.org/services/img/{ident}", "autor": criador, "ano": str(d.get("year") or ""),
                    "licenca": lic, "licenca_url": licurl, "atribuicao": f"{criador or d.get('title')} — Internet Archive ({lic})"})
    return out


def resolver_wikimedia(pageid: str, largura: int = 1920) -> str | None:
    """A Wikimedia bloqueia (429) downloads repetidos do original: pedimos a miniatura
    oficial de 1920 px (tamanho padrão do cache deles), que basta para vídeo 1080p."""
    r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=TEMPO, params={
        "action": "query", "format": "json", "pageids": pageid, "prop": "imageinfo",
        "iiprop": "url|size|mime", "iiurlwidth": largura})
    r.raise_for_status()
    ii = (r.json()["query"]["pages"][str(pageid)].get("imageinfo") or [{}])[0]
    if ii.get("mime", "").startswith("video/") or (ii.get("width") or 0) <= largura:
        return ii.get("url")
    return ii.get("thumburl") or ii.get("url")


def resolver_archive(ident: str) -> str | None:
    """Escolhe o melhor .mp4 de um item do Internet Archive."""
    r = requests.get(f"https://archive.org/metadata/{ident}", headers=UA, timeout=TEMPO)
    r.raise_for_status()
    arquivos = [f for f in r.json().get("files", []) if f.get("name", "").lower().endswith((".mp4", ".mpeg4", ".m4v"))]
    if not arquivos:
        arquivos = [f for f in r.json().get("files", []) if f.get("name", "").lower().endswith((".ogv", ".webm", ".avi", ".mpeg", ".mpg"))]
    if not arquivos:
        return None
    arquivos.sort(key=lambda f: (f.get("source") == "original", int(f.get("size", 0) or 0)), reverse=True)
    pref = [f for f in arquivos if int(f.get("size", 0) or 0) < 900_000_000] or arquivos
    return f"https://archive.org/download/{ident}/{pref[0]['name']}"


BANCOS = {"pexels": pexels, "pixabay": pixabay, "wikimedia": wikimedia, "openverse": openverse, "archive": archive}
