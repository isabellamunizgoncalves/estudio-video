"""Funções comuns do estúdio: raiz do repo, .env, canal, pastas do projeto e versões.

Todas as ferramentas importam daqui:

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from comum.estudio import carregar_canal, Projeto
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CANAIS = RAIZ / "canais"
PROJETOS = RAIZ / "projetos"

ETAPAS = {
    "pesquisa": "01_pesquisa",
    "roteiro": "02_roteiro",
    "narracao": "03_narracao",
    "visual": "04_visual",
    "edicao": "05_edicao",
    "publicacao": "06_publicacao",
}

for _fluxo in (sys.stdout, sys.stderr):
    if hasattr(_fluxo, "reconfigure"):
        _fluxo.reconfigure(encoding="utf-8", errors="replace")


def carregar_env() -> None:
    """Lê o .env da raiz (se existir) sem sobrescrever variáveis já definidas."""
    arquivo = RAIZ / ".env"
    if not arquivo.exists():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        valor = valor.split(" #", 1)[0].strip().strip('"').strip("'")
        if valor:
            os.environ.setdefault(chave.strip(), valor)


carregar_env()


def carregar_canal(canal_id: str) -> dict:
    import yaml

    pasta = CANAIS / canal_id
    arquivo = pasta / "canal.yaml"
    if not arquivo.exists():
        disponiveis = sorted(p.name for p in CANAIS.iterdir() if p.is_dir() and not p.name.startswith("_"))
        raise SystemExit(f"Canal '{canal_id}' não existe. Canais: {', '.join(disponiveis) or 'nenhum'}")
    dados = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
    dados["_pasta"] = str(pasta)
    tema = pasta / dados.get("visual", {}).get("tema", "tema.json")
    dados["_tema"] = json.loads(tema.read_text(encoding="utf-8")) if tema.exists() else {}
    return dados


def slugificar(texto: str) -> str:
    import unicodedata

    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto[:60] or "video"


def agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ler_json(caminho: Path, padrao=None):
    caminho = Path(caminho)
    if not caminho.exists():
        return padrao
    return json.loads(caminho.read_text(encoding="utf-8"))


def gravar_json(caminho: Path, dados) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return caminho


@dataclass
class Projeto:
    pasta: Path

    @classmethod
    def abrir(cls, alvo: str) -> "Projeto":
        """Aceita 'canal/slug', um caminho relativo ou absoluto."""
        candidatos = [Path(alvo), RAIZ / alvo, PROJETOS / alvo]
        for c in candidatos:
            if (c / "projeto.json").exists():
                return cls(c.resolve())
        raise SystemExit(f"Projeto '{alvo}' não encontrado. Crie com: ./scripts/novo-video.sh <canal> \"<tema>\"")

    @property
    def dados(self) -> dict:
        return ler_json(self.pasta / "projeto.json", {})

    @property
    def canal(self) -> dict:
        return carregar_canal(self.dados["canal"])

    def etapa(self, nome: str) -> Path:
        p = self.pasta / ETAPAS[nome]
        p.mkdir(parents=True, exist_ok=True)
        return p

    def rel(self, caminho: Path) -> str:
        return Path(caminho).resolve().relative_to(self.pasta).as_posix()

    def marcar(self, etapa: str, **info) -> None:
        dados = self.dados
        dados.setdefault("etapas", {})[etapa] = {"atualizado_em": agora(), **info}
        gravar_json(self.pasta / "projeto.json", dados)


def ultima_versao(pasta: Path, prefixo: str, ext: str) -> Path | None:
    """Maior <prefixo>_vNN<ext> da pasta (ou None)."""
    achados = []
    for p in Path(pasta).glob(f"{prefixo}_v*{ext}"):
        m = re.fullmatch(rf"{re.escape(prefixo)}_v(\d+){re.escape(ext)}", p.name)
        if m:
            achados.append((int(m.group(1)), p))
    return max(achados)[1] if achados else None


def proxima_versao(pasta: Path, prefixo: str, ext: str) -> Path:
    atual = ultima_versao(pasta, prefixo, ext)
    n = int(re.search(r"_v(\d+)", atual.name).group(1)) + 1 if atual else 1
    return Path(pasta) / f"{prefixo}_v{n:02d}{ext}"


def numero_versao(caminho: Path) -> str:
    m = re.search(r"_v(\d+)", Path(caminho).name)
    return m.group(1) if m else "01"
