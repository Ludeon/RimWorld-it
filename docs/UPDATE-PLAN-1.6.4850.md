# Translation update plan — RimWorld 1.6.4850

> Working branch: **`aggiornamento-1.6.4850`** (separate from `master`, merged only when ready
> for release).
> Session document. Status and decisions updated as we go.

## 0. RESUME — start here (last update 2026-06-25)

### Since 06-23 (committed)
- Namer review continued (Ideology roles/factions/places ordering + FR residuals + validations),
  `rwit namegen` injects the implicit `r_name->[terrain_word]` default, dashboard got
  validation-state badges + confirmation toasts in the Name-generator tab.
- **The translation itself is complete.** `rwit ledger todo` = 0. The remaining workstream is the
  **validation pass** (promote `translated → validated`): see the roadmap in **§5.4**.
- Ledger 2026-06-25: 34,034 strings — **161 validated · 677 keep · 33,196 to validate**. RulePackDef
  name-generators are essentially validated (all 161 validated rows are RulePackDef). Now starting
  **Phase A — backstories**, file `Core/DefInjected/BackstoryDef/Solid_Child.xml` (prose, in blocks).

**Active branch**: `aggiornamento-1.6.4850` (never push to master). Everything committed (NOT
pushed). To resume: `git checkout aggiornamento-1.6.4850`. **A second session works in parallel**
on Core namers (People/Scenarios/Outlander/settlements + `Strings/WordParts/Syllables`); always
`git add` your own files explicitly, never `git add -A`.

### Also done 2026-06-25 (this session)
- **Dead `baseDesc` cleanup**: in RW 1.6 backstories are `BackstoryDef` and the shown text is
  `<description>` (inherited from `Def`); the old `<baseDesc>` is no longer a Def field, so those
  injections were phantom strings the game never read (confirmed: game Defs + official FR/DE/ES×2
  ship `.description`, zero `.baseDesc`). New tool **`rwit strip-basedesc`** removed ~825 dead lines
  across 23 `*/DefInjected/BackstoryDef/*.xml`. When validating a backstory file, only
  `description`/`title*` are the live fields.
- **Games pluralia tantum in the Scenari namer**: `i dadi` / `gli scacchi` / `le carte` couldn't fit
  the singular `Game_Masculine/Feminine` (those feed `[maybe_am]`/`[transM]` = singular il/la-class).
  Wired 3 article-class plural files (`Games_Plural_Masculine` //i, `Games_Plural_Masculine_Gli` //gli
  *(new)*, `Games_Plural_Feminine` //le) + symbols in `RulePacks_Global` + branches in
  `RulePacks_Namers_Scenarios` with a **new `transPluralGli`** (degli/negli/sugli…) alongside
  `transPluralM`(dei) / `transPluralF`(delle). NB the file `//` header is **documentation only** —
  the article comes from the template's `trans*` symbol, not the header. `freshness` now counts the
  plural axis as a *residual* (guarded, no double-count) → **0 variant stale**. Verified via `namegen`.
- `Solid_Adult.xml` validated in `VALIDATION-FILES.csv` (live fields clean).

### 2026-06-26 (this session, Core console)
- **Phase A — `Solid_Child.xml` validation COMPLETE**: whole file reviewed in ~20-entry blocks and
  validated (1074 strings → `validated`, 0 left). **Next file**: continue `docs/VALIDATION-FILES.csv`
  in order — `Solid_Adult` already done, so next is `Solid_Rare`/`Special`, then `Tribal_*` etc.
- ⚠️ **Shared-CSV race observed**: midway, the other console's `ledger build` clobbered the
  validations written after its read (blocks from `RitualChild20` on reverted to `translated`).
  Recovered with a final `rwit ledger validate --file Solid_Child.xml --yes`. Lesson: after a parallel
  `ledger build`, re-run the per-file validate to confirm it stuck (`--list` should show 0).
- Content fixes committed (2 commits): slash forms `lo/la`/`preso/a` → ternaries; many fixed-gender
  adjectives/nouns (`pessimo`, `privo`, `pigro`, `l'eroe`, `neonato`, `scienziato`/`scienziata`
  titles, `lo costrinse`, `inviato`); a `Sebbene`+indicativo → congiuntivo; `mondo/pianeta` title
  coherence; one `\n\n` not in EN removed. **`GlitterworldKid85` was a full mistranslation** (wrong
  story) → retranslated to match the EN comment.
- ⚠️ **Shared ledger CSV not committed**: it interleaves this console's `Solid_Child` validations with
  the other console's `Solid_Adult` rows (other console committed `Solid_Adult.xml` but not the CSV).
  Validations are safe on disk (dashboard reads disk); commit the CSV in a coordinated `tooling()` step.

### 2026-06-26 (Keyed pass — Core console)
- **`Core/Keyed/Misc_Gameplay.xml` validation COMPLETE**: intero file riletto (2191 righe, IT↔EN);
  linter puliti. 27 fix in 1 commit `content(core)`: refusi (`recovero`,`alimali`,`appartieneva`,
  `deterioramente`); token rotti (`{0_nomeDef}`→`{0_nameDef}`, `{PAWN_possessive}`→`{PAWN_pronoun}`);
  falsi sensi (`Passaggio per il paradiso`/offworld, `Hackerare i progressi`, `Roped*` non "in sella",
  `Congelato`→`Refrigerato`); divergenze EN (CaravanDetectedRaidCountdownTip, RitualEndsIn `tra`,
  LordReportAttending, …); `avvenimento`→`avviamento`; `\n\n` ripristinati. Validato **962 voci**
  (scoping `--dlc Core` per non toccare le copie Anomaly/Biotech/Odyssey). CSV committato a parte.

### NEXT SESSION — TODO (priority order)
1. **Art namer plurals** (`RulePacks_Namers_Art.xml`): same treatment as the Scenari namer above, but
   Art needs the plural *indefinite* article (dei/degli/delle/∅) + **plural adjective agreement**
   (`maybe_adjective_mp`/`_fp` from the existing `*_Plural_Masculine/Feminine` adjective lists). Today
   Art still uses only the singular `Game_Masculine/Feminine`.
2. **Validation pass — Phase A backstories** (§5.4): keep walking `docs/VALIDATION-FILES.csv` in file
   order. `Solid_Adult` done; `Solid_Child` in progress on the other console. **Partition to avoid
   collisions**: one console owns Core, the other owns the DLCs' `DefInjected`.
3. **In-game tests** (needs the game): combat log `le braccia`/vowel elision after `nel/al`,
   `[WEAPON_indefinite]`/`[recipient_partN_definite]` resolution, namer output.
4. **Data-model residuals**: `[PersonalCharacteristic]` article; `di`+article fusion in the 6 Ideology
   Speech packs (`di il`→`del`).
5. **Cleanup**: remove the now-unused `Games_Singular_*` variant cruft (the live split is
   `_Masculine`/`_Feminine`; `_Singular_*` is unreferenced and was misleading).

### Done in the 2026-06-22/23 session (all committed)

**In-game namer review (driven screen-by-screen in the Ideoligion editor) — fixes:**
- **Role names** (`RulePacks_Ideo_Role`): the `[firstPart][secondPart]` glue gave "Bossoloocchio".
  Ported the FR model → `[secondPart] [firstPart]` (agent noun + prepositional complement),
  all firstParts → "dei bossoli"/"delle foglie"…, junk English suffix secondParts → real agent
  nouns. Now "Occhio dei bossoli", "Tiratore della mira".
- **Ritual names** (Festival/Funeral/Duel/Sacrifice/Mutilation): `[noun] [memeAdjective]` with
  mixed-gender noun lists gave "Fiera santo". Gender split (ES model, **no weight-zeroing, no name
  lost**): `[noun_M] [memeAdjective]` + `[noun_F] [memeAdjectiveFem]`; genitives on a general
  `[noun]` indirecting to both pools; `[chosenAdjective]` constrained to masculine nouns.
- **ideoName** (Structure_Ideological): bare "Etica" → doctrine `-ismo` like FR/ES:
  Eticismo/Ideologismo/Giustizialismo.
- **Deity titles** (`Memes_Structures_OriginsReligious`): "Creatore di l'universo" → moved the
  preposition into the values (`Creatore [all]` + `all->dell'universo`) → "Creatore dell'universo".
- **Relic names** (`RulePacks_Ideo_Relic`): `[first][second]` glue ("Lungoevocatore") → ES-style
  `[first] [second]` (evocative head + "di/d' X" complement, elision pre-resolved: "Eco di fuoco",
  "Manto d'ombra"); gender split relic_M/_F fixes "Eredità aperto" → "aperta". Known residual (as
  ES): `[thingLabel] [memeAdjective]` ("Fucile aperto") — runtime item gender, needs DE-style
  machinery.
- **lang-check / args-check pass**: fixed `stat{i}`→`stati` (Royalty Hospitality), 3 Spanish
  leftovers (`chatarra`→rottami, `carroñero`→spazzino in Ideology Places). Confirmed the remaining
  lang-check (32) and args-check (70) are all false positives (loanwords, proper nouns,
  name-for-pronoun, EN `UNUSED`/truncated comments, FR-validated `{1_gender}` indices).

**Dashboard review progress**: at **page 21** of the Name-generator paginator (resume there).

**New dev tool — `LangLive` mod** (separate repo `../LangLive`, MIT, packageId `b4p3p.langlive`):
live-reloads the active language in-game so edits show without restarting. Native reload via
`LanguageDatabase.SelectLanguage` (correct for Keyed+Strings+DefInjected, no unsafe reflection).
Auto-detects the active language folders (no config). **Guard: only reloads in `ProgramState.
Playing`** — a reload during the new-game/ideoligion setup runs ClearAllPlayData and WIPES the
in-progress config (learned the hard way). `install.ps1`/`install.sh` for one-command install.
Inspired by lordfanger/RimLanguageHotReload (unlicensed upstream → not forked). v1.1 roadmap:
fast per-file Keyed/Strings reload (no loading screen).

> **Reusable recipe** for a gender-aware namer (use this for any remaining one):
> 1. Need gender-split noun lists? `rwit variants noun-gender <List>` → `<List>_Singular_
>    Masculine/Feminine.txt` (Morph-it! + ending heuristic). Adjectives: `rwit variants adj`.
> 2. Wire the `_Masculine/_Feminine` symbols in `RulePacks_Global` (or local `<rulesFiles>` in
>    the pack, like NamerQuestDefault).
> 3. Make each template branch internally one-gender: `[X_Masculine] [adjM]` / `[X_Feminine]
>    [adjF]`; articulated prepositions per class (`nel/nella/nell'/nelle/nello`); explicit "di".
> 4. **Verify** with `namegen.generate(packs, key, context={...})` — for the combat/social log
>    pass a `context` with sample `_gender`/`_definite`/`_label` values (the simulator).

### Done in the 2026-06-13/14 session (all committed)

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
- **NamerArtCommon** + **NamerArtWeapon** (art names): every `[article][adj][noun]` gendered;
  possessive with "di"; ArtWeapon uses `*Badass_M/F` lists. Art group complete.
- **NamerScenario**: fixed preposition+article fusion (`[Trans] il`→`del/dal/nel/sul`, +F/Vowel/
  Plural), the English-plural bug (`[PersonJob]s`→`armaiolos` → `PersonJob_Plural_M/F` with
  `dei/delle`), and a malformed rule (`r_name>una`, missing `->`).
- **NamerSettlementPirate/Tribal**: the `[Color] [TerrainFeature]` agreement (`Rosso borgata`→
  `Rossa borgata`); appositions kept.
- **NamerQuestDefault**: `[questMasc] [adjCuriousMasc]` / `[questFem] [adjCuriousFem]` (noun→adj,
  local `<rulesFiles>` in the pack; lists via `rwit variants noun-gender`).
- **New tool `rwit variants noun-gender <List>`** — splits a noun list into `_Singular_
  Masculine/Feminine` (formalises the ad-hoc split used in the bonifica); morphit gained an
  Italian ending heuristic (`-a/-zione/-tà…`) as a fallback.

⚠️ **Lesson — the bonifica had wrongly split `Colors`/`Colors_Badass` as NOUNS** (all masc, fem
empty → "Grigio valle"). They're ADJECTIVES (each colour needs both forms). Fixed + `rwit
freshness` now also flags an EMPTY gender side (the noun-sum check alone missed it: M=base, F=0).

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
2. **Combat/social log** (the §5.2-ter workstream) — STARTED & now VERIFIABLE:
   - **namegen got a combat-context simulator**: it parses rule constraints `(X_gender==Male/
     Female)` and accepts a `context=` dict (sample `RECIPIENT_definite`, `recipient_part0_label/
     _gender`, `TOOL_definite/_gender`…) → you can finally verify the log's agreement OFFLINE
     (before, the runtime symbols showed as `<...>`).
   - **Combat_Deflect done as the verified template** (`RulePacks_CombatMelee.xml`): recipe =
     `(recipient_part0_gender==M/F)` → `nel/nella [part]`; `[TOOL_definite]` for the weapon
     article (engine uses our WordInfo/Gender, already huge: 2074 M / 1029 F); adjective split by
     `(TOOL_gender==M/F)` (`la spada è sfiorata` vs `il coltello è sfiorato`); dropped the wrong
     "a" (transitive verb). Verified for both genders via the simulator.
   - **Combat_Hit done (2026-06-14)**: same `nel/nella [recipient_part0_label]` split by
     `(recipient_part0_gender==M/F)`, verified offline (was hardcoded `nella` → "nella braccio").
   - **CombatRanged possessive bug fixed (2026-06-14)**: `Combat_RangedFire`/`_Thrown` used
     `il/la [WEAPON_label] di [INITIATOR_possessive]` / `[projectile] …` — but `[X_possessive]`
     is the **pronoun** → "di suo/sua" (wrong) and `il/la` showed literally. Adopted the **FR
     model**: `[WEAPON_indefinite]` / `[projectile_indefinite]` (engine supplies the article from
     gender, RW≥1.4); dropped the fixed article from `shot_a`/`threw_a`, restricted `shot_a` to a
     transitive verb (`ha sparato`). ⚠️ Needs **in-game confirm** that `[WEAPON_indefinite]`/
     `[projectile_indefinite]` resolve (FR ships them, so expected OK).
   - **WHOLE melee + ranged combat log DONE (2026-06-14)** — found & fixed **three systematic
     bugs** (all solved by porting the **FR** model; verified offline with the simulator):
     1. **Missing auxiliary**: `[INITIATOR] [damaged_past] [RECIPIENT]` rendered "Ursula ferito
        Cassio" — `[damaged_past]`/`[destroyed_past]` resolve to a BARE participle (from
        `RulePacks_Damage`/`_Maneuvers`); the aux goes in the TEMPLATE (FR: `a [damaged_past]`).
        Added `ha` to every active line.
     2. **`damaged_inf` is an INFINITIVE in IT** ("colpire", from `RulePacks_Maneuvers`): the
        noun-uses (`il [damaged_inf]`, `con un [damaged_inf]`) gave "il colpire" → restructured to
        infinitive (`che cercava di [damaged_inf]`) or replaced with `[implement]`.
     3. **`[X_possessive]` = "suo/sua" (no article, genderless)**: `[implement]` was
        `[INITIATOR_possessive] [WEAPON_label]` ("suo fucile") → now `[WEAPON_indefinite]`/
        `[TOOL_definite]`; `di [RECIPIENT_possessive]` → `di [RECIPIENT_definite]` or "sulla sua
        armatura"; part lists now use `[recipient_partN_definite]` (engine article: "il braccio"/
        "l'occhio").
     Also: **passive `è stato [damaged_past]` converted to ACTIVE** (IT can't append a gender
     suffix to the participle like FR's `[damaged_past]e`/`s`; `avere` avoids agreement entirely),
     fixed/full files: `RulePacks_CombatMelee` (Hit/Deflect/Dodge/Miss), `RulePacks_CombatIncludes`
     (implement/targetlist/wound-targets/result/wince/FailIncludes), `RulePacks_CombatRanged`
     (RangedDamage/ExplosionImpact/RangedDeflect; RangedFire/Thrown were done earlier).
   - **Social Interactions DONE (2026-06-14)** — swept ALL interaction logs (RulePackDef
     `Sentence_*` + InteractionDef `*.logRulesInitiator`) across Core + Royalty + Ideology +
     Biotech + Anomaly. Same bug classes + a few interaction-specific ones, all fixed:
     - **missing/auxiliary**: bare participles → `ha [v]`; **plural subject** (`[INITIATOR] e
       [RECIPIENT] [v]`) → `hanno [v]` (Chitchat/DeepTalk/SanguophageChat); verb symbols normalised
       to bare participles (were mixing `ha …`/imperfect/adjective).
     - **gender (essere)**: `era attratto`/`è riuscito`/`(non) è stato convinto`/`coinvolto` →
       split by `(RECIPIENT_gender==M/F)` or reworded to `avere` (no agreement).
     - **possessive `[X_possessive]`**: → `di [nameDef]` / `la propria …` / `le proprie qualità` /
       fixed-gender `la sua armatura`/`la sua crisi`; objective `[X_objective]` → `[nameDef]` or
       `tra sé e sé`; one botched `[RECIPIENT_possessive]del suo` (Anomaly) → `del suo`.
     - **prepositions/typos**: `detto su`→`parlato di`, `collare [nome]`→`collare a`, double-article
       `ai [problems]`, double-`di` (`di del`/`di degli`), invented symbol `pigro[RECIPIENT_o_a]`→
       ternary, `disloyalty`/untranslated, typo `esiguto`→`imposto`, tense (`accarezza`→`ha
       accarezzato`, `afferrò`→`ha afferrato`).
     - **genitive topics** (Anomaly `subjectDarkStudy`/`Insane` = `degli horax`/`dei fallimenti`;
       Ideology Speech): templates de-prepositioned (`a proposito [topic]` / `ha parlato [topic]`)
       to avoid `di degli`/`su degli`.
     Ideology `Interactions_Slave` was already clean. **Known residuals (documented, need data
     work, NOT bugs introduced now):** (1) **`[PersonalCharacteristic]`** article — shared
     mixed-gender Words list used in possessive+object+namer contexts → can't add article → e.g.
     "ha insultato eleganza di X" (missing l'). (2) **`di`+definite-article fusion** in 6 Ideology
     Speech packs with article-topics (AcceptRole/Blinding/Conversion/Execution/Funeral/Leader):
     "ha parlato di il …" instead of "del" — needs per-topic genitive conversion.
   - `RulePacks_DamageEvent`/`_Maneuvers` spot-check still pending (Maneuvers holds the
     `damaged_inf`(infinitive)/`damaged_past`(participle) lists — confirmed consistent for combat).
   - ⚠️ **In-game confirm needed**: that `[projectile_definite/indefinite]`, `[WEAPON_definite/
     indefinite]`, `[recipient_partN_definite]` all resolve (FR ships them on RW≥1.4 → expected
     OK). Residual: vowel-initial parts after `nel/al` (no Vowel constraint exists → "nel occhio"
     not "nell'occhio"); plural articles (`le braccia`) still need the upstream `.cs`.
   - Verify pattern: `namegen.generate(packs, "...· Combat_X", context={...})` passing the runtime
     symbols (`damaged_past='ferito'`, `damaged_inf='colpire'`, `implement='una spada'`,
     `recipient_part0_gender/_label`, `projectile_definite`…). Space-before-comma in sim output is
     an artifact (EN has the same structure; the engine normalizes).
3. Other namers if any remain (done: Namer_Novel, 9 biomes, Art ×2, Scenario, Settlement
   Pirate/Tribal, QuestDefault, factions). Spot-check the People/Animal/Trader/World namers for
   any residual `[adj] [noun]` agreement; most are appositions/proper names and already fine.
4. **In Dev mode (needs the game)**: verify the generated namer output (book titles, world/biome
   names, art names) and the combat log "le braccia"/"la mano" + `count==1/2/3` branches.
5. Optional cleanup: standardise the gender-variant file naming (`_Singular_Masculine` vs
   `_Masculine`); the few base-vs-game divergences if any turn out to be real (`rwit reconcile`).

**Quick tooling reference**: `rwit --help` · `rwit freshness` · `rwit ledger build|keep|todo` ·
`rwit syntax-check` · `rwit gender-check` (concordanza di genere, §5.4).
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
- [x] Verify the legacy argument mismatches (positional `{0}` style): `rwit args-check` triaged
  them; the certain bugs were fixed (incl. `stat{i}`→`stati`), the remaining ~70 are confirmed
  false positives (name-for-pronoun, EN `UNUSED`/truncated comments, FR-validated `{N_gender}`).
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
- [x] Template pack `Combat_Deflect` with gender constraints (template = fr pack) — done + verified
  offline with the namegen combat-context simulator.
- [x] Scale: CombatMelee → CombatRanged → Damage → Maneuvers → social Interactions — **DONE**
  (whole melee+ranged combat log + all social interaction logs, 3 systematic bugs fixed via the FR
  model; see §0 of the 06-13/14 session). ⬜ remaining: **in-game Dev-mode confirm** only.
- [ ] Tooling: `rwit wordinfo` (Gender/plural from Morph-it!), `rwit compare` (it↔fr↔es↔de).

### 5.3 Cleanup (priority 🧹)
- [x] Obsolete backstories: 6 fully-UNUSED files removed + single entries (~70 load errors).
- [x] Def inject-errors **removed** (verified absent in the 1.6.4850 Defs).
- [ ] **To handle with verification** (RENAMED/MOVED defs, not removed → no blind deletion):
  `NoInteraction`, `CompReloadable.chargeNoun`, `CompStatEntry`, sensors. Candidates for `rwit clean`.
- [ ] **95 unused keyed**: NOT removed in bulk — some are actually referenced. Needs `rwit clean`.
- [ ] Review the 109 keyed = English: most should be kept (symbols/units/acronyms).

### 5.4 Validation roadmap — next sessions (from 2026-06-25)

The translation is complete; what remains is the **quality/validation pass** that promotes
`translated → validated` in the ledger. State at 2026-06-25: **33,196 to validate** (161 done).
Too large to eyeball string-by-string, so combine three modes (leverage before brute force):

1. **Automated lint sweep (whole corpus, once).** Checker for the recurring bug classes: fixed
   article/adjective before a `{gender ? o:a}` suffix (e.g. `un bravo cadett{o:a}` → wrong for
   female), malformed ternaries (`>1 ?`/`:`, redundant `{e:e}`), broken `\n\n`, residual FR/EN,
   `[VAR]`/`{VAR}` integrity. Most exists already (`rwit lang-check`/`args-check`/`syntax-check`);
   **add a gender-agreement check**. Fix the real hits, then the files validate fast.
2. **Human prose review (high-visibility files only).** Read in blocks, fix naturalness + gender,
   validate in the dashboard. Reserve for player-facing narrative.
3. **Bulk-validate short labels (low risk).** Single-word/short-label defs — once the lint is
   clean, validate whole files from the dashboard without per-string reading.

**Phased order (by visibility/impact, resumable):**

| Phase | Content | ~strings | Mode |
|-------|---------|----------|------|
| **A** (in progress) | BackstoryDef: `Solid_Child` → `Solid_Adult` → `Solid_Rare`/`Special` → `Tribal_*` → `Offworld_*` → `Pirate`/`Outsider` → Royalty `Imperial*` → Anomaly | 4,157 | prose, blocks |
| **B** | ThoughtDef (Ideology 1001 → Core 847 → Biotech → Anomaly → Royalty → Odyssey) | 2,384 | lint + quick confirm |
| **C** | Keyed/UI (Core 4787 → Biotech → Ideology → Anomaly → Odyssey → Royalty) | 8,096 | lint placeholders + fast read |
| **D** | Def descriptions (Thing/Gene/Precept/Meme/Hediff/Incident/Tale/QuestScript) | ~10k | prose on `<description>`, bulk on `.label` |
| **E** | Short labels left (Body/Stat/Skill/Color/Recipe/categories…) | ~8k | lint + bulk-validate |
| **F** | Remaining RulePackDef + **in-game Dev-mode confirm** (combat/social log, namer output, §5.2-ter) → merge to master | — | needs the game |

**Per-session protocol:** (1) start `server.py`, pick the next file in the phase order; (2) optional
lint sweep on that file/phase → fix real hits, commit `content(<dlc>): …`; (3) review block-by-block
(prose) or whole-file (labels), validate in the dashboard (writes the CSV); (4) commit the ledger CSV
+ content fixes, update §0 RESUME with the file reached.

**`rwit gender-check` (NEW, 2026-06-25) — the gender-agreement linter.** Flags a FIXED gendered
article/adjective (un/il/del/nel/bravo…) left in front of a construct that flips gender
(`radice{VAR_gender ? o:a}` or `{VAR_gender ? uomo:donna}`) → one of the two renders is
ungrammatical (e.g. "un guerriera", "un donna", "il la propria figlia"). Skips article-only
ternaries (`{gender ? lo:la}`/`{un:una}`) so the clitic FP "Questo {lo:la}" is not flagged.
First run on the whole corpus: **5 real bugs, 0 false positives**, all fixed (`Solid_Child` ×4,
`Pirate_Adult`, `MechanoidNerd10`, `VatgrownAssassin20`, `AcademyStudent58`). Run per file/phase
before validating; the buggy form is usually in `.description` while the `.baseDesc` sibling is
already correct (move the article inside the ternary: `{gender ? un guerriero:una guerriera}`).

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
| Gender-aware namers (Novel, 9 biomes, Art×2, Scenario, Settlement, Quest, factions) | ✅ verified in preview |
| Tooling: Flask dashboard, `rwit freshness`, `variants noun-gender`, namegen constraints+context | ✅ |
| Data hygiene (gender variants regenerated, `_Neuter` cruft removed, Colors fixed) | ✅ |
| Combat/social log gender-aware | ✅ whole melee+ranged + social interactions (verified offline) |
| Ideoligion namers (roles, rituals, deity, relics, ideoName) gender/agreement | ✅ 2026-06-22/23 |
| Combat log in-game verification (Dev mode) | ⬜ needs the game |
| `LangLive` live-reload dev mod (separate repo) | ✅ built + guarded (`Playing` only); v1.1 fast-path TODO |
| Cleanup rename/unused keyed (→ `rwit clean`) | ⬜ tooling |
| RulePackDef namers validated (via Name-generator tab) | ✅ 161 validated rows |
| Validation pass `translated → validated` (roadmap §5.4) | 🔄 Phase A — `Solid_Child` baseDesc stripped (1547→1247), first block reviewed+validated; **213 validated** total |
| Merge to master | ⬜ at release (never direct push) |
