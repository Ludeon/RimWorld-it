"""Mini-motore di generazione nomi (anteprima delle RulePackDef in Python).

Simula in modo APPROSSIMATO il motore Grammar di RimWorld: parsa le rulesStrings
di un rulePack, espande i [simboli] ricorsivamente con i pesi (p=N), e carica le
liste di parole dei rulesFiles (Strings/Words/...). Serve a vedere che nomi
verrebbero generati (fazioni, mappa, gravship) senza aprire il gioco.

NON e fedele al 100% (il motore vero fa genere/elisione/maiuscole via
LanguageWorker e attinge ad altri RulePack a runtime): i simboli non risolvibili
sono mostrati come <simbolo>. Ma basta a scovare vocabolario brutto, articoli
sbagliati e leak di lingua.
"""
from __future__ import annotations

import random
import re
from collections import defaultdict
from pathlib import Path

from lxml import etree

import config

_SYM = re.compile(r"\[([^\]]+)\]")
_WEIGHT = re.compile(r"^(\w+)\s*\((?:p=)?([0-9.]+)\)$")

# Nessun campione hardcoded: lo strumento e AGNOSTICO alla lingua. I nomi escono
# nella lingua del repo in cui gira. I simboli forniti dal motore/altri RulePack
# si risolvono cross-pack dentro lo stesso repo; cio che resta -> <simbolo>.


def _pack_root(tag: str) -> str | None:
    if ".rulePack." not in tag:
        return None
    return tag.rsplit(".rulePack.", 1)[0]


def load_rulepacks(repo: Path | None = None, dlcs=None) -> dict[str, dict]:
    """Carica tutti i rulePack del DefInjected. Chiave leggibile -> struttura."""
    repo = repo or config.repo_root()
    dlcs = dlcs or config.DLCS
    packs: dict[str, dict] = {}
    for dlc in dlcs:
        base = repo / dlc / "DefInjected" / "RulePackDef"
        if not base.exists():
            continue
        for f in sorted(base.glob("*.xml")):
            try:
                root = etree.parse(str(f)).getroot()
            except (etree.XMLSyntaxError, OSError):
                continue
            for el in root:
                if not isinstance(el.tag, str):
                    continue
                name = _pack_root(el.tag)
                if name is None or not (el.tag.endswith("rulesStrings")
                                        or el.tag.endswith("rulesFiles")):
                    continue
                key = f"{dlc} · {f.stem} · {name}"
                p = packs.setdefault(key, {"rules": defaultdict(list), "files": {},
                                           "dlc": dlc, "file": str(f.relative_to(repo))})
                for li in el:
                    if not isinstance(li.tag, str):
                        continue
                    txt = (li.text or "").strip()
                    if "->" not in txt:
                        continue
                    left, right = txt.split("->", 1)
                    m = _WEIGHT.match(left.strip())
                    sym, w = (m.group(1), float(m.group(2))) if m else (left.strip(), 1.0)
                    if el.tag.endswith("rulesFiles"):
                        p["files"][sym] = right.strip()
                    else:
                        p["rules"][sym].append((w, right))
    return packs


def _load_words(repo: Path, dlc: str, relpath: str) -> list[str] | None:
    for d in (dlc, "Core"):
        f = repo / d / "Strings" / (relpath + ".txt")
        if f.exists():
            return [ln.strip() for ln in f.read_text(encoding="utf-8").splitlines()
                    if ln.strip() and not ln.lstrip().startswith("#")]
    return None


def _pick_root(rules: dict) -> str:
    for cand in ("r_name", "r_root", "name", "r_logentry"):
        if cand in rules:
            return cand
    return next(iter(rules)) if rules else ""


def _global_tables(packs: dict):
    """Unione dei simboli di TUTTI i rulePack del repo: fallback per i simboli
    condivisi (es. quelli di RulePacks_Global: [ConceptAny], [Character]...).
    Cosi i nomi restano nella lingua del repo, senza campioni hardcoded."""
    g_rules: dict[str, list] = defaultdict(list)
    g_files: dict[str, tuple] = {}
    for p in packs.values():
        for sym, opts in p["rules"].items():
            g_rules[sym].extend(opts)
        for sym, rel in p["files"].items():
            g_files.setdefault(sym, (p["dlc"], rel))
    return g_rules, g_files


def generate(packs: dict, key: str, n: int = 15, repo: Path | None = None,
             root: str | None = None, seed: int | None = None):
    """Genera n nomi dal rulePack indicato. Ritorna (lista, simbolo_radice)."""
    repo = repo or config.repo_root()
    pack = packs[key]
    rules, files = pack["rules"], pack["files"]
    g_rules, g_files = _global_tables(packs)
    rng = random.Random(seed)
    wcache: dict[str, list | None] = {}

    def words(sym: str):
        if sym not in wcache:
            if sym in files:
                wcache[sym] = _load_words(repo, pack["dlc"], files[sym])
            elif sym in g_files:
                dlc, rel = g_files[sym]
                wcache[sym] = _load_words(repo, dlc, rel)
            else:
                wcache[sym] = None
        return wcache[sym]

    def _choose(opts, depth):
        total = sum(w for w, _ in opts)
        r = rng.uniform(0, total)
        acc = 0.0
        chosen = opts[-1][1]
        for w, exp in opts:
            acc += w
            if r <= acc:
                chosen = exp
                break
        return _SYM.sub(lambda m: expand(m.group(1), depth + 1), chosen)

    def expand(sym: str, depth: int = 0) -> str:
        if depth > 30:
            return f"<{sym}>"
        if sym in rules:                       # 1. pack selezionato
            return _choose(rules[sym], depth)
        wl = words(sym)                          # 2. liste Words/ (rulesFiles)
        if wl:
            return rng.choice(wl)
        if sym in g_rules:                       # 3. fallback cross-pack (es. Global)
            return _choose(g_rules[sym], depth)
        base = sym.split("_")[0]                 # 4. variante di genere/numero -> base
        if base != sym and (base in rules or base in g_rules or base in files or base in g_files):
            return expand(base, depth + 1)
        return f"<{sym}>"                        # 5. simbolo di runtime: non risolvibile

    root = root or _pick_root(rules)
    out = []
    for _ in range(n):
        s = re.sub(r"\s+", " ", expand(root)).strip()
        if s:
            s = s[0].upper() + s[1:]
        out.append(s)
    return out, root
