"""Linter di concordanza di genere: articolo/aggettivo FISSO davanti a costrutto variabile.

Bug di stile (non rompe il parser, ma rende a schermo una frase sgrammaticata in
una delle due forme di genere): un articolo/determinante (o un aggettivo) lasciato a
genere FISSO precede un sostantivo/aggettivo che invece flette con la ternaria
`{VAR_gender ? o:a}`. Esempio reale (Solid_Child):

    ...come un bravo cadett{PAWN_gender ? o:a} spaziale   ->  femm.: "un bravo cadetta"
    ...come un figli{PAWN_gender ? o:a} unic{...}          ->  femm.: "un figlia unica"
    ...come un {PAWN_gender ? uomo:donna}                  ->  femm.: "un donna"

La forma corretta porta l'articolo (e l'aggettivo) DENTRO la ternaria:
`{PAWN_gender ? un bravo:una brava} cadett{...}`, `{PAWN_gender ? un:una} figli{...}`.

Strategia (alta precisione, pochi falsi positivi):
  1. Trova le ternarie di genere che FLETTONO il genere:
     - forma-suffisso  `radice{VAR_gender ? o:a}`  (la `{` segue una lettera) -> i due
       rami sono brevi e diversi (o/a);
     - forma-parola    `{VAR_gender ? uomo:donna}` -> ramo masch. (non finisce in -a) +
       ramo femm. (finisce in -a).
  2. Guarda il token IMMEDIATAMENTE precedente (saltando un eventuale aggettivo fisso):
     se e' un articolo/determinante di genere a forma FISSA (non chiuso da `}`, cioe'
     non gia' dentro una ternaria) -> SEGNALA.

Un articolo gia' variabile (`{PAWN_gender ? un:una} ...` -> il token prima e' `}`) NON
e' segnalato. Lavora sul SOLO lato IT (ledger.iter_strings, li-aware). Non tocca i file.

Limiti noti (per non introdurre falsi positivi): coppie femm. che non finiscono in -a
(poeta/poetessa, attore/attrice) NON sono rilevate come flessioni; i possessivi
(suo/sua...) sono esclusi dal set articoli. Recall < 100%, precisione alta.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import config
import ledger

# articoli/determinanti a genere marcato (forma singolare): se restano fissi davanti
# a un sostantivo che flette, una delle due rese e' sgrammaticata.
ARTICLES = {
    # indeterminativi
    "un", "uno", "una", "un'",
    # determinativi
    "il", "lo", "la", "l'",
    # preposizioni articolate (sing.)
    "del", "dello", "della", "dell'",
    "nel", "nello", "nella", "nell'",
    "al", "allo", "alla", "all'",
    "sul", "sullo", "sulla", "sull'",
    "dal", "dallo", "dalla", "dall'",
    "col", "collo", "colla",
    # dimostrativi (sing.)
    "quel", "quello", "quella", "quell'",
    "questo", "questa", "quest'",
}

# aggettivi comuni che possono stare fra articolo e nome (prenominali); ammessi come
# UN solo token-cuscinetto fra l'articolo e il costrutto flesso.
ADJECTIVES = {
    "bravo", "brava", "bello", "bella", "bel", "buono", "buona", "buon",
    "grande", "gran", "piccolo", "piccola", "vecchio", "vecchia",
    "nuovo", "nuova", "giovane", "povero", "povera", "caro", "cara",
    "solo", "sola", "stesso", "stessa", "primo", "prima", "ultimo", "ultima",
    "unico", "unica", "vero", "vera", "semplice", "fiero", "fiera",
    "vil", "vile", "puro", "pura",
}

# clitici/articoli/pronomi: se ENTRAMBI i rami della ternaria sono di questo insieme,
# la ternaria fa variare un articolo/pronome (gia' la forma corretta), NON un sostantivo
# -> niente concordanza da verificare. Evita il falso positivo "Questo {gender ? lo:la}"
# (pronome neutro "cio'" + clitico oggetto lo/la).
CLITICS = {
    "lo", "la", "li", "le", "gli", "l'", "ne",
    "il", "un", "uno", "una", "un'",
    "del", "della", "dei", "delle", "al", "alla", "nel", "nella",
}

# {VAR_gender ? A : B}  (cattura il primo ramo del 3-rami in B, ripulito dopo)
_TERNARY = re.compile(r"\{([A-Za-z0-9_]+)_gender \? ([^{}:]*?)\s*:\s*([^{}]*?)\}")
_WORD = re.compile(r"[A-Za-zÀ-ÿ']+")


@dataclass
class Hit:
    dlc: str
    file: str
    tag: str
    line: int | None
    kind: str            # "gender-agreement"
    detail: str          # snippet "articolo ... {ternaria}"
    it: str


def _flips_gender(a: str, b: str, is_suffix: bool) -> bool:
    """True se la ternaria fa cambiare genere al sostantivo/aggettivo."""
    a, b = a.strip(), b.split(":")[0].strip()  # b: primo ramo se 3-rami
    if not a or not b or a == b:
        return False
    if is_suffix:
        # suffissi brevi tipo o/a, e/i... una vera flessione di genere e' o<->a
        return len(a) <= 4 and len(b) <= 4 and (a.endswith("o") and b.endswith("a"))
    # forma-parola: i rami sono articoli/clitici (lo/la, un/una...) -> non un sostantivo
    if a.lower() in CLITICS and b.lower() in CLITICS:
        return False
    # ramo masch (non in -a) + ramo femm (in -a)
    return (not a.endswith("a")) and b.endswith("a")


def _preceding_word(it: str, pos: int) -> tuple[str | None, bool, int]:
    """Token (parola) prima di `pos`, saltando gli spazi.

    Ritorna (parola_lower, preceduto_da_chiusa_ternaria, start_index_della_parola).
    Se prima della parola c'e' `}` (articolo gia' variabile) -> il flag e' True.
    """
    j = pos
    while j > 0 and it[j - 1].isspace():
        j -= 1
    if j == 0:
        return None, False, j
    if it[j - 1] == "}":
        return None, True, j
    k = j
    while k > 0 and (it[k - 1].isalpha() or it[k - 1] == "'"):
        k -= 1
    word = it[k:j]
    return (word.lower() if word else None), False, k


def check_text(it: str) -> list[tuple[str, str]]:
    """Ritorna [(kind, detail), ...] per una stringa IT."""
    problems: list[tuple[str, str]] = []
    for m in _TERNARY.finditer(it):
        a, b = m.group(2), m.group(3)
        is_suffix = m.start() > 0 and it[m.start() - 1].isalpha()
        if not _flips_gender(a, b, is_suffix):
            continue
        # punto di partenza: inizio del costrutto flesso (radice, se forma-suffisso)
        start = m.start()
        if is_suffix:
            while start > 0 and (it[start - 1].isalpha() or it[start - 1] == "'"):
                start -= 1
        w1, ternary_before, w1_start = _preceding_word(it, start)
        if ternary_before or w1 is None:
            continue
        art_start = None
        if w1 in ARTICLES:
            art_start = w1_start
        elif w1 in ADJECTIVES:
            # salta l'aggettivo, cerca un articolo prima
            w2, t2, w2_start = _preceding_word(it, w1_start)
            if not t2 and w2 in ARTICLES:
                art_start = w2_start
        if art_start is not None:
            snippet = it[art_start:m.end()]
            problems.append(("gender-agreement", snippet[:100]))
    return problems


def scan(dlcs=None) -> list[Hit]:
    repo = config.repo_root()
    dlcs = dlcs or config.DLCS
    hits: list[Hit] = []
    for dlc, relfile, tag, line, it, _en in ledger.iter_strings(repo, dlcs):
        if not it:
            continue
        for kind, detail in check_text(it):
            hits.append(Hit(dlc, relfile, tag, line, kind, detail, it))
    return hits


if __name__ == "__main__":
    rows = scan()
    print(f"# gender-check - {len(rows)} stringhe con concordanza di genere sospetta\n")
    cur = None
    for h in rows:
        key = f"{h.dlc}\\{h.file}"
        if key != cur:
            cur = key
            print(f"\n=== {key} ===")
        loc = f"L{h.line}" if h.line else "  "
        print(f"  {loc:<7} [{h.kind}] {h.detail}")
        print(f"     IT: {h.it}")
