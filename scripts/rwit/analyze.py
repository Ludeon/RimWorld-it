"""Calcolo del gap reale: corpus inglese del report vs traduzioni del repo.

Nota: il TranslationReport va generato in gioco CON i symlink funzionanti.
Se i symlink sono rotti, il gioco carica zero italiano e segna come "mancante"
l'intero gioco: in quel caso questo confronto col repo recupera comunque il gap
reale (report - traduzioni gia presenti nel repo).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import config
import report as report_mod
import repo as repo_mod


@dataclass
class Gap:
    report: report_mod.Report
    keyed_missing: list       # chiavi assenti nel repo
    keyed_untranslated: list  # presenti nel repo ma vuote o == inglese
    def_missing: list         # def non ancora tradotti


def _def_translated(e: report_mod.DefEntry, def_repo: dict) -> bool:
    names = def_repo.get(e.deftype)
    if not names:
        return False
    if e.defpath in names:
        return True
    # liste rulesStrings.N: se il genitore esiste, consideriamo la lista coperta
    if "." in e.defpath:
        parent, last = e.defpath.rsplit(".", 1)
        if last.isdigit() and parent in names:
            return True
    return False


def compute(report_path, dlcs=None) -> Gap:
    dlcs = list(dlcs) if dlcs else config.DLCS
    rep = report_mod.parse(report_path)
    root = config.repo_root()
    keyed_repo = repo_mod.read_keyed(root, dlcs)
    def_repo = repo_mod.read_definjected(root, dlcs)

    keyed_missing, keyed_untrans = [], []
    for e in rep.keyed:
        if e.key not in keyed_repo:
            keyed_missing.append(e)
        else:
            val = keyed_repo[e.key].strip()
            if val == "" or val == e.text.strip():
                keyed_untrans.append(e)

    def_missing = [e for e in rep.defs if not _def_translated(e, def_repo)]
    return Gap(rep, keyed_missing, keyed_untrans, def_missing)


def def_by_type(def_missing) -> Counter:
    return Counter(e.deftype for e in def_missing)
