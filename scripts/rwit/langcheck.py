"""Rilevamento 'lingua sbagliata' nelle traduzioni (deterministico, offline).

Due livelli complementari, nessun token LLM:

  Tier A - match esatto cross-repo: le stringhe in lingua sbagliata sono quasi
    sempre COPIATE da un repo gemello (es. RimWorld-fr). Se un nostro valore
    coincide *identico* con un valore francese/spagnolo/tedesco -> copia non
    tradotta. Zero falsi positivi sulle frasi (una frase FR non compare per caso
    come testo IT).

  Tier B - language-ID statistico con `lingua`: prende il residuo che A non vede
    (parole singole, testo leggermente modificato). Conservativo: soglia di
    confidenza + lunghezza minima, whitelist di simboli/varianti.

Output: report gitignored in reports/langcheck_<data>.txt con file:riga, chiave,
lingua rilevata e (se presente) il commento EN adiacente -> si rivede solo la
shortlist, non i file interi.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from lxml import etree

import config

# Repo gemelli (cartelle sorelle) per lingua.
SIBLINGS = {"fr": "RimWorld-fr", "es": "RimWorld-Spanish", "de": "RimWorld-de"}

# Token da rimuovere prima del confronto/detezione: variabili {..} e [..],
# sequenze di a-capo letterali, e i pesi (p=N) delle rulesStrings.
_VAR = re.compile(r"\{[^}]*\}|\[[^\]]*\]|\\n|\(p=[0-9.]+\)")

# Policy per-lingua: (min lettere, margine minimo sull'italiano, sconto se copiata).
# Il francese e lessicalmente distinto dall'italiano -> affidabile anche su frasi
# brevi. Spagnolo/tedesco sono vicini (o ingannati da prestiti inglesi tipo
# 'mechtech') -> servono frasi piu lunghe e margine piu alto per evitare falsi
# positivi su italiano corretto.
_POLICY = {
    "fr": (12, 0.30, 0.12),
    "es": (18, 0.42, 0.10),
    "de": (18, 0.42, 0.10),
    "en": (12, 0.50, 0.10),
}


def _letters(s: str) -> str:
    """Solo lettere (per misurare quanta lingua naturale c'e davvero)."""
    return re.sub(r"[^A-Za-zÀ-ɏ]", "", s)


def _clean(text: str) -> str:
    """Testo ripulito da variabili/markup, pronto per confronto e language-ID.

    Per le rulesStrings ('simbolo->valore') tiene solo il valore (dopo l'ultima
    freccia), perche il lato sinistro e un simbolo tecnico, non lingua."""
    t = text.strip()
    if "->" in t:
        t = t.rsplit("->", 1)[1]  # solo il valore tradotto
    t = _VAR.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


def _iter_leaves(repo: Path, dlc: str):
    """Genera (file, sourceline, tag, testo_grezzo) per ogni nodo con testo utile,
    sotto Keyed/ e DefInjected/ della DLC indicata."""
    for sub in ("Keyed", "DefInjected"):
        base = repo / dlc / sub
        if not base.exists():
            continue
        for f in sorted(base.rglob("*.xml")):
            try:
                root = etree.parse(str(f)).getroot()
            except (etree.XMLSyntaxError, OSError):
                continue
            for el in root.iter():
                if not isinstance(el.tag, str):  # salta commenti / PI
                    continue
                txt = (el.text or "").strip()
                if not txt:
                    continue
                prev = el.getprevious()
                en = ""
                if prev is not None and not isinstance(prev.tag, str) and prev.text:
                    m = re.match(r"\s*EN:\s*(.*)", prev.text, re.S)
                    en = (m.group(1) if m else prev.text).strip()
                yield f, el.sourceline, el.tag, txt, en


def _sibling_corpus(lang_folder: str) -> dict[str, set[str]]:
    """Per ogni DLC, l'insieme dei testi-foglia ripuliti del repo gemello.
    Chiave = DLC; valore = set di stringhe pulite (per il match esatto Tier A)."""
    root = config.repo_root().parent / lang_folder
    out: dict[str, set[str]] = defaultdict(set)
    if not root.exists():
        return out
    for dlc in config.DLCS:
        for _f, _ln, _tag, txt, _en in _iter_leaves(root, dlc):
            c = _clean(txt)
            if len(_letters(c)) >= 2:
                out[dlc].add(c)
    return out


def _build_detector(langs):
    from lingua import Language, LanguageDetectorBuilder

    name = {
        "it": Language.ITALIAN, "fr": Language.FRENCH, "es": Language.SPANISH,
        "de": Language.GERMAN, "en": Language.ENGLISH, "pt": Language.PORTUGUESE,
        "la": Language.LATIN,
    }
    chosen = [name[l] for l in langs]
    return LanguageDetectorBuilder.from_languages(*chosen).build(), name


class Hit:
    __slots__ = ("file", "line", "tag", "text", "verdict", "detail", "en")

    def __init__(self, file, line, tag, text, verdict, detail, en=""):
        self.file = file
        self.line = line
        self.tag = tag
        self.text = text
        self.verdict = verdict  # es. 'lingua=fr'
        self.detail = detail
        self.en = en  # commento EN adiacente (fonte per la ritraduzione)


def scan(dlcs=None, min_conf=0.55, min_letters=5):
    """`lingua` fa da gate (lingua != it), il match cross-repo fa da conferma.

    Cosi i token condivisi (nomi propri, sigle, simboli) identici tra piu lingue
    NON vengono segnalati: lo sono solo le stringhe che il language-ID riconosce
    come straniere. Il match col gemello fr/es/de alza la confidenza a quasi-certa.
    """
    repo = config.repo_root()
    dlcs = dlcs or config.DLCS

    # Tier A (conferma): corpora gemelli.
    corp = {lang: _sibling_corpus(folder) for lang, folder in SIBLINGS.items()}

    # Tier B (gate): detector lingua. Niente latino/portoghese: non sono lingue
    # attese e generano misclassificazioni sui nomi pseudo-latini del gioco.
    detector, _ = _build_detector(["it", "fr", "es", "de", "en"])
    from lingua import Language
    IT = Language.ITALIAN

    hits: list[Hit] = []
    for dlc in dlcs:
        for f, line, tag, txt, en in _iter_leaves(repo, dlc):
            cleaned = _clean(txt)
            letters = _letters(cleaned)
            # Serve prosa (spazio); i path-simbolo (con '/') si scartano.
            if " " not in cleaned or "/" in cleaned:
                continue

            conf_vals = detector.compute_language_confidence_values(cleaned)
            top = conf_vals[0]
            iso = top.language.iso_code_639_1.name.lower()
            if top.language == IT or iso not in _POLICY:
                continue  # italiano in testa (o lingua non gestita) -> ok
            it_conf = next((c.value for c in conf_vals if c.language == IT), 0.0)
            margin = top.value - it_conf  # quanto la lingua straniera batte l'italiano

            # Conferma cross-repo: identico al gemello di QUELLA lingua (copia verbatim)?
            copied = [l for l in SIBLINGS if cleaned in corp[l].get(dlc, ())]
            corrob = iso in copied

            # Decisione per-lingua: lunghezza minima + margine sull'italiano sempre
            # richiesti (le frasi straniere vere staccano netto). La copia verbatim
            # dal gemello sconta il margine.
            min_let, need, disc = _POLICY[iso]
            if len(letters) < min_let:
                continue
            if margin < (need - disc if corrob else need):
                continue

            detail = f"m={margin:.2f}"
            if copied:
                detail += " =" + "/".join(copied)
            hits.append(Hit(str(f.relative_to(repo)), line, tag, txt,
                            f"lingua={iso}", detail, en))
    return hits
