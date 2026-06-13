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
_LEFT = re.compile(r"^(\w+)\s*(?:\((.*)\))?$")


def _parse_left(left: str):
    """Lato sinistro 'sym(p=N,VINCOLI)' -> (nome, peso, [(chiave, valore)]).

    Gestisce i pesi (p=N o N) e i vincoli di uguaglianza (X_gender==Male). I vincoli
    non-uguaglianza (es. length_x[less_than]20) sono ignorati (sempre veri)."""
    m = _LEFT.match(left.strip())
    if not m:
        return left.strip(), 1.0, []
    name, args = m.group(1), m.group(2)
    weight, cons = 1.0, []
    if args:
        for tok in args.split(","):
            tok = tok.strip()
            wm = re.match(r"^(?:p=)?([0-9.]+)$", tok)
            if wm:
                weight = float(wm.group(1))
            elif "==" in tok:
                k, v = tok.split("==", 1)
                cons.append((k.strip(), v.strip()))
    return name, weight, cons

# Nessun campione hardcoded: lo strumento e AGNOSTICO alla lingua. I nomi escono
# nella lingua del repo in cui gira. I simboli forniti dal motore/altri RulePack
# si risolvono cross-pack dentro lo stesso repo; cio che resta -> <simbolo>.


# Simboli RUNTIME comuni del motore (cifre, lettere, numeri romani): l'anteprima li
# genera cosi i nomi numerici (es. "H-72", "Vega III") escono realistici.
_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


def _runtime(sym: str, rng: random.Random) -> str | None:
    if sym == "Digit":
        return rng.choice("0123456789")
    if sym == "Letter":
        return rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    if sym == "RomanNumeral":
        return rng.choice(_ROMAN)
    return None


_game_files_cache: dict | None = None


def _game_def_files(dlcs) -> dict:
    """Mappe simbolo->file dai <rulesFiles> dei Def del GIOCO BASE (non presenti nel
    nostro DefInjected, es. celestial_name->Names/Celestial). Permette all'anteprima
    di risolverle caricando le liste ITALIANE corrispondenti (Strings/Names/...)."""
    global _game_files_cache
    if _game_files_cache is not None:
        return _game_files_cache
    out: dict = {}
    try:
        game = config.game_data()
    except Exception:  # noqa: BLE001 - senza gioco l'anteprima resta com'era
        _game_files_cache = out
        return out
    for dlc in dlcs:
        base = game / dlc / "Defs" / "RulePackDefs"
        if not base.exists():
            continue
        for f in sorted(base.glob("*.xml")):
            try:
                root = etree.parse(str(f)).getroot()
            except (etree.XMLSyntaxError, OSError):
                continue
            for rf in root.iter():
                if not (isinstance(rf.tag, str) and rf.tag.endswith("rulesFiles")):
                    continue
                for li in rf:
                    t = (li.text or "").strip()
                    if "->" not in t:
                        continue
                    sym, path = (x.strip() for x in t.split("->", 1))
                    if path.startswith(("Words/", "Names/")) and sym not in out:
                        out[sym] = (dlc, path)
    _game_files_cache = out
    return out


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
                    sym, w, cons = _parse_left(left)
                    if el.tag.endswith("rulesFiles"):
                        p["files"][sym] = right.strip()
                    else:
                        p["rules"][sym].append((w, cons, right))
    return packs


def _load_words(repo: Path, dlc: str, relpath: str) -> list[str] | None:
    for d in (dlc, "Core"):
        f = repo / d / "Strings" / (relpath + ".txt")
        if f.exists():
            out = []
            for ln in f.read_text(encoding="utf-8").splitlines():
                ln = ln.lstrip("﻿").strip()           # via BOM
                if ln and not ln.startswith(("#", "//")):   # salta i commenti
                    out.append(ln)
            return out
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
    # simboli file-backed definiti SOLO nei Def del gioco base (es. celestial_name)
    for sym, dlc_rel in _game_def_files(config.DLCS).items():
        g_files.setdefault(sym, dlc_rel)
    return g_rules, g_files


def generate(packs: dict, key: str, n: int = 15, repo: Path | None = None,
             root: str | None = None, seed: int | None = None, context: dict | None = None):
    """Genera n nomi dal rulePack indicato. Ritorna (lista, simbolo_radice).

    `context` simula i simboli runtime (combat/social log): es.
    {"RECIPIENT_gender":"Female", "recipient_part0_label":"mano",
     "recipient_part0_definite":"la mano", ...}. Filtra le regole per i vincoli
     (X_gender==Y) e risolve i simboli del contesto."""
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

    ctx = context or {}

    def _ok(cons):
        """Vincoli X==Y soddisfatti dal contesto (X non in contesto -> passa)."""
        return all(ctx.get(k, v) == v for k, v in cons)

    def _weighted(opts):
        """Filtra per vincoli, sceglie pesato; ritorna l'espansione grezza (o None)."""
        opts = [(w, exp) for w, cons, exp in opts if _ok(cons)]
        if not opts:
            return None
        total = sum(w for w, _ in opts)
        r = rng.uniform(0, total)
        acc = 0.0
        for w, exp in opts:
            acc += w
            if r <= acc:
                return exp
        return opts[-1][1]

    def _choose(opts, depth):
        exp = _weighted(opts)
        return "" if exp is None else _SYM.sub(lambda m: expand(m.group(1), depth + 1), exp)

    def expand(sym: str, depth: int = 0) -> str:
        if depth > 30:
            return f"<{sym}>"
        if sym in ctx:                           # 0. contesto simulato (runtime)
            return ctx[sym]
        if sym in rules:                         # 1. pack selezionato
            return _choose(rules[sym], depth)
        wl = words(sym)                          # 2. liste Words/ (rulesFiles)
        if wl:
            return rng.choice(wl)
        if sym in g_rules:                       # 3. fallback cross-pack (es. Global)
            return _choose(g_rules[sym], depth)
        base = sym.split("_")[0]                 # 4. variante di genere/numero -> base
        if base != sym and (base in rules or base in g_rules or base in files or base in g_files):
            return expand(base, depth + 1)
        rt = _runtime(sym, rng)                   # 5. simbolo runtime noto (Digit/Letter/...)
        if rt is not None:
            return rt
        return f"<{sym}>"                        # 6. runtime non risolvibile (pawn names)

    root = root or _pick_root(rules)
    root_opts = rules.get(root) or g_rules.get(root) or []
    out = []
    for _ in range(n):
        tmpl = (_weighted(root_opts) or root) if root_opts else root
        s = _SYM.sub(lambda m: expand(m.group(1), 1), tmpl)
        s = re.sub(r"\s+", " ", s).strip()
        if s:
            s = s[0].upper() + s[1:]
        out.append((s, tmpl.strip()))           # (nome risolto, template d'origine)
    return out, root
