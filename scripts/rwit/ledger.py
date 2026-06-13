"""Registro versionato delle traduzioni (stile gettext 'fuzzy'), tracciato in git.

Scopo: dare a sviluppatori e tool/LLM esterni una fonte unica per sapere QUALI
stringhe tradurre, e tracciare nel tempo quali traduzioni cambiano.

Il ledger e un CSV deterministico (ordinato) in scripts/dashboard/ -> diff git
leggibili, merge gestibili, apribile in Excel. NON e l'autorita delle traduzioni
(quella resta l'XML): memorizza
solo cio che git da solo non sa, cioe lo STATO e gli HASH di riferimento:

  - en_sha: hash della fonte inglese (il commento <!-- EN: -->). Se cambia a monte
    (es. dopo 'Pulisci lingue'), la stringa diventa `stale` -> da ritradurre.
  - it_sha: hash dell'italiano al momento della validazione. Se l'italiano cambia
    dopo la validazione, la stringa diventa `modified` -> da rivalidare.

Stati: untranslated | translated | validated | keep | stale | modified.
('keep' = volutamente non tradotto: prestiti, nomi propri, sigle, format-string.)

Comandi:
  rwit ledger build      (ri)costruisce/fonde il CSV, preservando le validazioni
  rwit ledger stats      conteggi per stato e per DLC
  rwit ledger validate   promuove a 'validated' (fissa la baseline degli hash)
  rwit ledger todo       esporta la worklist per LLM/tool esterno (solo da fare)
"""
from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

from lxml import etree

import config

LEDGER = config.repo_root() / "scripts" / "dashboard" / "translation-ledger.csv"
FIELDS = ["dlc", "file", "tag", "status", "lang_flag", "en_sha", "it_sha"]

_EN = re.compile(r"\s*EN:\s*(.*)", re.S)


def _sha(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12] if text else ""


_LI = re.compile(r"<li>(.*?)</li>", re.S)


def _value_side(s: str) -> str:
    """Lato destro di 'simbolo->valore' (la lingua vera); intero se non c'e '->'."""
    s = s.strip()
    return s.rsplit("->", 1)[1].strip() if "->" in s else s


def _li_values_from_text(raw: str) -> str:
    """Valori (lato destro) di ogni <li> in una stringa grezza (es. commento EN)."""
    return "\n".join(_value_side(m) for m in _LI.findall(raw or "")).strip()


def _li_values_from_children(el) -> str:
    """Valori (lato destro) di ogni <li> discendente di un elemento.

    Copre sia i rulesStrings (li figli diretti) sia gli slateRef, che annidano
    i <li> sotto un <rulesStrings> interno (quindi li-nipoti)."""
    return "\n".join(_value_side(c.text or "") for c in el.iter("li")).strip()


def iter_strings(repo: Path, dlcs):
    """(dlc, relfile, tag, line, it_text, en_text) per Keyed e DefInjected."""
    for dlc in dlcs:
        for sub in ("Keyed", "DefInjected"):
            base = repo / dlc / sub
            if not base.exists():
                continue
            for f in sorted(base.rglob("*.xml")):
                try:
                    root = etree.parse(str(f)).getroot()
                except (etree.XMLSyntaxError, OSError):
                    continue
                for el in root:
                    if not isinstance(el.tag, str):
                        continue
                    prev = el.getprevious()
                    comment = (prev.text if prev is not None
                               and not isinstance(prev.tag, str) and prev.text else "")
                    has_li = next(el.iter("li"), None) is not None
                    if has_li:
                        # rulesStrings & liste: il testo IT sta nei figli <li>, non in
                        # el.text. Confronta solo il lato-valore (dopo '->') con l'EN
                        # elencato nel commento, altrimenti tutto risulterebbe vuoto.
                        it = _li_values_from_children(el)
                        en = _li_values_from_text(comment)
                    else:
                        it = (el.text or "").strip()
                        m = _EN.match(comment) if comment else None
                        en = (m.group(1) if m else comment).strip()
                    yield dlc, str(f.relative_to(repo)), el.tag, el.sourceline, it, en


def texts_for_file(relfile: str) -> dict:
    """{tag: (it, en)} per un singolo file, testi live dall'XML (li-aware)."""
    path = config.repo_root() / relfile
    out: dict[str, tuple[str, str]] = {}
    try:
        root = etree.parse(str(path)).getroot()
    except (etree.XMLSyntaxError, OSError):
        return out
    for el in root:
        if not isinstance(el.tag, str):
            continue
        prev = el.getprevious()
        comment = (prev.text if prev is not None
                   and not isinstance(prev.tag, str) and prev.text else "")
        if next(el.iter("li"), None) is not None:
            it, en = _li_values_from_children(el), _li_values_from_text(comment)
        else:
            it = (el.text or "").strip()
            m = _EN.match(comment) if comment else None
            en = (m.group(1) if m else comment).strip()
        out[el.tag] = (it, en)
    return out


def _base_status(it: str, en: str) -> str:
    """Stato iniziale euristico: senza intervento umano.

    Untranslated = c'e una fonte inglese ma l'italiano manca o la ricopia. Se anche
    l'inglese e vuoto (es. <li>questDescription-></li>, valore-vuoto rispecchiato)
    non c'e nulla da tradurre."""
    if (not it and en) or (en and it == en):
        return "untranslated"
    return "translated"


def load() -> dict[tuple, dict]:
    if not LEDGER.exists():
        return {}
    out = {}
    with LEDGER.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            out[(row["dlc"], row["file"], row["tag"])] = row
    return out


def build(dlcs=None, lang_flags: dict | None = None) -> dict:
    """Fonde lo stato corrente del repo col ledger esistente. Ritorna i conteggi."""
    repo = config.repo_root()
    dlcs = dlcs or config.DLCS
    lang_flags = lang_flags or {}
    old = load()
    rows = []
    counts: dict[str, int] = {}

    for dlc, relf, tag, _line, it, en in iter_strings(repo, dlcs):
        key = (dlc, relf, tag)
        en_sha, it_sha = _sha(en), _sha(it)
        base = _base_status(it, en)
        prev = old.get(key)

        if prev is None:
            status = base
        elif prev["status"] == "validated":
            if prev["en_sha"] != en_sha:
                status = "stale"      # inglese cambiato a monte
            elif prev["it_sha"] != it_sha:
                status = "modified"   # italiano cambiato dopo la validazione
            else:
                status = "validated"
        elif prev["status"] == "keep":
            # 'keep' = volutamente non tradotto (prestito, nome proprio, sigla...).
            # Sticky finche l'inglese non cambia; se cambia a monte torna in
            # revisione (stale). Se qualcuno la traduce davvero (it != en) -> translated.
            if prev["en_sha"] != en_sha:
                status = "stale"
            elif base == "translated":
                status = "translated"
            else:
                status = "keep"
        elif prev["status"] in ("stale", "modified"):
            status = "untranslated" if base == "untranslated" else prev["status"]
        else:
            status = base

        flag = lang_flags.get(key, prev["lang_flag"] if prev else "")
        rows.append({"dlc": dlc, "file": relf, "tag": tag, "status": status,
                     "lang_flag": flag, "en_sha": en_sha, "it_sha": it_sha})
        counts[status] = counts.get(status, 0) + 1

    # Conserva eventuali DLC non ricostruite in questa passata.
    if dlcs != config.DLCS:
        touched = set(dlcs)
        for key, row in old.items():
            if key[0] not in touched:
                rows.append(row)

    rows.sort(key=lambda r: (config.DLCS.index(r["dlc"]) if r["dlc"] in config.DLCS
                             else 99, r["file"], r["tag"]))
    LEDGER.parent.mkdir(exist_ok=True)
    with LEDGER.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return counts


def validate(dlcs=None, only_translated=True) -> int:
    """Promuove a 'validated' fissando la baseline. Ritorna quante righe toccate."""
    repo = config.repo_root()
    dlcs = set(dlcs or config.DLCS)
    cur = {(d, f, t): (it, en) for d, f, t, _l, it, en in iter_strings(repo, dlcs)}
    rows = list(load().values())
    n = 0
    for row in rows:
        if row["dlc"] not in dlcs:
            continue
        if only_translated and row["status"] not in ("translated", "modified"):
            continue
        key = (row["dlc"], row["file"], row["tag"])
        if key not in cur:
            continue
        it, en = cur[key]
        row["status"] = "validated"
        row["en_sha"], row["it_sha"] = _sha(en), _sha(it)
        n += 1
    with LEDGER.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return n


def set_keep(dlcs=None, only_untranslated=True) -> int:
    """Marca come 'keep' (da-non-tradurre) le voci volutamente lasciate in inglese
    (prestiti, nomi propri, sigle, format-string). Di default agisce sulle sole
    'untranslated' (cioe IT == EN gia riviste). Ritorna quante righe toccate."""
    repo = config.repo_root()
    dlcs = set(dlcs or config.DLCS)
    cur = {(d, f, t): (it, en) for d, f, t, _l, it, en in iter_strings(repo, dlcs)}
    rows = list(load().values())
    n = 0
    for row in rows:
        if row["dlc"] not in dlcs:
            continue
        if only_untranslated and row["status"] != "untranslated":
            continue
        key = (row["dlc"], row["file"], row["tag"])
        if key not in cur:
            continue
        it, en = cur[key]
        row["status"] = "keep"
        row["en_sha"], row["it_sha"] = _sha(en), _sha(it)
        n += 1
    with LEDGER.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return n


def set_status_keys(keys, status: str) -> int:
    """Imposta lo stato di righe specifiche (set/list di tuple (dlc,file,tag)).

    Per 'validated'/'keep' rifissa la baseline degli hash dal testo XML corrente,
    cosi diventano sticky finche l'inglese non cambia. Ritorna le righe toccate."""
    keys = {tuple(k) for k in keys}
    # testi solo dei file toccati (veloce: niente scansione dell'intera DLC)
    cur: dict[tuple, tuple[str, str]] = {}
    for relf in {k[1] for k in keys}:
        for tag, (it, en) in texts_for_file(relf).items():
            cur[(relf, tag)] = (it, en)
    rows = list(load().values())
    n = 0
    for row in rows:
        key = (row["dlc"], row["file"], row["tag"])
        if key not in keys:
            continue
        row["status"] = status
        tx = cur.get((row["file"], row["tag"]))
        if tx and status in ("validated", "keep"):
            row["en_sha"], row["it_sha"] = _sha(tx[1]), _sha(tx[0])
        n += 1
    with LEDGER.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return n


_STATE_COLORS = {
    "validated": "#3fb950", "translated": "#58a6ff", "modified": "#d29922",
    "keep": "#8b949e", "stale": "#db6d28", "untranslated": "#6e7681",
}


def report_html(out_path: Path, generated: str) -> Path:
    """Dashboard HTML self-contained (nessuna dipendenza, nessun server)."""
    from collections import Counter, defaultdict
    rows = list(load().values())
    total = len(rows)
    overall = Counter(r["status"] for r in rows)
    wrong = sum(1 for r in rows if r["lang_flag"])
    per_dlc: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        per_dlc[r["dlc"]][r["status"]] += 1

    order = ["validated", "translated", "keep", "modified", "stale", "untranslated"]

    def bar(counts: Counter, tot: int) -> str:
        if not tot:
            return ""
        segs = []
        for st in order:
            n = counts.get(st, 0)
            if n:
                segs.append(f'<span style="width:{n/tot*100:.2f}%;background:{_STATE_COLORS[st]}" '
                            f'title="{st}: {n}"></span>')
        return f'<div class="bar">{"".join(segs)}</div>'

    def pct_done(counts: Counter, tot: int) -> str:
        done = (counts.get("validated", 0) + counts.get("translated", 0)
                + counts.get("modified", 0) + counts.get("keep", 0))
        return f"{done/tot*100:.1f}%" if tot else "-"

    dlc_rows = ""
    for dlc in config.DLCS:
        if dlc not in per_dlc:
            continue
        c = per_dlc[dlc]
        tot = sum(c.values())
        dlc_rows += (f'<tr><td class="dlc">{dlc}</td><td class="num">{tot}</td>'
                     f'<td class="num">{pct_done(c, tot)}</td>'
                     f'<td class="num val">{c.get("validated", 0)}</td>'
                     f'<td>{bar(c, tot)}</td></tr>')

    legend = "".join(
        f'<span class="lg"><i style="background:{_STATE_COLORS[s]}"></i>{s} ({overall.get(s,0)})</span>'
        for s in order)

    done_overall = pct_done(overall, total)
    html = f"""<!DOCTYPE html><html lang="it"><head><meta charset="utf-8">
<title>RimWorld-it - progresso traduzione</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0d1117;color:#c9d1d9;margin:0;padding:32px;}}
 h1{{font-size:22px;margin:0 0 4px;}} .sub{{color:#8b949e;font-size:13px;margin-bottom:24px;}}
 .big{{font-size:46px;font-weight:700;color:#3fb950;}}
 .bar{{display:flex;height:16px;border-radius:8px;overflow:hidden;background:#161b22;}}
 .bar span{{display:block;height:100%;}}
 table{{width:100%;border-collapse:collapse;margin-top:20px;font-size:14px;}}
 th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid #21262d;}}
 th{{color:#8b949e;font-weight:600;font-size:12px;text-transform:uppercase;}}
 td.num{{text-align:right;font-variant-numeric:tabular-nums;}} td.val{{color:#3fb950;}}
 td.dlc{{font-weight:600;}} td:last-child{{width:38%;}}
 .lg{{display:inline-flex;align-items:center;gap:6px;margin-right:16px;font-size:12px;color:#8b949e;}}
 .lg i{{width:11px;height:11px;border-radius:3px;display:inline-block;}}
 .warn{{color:#db6d28;font-weight:600;}}
 .card{{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:24px;margin-bottom:20px;}}
</style></head><body>
<h1>RimWorld-it — progresso traduzione</h1>
<div class="sub">Generato {generated} · {total} stringhe · gioco 1.6.4850</div>
<div class="card">
  <div class="big">{done_overall}</div>
  <div class="sub">tradotte o validate sul totale</div>
  {bar(overall, total)}
  <div style="margin-top:16px">{legend}</div>
  {f'<div style="margin-top:12px" class="warn">⚠ {wrong} stringhe segnalate in lingua sbagliata</div>' if wrong else ''}
</div>
<table>
 <tr><th>DLC</th><th>Stringhe</th><th>Fatte</th><th>Validate</th><th>Composizione</th></tr>
 {dlc_rows}
</table>
</body></html>"""
    out_path.write_text(html, encoding="utf-8")
    return out_path


def todo(dlcs=None, statuses=("untranslated", "stale")):
    """Worklist per LLM/tool esterno: righe da tradurre, con EN e IT correnti."""
    repo = config.repo_root()
    dlcs = set(dlcs or config.DLCS)
    want = {(r["dlc"], r["file"], r["tag"]): r["status"]
            for r in load().values()
            if r["dlc"] in dlcs and (r["status"] in statuses or r["lang_flag"])}
    out = []
    for d, f, t, line, it, en in iter_strings(repo, dlcs):
        k = (d, f, t)
        if k in want:
            out.append({"dlc": d, "file": f, "tag": t, "line": line,
                        "status": want[k], "en": en, "it": it})
    return out
