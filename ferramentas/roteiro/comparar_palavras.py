#!/usr/bin/env python3
"""Garante que a humanização não mudou nenhuma palavra: só pontuação e quebras.

    python ferramentas/roteiro/comparar_palavras.py <original.txt> <humanizado.txt>

Saída 0 = mesmas palavras na mesma ordem. Saída 5 = diferenças (mostra onde).
"""

from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path


def palavras(texto: str) -> list[str]:
    return re.findall(r"[\w’'-]+", texto.lower().replace("’", "'"))


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    a = palavras(Path(sys.argv[1]).read_text(encoding="utf-8"))
    b = palavras(Path(sys.argv[2]).read_text(encoding="utf-8"))
    if a == b:
        print(f"OK: {len(a)} palavras idênticas, só pontuação e quebras mudaram.")
        return
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        ctx = " ".join(a[max(0, i1 - 5):i1])
        print(f"[{op}] …{ctx} | original: «{' '.join(a[i1:i2])}» → humanizado: «{' '.join(b[j1:j2])}»")
    sys.exit(5)


if __name__ == "__main__":
    main()
