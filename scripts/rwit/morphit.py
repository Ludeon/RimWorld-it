"""Morfologia italiana via Morph-it! (lessico) + fallback a regole.

Morph-it! (scripts/.tools/morph-it.txt, gitignored) e un lessico di forme
flesse: 'forma<TAB>lemma<TAB>tratti', es:
    oscura   oscuro   ADJ:pos+f+s
    braccia  braccio  NOUN-F:p
Da qui ricaviamo, in modo deterministico:
  - aggettivi: le 4 forme (m/f x sing/plur) da un lemma maschile singolare;
  - nomi: genere e plurale (inclusi irregolari come braccio->braccia).
Per i lemmi assenti (invariabili, prestiti) si usa il fallback a regole.

Morph-it! (Baroni & Zanchetta, licenza Creative Commons) non e tracciato in git
(e in scripts/.tools/, gitignored). Per scaricarlo una tantum:
    curl -L -o scripts/.tools/morph-it.txt \\
      https://raw.githubusercontent.com/giodegas/morphit-lemmatizer/master/master/morph-it_048.txt
"""
from __future__ import annotations

import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import config

LEX = config.repo_root() / "scripts" / ".tools" / "morph-it.txt"

_ADJ_RE = re.compile(r"^ADJ:pos\+([mf])\+([sp])$")
_NOUN_RE = re.compile(r"^NOUN-([MF]):([sp])$")


@lru_cache(maxsize=1)
def _load():
    """lemma -> {(genere,numero): forma} per aggettivi e nomi."""
    adj: dict[str, dict] = defaultdict(dict)
    noun: dict[str, dict] = defaultdict(dict)
    if not LEX.exists():
        return adj, noun
    with LEX.open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            form, lemma, feat = parts
            m = _ADJ_RE.match(feat)
            if m:
                adj[lemma][(m.group(1), m.group(2))] = form
                continue
            m = _NOUN_RE.match(feat)
            if m:
                noun[lemma][(m.group(1).lower(), m.group(2))] = form
    return adj, noun


# --- fallback a regole (lemmi assenti dal lessico) ------------------------
def _adj_rules(a: str):
    """(m_sing, f_sing, m_plur, f_plur) best-effort dal maschile singolare."""
    if " " in a:                              # locuzioni (es. "alla mano") -> invariabili
        return a, a, a, a
    if a.endswith("io"):                      # sanguinario -> sanguinari/e
        return a, a[:-2] + "ia", a[:-2] + "i", a[:-2] + "ie" if a[-3] not in "cg" else a[:-3] + "ge"
    if a.endswith(("co", "go")):              # -co/-go: velare (default -chi/-ghi)
        b, h = a[:-1], "h"
        return a, b + "a", b + h + "i", b + h + "e"
    if a.endswith("o"):                        # oscuro -> oscura/oscuri/oscure
        b = a[:-1]
        return a, b + "a", b + "i", b + "e"
    if a.endswith("a"):                        # omicida (comune) -> omicidi/e
        b = a[:-1]
        return a, a, b + "i", b + "e"
    if a.endswith("e"):                        # feroce -> feroci
        return a, a, a[:-1] + "i", a[:-1] + "i"
    return a, a, a, a                           # invariabile


def _noun_rules(lemma: str):
    """(genere, plurale) best-effort."""
    if " " in lemma:                            # multi-parola: pluralizza la TESTA
        head, _, tail = lemma.partition(" ")    # "trasgressore della legge"
        g, hp = _noun_rules(head)               # -> "trasgressori" + " della legge"
        return g, f"{hp} {tail}"
    if lemma.endswith("a"):
        return "f", lemma[:-1] + "e"
    if lemma.endswith(("o", "e")):
        return "m", lemma[:-1] + "i"
    return "m", lemma                           # invariabile (tribù, citta, prestiti...)


# Suffissi italiani a genere quasi-certo: disambiguano i lemmi che Morph-it!
# registra con entrambi i generi (es. "azione" -> f, non m).
_FEM_SUFFIX = ("zione", "sione", "gione", "tà", "tù", "udine", "aggine",
               "ezza", "izia", "enza", "anza", "trice")
_MAS_SUFFIX = ("ore", "ame", "mento", "ismo", "iere")


def _suffix_gender(lemma: str) -> str | None:
    if lemma.endswith(_FEM_SUFFIX):
        return "f"
    if lemma.endswith(_MAS_SUFFIX):
        return "m"
    return None


# --- API ------------------------------------------------------------------
def adjective_forms(lemma: str):
    """(m_sing, f_sing, m_plur, f_plur). Morph-it! se disponibile, altrimenti regole."""
    adj, _ = _load()
    e = adj.get(lemma)
    if e and all(k in e for k in (("m", "s"), ("f", "s"), ("m", "p"), ("f", "p"))):
        return e[("m", "s")], e[("f", "s")], e[("m", "p")], e[("f", "p")]
    return _adj_rules(lemma)


def noun_info(lemma: str):
    """(genere 'm'/'f', plurale). Preferisce il plurale dello stesso genere del singolare."""
    _, noun = _load()
    e = noun.get(lemma)
    if e:
        has_m, has_f = ("m", "s") in e, ("f", "s") in e
        if has_m and has_f:                     # ambiguo: disambigua dal suffisso
            gender = _suffix_gender(lemma) or "m"
        else:
            gender = "f" if has_f else "m" if has_m else next(iter(e))[0]
        plural = e.get((gender, "p")) or e.get(("m", "p")) or e.get(("f", "p"))
        if plural:
            return gender, plural
    return _noun_rules(lemma)


def has_adjective(lemma: str) -> bool:
    adj, _ = _load()
    e = adj.get(lemma)
    return bool(e) and all(k in e for k in (("m", "s"), ("f", "s"), ("m", "p"), ("f", "p")))


def has_noun(lemma: str) -> bool:
    _, noun = _load()
    return lemma in noun


def available() -> bool:
    return LEX.exists()
