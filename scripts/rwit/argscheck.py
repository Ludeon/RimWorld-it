"""Controllo dei segnaposto di formato {...} fra traduzione IT e fonte EN,
con conferma incrociata sulle traduzioni ufficiali (fr/de/es).

Bug tipico: una vecchia versione del gioco usava una format-string con {0} che
ora non e' piu' tale (il motore compone da solo "etichetta: valore"). La
traduzione ha conservato il {0}, che quindi appare letterale a schermo
(es. "Causato dal passato: {0}: Topo di biblioteca").

Confronta, per ogni stringa tradotta, l'insieme dei segnaposto presenti nell'IT
con quelli del commento <!-- EN: -->:
  - posizionali  {0} {1} {0_gender} ...  -> indice numerico
  - nominali     {PAWN_label} {VAR} ...  (senza spazi: i ternari di genere
    {X_gender ? o : a} sono esclusi perche' il loro contenuto cambia in IT)
  - radici flesse  {ROOT_gender ? ..}, [ROOT_pronoun] -> radice nominale

PERCHE' SERVE L'INCROCIO CON LE ALTRE LINGUE
--------------------------------------------
Ne' il commento EN ne' il Def canonico elencano *tutti* gli argomenti che il
motore fornisce: la stringa EN spesso ne usa un sottoinsieme. Esempio reale:
"my half-sibling {0} died" mostra solo {0}, ma il motore passa anche {1} (il
pawn defunto, con genere) -> {1_gender} e' lecito anche se "in piu'" rispetto
all'EN. All'opposto, {3} sulle malattie NON e' fornito dal motore e rompe il
resolver ("Could not resolve symbol 3").

Un confronto puramente IT-vs-EN non distingue i due casi (entrambi "+pos in
piu'"). La discriminante affidabile sono le traduzioni ufficiali ben mantenute
(fr/de/es, cloni fratelli del repo - vedi docs/REFERENCES.md): se nessuna usa
quel segnaposto -> bug molto probabile; se piu' lingue lo usano -> arg valido.

Offline, deterministico. Non tocca i file.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

import config
import ledger

_NUM = re.compile(r"\{(\d+)")              # {0}, {12}, {0_gender}, {1_label}
_NAMED = re.compile(r"\{([A-Za-z_]\w*)\}")  # {VAR}, {PAWN_label} (niente spazi -> no ternari)

# Famiglia pronome/genere: la traduzione la rende lecitamente con 'il proprio/suo',
# riformula o usa un ternario -> NON contarla come buco (sarebbe quasi tutto rumore).
_PRONOUN = re.compile(r"_(pronoun|possessive|objective|gender|reflexive)$", re.I)

# Radice flessa per genere/pronome dentro {..} o [..]: {animalKindDef_gender ? ..},
# [asker_pronoun]. Cattura la sola radice nominale (le posizionali tipo {1_gender}
# restano ai numeri perche' la radice qui deve iniziare con lettera/underscore).
_GSYM = re.compile(r"[\{\[]\s*([A-Za-z_]\w*?)_(?:pronoun|possessive|objective|gender|reflexive)\b")

# Lingue ufficiali di riferimento: cloni fratelli del repo (docs/REFERENCES.md).
_REF_LANGS = (("fr", "RimWorld-fr"), ("de", "RimWorld-de"), ("es", "RimWorld-Spanish"))


def _nums(s: str) -> set[str]:
    return set(_NUM.findall(s or ""))


def _named(s: str) -> set[str]:
    """Variabili nominali {NOME} di contenuto (esclusa la famiglia pronome/genere)."""
    return {v for v in _NAMED.findall(s or "") if not _PRONOUN.search(v)}


def _groots(s: str) -> set[str]:
    """Radici flesse per genere/pronome (es. 'animalKindDef' da {animalKindDef_gender ? ..})."""
    return set(_GSYM.findall(s or ""))


# --- conferma incrociata con le lingue ufficiali ---------------------------

def ref_roots() -> list[tuple[str, Path]]:
    """(codice_lingua, percorso_clone) per i cloni di riferimento presenti."""
    parent = config.repo_root().parent
    return [(code, parent / name) for code, name in _REF_LANGS if (parent / name).exists()]


_ref_cache: dict[tuple[str, str], dict[str, str]] = {}


def _ref_tags(root: Path, relfile: str) -> dict[str, str]:
    """{tag: testo} di un file in una lingua di riferimento (l'intero contenuto
    testuale dell'elemento, li compresi). Cache per (lingua, file)."""
    key = (str(root), relfile)
    cached = _ref_cache.get(key)
    if cached is not None:
        return cached
    out: dict[str, str] = {}
    try:
        xml = etree.parse(str(root / relfile)).getroot()
        for el in xml:
            if isinstance(el.tag, str):
                out[el.tag] = " ".join(el.itertext())
    except (etree.XMLSyntaxError, OSError):
        pass
    _ref_cache[key] = out
    return out


# Una radice il cui nome finisce in "Def" e' per convenzione RimWorld un
# riferimento a un Def (animalKindDef, weaponDef, ...): non ha MAI genere nel
# resolver. Se l'IT le applica _gender/_pronoun e' il bug "Could not resolve
# symbol xDef_gender" (a differenza di Cose/Pawn, dove il genere c'e' davvero,
# quindi qui NON serve l'incrocio con le altre lingue: e' un segnale strutturale).
def _def_roots(roots: set[str]) -> list[str]:
    return sorted(r for r in roots if r.endswith("Def"))


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
    # conferma incrociata (solo per le categorie "in piu'", popolata da scan):
    num_sup: dict[str, list[str]] = field(default_factory=dict)    # indice -> [lingue che lo usano]
    suffix_sus: list[str] = field(default_factory=list)  # radici "...Def" (senza genere) flesse dall'IT
    ref_judged: bool = False  # almeno una lingua di riferimento aveva il tag

    @property
    def kind(self) -> str:
        # Le posizionali "in piu'" non confermate da nessuna lingua sono il caso
        # piu' pericoloso (rompono il resolver). Se invece >=1 lingua le usa,
        # sono quasi certamente argomenti validi che l'EN non mostra.
        if self.extra_num:
            if self.ref_judged and any(not self.num_sup.get(i) for i in self.extra_num):
                return "extra-pos-bug"
            if self.ref_judged:
                return "extra-pos-ok"
            return "extra-pos"
        if self.suffix_sus:
            return "extra-suffix"
        if self.miss_num:
            return "manca-pos"
        if self.extra_var:
            return "extra-var"
        return "manca-var"


def scan(dlcs=None) -> list[Hit]:
    repo = config.repo_root()
    dlcs = dlcs or config.DLCS
    refs = ref_roots()
    hits: list[Hit] = []
    for dlc, relfile, tag, line, it, en in ledger.iter_strings(repo, dlcs):
        if not it or not en or it == en:
            continue  # serve sia IT sia EN, e dev'essere effettivamente tradotta
        en_n, it_n = _nums(en), _nums(it)
        en_v, it_v = _named(en), _named(it)
        en_g, it_g = _groots(en), _groots(it)
        extra_num, miss_num = it_n - en_n, en_n - it_n
        extra_var, miss_var = it_v - en_v, en_v - it_v
        extra_g = it_g - en_g  # radici che SOLO l'IT flette per genere/pronome
        base = bool(extra_num or miss_num or extra_var or miss_var)
        if not (base or extra_g):
            continue

        # Sospetti suffisso: radici "...Def" che l'IT flette per genere/pronome
        # -> Def senza genere (es. {animalKindDef_gender ...}). Segnale strutturale,
        # non serve l'incrocio (le Cose/Pawn hanno genere e non finiscono in Def).
        suffix_sus = _def_roots(extra_g)

        # extra_g su radici non-Def (Cose/Pawn, genere lecito) non e' un caso da
        # segnalare: evita di creare hit fantasma che cadrebbero nel fallback.
        if not (base or suffix_sus):
            continue

        # Conferma incrociata per i posizionali in piu' (per-tag).
        num_sup: dict[str, list[str]] = {}
        ref_judged = False
        if extra_num and refs:
            ref_texts = [(c, rt) for c, root in refs
                         if (rt := _ref_tags(root, relfile).get(tag)) is not None]
            ref_judged = bool(ref_texts)
            for idx in extra_num:
                num_sup[idx] = [c for c, t in ref_texts if idx in _nums(t)]

        hits.append(Hit(dlc, relfile, tag, line,
                        sorted(extra_num, key=int), sorted(miss_num, key=int),
                        sorted(extra_var), sorted(miss_var), en, it,
                        num_sup=num_sup, suffix_sus=suffix_sus, ref_judged=ref_judged))
    return hits
