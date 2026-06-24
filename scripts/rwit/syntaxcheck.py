"""Linter di sintassi del motore: ternarie di genere e bilanciamento simboli.

Verifica deterministica delle regole strutturali (TRANSLATION-SYNTAX.md) che, se
violate, ROMPONO il parser del gioco a runtime — non sono questioni di stile:

  - ternaria di genere ben formata: `{VAR_gender ? a : b}` (un solo `?`, e 1 o 2 `:`
    per la forma a 3 rami m/f/neutro `{0_gender ? o : a : o}`). Robusto agli annidamenti
    `{... ? il {NAME} : la {NAME}}` (conta `?`/`:` solo al livello immediato del gruppo).
  - graffe `{}` bilanciate (un `{` senza `}` manda in errore la risoluzione).
  - parentesi-simbolo `[]` bilanciate (i simboli RulePack/grammatica sono `[symbol]`).

Lavora sul SOLO lato IT (via ledger.iter_strings, li-aware): i simboli legittimi della
fonte inglese non sono falsi positivi. Offline, deterministico. Non tocca i file.
"""
from __future__ import annotations

from dataclasses import dataclass

import config
import ledger


@dataclass
class Hit:
    dlc: str
    file: str
    tag: str
    line: int | None
    kind: str            # "ternary-malformed" | "brace-unbalanced" | "bracket-unbalanced"
    detail: str
    it: str


def _validate_group(grp: str) -> bool:
    """True se il gruppo {..} e' una ternaria MALFORMATA. grp include le graffe.

    Conta `?` e `:` al livello immediato (ignora graffe annidate). Non-ternaria
    (0 `?`, es. {PAWN_nameDef}) -> ok. Ternaria valida = 1 `?` e 1 o 2 `:`.
    """
    inner = grp[1:-1]
    depth = q = colon = 0
    for c in inner:
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif depth == 0:
            if c == "?":
                q += 1
            elif c == ":":
                colon += 1
    if q == 0:
        return False
    return not (q == 1 and colon in (1, 2))


def check_text(it: str) -> list[tuple[str, str]]:
    """Ritorna [(kind, detail), ...] per una stringa IT."""
    problems: list[tuple[str, str]] = []
    nbo, nbc = it.count("{"), it.count("}")
    if nbo != nbc:
        problems.append(("brace-unbalanced", f"{{={nbo} }}={nbc}"))
    sbo, sbc = it.count("["), it.count("]")
    if sbo != sbc:
        problems.append(("bracket-unbalanced", f"[={sbo} ]={sbc}"))
    # estrai i gruppi {..} top-level e valida le ternarie (solo se graffe bilanciate)
    if nbo == nbc:
        depth = start = 0
        start = -1
        for i, c in enumerate(it):
            if c == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0 and start >= 0:
                    grp = it[start:i + 1]
                    if _validate_group(grp):
                        problems.append(("ternary-malformed", grp[:90]))
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
    print(f"# syntax-check - {len(rows)} stringhe con sintassi sospetta\n")
    cur = None
    for h in rows:
        key = f"{h.dlc}\\{h.file}"
        if key != cur:
            cur = key
            print(f"\n=== {key} ===")
        loc = f"L{h.line}" if h.line else "  "
        print(f"  {loc:<7} [{h.kind}] {h.detail}")
        print(f"     IT: {h.it}")
