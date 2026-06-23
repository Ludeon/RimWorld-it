"""Pulizia guidata di voci morte dal TranslationReport.

Due categorie dal report:
  1. "Unnecessary keyed translations (will never be used)" — chiavi keyed presenti
     nell'IT che il gioco non usa piu'. RIMOVIBILI in sicurezza SOLO se la chiave e'
     anche ASSENTE dai Keyed inglesi del gioco (altrimenti e' un falso positivo: la
     chiave esiste, va tenuta). Questo incrocio elimina il rischio segnalato nel piano
     ("alcune sono in realta' referenziate").
  2. "Def-injected translations load errors" — iniezioni fallite (def rinominati/spostati,
     handle di parti del corpo rimossi, comp spostati). Solo DIAGNOSI + posizione nel
     repo: la rimappatura e' una scelta umana, niente cancellazioni automatiche.

Tutto offline. La rimozione keyed (--apply) e' chirurgia testuale riga-per-riga
(niente riscrittura XML che riformatterebbe il file); git resta la rete di sicurezza.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lxml import etree

import config
import report as report_mod


# ---------------------------------------------------------------- indici repo/gioco

def english_keys(dlcs, game_data: Path) -> set[str]:
    """Tutte le chiavi keyed inglesi del gioco, su tutte le DLC indicate."""
    keys: set[str] = set()
    for dlc in dlcs:
        base = game_data / dlc / "Languages" / "English" / "Keyed"
        if not base.exists():
            continue
        for f in sorted(base.rglob("*.xml")):
            try:
                root = etree.parse(str(f)).getroot()
            except (etree.XMLSyntaxError, OSError):
                continue
            for el in root:
                if isinstance(el.tag, str):
                    keys.add(el.tag)
    return keys


def repo_keyed_index(dlcs) -> dict[str, list[tuple[str, Path, int]]]:
    """key -> [(dlc, path, sourceline), ...] dai Keyed del repo."""
    root = config.repo_root()
    idx: dict[str, list[tuple[str, Path, int]]] = {}
    for dlc in dlcs:
        base = root / dlc / "Keyed"
        if not base.exists():
            continue
        for f in sorted(base.rglob("*.xml")):
            try:
                tree = etree.parse(str(f))
            except (etree.XMLSyntaxError, OSError):
                continue
            for el in tree.getroot():
                if isinstance(el.tag, str):
                    idx.setdefault(el.tag, []).append((dlc, f, el.sourceline))
    return idx


def repo_definjected_index(dlcs) -> dict[tuple[str, str], tuple[str, Path, int]]:
    """(deftype, tagpath) -> (dlc, path, sourceline) dai DefInjected del repo."""
    root = config.repo_root()
    idx: dict[tuple[str, str], tuple[str, Path, int]] = {}
    for dlc in dlcs:
        di = root / dlc / "DefInjected"
        if not di.exists():
            continue
        for typedir in sorted(p for p in di.iterdir() if p.is_dir()):
            for f in sorted(typedir.rglob("*.xml")):
                try:
                    tree = etree.parse(str(f))
                except (etree.XMLSyntaxError, OSError):
                    continue
                for el in tree.getroot():
                    if isinstance(el.tag, str):
                        idx.setdefault((typedir.name, el.tag), (dlc, f, el.sourceline))
    return idx


# ---------------------------------------------------------------- analisi keyed

@dataclass
class KeyedRow:
    key: str
    verdict: str          # "orfana" | "in-EN" | "assente"
    dlc: str | None
    rel: str | None       # path relativo al repo, o None
    line: int | None
    text: str


def scan_keyed(rep: report_mod.Report, dlcs, game_data: Path) -> list[KeyedRow]:
    en = english_keys(dlcs, game_data)
    idx = repo_keyed_index(dlcs)
    root = config.repo_root()
    rows: list[KeyedRow] = []
    for u in rep.unused_keyed:
        locs = idx.get(u.key) or []
        # disambigua per basename del file (il report da' solo il basename)
        loc = None
        if locs:
            same = [l for l in locs if l[1].name == u.file]
            loc = (same or locs)[0]
        if loc is None:
            rows.append(KeyedRow(u.key, "assente", None, None, None, u.text))
            continue
        dlc, path, line = loc
        rel = str(path.relative_to(root)).replace("\\", "/")
        verdict = "in-EN" if u.key in en else "orfana"
        rows.append(KeyedRow(u.key, verdict, dlc, rel, line, u.text))
    return rows


# ---------------------------------------------------------------- analisi load-error

@dataclass
class LoadRow:
    kind: str             # "comp" | "bodypart" | "def-rinominato" | "handle"
    detail: str           # spiegazione breve
    inject_path: str
    deftype: str
    src_file: str         # file Defs di origine
    dlc: str | None       # dove sta la voce IT nel repo
    rel: str | None
    line: int | None


def _classify(e: report_mod.LoadError) -> tuple[str, str]:
    if e.kind == "nodef":
        return "def-rinominato", f"nessun {e.target} chiamato '{e.reason}' (def rinominato/rimosso)"
    handle = e.reason.split("handle named ", 1)[-1].rstrip(".") if "handle named" in e.reason else ""
    if handle.startswith(("CompReloadable", "CompStatEntry", "Comp")):
        return "comp", f"comp spostato/rinominato: handle '{handle}' assente"
    if "sensor" in handle or "_sight" in handle or "_hearing" in handle:
        return "bodypart", f"parte del corpo rimossa: handle '{handle}' assente"
    return "handle", e.reason


def _short_deftype(t: str) -> str:
    return t.rsplit(".", 1)[-1]  # "Verse.ThingDef" -> "ThingDef"


def scan_load_errors(rep: report_mod.Report, dlcs) -> list[LoadRow]:
    di_idx = repo_definjected_index(dlcs)
    root = config.repo_root()
    rows: list[LoadRow] = []
    for e in rep.load_errors:
        kind, detail = _classify(e)
        deftype = _short_deftype(e.target)
        loc = di_idx.get((deftype, e.path))
        dlc = rel = line = None
        if loc:
            dlc, path, ln = loc
            rel = str(path.relative_to(root)).replace("\\", "/")
            line = ln
        rows.append(LoadRow(kind, detail, e.path, deftype, e.file, dlc, rel, line))
    return rows


# ---------------------------------------------------------------- rimozione keyed

# commenti che "appartengono" alla voce sottostante e vanno rimossi con essa
def _is_owned_comment(stripped: str) -> bool:
    return stripped.startswith("<!--") and stripped.endswith("-->") and (
        stripped.startswith("<!-- EN:") or "UNUSED" in stripped.upper()
    )


def _remove_located(items: list[tuple[str, int, str]]) -> tuple[int, list[str]]:
    """Rimuove voci single-line `<tag>...</tag>` (+ commento EN/UNUSED adiacente).

    items = [(rel, line, tag), ...]. Ritorna (n_rimosse, avvisi). Salta in
    sicurezza le voci multi-riga o non confermate alla riga attesa.
    """
    root = config.repo_root()
    by_file: dict[Path, list[tuple[int, str]]] = {}
    for rel, line, tag in items:
        if rel and line:
            by_file.setdefault(root / rel, []).append((line, tag))

    removed = 0
    warnings: list[str] = []
    for path, rows in by_file.items():
        rel = str(path.relative_to(root)).replace("\\", "/")
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        drop: set[int] = set()  # indici 0-based da eliminare
        for line, tag in rows:
            i = line - 1  # sourceline e' 1-based
            if not (0 <= i < len(lines)):
                warnings.append(f"{rel}:{line} fuori range, salto {tag}")
                continue
            ln = lines[i]
            if f"<{tag}>" not in ln:
                warnings.append(f"{rel}:{line} tag {tag} non alla riga attesa, salto")
                continue
            if f"</{tag}>" not in ln:
                warnings.append(f"{rel}:{line} {tag} e' multi-riga: rimozione manuale")
                continue
            drop.add(i)
            j = i - 1  # commento posseduto immediatamente sopra
            if j >= 0 and _is_owned_comment(lines[j].strip()):
                drop.add(j)
        if not drop:
            continue
        new = [l for k, l in enumerate(lines) if k not in drop]
        path.write_text("".join(new), encoding="utf-8")
        removed += sum(1 for line, _ in rows if (line - 1) in drop)
    return removed, warnings


def apply_keyed(orphans: list[KeyedRow]) -> tuple[int, list[str]]:
    """Rimuove le voci keyed orfane (e l'eventuale commento EN/UNUSED adiacente)."""
    return _remove_located([(r.rel, r.line, r.key) for r in orphans if r.rel and r.line])


def apply_defs(rows: list[LoadRow]) -> tuple[int, list[str]]:
    """Rimuove le voci DefInjected dei load-error localizzate nel repo.

    Sicuro per costruzione: una voce che il gioco NON riesce a iniettare e' inerte;
    rimuoverla non cambia il comportamento. git + report restano la rete di sicurezza.
    """
    return _remove_located([(r.rel, r.line, r.inject_path) for r in rows if r.rel and r.line])
