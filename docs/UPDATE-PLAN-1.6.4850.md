# Translation update plan — RimWorld 1.6.4850

> Working branch: **`aggiornamento-1.6.4850`** (separate from `master`, merged only when ready
> for release).
> Session document. Status and decisions updated as we go.

## 0. RESUME — start here (last update 2026-06-13)

**Active branch**: `aggiornamento-1.6.4850` (never push to master). Clean working tree,
everything committed (NOT pushed). To resume: `git checkout aggiornamento-1.6.4850`.

### Done in the 2026-06-13 session (all committed)

**Tooling / dashboard — major changes:**
- **Dashboard rewritten in Flask** (`scripts/dashboard/server.py`, replaces the Streamlit
  `app.py`). Run: `.venv\Scripts\python scripts\dashboard\server.py` → http://127.0.0.1:5000
  (or `python scripts\dashboard\start.py`). **Stateless, no cache** (`Cache-Control:no-store`,
  reads CSV+XML fresh per request) — Streamlit's `@st.cache_data` kept showing STALE data, the
  root cause of much confusion. Multilingual (EN default, cookie). Tabs: **Progress/review**
  (per-DLC + per-file tables, click to validate/keep per-string or whole-file, sticky) and
  **Name generator** (Core-first, default filter "Namer", paginator, copyable source file,
  full-width table, dedup with ×N, and a **template column** showing the `[tag]` each part of a
  name comes from). `app.py` (Streamlit) kept but **deprecated**.
- **`namegen` preview upgraded**: now resolves file-backed symbols defined ONLY in the GAME's
  base Defs (e.g. `celestial_name`→`Names/Celestial`, loading the Italian list) + runtime
  `Digit/Letter/RomanNumeral`. Only true runtime person names (`NamePerson`/`ANYPAWN`) stay as
  `<...>`. `generate()` returns `(name, template)` pairs.
- **`rwit ledger` fixed + extended**: `iter_strings` was reading `el.text`, but rulesStrings/
  slateRef hold the IT text in child/grandchild `<li>` → ALL rulesStrings were false-flagged
  untranslated. Now li-aware → **worklist 1634 → ~679 real**. New state **`keep`** (do-not-
  translate: loanwords/proper nouns/format strings, sticky, counts as done) + `rwit ledger keep`;
  `texts_for_file`/`set_status_keys` for the UI. The ~679 IT==EN were all reviewed and marked
  `keep` → dashboard at 100%.
- **`rwit freshness`** (NEW): content check the structural checks missed. (1) base IT vs the
  GAME's English (**heuristic** — IT lists are alphabetised and collapse English synonyms, so a
  line-count diff is usually benign; verify content with `rwit reconcile`). (2) gender-variant
  files vs base (**actionable**: sum of M/F/Vowel/Lo must == base). Auto-warns at end of
  `ledger build`. Lesson: earlier "checked/aligned" meant file PRESENCE + reference resolution,
  NOT content completeness — I'd wired stale variants into the biome namers without verifying.

**LanguageWorker `.cs` — decision finalised:** a pure XML/TXT pack CANNOT load a custom worker
(the game resolves `languageWorkerClass=LanguageWorker_Italian` by name to its BUILT-IN class via
`GenTypes.GetTypeInAnyAssembly`). So the root `.cs` is **never loaded**; it's only an upstream-PR
candidate. Header comment in `LanguageWorker_Italian.cs` documents this + the data-driven strategy.
**Heteroclite question answered from the engine** (no Discord reply needed): the engine
**pluralises FIRST, then `ResolveGender` on the already-pluralised string** (verified:
`WithDefiniteArticle(Pluralize(label), ResolveGender(Pluralize(label)), plural:true)`), so
`plural.txt` + `braccia` in Female.txt yields the right gender — BUT the **stock worker ignores
the `plural` flag for articles** (→ "la braccia", not "le braccia"). That one gap (plural
articles `i/gli/le`, `dei/degli/delle`) is the ONLY thing the `.cs` would fix; everything else is
data (plural.txt) + explicit articles in rulesStrings. The grammar of book titles & namers does
NOT depend on the worker (explicit articles), so it renders as previewed.

**Gender-aware namers (data-driven, French M/F model)** — method: gender-split shared Words
lists wired in `RulePacks_Global` (`ConceptAny/Animal/Color/Game/TerrainFeature/Artwork/...
_Masculine/_Feminine`, + `_Vowel/_Lo` for terrain) generated via **Morph-it!**, gender-consistent
templates, articulated prepositions (`nel/nella/nell'/nelle/nello`), explicit possessive "di".
Done & verified in preview:
- **Namer_Novel** (book titles): fixes adjective agreement, place article (`presso il Rovine`→
  `vicino alle Rovine`, elision `nell'Abisso`), possessive (`Picchio backgammon`→`Compendio di X`).
- **9 biome WorldFeatures namers**: Core (Desert/Ocean/Swamp/TropicalRainforest) + Odyssey
  (GlacialPlain/Glowforest/Grasslands/LavaField/Scarlands). Shared `narrative_name` split into
  `narrative_name_M/F` (+ a neutral one for terrain apposition).
- **NamerArtCommon** (art names): every `[article][adj][noun]` gendered; possessive with "di".
- **NamerArtWeapon**: possessives fixed; full agreement still TODO (needs `*Badass` gender-split).

**Data hygiene (bonifica, guided by `rwit freshness`):** regenerated 28 stale `_Singular_M/F`
variant sets from current base; removed 37 `_Neuter` cruft files (Italian has no neuter, unused);
fixed a malformed comment in `Weapons.txt` (`﻿ // armi da taglio` — space after BOM, the game
could read it as a weapon). Result: 0 stale variants. 5 base-vs-game divergences remain but are
heuristic/benign (verified, e.g. PoliticalUnions already has planetaria/mondiale).

**Other content:** created **`Words/Verbs/Friendly.txt`** (only missing base list vs the game →
was English-fallback for `[VerbFriendly]`) + adapted 4 Tales frames to gerund. Loanword review
(conservative policy): `villain→cattivo`, `busker→musicista di strada`, `camera→telecamera`
(false friend). Anomaly etc. unchanged.

### NEXT STEPS (tomorrow)
1. **Restart the Flask dashboard** after pulling code changes (it auto-reloads, but the first
   time start fresh): `python scripts\dashboard\server.py`. NEVER use the old Streamlit `app.py`.
2. **Remaining gender-aware namers**: NamerArtWeapon agreement (generate `*Badass` gender-split
   first), Scenario (`da il`→`dal`, malformed plurals `armaiolos`), Settlement Pirate/Tribal
   (`Rosso borgata`→`Rossa borgata`), social-log Interactions.
3. **Combat/social log** (the §5.2-ter workstream): explicit articles + gender constraints; the
   only thing needing the worker is plural articles — accept the residual or pursue the upstream PR.
4. **In Dev mode (needs the game)**: verify the generated namer output (book titles, world/biome
   names, art names) and the combat log "le braccia"/"la mano" + `count==1/2/3` branches.
5. Optional cleanup: standardise the gender-variant file naming (`_Singular_Masculine` vs
   `_Masculine`); the few base-vs-game divergences if any turn out to be real (`rwit reconcile`).

**Quick tooling reference**: `rwit --help` · `rwit freshness` · `rwit ledger build|keep|todo`.
Dashboard: `python scripts\dashboard\server.py` (Flask, :5000). Sibling repos:
`RimWorld-fr` (M/F, our gender model) `/de` (M/F/N + cases, fully data-driven) `/Spanish`.
Game install auto-detected (`config.game_data()`); decompiler: `scripts/.tools/ilspycmd.exe`.

## 1. Context

The game was updated to **1.6.4850**. The "Italiano" language folder inside the install is
symlinked to this repo (see `rwit link`), so the in-game **"Clean languages"** command rewrote
the repo files. A fresh `TranslationReport.txt` was generated.

## 2. What "Clean languages" actually changed

Analysed the whole diff (43 files). The changes are **almost all cosmetic**, NOT new
translations:

1. **English typo fixes** inside the `<!-- EN: ... -->` comments (e.g. `fibre→fiber`,
   `courtesean→courtesan`, `enlightment→enlightenment`, `abilites→abilities`…). **The English
   meaning does not change** → the Italian translation stays valid. None require re-translation.
2. **Whitespace normalization** (trailing spaces, last line without newline).
3. The **4 "ancient bridge" TerrainDefs** translated in the previous session — already fine.
4. One real IT change already in the working tree: `<Required>` from *Necessario* → *Richiesto*.

> **Conclusion**: the game diff is noise (EN comments + whitespace). The real work is the
> **quality review** and the **bugs** from the report, not the diff.

## 3. State from the TranslationReport (1.6.4850)

- **Missing Keyed: 0** ✅
- **Missing DefInjected: 0** ✅
- 91 load errors (obsolete backstory/def) → cleanup
- 95 unused keyed (never used) → cleanup
- 109 keyed = English → review (most should be kept: symbols, units, acronyms)
- 9 argument mismatches → 1 real bug + 8 legacy positional

## 4. Branch and commit strategy

To separate noise from real work and keep the review clean:

1. **"Baseline" commit**: the game regeneration (EN comments + whitespace + 4 bridges).
2. **Subsequent thematic commits**: bug fixes, per-DLC review, cleanup.
3. Merge to `master` only when the review is complete.

## 5. Worklist

### 5.1 Confirmed bugs (priority 🔴)
- [x] ~~Malformed ternary in `LetterCatatonicMentalBreak`~~ → **FALSE POSITIVE**. `{0_gender ? o : a : o}`
  is the valid **3-branch** form (masc/fem/neuter-None), confirmed on fr/de/es. No change.
- [x] `"Ma ai le basi adesso"` → `"Ma hai le basi adesso"` + realigned the 5 tutorial steps.
- [x] `"Sei sei sicuro"` → `"Sei sicuro"`.
- [ ] Verify the 8 legacy argument mismatches (positional `{0}` style): mostly ok, confirm they
  do not break.
- [x] 🔴 **Wrong language (French) in Anomaly** — RESOLVED. The "~14" estimate was wrong: with
  `rwit lang-check` found and re-translated **40** FR strings in Anomaly (`Precepts` whole file,
  `Keyed/Misc_Gameplay.xml` UnnaturalCorpse+GoldenCube block, `Tales_Double.xml`, + isolated
  words: `cracheur`→sputatore, `noctolithe`→noctolite, typo `difdeforme`→contorta). 2 Italian
  false positives remain (`Carne del revenant`, `una figura indistinta`).
- [x] **Per-string wrong language in other DLCs**: triage done. The ~19 fr hits are almost all
  **Italian false positives** ("revenant"/"menù" fool `lingua`). No action.
- [x] 🟠 **Two whole FR Namer files (Odyssey)** → RESOLVED. Found with `rwit lang-check --files`;
  rebuilt for Italian grammar from the EN source (not translated from French), verified in
  preview. (Deity_Names, Xenohumans, Genepacks, Biosignatures match FR but are **neutral
  invented syllables** — not touched.)

> **NEW TOOLING (this session)** — all in `scripts/rwit/`, offline, zero LLM tokens: see §0.
> Current state: **95.2%** done, 1634 to translate/equal-to-EN, out of 34,033 strings.

### 5.2 Broad review (decided with the maintainer)
A quality pass file by file, per DLC, on naturalness/idioms/terminology consistency. Criterion:
fix **imprecisions too**, not just errors (e.g. "crushed" → "schiacciati", not "distrutti").
See `docs/TRANSLATION-SYNTAX.md` and `docs/CONTRIBUTING.md`.

Suggested order (by impact/visibility): `Core/Keyed` → `Core/DefInjected` → DLC: Royalty →
Ideology → Biotech → Anomaly → Odyssey. For each file: `[VAR]`/`{VAR}` intact, `->` in
rulesStrings, `\n\n` preserved, valid gender ternary, `<!-- EN: -->` comments unchanged.

### 5.2-bis Names, plurals and grammar (workstream)
See [`NAME-GENERATION-AND-GRAMMAR.md`](NAME-GENERATION-AND-GRAMMAR.md).
- [x] Decompiled `LanguageWorker_Italian` from the DLL; improved `.cs` in root (signatures verified).
- [x] **Faction Namers rewired** with gender agreement (Core/Odyssey/Biotech) + variants generator.
- [x] **`WordInfo/plural.txt`** created (heteroclite body parts) + ~60 body parts in `Gender/`.
- [ ] WordInfo/Gender: remaining English (fix at the `.label`), doubtful (-e) genders.
- [ ] Strings: align lists to the game's English (`rwit reconcile`); the legacy positional pairs.

### 5.2-ter Generated log (combat/social) — priority objective
See [`NAME-GENERATION-AND-GRAMMAR.md`](NAME-GENERATION-AND-GRAMMAR.md) §5. Measured root cause:
**it 1 gender constraint vs fr 122 / es 100 / de 95**. Strategy (all text files, data-driven):
`(X_gender==Male/Female)` constraints + `[X_definite]` suffixes + `WordInfo/Gender` and
`plural.txt`. Works with the stock worker.
- [x] Body parts in `WordInfo/Gender` + irregular plurals in `WordInfo/plural.txt`.
- [ ] Template pack `Combat_Deflect` with gender constraints (template = fr pack); verify in Dev mode.
- [ ] Scale: CombatMelee → CombatRanged → Damage → Maneuvers → social Interactions.
- [ ] Tooling: `rwit wordinfo` (Gender/plural from Morph-it!), `rwit compare` (it↔fr↔es↔de).

### 5.3 Cleanup (priority 🧹)
- [x] Obsolete backstories: 6 fully-UNUSED files removed + single entries (~70 load errors).
- [x] Def inject-errors **removed** (verified absent in the 1.6.4850 Defs).
- [ ] **To handle with verification** (RENAMED/MOVED defs, not removed → no blind deletion):
  `NoInteraction`, `CompReloadable.chargeNoun`, `CompStatEntry`, sensors. Candidates for `rwit clean`.
- [ ] **95 unused keyed**: NOT removed in bulk — some are actually referenced. Needs `rwit clean`.
- [ ] Review the 109 keyed = English: most should be kept (symbols/units/acronyms).

## 6. Documentation for future developers (this session)

- `CLAUDE.md` (root, tracked): project instructions, personal paths removed, points to the docs.
- `docs/CONTRIBUTING.md`: env setup, workflow, `rwit` tooling.
- `docs/TRANSLATION-SYNTAX.md`: allowed syntax (gender ternary, variables, rulesStrings, `\n\n`, elision).
- `docs/RULEPACK-GRAMMAR.md`: full RulePack language (conditions, counts, weights, combat log).
- `docs/REFERENCES.md`: reference repos (fr/es/de), WordInfo strategy, Ludeon links.
- `docs/LOCAL-TOOLING.md`: local/offline tooling strategy (Morph-it!, embeddings, local LLM as finder).
- `docs/VALIDATION.md` + `docs/VALIDATION-FILES.csv`: file validation tracking and the integrity note.
- `docs/UPDATE-PLAN-1.6.4850.md`: this file.

## 7. Progress

| Phase | Status |
|-------|--------|
| Branch `aggiornamento-1.6.4850` created | ✅ |
| Game diff analysis | ✅ |
| Docs for future developers | ✅ (English) |
| CLAUDE.md tracked and cleaned | ✅ |
| Confirmed bugs | ✅ |
| Wrong-language cleanup (Anomaly FR + Odyssey Namers) | ✅ |
| Name/grammar workstream (tooling + Namers rewired + WordInfo) | ✅ |
| LanguageWorker decision (data-driven) | ✅ |
| Combat log (plural.txt + Gender) | ✅ data; ⬜ in-game verify |
| Cleanup rename/unused keyed (→ `rwit clean`) | ⬜ tooling |
| Broad translation review (iterative, per DLC) | 🔄 in progress |
| Merge to master | ⬜ at release (never direct push) |
