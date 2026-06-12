"""Diff dei file di testo (Strings/Words, Strings/Names) IT vs INGLESE DEL GIOCO.

I .txt italiani sono fermi a versioni vecchie: la fonte di verita e l'inglese
del gioco (Data/<DLC>/Languages/English/Strings). Questo confronto trova:

  MANCANTE   - file presente in EN ma assente in IT (contenuto nuovo da aggiungere)
  UGUALE-EN  - file presente ma contenuto identico all'inglese (non tradotto)
  CORTO      - file con MENO voci dell'inglese (probabilmente incompleto/vecchio)

I tanti file extra dell'IT (varianti di genere/numero) NON sono segnalati: si
parte sempre dall'inventario inglese.
"""
from __future__ import annotations

from pathlib import Path

import config


def _read(f: Path) -> list[str]:
    out = []
    try:
        text = f.read_text(encoding="utf-8")
    except OSError:
        return out
    for ln in text.splitlines():
        ln = ln.lstrip("﻿").strip()
        if ln and not ln.startswith(("#", "//")):
            out.append(ln)
    return out


def en_root(dlc: str, game_data: Path) -> Path:
    return game_data / dlc / "Languages" / "English" / "Strings"


def diff(dlcs=None, game_data=None):
    """Ritorna [(dlc, relpath, stato, n_en, n_it)] dei file da sistemare."""
    repo = config.repo_root()
    gd = config.game_data(game_data)
    dlcs = dlcs or config.DLCS
    rows = []
    for dlc in dlcs:
        root = en_root(dlc, gd)
        if not root.exists():
            continue
        for enf in sorted(root.rglob("*.txt")):
            rel = enf.relative_to(root)
            itf = repo / dlc / "Strings" / rel
            en_lines = _read(enf)
            if not itf.exists():
                rows.append((dlc, rel.as_posix(), "MANCANTE", len(en_lines), 0))
                continue
            it_lines = _read(itf)
            en_low = [w.lower() for w in en_lines]
            it_low = [w.lower() for w in it_lines]
            if it_low == en_low and en_lines:
                rows.append((dlc, rel.as_posix(), "UGUALE-EN", len(en_lines), len(it_lines)))
            elif len(it_lines) < len(en_lines):
                rows.append((dlc, rel.as_posix(), "CORTO", len(en_lines), len(it_lines)))
    return rows
