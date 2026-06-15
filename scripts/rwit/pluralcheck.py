"""Controllo del plurale 'inglese' [Simbolo]s nelle stringhe IT.

Bug tipico (RulePack generativi): la regola inglese pluralizza un simbolo
aggiungendo 's' -> [Weapon]s, [Animal]s, [PersonJob]s. Tradotta alla lettera
in italiano, la 's' resta incollata al valore risolto a runtime e a schermo
compare 'razzos', 'cittadinos', 'pirati' -> 'piratis' ecc.

La forma corretta usa un simbolo plurale dedicato gia' presente nel pacchetto
(es. [WeaponPlural], [AnimalPlural], [PersonJob_PluralMasculine]) oppure parole
italiane gia' al plurale.

Confronta SOLO il lato IT (ledger.iter_strings restituisce il testo tradotto,
non il commento <!-- EN: -->, quindi i plurali inglesi LEGITTIMI della fonte
non sono falsi positivi). Offline, deterministico. Non tocca i file.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import config
import ledger

# Un ']' di chiusura simbolo seguito subito da 's' e da confine di parola:
#   [Weapon]s   [Animal]s.   [Enemy]s,   ma NON [X]sole (parola che inizia per s)
_GLUED_S = re.compile(r"\][A-Za-z0-9_]*\]?s(?![A-Za-z])")
# piu' preciso: ']' + 's' + boundary  (il simbolo e' [..]; ci interessa ]s)
_PLURAL_S = re.compile(r"\]s(?![A-Za-z])")
# cattura il nome del simbolo che precede la 's' per il report: [Name]s
_SYMBOL_S = re.compile(r"\[([A-Za-z0-9_]+)\]s(?![A-Za-z])")


@dataclass
class Hit:
    dlc: str
    file: str
    tag: str
    line: int | None
    symbols: list[str]   # simboli pluralizzati con 's' (es. Weapon, Animal)
    it: str
    en: str


def scan(dlcs=None) -> list[Hit]:
    repo = config.repo_root()
    dlcs = dlcs or config.DLCS
    hits: list[Hit] = []
    for dlc, relfile, tag, line, it, en in ledger.iter_strings(repo, dlcs):
        if not it:
            continue
        if not _PLURAL_S.search(it):
            continue
        syms = _SYMBOL_S.findall(it)
        hits.append(Hit(dlc, relfile, tag, line, syms, it, en or ""))
    return hits


if __name__ == "__main__":
    rows = scan()
    print(f"# plural-check - {len(rows)} stringhe IT con plurale inglese [..]s\n")
    cur = None
    for h in rows:
        key = f"{h.dlc}\\{h.file}"
        if key != cur:
            cur = key
            print(f"\n=== {key} ===")
        loc = f"L{h.line}" if h.line else "  "
        print(f"  {loc:<7} {h.tag}")
        print(f"     simboli: {', '.join('['+s+']s' for s in h.symbols) or '?'}")
        print(f"     IT: {h.it}")
