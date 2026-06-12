"""Live translation-progress dashboard (Streamlit), multilingual UI.

Run (from the repo root, with the venv):
    .venv\\Scripts\\streamlit run scripts\\dashboard\\app.py

It reads the ledger CSV on every interaction (instant, no XML scan). The "Rebuild"
button re-scans the repo and refreshes the numbers. This is a viewer: the source of
truth stays the XML and `scripts/dashboard/translation-ledger.csv` (tracked in git).
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

# Make the rwit package importable (it lives in scripts/rwit/, one level up).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "rwit"))

import streamlit as st  # noqa: E402

import config  # noqa: E402
import ledger as ledger_mod  # noqa: E402
import namegen as namegen_mod  # noqa: E402

STATE_COLORS = {
    "validated": "#3fb950", "translated": "#58a6ff", "modified": "#d29922",
    "stale": "#db6d28", "untranslated": "#6e7681",
}
ORDER = ["validated", "translated", "modified", "stale", "untranslated"]

# --- i18n -------------------------------------------------------------------
LANGS = {"en": "English", "it": "Italiano", "es": "Español", "fr": "Français", "de": "Deutsch"}

TR = {
    "title": {"en": "translation progress", "it": "progresso traduzione",
              "es": "progreso de traducción", "fr": "progression de la traduction",
              "de": "Übersetzungsfortschritt"},
    "rebuild": {"en": "🔄 Rebuild ledger", "it": "🔄 Ricostruisci ledger",
                "es": "🔄 Reconstruir registro", "fr": "🔄 Reconstruire le registre",
                "de": "🔄 Ledger neu aufbauen"},
    "rebuild_help": {"en": "Re-scan the repo and refresh states and hashes",
                     "it": "Ri-scansiona il repo e aggiorna stati e hash",
                     "es": "Vuelve a escanear el repo y actualiza estados y hashes",
                     "fr": "Réanalyse le dépôt et met à jour états et hachages",
                     "de": "Repo neu scannen, Status und Hashes aktualisieren"},
    "scanning": {"en": "Scanning the repo...", "it": "Scansione del repo...",
                 "es": "Escaneando el repo...", "fr": "Analyse du dépôt...",
                 "de": "Repo wird gescannt..."},
    "updated": {"en": "Ledger updated", "it": "Ledger aggiornato",
                "es": "Registro actualizado", "fr": "Registre mis à jour",
                "de": "Ledger aktualisiert"},
    "empty": {"en": "Ledger empty. Click «Rebuild» or run `rwit ledger build`.",
              "it": "Ledger vuoto. Premi «Ricostruisci» o esegui `rwit ledger build`.",
              "es": "Registro vacío. Pulsa «Reconstruir» o ejecuta `rwit ledger build`.",
              "fr": "Registre vide. Cliquez «Reconstruire» ou lancez `rwit ledger build`.",
              "de": "Ledger leer. «Neu aufbauen» klicken oder `rwit ledger build`."},
    "completion": {"en": "Completion", "it": "Completamento", "es": "Progreso",
                   "fr": "Avancement", "de": "Fortschritt"},
    "total": {"en": "Total strings", "it": "Stringhe totali", "es": "Cadenas totales",
              "fr": "Chaînes totales", "de": "Strings gesamt"},
    "validated_m": {"en": "Validated", "it": "Validate", "es": "Validadas",
                    "fr": "Validées", "de": "Validiert"},
    "wrong": {"en": "Wrong language", "it": "Lingua sbagliata", "es": "Idioma incorrecto",
              "fr": "Mauvaise langue", "de": "Falsche Sprache"},
    "h_states": {"en": "States", "it": "Stati", "es": "Estados", "fr": "États", "de": "Status"},
    "h_perdlc": {"en": "By DLC", "it": "Per DLC", "es": "Por DLC", "fr": "Par DLC", "de": "Nach DLC"},
    "h_worklist": {"en": "To translate / review", "it": "Da tradurre / rivedere",
                   "es": "Para traducir / revisar", "fr": "À traduire / réviser",
                   "de": "Zu übersetzen / prüfen"},
    "f_status": {"en": "Status", "it": "Stato", "es": "Estado", "fr": "Statut", "de": "Status"},
    "wrong_opt": {"en": "(wrong language)", "it": "(lingua sbagliata)",
                  "es": "(idioma incorrecto)", "fr": "(mauvaise langue)", "de": "(falsche Sprache)"},
    "n_strings": {"en": "{n} strings", "it": "{n} stringhe", "es": "{n} cadenas",
                  "fr": "{n} chaînes", "de": "{n} Strings"},
    "lang": {"en": "Language", "it": "Lingua", "es": "Idioma", "fr": "Langue", "de": "Sprache"},
    "tab_prog": {"en": "Progress", "it": "Progresso", "es": "Progreso", "fr": "Progression", "de": "Fortschritt"},
    "tab_names": {"en": "Name generator", "it": "Generatore nomi", "es": "Generador de nombres",
                  "fr": "Générateur de noms", "de": "Namensgenerator"},
    "ng_intro": {
        "en": "Preview the names the game would generate from a RulePack (factions, map, gravship). Approximate: unresolved symbols show as <symbol>.",
        "it": "Anteprima dei nomi che il gioco genererebbe da un RulePack (fazioni, mappa, gravship). Approssimato: i simboli non risolti appaiono come <simbolo>.",
        "es": "Vista previa de los nombres que el juego generaría desde un RulePack. Aproximado: los símbolos sin resolver aparecen como <símbolo>.",
        "fr": "Aperçu des noms que le jeu générerait depuis un RulePack. Approximatif : les symboles non résolus s'affichent comme <symbole>.",
        "de": "Vorschau der Namen, die das Spiel aus einem RulePack generieren würde. Annähernd: ungelöste Symbole erscheinen als <Symbol>."},
    "ng_filter": {"en": "Filter rulepacks", "it": "Filtra rulepack", "es": "Filtrar rulepacks",
                  "fr": "Filtrer les rulepacks", "de": "Rulepacks filtern"},
    "ng_pack": {"en": "RulePack", "it": "RulePack", "es": "RulePack", "fr": "RulePack", "de": "RulePack"},
    "ng_count": {"en": "How many", "it": "Quanti", "es": "Cuántos", "fr": "Combien", "de": "Wie viele"},
    "ng_gen": {"en": "🎲 Generate", "it": "🎲 Genera", "es": "🎲 Generar", "fr": "🎲 Générer", "de": "🎲 Generieren"},
    "ng_none": {"en": "No rulepack matches the filter.", "it": "Nessun rulepack corrisponde al filtro.",
                "es": "Ningún rulepack coincide.", "fr": "Aucun rulepack ne correspond.", "de": "Kein Rulepack passt."},
    "ng_prev": {"en": "◀ Prev", "it": "◀ Prec", "es": "◀ Ant", "fr": "◀ Préc", "de": "◀ Zurück"},
    "ng_next": {"en": "Next ▶", "it": "Succ ▶", "es": "Sig ▶", "fr": "Suiv ▶", "de": "Weiter ▶"},
    "ng_jump": {"en": "Go to #", "it": "Vai a #", "es": "Ir a #", "fr": "Aller à #", "de": "Gehe zu #"},
    "ng_rules": {"en": "Rules (debug)", "it": "Regole (debug)", "es": "Reglas (debug)",
                 "fr": "Règles (debug)", "de": "Regeln (Debug)"},
}

STATUS_NAMES = {
    "validated": {"en": "validated", "it": "validato", "es": "validado", "fr": "validé", "de": "validiert"},
    "translated": {"en": "translated", "it": "tradotto", "es": "traducido", "fr": "traduit", "de": "übersetzt"},
    "modified": {"en": "modified", "it": "modificato", "es": "modificado", "fr": "modifié", "de": "geändert"},
    "stale": {"en": "stale", "it": "obsoleto", "es": "obsoleto", "fr": "obsolète", "de": "veraltet"},
    "untranslated": {"en": "untranslated", "it": "da tradurre", "es": "sin traducir",
                     "fr": "non traduit", "de": "unübersetzt"},
}

st.set_page_config(page_title="RimWorld translation", page_icon="🌍", layout="wide")

lang = "en"  # impostata dalla navbar in cima alla pagina
def t(key, **kw):
    s = TR[key].get(lang, TR[key]["en"])
    return s.format(**kw) if kw else s
def sname(status):
    return STATUS_NAMES[status].get(lang, status)


def load_rows():
    return list(ledger_mod.load().values())


@st.cache_data(show_spinner=False)
def text_index():
    """(dlc,file,tag) -> (EN source, IT text). Scansione XML una sola volta per
    sessione (cachata); serve a mostrare testo EN e traduzione nella worklist."""
    idx = {}
    for d, f, tag, _line, it, en in ledger_mod.iter_strings(config.repo_root(), config.DLCS):
        idx[(d, f, tag)] = (en, it)
    return idx


# --- navbar in cima (non fixed: scorre con la pagina) ---
nav = st.columns([5, 1.4, 1.7], vertical_alignment="center")
lang = nav[1].selectbox("🌐", list(LANGS), format_func=lambda k: LANGS[k],
                        label_visibility="collapsed")
nav[0].title(f"🌍 RimWorld — {t('title')}")
with nav[2]:
    if st.button(t("rebuild"), use_container_width=True, help=t("rebuild_help")):
        with st.spinner(t("scanning")):
            ledger_mod.build()
        st.cache_data.clear()  # rinfresca anche l'indice testi
        st.success(t("updated"))
st.divider()

@st.cache_data(show_spinner=False)
def load_rulepacks():
    return namegen_mod.load_rulepacks()


def render_progress():
    rows = load_rows()
    if not rows:
        st.warning(t("empty"))
        return
    total = len(rows)
    overall = Counter(r["status"] for r in rows)
    done = overall.get("validated", 0) + overall.get("translated", 0) + overall.get("modified", 0)
    wrong = sum(1 for r in rows if r["lang_flag"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("completion"), f"{done/total*100:.1f}%")
    c2.metric(t("total"), f"{total:,}")
    c3.metric(t("validated_m"), f"{overall.get('validated', 0):,}")
    c4.metric(t("wrong"), wrong)
    st.progress(done / total)

    st.subheader(t("h_states"))
    scols = st.columns(len(ORDER))
    for col, stt in zip(scols, ORDER):
        col.markdown(
            f"<div style='border-left:4px solid {STATE_COLORS[stt]};padding-left:8px'>"
            f"<b>{overall.get(stt, 0):,}</b><br><small>{sname(stt)}</small></div>",
            unsafe_allow_html=True)

    st.subheader(t("h_perdlc"))
    per_dlc: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        per_dlc[r["dlc"]][r["status"]] += 1
    for dlc in config.DLCS:
        if dlc not in per_dlc:
            continue
        c = per_dlc[dlc]
        tot = sum(c.values())
        d = c.get("validated", 0) + c.get("translated", 0) + c.get("modified", 0)
        left, right = st.columns([1, 5])
        left.write(f"**{dlc}**  \n{d}/{tot}")
        right.progress(d / tot if tot else 0)

    st.subheader(t("h_worklist"))
    fcol1, fcol2 = st.columns(2)
    sel_dlc = fcol1.multiselect("DLC", config.DLCS, default=config.DLCS)
    status_opts = ORDER + ["__wrong__"]
    sel_status = fcol2.multiselect(
        t("f_status"), status_opts,
        default=["untranslated", "stale", "modified", "__wrong__"],
        format_func=lambda s: t("wrong_opt") if s == "__wrong__" else sname(s))

    want_lang = "__wrong__" in sel_status
    want_states = {s for s in sel_status if s != "__wrong__"}
    idx = text_index()
    table = []
    for r in rows:
        if r["dlc"] not in sel_dlc:
            continue
        if not (r["status"] in want_states or (want_lang and r["lang_flag"])):
            continue
        en, it = idx.get((r["dlc"], r["file"], r["tag"]), ("", ""))
        table.append({
            "DLC": r["dlc"], "tag": r["tag"], "EN": en, "IT": it,
            t("f_status"): sname(r["status"]), t("wrong"): r["lang_flag"],
        })
    st.caption(t("n_strings", n=len(table)))
    st.dataframe(
        table, use_container_width=True, height=460, hide_index=True,
        column_config={
            "EN": st.column_config.TextColumn("EN", width="large"),
            "IT": st.column_config.TextColumn("IT", width="large"),
            "tag": st.column_config.TextColumn("tag", width="medium"),
        },
    )


def render_names():
    st.caption(t("ng_intro"))
    packs = load_rulepacks()
    ss = st.session_state

    f0, f1, f2 = st.columns([1.2, 2.6, 1])
    dlc_sel = f0.selectbox("DLC", ["—"] + config.DLCS,
                           format_func=lambda d: "★ " + (d if d != "—" else "tutte"))
    flt = f1.text_input(t("ng_filter"), value="Namer")
    count = f2.number_input(t("ng_count"), min_value=5, max_value=60, value=15, step=5)
    keys = [k for k, p in packs.items()
            if (dlc_sel == "—" or p["dlc"] == dlc_sel)
            and (not flt or flt.lower() in k.lower())]
    if not keys:
        st.info(t("ng_none"))
        return

    # --- paginatore: ◀ Prec / vai a # / nome / Succ ▶ ---
    ss.setdefault("ng_idx", 0)
    sig = (dlc_sel, flt)
    if ss.get("ng_sig") != sig:           # reset posizione se cambia il filtro
        ss.ng_idx = 0
        ss.ng_sig = sig
    n = len(keys)
    nav_prev, nav_pos, nav_name, nav_next = st.columns([1, 1.3, 5, 1], vertical_alignment="bottom")
    if nav_prev.button(t("ng_prev"), use_container_width=True):
        ss.ng_idx = (ss.ng_idx - 1) % n
    if nav_next.button(t("ng_next"), use_container_width=True):
        ss.ng_idx = (ss.ng_idx + 1) % n
    ss.ng_idx = max(0, min(ss.ng_idx, n - 1))
    # Sincronizzazione robusta: la posizione canonica e ss.ng_idx. Prima di creare
    # i widget allineo le loro chiavi a ss.ng_idx; le callback riscrivono ss.ng_idx.
    ss.ng_page = ss.ng_idx + 1
    ss.ng_combo = ss.ng_idx

    def _from_page():
        ss.ng_idx = int(ss.ng_page) - 1

    def _from_combo():
        ss.ng_idx = int(ss.ng_combo)

    nav_pos.number_input(f"{t('ng_jump')} (1–{n})", min_value=1, max_value=n, step=1,
                         key="ng_page", on_change=_from_page)
    nav_name.selectbox(t("ng_pack"), range(n), key="ng_combo",
                       format_func=lambda i: keys[i], on_change=_from_combo)
    key = keys[ss.ng_idx]

    g1, g2 = st.columns([1, 5], vertical_alignment="center")
    if g1.button(t("ng_gen"), type="primary", use_container_width=True):
        ss["ng_seed"] = ss.get("ng_seed", 0) + 1
    g2.caption(f"`{packs[key]['file']}`")

    names, root = namegen_mod.generate(packs, key, int(count), seed=ss.get("ng_seed", 1))
    st.code("\n".join(names), language=None)

    with st.expander(f"{t('ng_rules')} · root = [{root}]"):
        lines = []
        for sym, opts in packs[key]["rules"].items():
            for w, exp in opts:
                wt = "" if w == 1.0 else f"(p={w:g})"
                lines.append(f"{sym}{wt} -> {exp}")
        for sym, rel in packs[key]["files"].items():
            lines.append(f"{sym} -> [file] {rel}")
        st.code("\n".join(lines) or "—", language=None)


tab_prog, tab_names = st.tabs([t("tab_prog"), t("tab_names")])
with tab_prog:
    render_progress()
with tab_names:
    render_names()
