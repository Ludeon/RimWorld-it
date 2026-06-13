"""Controllo freschezza delle liste Words.

Copre due classi di problema che gli altri controlli (presenza file, risoluzione
dei riferimenti) NON vedono perche guardano la struttura, non il contenuto:

  1. Base IT indietro/avanti rispetto all'INGLESE DEL GIOCO (EURISTICO): il conteggio
     righe IT != EN puo' indicare voci mancanti, MA spesso e' benigno - sinonimi
     inglesi che collassano su un'unica parola italiana, liste riordinate
     alfabeticamente, voci tenute volutamente in inglese. Verificare il CONTENUTO
     (es. con `rwit reconcile`) prima di aggiungere/togliere.
  2. Varianti di genere che non coprono piu la base, perche rigenerate da una base
     piu vecchia (es. Animals 141/178). Per i NOMI: somma M+F deve == base; per
     AGGETTIVI/COLORI (ogni voce ha forma M e F): ciascuna variante == base.

Uso: rwit freshness  (richiede l'installazione del gioco per il confronto EN).
"""
from __future__ import annotations

import re
from pathlib import Path

import config

_COMMENT = ("//", "#")

# Suffissi che marcano un file-VARIANTE (da non trattare come lista base).
_VARIANT_RE = re.compile(
    r"_(?:Singular_|Plural_)?(?:Masculine|Feminine|Neuter|Vowel|Lo|Di)$"
    r"|_(?:M|F|MP|FP|MS|FS|I|Gli|Le)$"
)


def _count(p: Path) -> int | None:
    """Righe-voce (non vuote, non-commento) in un file Words; None se assente.

    Conta le RIGHE, non le voci uniche: una lista pool e 'completa' se ogni slot
    inglese ha la sua riga italiana, anche se piu righe ripetono la stessa parola
    (sinonimi inglesi che collassano su un'unica parola italiana). Toglie il BOM
    PRIMA dello strip, cosi i commenti malformati '﻿ //...' sono riconosciuti."""
    if not p.exists():
        return None
    n = 0
    for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = ln.lstrip("﻿").strip()
        if s and not s.startswith(_COMMENT):
            n += 1
    return n


# Classi dello split SINGOLARE italiano (genere + iniziale per l'articolo): la loro
# copertura totale deve uguagliare la base. NIENTE Neuter (l'italiano non ce l'ha:
# i file _Neuter sono cruft di vecchie generazioni). Le _Plural_ sono un altro asse.
_SING_CLASSES = ("Masculine", "Feminine", "Vowel", "Lo")


def _variant_counts(base: Path) -> dict[str, int]:
    """{classe: conteggio} delle varianti singolari di X.txt (X_<c> o X_Singular_<c>)."""
    out: dict[str, int] = {}
    for cls in _SING_CLASSES:
        for suf in (f"_{cls}", f"_Singular_{cls}"):
            p = base.with_name(f"{base.stem}{suf}.txt")
            if p.exists():
                out[cls] = _count(p) or 0
                break
    return out


def check(dlcs=None, game_override: str | None = None):
    """Ritorna (base_issues, var_issues, has_game).

    base_issues: [(dlc, rel, it_count, en_count)] dove IT != EN del gioco.
    var_issues:  [(dlc, rel, base, m, f)] dove le varianti non coprono la base.
    """
    repo = config.repo_root()
    try:
        game = config.game_data(game_override)
    except FileNotFoundError:
        game = None
    dlcs = dlcs or config.DLCS
    base_issues: list[tuple] = []
    var_issues: list[tuple] = []
    for dlc in dlcs:
        wdir = repo / dlc / "Strings" / "Words"
        if not wdir.exists():
            continue
        engdir = (game / dlc / "Languages" / "English" / "Strings" / "Words") if game else None
        for f in sorted(wdir.rglob("*.txt")):
            if _VARIANT_RE.search(f.stem):
                continue
            it_n = _count(f)
            rel = f.relative_to(wdir).as_posix()
            if engdir is not None:
                en_n = _count(engdir / f.relative_to(wdir))
                if en_n is not None and it_n is not None and en_n != it_n:
                    base_issues.append((dlc, rel, it_n, en_n))
            vc = _variant_counts(f)
            if "Masculine" in vc and "Feminine" in vc and it_n is not None:
                mc, fc = vc["Masculine"], vc["Feminine"]
                total = sum(vc.values())
                # nomi: somma di tutte le classi == base ; aggettivi/colori: M == base == F
                ok = total == it_n or mc == it_n == fc
                # un genere VUOTO mentre l'altro e pieno = quasi sempre un errore (es. una
                # lista di aggettivi/colori splittata per sbaglio come nome): segnalalo
                # anche se la somma tornasse (M=base, F=0 -> M+F=base ma e sbagliato).
                one_empty = (mc == 0) != (fc == 0)
                if not ok or one_empty:
                    var_issues.append((dlc, rel, it_n, mc, fc, total))
    return base_issues, var_issues, game is not None
