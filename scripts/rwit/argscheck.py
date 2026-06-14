"""Controllo dei segnaposto di formato {...} fra traduzione IT e fonte EN.

Bug tipico: una vecchia versione del gioco usava una format-string con {0} che
ora non e' piu' tale (il motore compone da solo "etichetta: valore"). La
traduzione ha conservato il {0}, che quindi appare letterale a schermo
(es. "Causato dal passato: {0}: Topo di biblioteca").

Confronta, per ogni stringa tradotta, l'insieme dei segnaposto presenti nell'IT
con quelli del commento <!-- EN: -->:
  - posizionali  {0} {1} {0_gender} ...  -> indice numerico
  - nominali     {PAWN_label} {VAR} ...  (senza spazi: i ternari di genere
    {X_gender ? o : a} sono esclusi perche' il loro contenuto cambia in IT)

Segnala i segnaposto IN PIU' nell'IT (probabile residuo) e quelli MANCANTI
(argomento perso). Offline, deterministico. Non tocca i file.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import config
import ledger

_NUM = re.compile(r"\{(\d+)")              # {0}, {12}, {0_gender}, {1_label}
_NAMED = re.compile(r"\{([A-Za-z_]\w*)\}")  # {VAR}, {PAWN_label} (niente spazi -> no ternari)

# Famiglia pronome/genere: la traduzione la rende lecitamente con 'il proprio/suo',
# riformula o usa un ternario -> NON contarla come buco (sarebbe quasi tutto rumore).
_PRONOUN = re.compile(r"_(pronoun|possessive|objective|gender|reflexive)$", re.I)


def _nums(s: str) -> set[str]:
    return set(_NUM.findall(s or ""))


def _named(s: str) -> set[str]:
    """Variabili nominali {NOME} di contenuto (esclusa la famiglia pronome/genere)."""
    return {v for v in _NAMED.findall(s or "") if not _PRONOUN.search(v)}


@dataclass
class Hit:
    dlc: str
    file: str
    tag: str
    line: int | None
    extra_num: list[str]   # in IT, non in EN (es. {0} fantasma)
    miss_num: list[str]    # in EN, non in IT (argomento perso)
    extra_var: list[str]
    miss_var: list[str]
    en: str
    it: str

    @property
    def kind(self) -> str:
        if self.extra_num:
            return "extra-pos"       # il caso piu' frequente/visibile
        if self.miss_num:
            return "manca-pos"
        if self.extra_var:
            return "extra-var"
        return "manca-var"


def scan(dlcs=None) -> list[Hit]:
    repo = config.repo_root()
    dlcs = dlcs or config.DLCS
    hits: list[Hit] = []
    for dlc, relfile, tag, line, it, en in ledger.iter_strings(repo, dlcs):
        if not it or not en or it == en:
            continue  # serve sia IT sia EN, e dev'essere effettivamente tradotta
        en_n, it_n = _nums(en), _nums(it)
        en_v, it_v = _named(en), _named(it)
        extra_num, miss_num = it_n - en_n, en_n - it_n
        extra_var, miss_var = it_v - en_v, en_v - it_v
        if extra_num or miss_num or extra_var or miss_var:
            hits.append(Hit(dlc, relfile, tag, line,
                            sorted(extra_num, key=int), sorted(miss_num, key=int),
                            sorted(extra_var), sorted(miss_var), en, it))
    return hits
