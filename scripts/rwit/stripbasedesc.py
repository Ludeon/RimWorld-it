"""Rimuove le iniezioni morte `*.baseDesc` dalle BackstoryDef.

In RimWorld <=1.4 le backstory erano la classe `Backstory` col campo `baseDesc`.
Dalla 1.5/1.6 sono `BackstoryDef : Def` e il testo mostrato e' il campo `description`
(ereditato da Def). Il vecchio `baseDesc` NON e' piu' un campo del Def: le iniezioni
`<X.baseDesc>` non vengono lette dal gioco -> sono stringhe fantasma.

Verificato: i Def inglesi del gioco (Data/Core/Defs/BackstoryDefs) usano `<description>`
e ZERO `<baseDesc>`; e le traduzioni UFFICIALI incluse nel gioco (FR/DE/ES x2) spediscono
`.description` x N e `.baseDesc` x 0. Questo repo e' l'unico a trascinarsi i baseDesc.

Operazione: elimina le righe `<X.baseDesc>...</X.baseDesc>` dai file
`<DLC>/DefInjected/BackstoryDef/*.xml`. I baseDesc qui sono sempre su riga singola
(con `\\n\\n` letterali, mai veri a-capo): la rimozione riga-per-riga e' sicura e non
tocca commenti EN, description ne' titoli. Default DRY-RUN; scrive solo con apply=True.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import config

_BASEDESC_LINE = re.compile(r"^\s*<([A-Za-z0-9_]+)\.baseDesc>.*</\1\.baseDesc>\s*$")


@dataclass
class FileResult:
    path: Path
    rel: str
    removed: int


def find_files(repo: Path, dlcs=None) -> list[Path]:
    """Tutti i <DLC>/DefInjected/BackstoryDef/*.xml del repo (esclude dist/)."""
    dlcs = dlcs or config.DLCS
    out: list[Path] = []
    for dlc in dlcs:
        d = repo / dlc / "DefInjected" / "BackstoryDef"
        if d.exists():
            out.extend(sorted(d.glob("*.xml")))
    return out


def strip_text(text: str) -> tuple[str, int]:
    """Ritorna (nuovo_testo, n_righe_rimosse). Preserva il fine-riga originale."""
    nl = "\r\n" if "\r\n" in text else "\n"
    trailing = text.endswith(("\n", "\r"))
    lines = text.splitlines()
    kept = [ln for ln in lines if not _BASEDESC_LINE.match(ln)]
    removed = len(lines) - len(kept)
    new = nl.join(kept) + (nl if trailing else "")
    return new, removed


def run(dlcs=None, exclude: set[str] | None = None, apply: bool = False) -> list[FileResult]:
    repo = config.repo_root()
    exclude = {e.lower() for e in (exclude or set())}
    results: list[FileResult] = []
    for f in find_files(repo, dlcs):
        if f.stem.lower() in exclude or f.name.lower() in exclude:
            continue
        text = f.read_text(encoding="utf-8")
        new, removed = strip_text(text)
        if removed:
            results.append(FileResult(f, f.relative_to(repo).as_posix(), removed))
            if apply:
                f.write_text(new, encoding="utf-8")
    return results
