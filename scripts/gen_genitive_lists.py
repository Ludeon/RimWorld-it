#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Genera le liste "genitive" (preposizione articolata fusa + nome) per i namer.

Per ogni lista di nomi gia' divisa per genere (es. Animals_Singular_Masculine.txt)
produce la versione con la preposizione di + articolo gia' fusa e accordata per
genere ed elisione: "del toporagno", "dello scoiattolo", "dell'orso",
"della pantera", "dell'aquila".

L'algoritmo di elisione e' la stessa logica di LanguageWorker_Italian.cs
(StartsWithVowelSound + MasculineNeedsLo), cosi' le liste restano coerenti col
resto della traduzione. I file sorgente NON vengono toccati: si scrivono nuovi
file *_Genitive_Masculine / *_Genitive_Feminine accanto ad essi.

Uso:
    .venv\\Scripts\\python scripts\\gen_genitive_lists.py
"""
from pathlib import Path

NOUNS = Path(__file__).resolve().parent.parent / "Core" / "Strings" / "Words" / "Nouns"

# (sorgente senza estensione, genere)  ->  i nomi di output derivano dal sorgente
SOURCES = [
    ("Animals_Singular_Masculine", "m"),
    ("Animals_Singular_Feminine", "f"),
    ("NaturalObject_Singular_Masculine", "m"),
    ("NaturalObject_Singular_Feminine", "f"),
    ("TreeTypes_Singular_Masculine", "m"),
    ("TreeTypes_Singular_Feminine", "f"),
    ("Vegetables_Singular_Masculine", "m"),
    ("Vegetables_Singular_Feminine", "f"),
]

VOWELS = set("aeiouAEIOU")


def starts_with_vowel_sound(w: str) -> bool:
    """Vocale, oppure h muta + vocale (hotel, hostess)."""
    c = w[0]
    if c in VOWELS:
        return True
    if c in "hH" and len(w) >= 2 and w[1] in VOWELS:
        return True
    return False


def masculine_needs_lo(w: str) -> bool:
    """s impura, z, x, y, ps, pn, gn, i + vocale (semiconsonante)."""
    c0 = w[0].lower()
    c1 = w[1].lower() if len(w) >= 2 else ""
    second_is_vowel = len(w) >= 2 and w[1] in VOWELS
    if c0 in "zxy":
        return True
    if c0 == "s" and not second_is_vowel:  # s impura
        return True
    if c0 == "p" and c1 in ("s", "n"):     # ps, pn
        return True
    if c0 == "g" and c1 == "n":            # gn
        return True
    if c0 == "i" and second_is_vowel:      # i + vocale: lo iato, lo ione
        return True
    return False


def genitive(word: str, gender: str) -> str:
    if gender == "f":
        return ("dell'" + word) if starts_with_vowel_sound(word) else ("della " + word)
    # maschile
    if starts_with_vowel_sound(word):
        return "dell'" + word
    if masculine_needs_lo(word):
        return "dello " + word
    return "del " + word


def read_entries(path: Path):
    out = []
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        s = raw.strip()
        if not s or s.startswith("//"):
            continue
        out.append(s)
    return out


def main():
    for stem, gender in SOURCES:
        src = NOUNS / f"{stem}.txt"
        entries = read_entries(src)
        out_name = stem.replace("_Singular_", "_Genitive_")
        dst = NOUNS / f"{out_name}.txt"
        header = "// generato da scripts/gen_genitive_lists.py — non modificare a mano"
        lines = [header, ""] + [genitive(w, gender) for w in entries]
        dst.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8", newline="")
        print(f"{src.name:42} -> {dst.name:42} ({len(entries)} voci)")


if __name__ == "__main__":
    main()
