"""Riconciliazione riga-per-riga delle liste Words con l'inglese del gioco.

Va piu in profondita di `strings-diff` (che lavora a livello di file): dentro ogni
lista condivisa segnala le voci problematiche, in modo robusto (niente assunzioni
sull'ordine):

  GLOSS    - la voce IT contiene una parentesi: glossa inglese lasciata dal
             traduttore, es. "teppista (banger)" -> va ripulita in "teppista".
  ENGLISH  - la voce IT coincide con una parola inglese (probabile non tradotta).
  MISSING  - l'inglese ha piu voci dell'italiano (contenuto nuovo da tradurre).

`--fix-glosses` rimuove le parentesi in automatico (deterministico, sicuro).
"""
from __future__ import annotations

import re
from pathlib import Path

import config
import stringsdiff

_PAREN = re.compile(r"\s*\([^)]*\)")


def _issues_for(en_lines: list[str], it_lines: list[str], allow_english: bool = True):
    en_set = {w.lower() for w in en_lines}
    # Frazione di voci IT identiche all'EN: se alta, il file e tenuto-uguale di
    # proposito (sillabe, nomi, numeri) -> non segnalare i singoli ENGLISH.
    if it_lines:
        frac = sum(1 for w in it_lines if w.lower() in en_set) / len(it_lines)
        if frac > 0.4:
            allow_english = False
    out = []
    for i, w in enumerate(it_lines):
        if "(" in w and ")" in w:
            out.append((i + 1, "GLOSS", w, _PAREN.sub("", w).strip()))
        elif allow_english and w.lower() in en_set:
            out.append((i + 1, "ENGLISH", w, ""))
    if len(en_lines) > len(it_lines):
        out.append((len(it_lines) + 1, "MISSING",
                    f"(EN ha {len(en_lines) - len(it_lines)} voci in piu)", ""))
    return out


def scan(dlcs=None, game_data=None):
    """[(dlc, relpath, [issues])] per le liste con problemi."""
    repo = config.repo_root()
    gd = config.game_data(game_data)
    dlcs = dlcs or config.DLCS
    rows = []
    for dlc in dlcs:
        root = stringsdiff.en_root(dlc, gd)
        if not root.exists():
            continue
        for enf in sorted(root.rglob("*.txt")):
            rel = enf.relative_to(root)
            itf = repo / dlc / "Strings" / rel
            if not itf.exists():
                continue
            # Pool nomi propri e sillabe: lingua-neutri -> niente ENGLISH per-riga.
            allow_en = rel.parts[0] not in ("Names", "WordParts")
            issues = _issues_for(stringsdiff._read(enf), stringsdiff._read(itf), allow_en)
            if issues:
                rows.append((dlc, rel.as_posix(), issues))
    return rows


def fix_glosses(dlcs=None) -> int:
    """Rimuove le glosse tra parentesi dalle liste IT. Ritorna il numero di voci corrette."""
    repo = config.repo_root()
    dlcs = dlcs or config.DLCS
    n = 0
    for dlc in dlcs:
        for itf in sorted((repo / dlc / "Strings").rglob("*.txt")):
            raw = itf.read_text(encoding="utf-8")
            new_lines = []
            changed = False
            for ln in raw.splitlines():
                body = ln.lstrip("﻿").strip()
                if body and not body.startswith(("#", "//")) and "(" in body and ")" in body:
                    fixed = _PAREN.sub("", ln)
                    if fixed != ln:
                        changed = True
                        n += 1
                        new_lines.append(fixed)
                        continue
                new_lines.append(ln)
            if changed:
                itf.write_text("\n".join(new_lines) + ("\n" if raw.endswith("\n") else ""),
                               encoding="utf-8")
    return n
