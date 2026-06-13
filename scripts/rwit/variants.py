"""Generatore di varianti morfologiche per le liste Strings/Words (via Morph-it!).

Da una lista di LEMMI produce, in modo deterministico, le forme flesse divise per
genere/numero (aggettivi) o per articolo (nomi), con schema di naming coerente.
Sostituisce i file variante creati a mano (incoerenti/incompleti).

Aggettivi (lemma = maschile singolare) -> 5 file:
    <Nome>.txt                      (base = maschile singolare, usato da [AdjectiveX])
    <Nome>_Singular_Masculine.txt
    <Nome>_Singular_Feminine.txt
    <Nome>_Plural_Masculine.txt
    <Nome>_Plural_Feminine.txt

Nomi (lemma = singolare) -> bucket per articolo del PLURALE:
    <Nome>_I.txt    (maschile plurale con articolo "I":  i cani)
    <Nome>_Gli.txt  (maschile plurale con articolo "Gli": gli orsi, gli zaini)
    <Nome>_Le.txt   (femminile plurale con articolo "Le": le volpi)
"""
from __future__ import annotations

from pathlib import Path

import config
import morphit

HEADER = "// Auto-generato da `rwit variants` (Morph-it!). Non modificare a mano."

# Iniziali che in italiano richiedono lo/gli invece di il/i.
_GLI_START = ("a", "e", "i", "o", "u", "z", "x", "y", "gn", "pn", "ps")


def _read(f: Path) -> list[str]:
    out = []
    for ln in f.read_text(encoding="utf-8").splitlines():
        ln = ln.lstrip("﻿").strip()
        if ln and not ln.startswith(("#", "//")):
            out.append(ln)
    return out


def _write(f: Path, words: list[str]) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(HEADER + "\n" + "\n".join(words) + "\n", encoding="utf-8")


def _wants_gli(plural: str) -> bool:
    p = plural.lower()
    if p[:2] in ("gn", "pn", "ps"):
        return True
    if p[0] == "s" and len(p) > 1 and p[1] not in "aeiou":  # s impura
        return True
    return p[0] in _GLI_START


def gen_adjective(name: str, dlc: str = "Core", lemmas: list[str] | None = None):
    """Genera i 5 file aggettivo. Ritorna i lemmi caduti sul fallback (da rivedere)."""
    base = config.repo_root() / dlc / "Strings" / "Words" / "Adjectives"
    if lemmas is None:
        for cand in (base / f"{name}_Singular_Masculine.txt", base / f"{name}.txt"):
            if cand.exists():
                lemmas = _read(cand)
                break
    if not lemmas:
        raise FileNotFoundError(f"Nessun lemma per {name} in {base}")

    ms, fs, mp, fp, fallback = [], [], [], [], []
    for lem in lemmas:
        a, b, c, d = morphit.adjective_forms(lem)
        ms.append(a); fs.append(b); mp.append(c); fp.append(d)
        if not morphit.has_adjective(lem):
            fallback.append(lem)
    _write(base / f"{name}.txt", ms)
    _write(base / f"{name}_Singular_Masculine.txt", ms)
    _write(base / f"{name}_Singular_Feminine.txt", fs)
    _write(base / f"{name}_Plural_Masculine.txt", mp)
    _write(base / f"{name}_Plural_Feminine.txt", fp)
    return fallback


def gen_noun(name: str, dlc: str = "Core", lemmas: list[str] | None = None):
    """Genera i bucket nome per articolo del plurale. Ritorna i fallback."""
    base = config.repo_root() / dlc / "Strings" / "Words" / "Nouns"
    if lemmas is None:
        cand = base / f"{name}.txt"
        if cand.exists():
            lemmas = _read(cand)
    if not lemmas:
        raise FileNotFoundError(f"Nessun lemma per {name} in {base}")

    buckets = {"I": [], "Gli": [], "Le": []}
    fallback = []
    for lem in lemmas:
        gender, plural = morphit.noun_info(lem)
        if not morphit.has_noun(lem):
            fallback.append(lem)
        if gender == "f":
            buckets["Le"].append(plural)
        else:
            buckets["Gli" if _wants_gli(plural) else "I"].append(plural)
    for art, words in buckets.items():
        if words:
            _write(base / f"{name}_{art}.txt", words)
    return fallback


def gen_noun_gender(name: str, dlc: str = "Core", lemmas: list[str] | None = None):
    """Spezza una lista nomi (singolari) per genere -> 2 file:
        <Nome>_Singular_Masculine.txt
        <Nome>_Singular_Feminine.txt
    Serve ai namer che accordano aggettivo/articolo col nome (es. NamerQuestDefault).
    Ritorna i lemmi caduti sul fallback (genere indovinato dalle regole, da rivedere).
    """
    base = config.repo_root() / dlc / "Strings" / "Words" / "Nouns"
    if lemmas is None:
        cand = base / f"{name}.txt"
        if cand.exists():
            lemmas = _read(cand)
    if not lemmas:
        raise FileNotFoundError(f"Nessun lemma per {name} in {base}")

    ms, fs, fallback = [], [], []
    for lem in lemmas:
        gender, _ = morphit.noun_info(lem)
        (fs if gender == "f" else ms).append(lem)
        if not morphit.has_noun(lem):
            fallback.append(lem)
    _write(base / f"{name}_Singular_Masculine.txt", ms)
    _write(base / f"{name}_Singular_Feminine.txt", fs)
    return fallback
