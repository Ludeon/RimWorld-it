"""Review dashboard (Flask) — stateless, no cache, multilingual.

Every request re-reads the ledger CSV and the XML texts: what you see is ALWAYS
the current repo state (no staleness, unlike the old Streamlit app with
@st.cache_data). UI language via a cookie (English by default, for all the
translator teams).

Run:  .venv\\Scripts\\python scripts\\dashboard\\server.py
Then open http://127.0.0.1:5000
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rwit"))
import config            # noqa: E402
import ledger as L       # noqa: E402
import namegen as NG     # noqa: E402

from flask import Flask, request, jsonify, abort, make_response  # noqa: E402

app = Flask(__name__)

STATES = ["validated", "keep", "translated", "modified", "stale", "untranslated"]
DONE = {"validated", "translated", "modified", "keep"}
COLORS = L._STATE_COLORS

# Istruzioni antemposte al blocco "copy for debug": query in inglese, risposta
# nella lingua dell'utente, cosi la sessione di review e ripetibile senza
# riscriverle ogni volta. NON e una f-string: { } e [ ] restano letterali.
DEBUG_PROMPT = """\
This block is from the namegen dashboard "copy for debug" of the Italian
RimWorld translation (repo RimWorld-it). Line 1 = pack (game/DLC, file, namer),
line 2 = source file, then rows `generated name <- template`, where the template
shows the source [tags] and xN = how often it recurred.

Review the Italian for errors and unnatural output, FIX them in the file, and
cross-check the other language packs.

Look specifically for:
- concatenated compounds that don't exist in Italian (EN "Redrock"/"Greatclaw"
  -> "rossolegno"/"grandeartiglio"): Italian needs noun+adjective with
  agreement, or a "X di Y" genitive
- English calques / literal translations
- bare adjectives or abstract words that don't read as a place name
- wrong sense/register, or a word that's wrong for that biome/feature
- gender agreement (noun <-> adjective/color/article): use the gendered symbol
  variants (_Masculine/_Feminine, ...MS/FS) when an adjective must agree, and
  verify the referenced word-list .txt exists and is populated before using it

Cross-check how the sibling repos solved the SAME namer (folders next to this
repo): RimWorld-fr (closest model), RimWorld-Spanish, RimWorld-de.

Respect the rules: never touch the <!-- EN: --> comments; keep [tags] and {var}
names; rulesStrings keep the -> arrow and identical left side; preserve XML
structure/indent and \\n\\n; gender ternary {X_gender ? o : a}. This block is a
snapshot: open and read the real file before editing, then validate the XML.

Write the analysis in English; reply to me in Italian."""

# ---------------------------------------------------------------- i18n --------
LANGS = {"en": "English", "it": "Italiano", "es": "Español", "fr": "Français", "de": "Deutsch"}
TR = {
    "title": {"en": "translation review", "it": "revisione traduzione", "es": "revisión de traducción",
              "fr": "révision de la traduction", "de": "Übersetzungsprüfung"},
    "tab_prog": {"en": "Progress", "it": "Progresso", "es": "Progreso", "fr": "Progression", "de": "Fortschritt"},
    "tab_names": {"en": "Name generator", "it": "Generatore nomi", "es": "Generador de nombres",
                  "fr": "Générateur de noms", "de": "Namensgenerator"},
    "hdr_done": {"en": "translated", "it": "tradotto", "es": "traducido", "fr": "traduit", "de": "übersetzt"},
    "hdr_val": {"en": "validated", "it": "validato", "es": "validado", "fr": "validé", "de": "validiert"},
    "to_namegen": {"en": "review in the name generator", "it": "rivedi nel generatore nomi",
                   "es": "revisar en el generador de nombres", "fr": "réviser dans le générateur de noms",
                   "de": "im Namensgenerator prüfen"},
    "ng_only": {"en": "name generators only", "it": "solo generatori nomi",
                "es": "solo generadores de nombres", "fr": "générateurs de noms seulement",
                "de": "nur Namensgeneratoren"},
    "ng_badge": {"en": "name/grammar generator — review in the Name generator tab",
                 "it": "generatore nomi/grammatica — rivedi nella scheda Generatore nomi",
                 "es": "generador de nombres/gramática — revisar en la pestaña Generador de nombres",
                 "fr": "générateur de noms/grammaire — réviser dans l'onglet Générateur de noms",
                 "de": "Namens-/Grammatikgenerator — im Tab Namensgenerator prüfen"},
    "rebuild": {"en": "↻ Rebuild ledger", "it": "↻ Ricostruisci ledger", "es": "↻ Reconstruir registro",
                "fr": "↻ Reconstruire", "de": "↻ Neu aufbauen"},
    "by_dlc": {"en": "By DLC", "it": "Per DLC", "es": "Por DLC", "fr": "Par DLC", "de": "Nach DLC"},
    "files_review": {"en": "Files to review", "it": "File da revisionare", "es": "Archivos a revisar",
                     "fr": "Fichiers à réviser", "de": "Zu prüfende Dateien"},
    "files_with": {"en": "{n} files with «{s}» entries", "it": "{n} file con voci «{s}»",
                   "es": "{n} archivos con «{s}»", "fr": "{n} fichiers avec «{s}»", "de": "{n} Dateien mit «{s}»"},
    "col_file": {"en": "File", "it": "File", "es": "Archivo", "fr": "Fichier", "de": "Datei"},
    "col_comp": {"en": "composition", "it": "composizione", "es": "composición", "fr": "composition", "de": "Zusammensetzung"},
    "col_done": {"en": "done", "it": "fatte", "es": "hechas", "fr": "faites", "de": "fertig"},
    "col_actions": {"en": "actions", "it": "azioni", "es": "acciones", "fr": "actions", "de": "Aktionen"},
    "validate_all": {"en": "validate all", "it": "valida tutto", "es": "validar todo", "fr": "tout valider", "de": "alle validieren"},
    "validate_file": {"en": "✓ validate whole file", "it": "✓ valida tutto il file", "es": "✓ validar todo el archivo",
                      "fr": "✓ valider tout le fichier", "de": "✓ ganze Datei validieren"},
    "keep_all": {"en": "keep all", "it": "keep tutto", "es": "keep todo", "fr": "keep tout", "de": "alle keep"},
    "back": {"en": "← back", "it": "← indietro", "es": "← atrás", "fr": "← retour", "de": "← zurück"},
    "empty_val": {"en": "empty", "it": "vuoto", "es": "vacío", "fr": "vide", "de": "leer"},
    "ng_intro": {
        "en": "Preview the names the game would generate from a RulePack. Approximate: unresolved runtime symbols (pawn names, subjects) show as «symbol». Reload to reroll.",
        "it": "Anteprima dei nomi che il gioco genererebbe da un RulePack. Approssimato: i simboli runtime non risolti (nomi pawn, soggetti) appaiono come «simbolo». Ricarica per rigenerare.",
        "es": "Vista previa de los nombres que el juego generaría desde un RulePack. Aproximado: los símbolos sin resolver aparecen como «símbolo». Recarga para regenerar.",
        "fr": "Aperçu des noms générés depuis un RulePack. Approximatif : symboles non résolus en «symbole». Rechargez pour relancer.",
        "de": "Vorschau der aus einem RulePack generierten Namen. Annähernd: ungelöste Symbole als «Symbol». Neu laden zum Neuwürfeln."},
    "ng_filter": {"en": "Filter", "it": "Filtra", "es": "Filtrar", "fr": "Filtrer", "de": "Filtern"},
    "ng_count": {"en": "How many", "it": "Quanti", "es": "Cuántos", "fr": "Combien", "de": "Wie viele"},
    "ng_gen": {"en": "🎲 Generate", "it": "🎲 Genera", "es": "🎲 Generar", "fr": "🎲 Générer", "de": "🎲 Generieren"},
    "ng_none": {"en": "No rulepack matches the filter.", "it": "Nessun rulepack corrisponde.",
                "es": "Ningún rulepack coincide.", "fr": "Aucun rulepack ne correspond.", "de": "Kein Rulepack passt."},
    "ng_prev": {"en": "◀ Prev", "it": "◀ Prec", "es": "◀ Ant", "fr": "◀ Préc", "de": "◀ Zurück"},
    "ng_next": {"en": "Next ▶", "it": "Succ ▶", "es": "Sig ▶", "fr": "Suiv ▶", "de": "Weiter ▶"},
    "ng_pos": {"en": "pack {i}/{n}", "it": "pack {i}/{n}", "es": "pack {i}/{n}",
               "fr": "pack {i}/{n}", "de": "Pack {i}/{n}"},
}
STATUS_NAMES = {
    "validated": {"en": "validated", "it": "validate", "es": "validadas", "fr": "validées", "de": "validiert"},
    "translated": {"en": "translated", "it": "tradotte", "es": "traducidas", "fr": "traduites", "de": "übersetzt"},
    "modified": {"en": "modified", "it": "modificate", "es": "modificadas", "fr": "modifiées", "de": "geändert"},
    "keep": {"en": "do not translate", "it": "da non tradurre", "es": "no traducir",
             "fr": "ne pas traduire", "de": "nicht übersetzen"},
    "stale": {"en": "stale", "it": "obsolete", "es": "obsoletas", "fr": "obsolètes", "de": "veraltet"},
    "untranslated": {"en": "untranslated", "it": "da tradurre", "es": "sin traducir",
                     "fr": "non traduites", "de": "unübersetzt"},
}


def lang() -> str:
    return request.cookies.get("lang", "en") if request else "en"


def t(key: str, **fmt) -> str:
    s = TR.get(key, {}).get(lang(), TR.get(key, {}).get("en", key))
    return s.format(**fmt) if fmt else s


def sname(state: str) -> str:
    return STATUS_NAMES[state].get(lang(), STATUS_NAMES[state]["en"])


# ------------------------------------------------------------- rendering ------
SHELL = """<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>RimWorld IT — {title}</title><style>
:root{{color-scheme:dark}} *{{box-sizing:border-box}}
body{{margin:0;font:14px/1.5 system-ui,Segoe UI,sans-serif;background:#0d1117;color:#c9d1d9}}
a{{color:#58a6ff;text-decoration:none}} a:hover{{text-decoration:underline}}
header{{position:sticky;top:0;background:#161b22;border-bottom:1px solid #30363d;padding:10px 20px;display:flex;align-items:center;gap:16px;z-index:5;flex-wrap:wrap}}
h1{{font-size:17px;margin:0}}
nav a{{padding:5px 10px;border-radius:6px}} nav a.on{{background:#21262d;color:#c9d1d9}}
.sp{{flex:1}}
.btn{{background:#21262d;border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:6px 12px;cursor:pointer;font:inherit}}
.btn:hover{{border-color:#8b949e}} .btn.g{{border-color:#238636;color:#3fb950}} .btn.k{{border-color:#6e7681}}
main{{padding:20px;max-width:1200px;margin:auto}}
.bar{{display:flex;height:14px;border-radius:7px;overflow:hidden;margin:8px 0}} .bar span{{display:block}}
.chips{{display:flex;gap:18px;flex-wrap:wrap;margin:10px 0}}
.chip{{border-left:4px solid #444;padding:2px 10px}} .chip b{{font-size:18px}} .chip small{{color:#8b949e}}
table{{border-collapse:collapse;width:100%;margin-top:10px}}
th,td{{text-align:left;padding:6px 10px;border-bottom:1px solid #21262d;vertical-align:top}}
th{{color:#8b949e;font-weight:600;position:sticky;top:50px;background:#0d1117}}
tr:hover td{{background:#161b22}}
.tag{{font:12px ui-monospace,monospace;color:#8b949e}} .en{{color:#8b949e}}
.s{{font:12px ui-monospace,monospace;padding:1px 7px;border-radius:10px;white-space:nowrap}}
.pct{{color:#8b949e;font-variant-numeric:tabular-nums}}
.dlcrow{{display:flex;align-items:center;gap:12px;margin:4px 0}}
.dlcrow .nm{{width:80px;font-weight:600}} .dlcrow .bar{{flex:1;margin:0}}
.flt{{display:flex;gap:8px;align-items:center;margin:14px 0;flex-wrap:wrap}}
select,input{{background:#0d1117;border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:5px 8px;font:inherit}}
.muted{{color:#8b949e}} .right{{text-align:right}}
.names div{{break-inside:avoid;padding:2px 0}}
.toast{{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#238636;color:#fff;padding:10px 18px;border-radius:8px;box-shadow:0 4px 16px #0008;z-index:50;opacity:0;pointer-events:none;transition:opacity .2s;font-weight:600}}
.toast.show{{opacity:1}}
.toast.err{{background:#da3633}}
</style>
<script>
// Ricorda l'ultima pagina visitata e ripristinala UNA VOLTA per sessione del browser:
// riaprendo la dashboard (es. il giorno dopo) torni dov'eri; dentro la stessa sessione
// la navigazione resta libera (Home non ti rimbalza indietro).
(function(){{try{{
  var KEY='rwit_last', here=location.pathname+location.search;
  if(location.pathname=='/'&&!location.search&&!sessionStorage.getItem('rwit_restored')){{
    sessionStorage.setItem('rwit_restored','1');
    var last=localStorage.getItem(KEY);
    if(last&&last!='/'&&last!=here){{location.replace(last);return;}}
  }}
  localStorage.setItem(KEY,here);
}}catch(e){{}}}})();
</script>
</head><body>
<header>
  <h1>🌍 RimWorld IT</h1>
  <nav><a href="/" class="{on_prog}">{tab_prog}</a><a href="/namegen" class="{on_names}">{tab_names}</a></nav>
  <span class=sp></span>
  <span class=pct>{completion}</span>
  <select onchange="document.cookie='lang='+this.value+';path=/;max-age=31536000';location.reload()">{langopts}</select>
  <button class=btn onclick="rebuild()">{rebuild}</button>
</header><main>{body}</main>
<div id=toast class=toast></div>
<script>
function showToast(msg,err){{
  var el=document.getElementById('toast'); if(!el)return;
  el.textContent=msg; el.className='toast show'+(err?' err':'');
  clearTimeout(window.__tt); window.__tt=setTimeout(function(){{el.className='toast';}},2400);
}}
// messaggio "flash" che sopravvive al reload (l'azione è salvata PRIMA del reload)
(function(){{try{{var f=sessionStorage.getItem('rwit_flash');if(f){{sessionStorage.removeItem('rwit_flash');showToast(f);}}}}catch(e){{}}}})();
async function setStatus(keys,status){{
  const r=await fetch('/api/set',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{keys,status}})}});
  if(r.ok){{
    let c=0; try{{c=(await r.json()).changed;}}catch(e){{}}
    try{{sessionStorage.setItem('rwit_flash','✓ '+c+' voci salvate → '+status);}}catch(e){{}}
    location.reload();
  }} else {{ showToast('errore nel salvataggio',true); }}
}}
function fileAction(f,status){{ setStatus([['__file__',f,'*']],status); }}
async function rebuild(){{ const r=await fetch('/api/rebuild',{{method:'POST'}}); if(r.ok){{try{{sessionStorage.setItem('rwit_flash','↻ ledger ricostruito');}}catch(e){{}}location.reload();}} else showToast('errore',true); }}
function copyTxt(t,el){{ navigator.clipboard.writeText(t).then(()=>{{if(el){{const o=el.textContent;el.textContent='✓';setTimeout(()=>el.textContent=o,900);}}}}); }}
</script></body></html>"""


def render(body: str, active: str = "prog", completion: str = "") -> str:
    langopts = "".join(f'<option value="{c}" {"selected" if c==lang() else ""}>{n}</option>'
                       for c, n in LANGS.items())
    return SHELL.format(
        title=t("title"), tab_prog=t("tab_prog"), tab_names=t("tab_names"),
        on_prog="on" if active == "prog" else "", on_names="on" if active == "names" else "",
        completion=completion, langopts=langopts, rebuild=t("rebuild"), body=body)


def segbar(counts: Counter, total: int) -> str:
    if not total:
        return ""
    segs = "".join(
        f'<span style="width:{counts.get(s,0)/total*100:.3f}%;background:{COLORS[s]}" '
        f'title="{sname(s)}: {counts.get(s,0)}"></span>'
        for s in STATES if counts.get(s, 0))
    return f'<div class=bar>{segs}</div>'


@app.after_request
def no_cache(resp):
    resp.headers["Cache-Control"] = "no-store"
    return resp


# --------------------------------------------------------------- routes -------
@app.route("/")
def index():
    rows = list(L.load().values())
    total = len(rows)
    overall = Counter(r["status"] for r in rows)
    done = sum(overall.get(s, 0) for s in DONE)
    validated = overall.get("validated", 0)
    sel_dlc = request.args.get("dlc", "")
    sel_status = request.args.get("status", "translated")
    sel_ng = request.args.get("ng", "")

    chips = "".join(
        f'<div class=chip style="border-color:{COLORS[s]}"><b>{overall.get(s,0):,}</b>'
        f'<br><small>{sname(s)}</small></div>' for s in STATES)

    perdlc = defaultdict(Counter)
    for r in rows:
        perdlc[r["dlc"]][r["status"]] += 1
    dlcbars = ""
    for d in config.DLCS:
        if d not in perdlc:
            continue
        c = perdlc[d]
        tot = sum(c.values())
        v = c.get("validated", 0)
        dlcbars += (f'<div class=dlcrow><span class=nm>{d}</span>{segbar(c,tot)}'
                    f'<span class=pct><b style="color:{COLORS["validated"]}">{v:,}</b>/{tot:,}</span></div>')

    perfile = defaultdict(Counter)
    for r in rows:
        perfile[(r["dlc"], r["file"])][r["status"]] += 1
    # File-namegen (RulePackDef): si revisionano nella scheda Generatore nomi, non
    # leggendo l'XML. Set derivato live dai pack -> badge + filtro + scorciatoia,
    # niente DB. Hanno poche stringhe l'uno, quindi senza il filtro ng finiscono
    # in fondo alla lista (oltre il taglio a 400) e non si vedono.
    ng_files = {p["file"] for p in NG.load_rulepacks().values()}
    frows = sorted(
        ((c.get(sel_status, 0), d, f, sum(c.values()), sum(c.get(s, 0) for s in DONE), c)
         for (d, f), c in perfile.items()
         if c.get(sel_status, 0) and (not sel_dlc or d == sel_dlc)
         and (not sel_ng or f in ng_files)),
        key=lambda x: -x[0])

    # File-namegen (RulePackDef): si revisionano nella scheda Generatore nomi, non
    # leggendo l'XML. Set derivato live dai pack -> badge + scorciatoia, niente DB.
    opt_dlc = "".join(f'<option {"selected" if d==sel_dlc else ""}>{d}</option>' for d in [""] + config.DLCS)
    opt_st = "".join(f'<option value="{s}" {"selected" if s==sel_status else ""}>{sname(s)}</option>' for s in STATES)
    trs = ""
    for pend, d, f, tot, dn, c in frows[:400]:
        short = f.replace("\\", "/").split("/")[-1]
        is_ng = f in ng_files
        stem = short[:-4] if short.endswith(".xml") else short
        badge = (f' <span title="{t("ng_badge")}" style="cursor:help">🎲</span>' if is_ng else "")
        ngbtn = (f'<a class="btn" title="{t("to_namegen")}" href="/namegen?q={quote(f"{d} · {stem}")}">🎲</a> '
                 if is_ng else "")
        trs += (f'<tr><td><a href="/file?f={quote(f, safe="")}">{short}</a>{badge}<br><span class=tag>{d} · {_h(f)}</span></td>'
                f'<td class=right><b>{pend}</b></td><td>{segbar(c,tot)}</td><td class="right pct">{dn}/{tot}</td>'
                f'<td class="right pct"><b style="color:{COLORS["validated"]}">{c.get("validated",0)}</b>/{tot}</td>'
                f'<td class=right style="white-space:nowrap">{ngbtn}'
                f'<button class="btn g" title="{t("validate_all")}" onclick=\'fileAction("{_js(f)}","validated")\'>✓</button> '
                f'<button class="btn k" title="{t("keep_all")}" onclick=\'fileAction("{_js(f)}","keep")\'>🔒</button></td></tr>')

    body = f"""<div class=chips>{chips}</div>{segbar(overall,total)}
    <h3>{t("by_dlc")}</h3>{dlcbars}
    <h3>{t("files_review")}</h3>
    <div class=flt>DLC <select onchange="location.href='/?dlc='+this.value+'&status={sel_status}&ng={sel_ng}'">{opt_dlc}</select>
      <select onchange="location.href='/?dlc={sel_dlc}&status='+this.value+'&ng={sel_ng}'">{opt_st}</select>
      <a class="btn{' g' if sel_ng else ''}" href="/?dlc={sel_dlc}&status={sel_status}&ng={'' if sel_ng else '1'}">🎲 {t("ng_only")}</a>
      <span class=muted>{t("files_with", n=len(frows), s=sname(sel_status))}</span></div>
    <table><thead><tr><th>{t("col_file")}</th><th class=right>«{sname(sel_status)}»</th><th>{t("col_comp")}</th>
      <th class=right>{t("col_done")}</th><th class=right>{t("hdr_val")}</th><th class=right>{t("col_actions")}</th></tr></thead><tbody>{trs}</tbody></table>"""
    completion = (f'{t("hdr_done")} {done/total*100:.1f}% · '
                  f'{t("hdr_val")} {validated/total*100:.1f}% ({validated:,}/{total:,})'
                  if total else "")
    return render(body, "prog", completion)


@app.route("/file")
def file_view():
    f = request.args.get("f", "")
    rows = [r for r in L.load().values() if r["file"] == f]
    if not rows:
        abort(404)
    texts = L.texts_for_file(f)
    order = {s: i for i, s in enumerate(["untranslated", "stale", "modified", "translated", "keep", "validated"])}
    rows.sort(key=lambda r: (order.get(r["status"], 9), r["tag"]))
    c = Counter(r["status"] for r in rows)
    empty_it = f'<i class=muted>{t("empty_val")}</i>'
    trs = ""
    for r in rows:
        it, en = texts.get(r["tag"], ("", ""))
        st = r["status"]
        k = f'["{_js(r["dlc"])}","{_js(r["file"])}","{_js(r["tag"])}"]'
        acts = ("" if st == "validated" else f'<button class="btn g" onclick=\'setStatus({k},"validated")\'>✓</button> ')
        acts += ("" if st == "keep" else f'<button class="btn k" onclick=\'setStatus({k},"keep")\'>keep</button>')
        it_cell = _h(it) or empty_it
        en_cell = _h(en) or "—"
        trs += (f'<tr><td class=tag>{_h(r["tag"])}</td><td class=en>{en_cell}</td>'
                f'<td>{it_cell}</td>'
                f'<td><span class=s style="background:{COLORS[st]}22;color:{COLORS[st]}">{sname(st)}</span></td>'
                f'<td class=right>{acts}</td></tr>')
    short = f.replace("\\", "/").split("/")[-1]
    comp = " · ".join(f'<span style="color:{COLORS[s]}">{sname(s)}: {c[s]}</span>' for s in STATES if c.get(s))
    body = f"""<p><a href="/">{t("back")}</a></p><h3>{short} <span class=tag>{_h(f)}</span></h3><p>{comp}</p>
    <p><button class="btn g" onclick='fileAction("{_js(f)}","validated")'>{t("validate_file")}</button>
       <button class="btn k" onclick='fileAction("{_js(f)}","keep")'>{t("keep_all")}</button></p>
    <table><thead><tr><th>tag</th><th>EN</th><th>IT</th><th></th><th></th></tr></thead><tbody>{trs}</tbody></table>"""
    return render(body, "prog")


def _pack_order(k: str):
    """Ordina i rulepack per DLC (Core per primo), poi per nome."""
    dlc = k.split(" · ", 1)[0]
    return (config.DLCS.index(dlc) if dlc in config.DLCS else 99, k)


@app.route("/namegen")
def namegen_view():
    packs = NG.load_rulepacks()                       # rilettura fresca
    keys = sorted(packs.keys(), key=_pack_order)      # Core per primo
    # default "Namer" come la vecchia dashboard: mostra solo i pack che generano
    # nomi (~158), non le frasi di interazione/log/descrizioni (i ~288 totali).
    q_raw = request.args.get("q", "Namer").strip()
    q = q_raw.lower()
    shown = [k for k in keys if q in k.lower()] if q else keys
    n = max(1, min(200, int(request.args.get("n", 20) or 20)))

    if not shown:
        return render(f'<p class=muted>{t("ng_intro")}</p>'
                      f'{_ng_form(q_raw, "", n, 0, 0)}<p class=muted>{t("ng_none")}</p>', "names")

    # paginatore: indice del pack nella lista filtrata (Prec/Succ/Vai a #)
    i = int(request.args.get("i", 0) or 0)
    i = max(0, min(i, len(shown) - 1))
    sel = shown[i]

    try:
        pairs, _ = NG.generate(packs, sel, n=n)       # [(nome risolto, template d'origine)]
    except Exception as e:                            # noqa: BLE001
        pairs = [(f"<error: {e}>", "")]
    # dedup preservando l'ordine (per coppia nome+template): un pack a regola singola
    # = 1 riga; un namer mostra la varieta reale, con ×N se ripetuto.
    cnt = Counter(pairs)
    uniq = list(dict.fromkeys(pairs))
    # tabella full-width: NOME risolto | TEMPLATE coi [tag] d'origine (cosi sai da
    # quale simbolo viene ogni parte e non cancelli tag importanti) | ×N.
    rows_html = "".join(
        f'<tr><td>{_h(name)}</td>'
        f'<td class=tag>{_h(tmpl)}</td>'
        f'<td class="right muted" style="width:48px;white-space:nowrap">'
        f'{"×"+str(cnt[(name, tmpl)]) if cnt[(name, tmpl)] > 1 else ""}</td></tr>'
        for name, tmpl in uniq)
    cap = (f'{len(uniq)} unici / {len(pairs)} generati' if lang() == "it"
           else f'{len(uniq)} unique / {len(pairs)} generated')
    legend = ("la colonna «template» mostra da quale [tag] deriva ogni parte — non "
              "cancellarli nei file." if lang() == "it"
              else "the «template» column shows which [tag] each part comes from.")
    th = ("nome", "template (tag d'origine)") if lang() == "it" else ("name", "template (source tags)")
    names_html = (f'<p class=muted>{cap} · {legend}</p>'
                  f'<table class=gen><thead><tr><th>{th[0]}</th><th>{th[1]}</th><th></th>'
                  f'</tr></thead><tbody>{rows_html}</tbody></table>')

    qs = f'q={quote(q_raw)}&n={n}'
    prev = f'<a class=btn href="/namegen?{qs}&i={i-1}">{t("ng_prev")}</a>' if i > 0 else f'<span class="btn" style="opacity:.4">{t("ng_prev")}</span>'
    nxt = f'<a class=btn href="/namegen?{qs}&i={i+1}">{t("ng_next")}</a>' if i < len(shown) - 1 else f'<span class="btn" style="opacity:.4">{t("ng_next")}</span>'
    opts = "".join(f'<option {"selected" if j==i else ""}>{_h(k)}</option>' for j, k in enumerate(shown))
    dropdown = (f'<select style="min-width:340px" '
                f'onchange="location.href=\'/namegen?{qs}&i=\'+this.selectedIndex">{opts}</select>')
    jump = (f'<input type=number min=1 max={len(shown)} value="{i+1}" style="width:64px" '
            f"onchange=\"location.href='/namegen?{qs}&i='+(this.value-1)\">")
    pager = (f'<div class=flt>{prev}{nxt}'
             f'<span class=muted>{t("ng_pos", i=i+1, n=len(shown))}</span>{dropdown}{jump}</div>')

    # file sorgente del pack: copiabile + link alla revisione di quel file +
    # azioni di validazione (valida/keep tutto il file) e progresso, cosi i
    # generatori nomi si validano da qui senza aprire l'XML.
    relfile = packs[sel].get("file", "")
    lrows = [r for r in L.load().values() if r["file"] == relfile]
    vdone = sum(1 for r in lrows if r["status"] == "validated")
    valbtns = (f'<button class="btn g" onclick=\'fileAction("{_js(relfile)}","validated")\'>{t("validate_file")}</button> '
               f'<button class="btn k" onclick=\'fileAction("{_js(relfile)}","keep")\'>{t("keep_all")}</button> '
               f'<span class=pct><b style="color:{COLORS["validated"]}">{vdone}</b>/{len(lrows)}</span>'
               if relfile and lrows else "")
    fileline = (f'<p>📄 <a href="/file?f={quote(relfile, safe="")}">{_h(relfile)}</a> '
                f'<button class=btn style="padding:2px 8px" '
                f'onclick=\'copyTxt("{_js(relfile)}",this)\'>📋</button></p>'
                f'<p>{valbtns}</p>')

    # blocco debug: un solo copia con pack (dove sei) + file + nomi<-template,
    # pronto da incollare in console.
    dbg = [DEBUG_PROMPT, "", "---", "", f"# {sel}", f"# {relfile}", ""]
    for name, tmpl in uniq:
        c = cnt[(name, tmpl)]
        dbg.append(f"{name}\t<- {tmpl}" + (f"  x{c}" if c > 1 else ""))
    copy_dbg = (f'<p><button class=btn onclick="copyTxt(document.getElementById(\'dbg\')'
                f'.textContent,this)">📋 {"copia per debug (istruzioni + pack + nomi + tag)" if lang()=="it" else "copy for debug (instructions + pack + names + tags)"}</button></p>'
                f'<pre id=dbg hidden>{_h(chr(10).join(dbg))}</pre>')

    body = (f'<p class=muted>{t("ng_intro")}</p>{_ng_form(q_raw, sel, n, i, len(shown))}'
            f'<h3>{_h(sel)}</h3>{fileline}{pager}{copy_dbg}{names_html}')
    return render(body, "names")


def _ng_form(q: str, sel: str, n: int, i: int, total: int) -> str:
    return (f'<form class=flt method=get>{t("ng_filter")} '
            f'<input name=q value="{_h(q)}" style="width:220px" placeholder="namer / faction / map…">'
            f'<input type=hidden name=i value="{i}">'
            f'{t("ng_count")} <input name=n type=number min=1 max=200 value="{n}" style="width:70px">'
            f'<button class=btn type=submit>{t("ng_gen")}</button></form>')


@app.post("/api/set")
def api_set():
    data = request.get_json(force=True)
    raw = data["keys"]
    if raw and raw[0][0] == "__file__":
        f = raw[0][1]
        keys = {(r["dlc"], r["file"], r["tag"]) for r in L.load().values() if r["file"] == f}
    else:
        keys = {tuple(k) for k in raw}
    return jsonify(ok=True, changed=L.set_status_keys(keys, data["status"]))


@app.post("/api/rebuild")
def api_rebuild():
    L.build()
    return jsonify(ok=True)


def _h(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _js(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')


if __name__ == "__main__":
    print("Review dashboard → http://127.0.0.1:5000  (Ctrl+C to stop)")
    # use_reloader: auto-restart when server.py changes, so you never restart by hand.
    # Data (CSV/XML/rulepacks) is already read fresh per request — no restart for those.
    app.run(debug=True, use_reloader=True, port=5000)
