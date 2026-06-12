# Piano di aggiornamento traduzione — RimWorld 1.6.4850

> Branch di lavoro: **`aggiornamento-1.6.4850`** (separato da `master`, si fonde solo a rilascio pronto).
> Documento di sessione. Stato e decisioni aggiornati man mano.

## 0. RIPARTENZA — riprendere da qui (ultimo aggiornamento 2026-06-12, sessione sera)

**Branch attivo**: `aggiornamento-1.6.4850` (mai pushare su master). Working tree pulito,
tutto committato. Per riprendere: `git checkout aggiornamento-1.6.4850`.

### Fatto in questa sessione (tutto committato)

**Tooling `rwit` (Python, offline) — molto ampliato:**
- `lang-check [--files]` — rileva lingua sbagliata per-stringa e **interi file** copiati
  (lingua + match cross-repo + margine). Trovò il francese in Anomaly e i 2 Namer Odyssey.
- `ledger` (build/stats/validate/todo/report) — registro versionato `scripts/dashboard/
  translation-ledger.csv` (stati untranslated/translated/validated/stale/modified).
- `strings-diff` — liste `Words/Names` IT vs **inglese del gioco** (mancanti/non tradotte/corte).
- `reconcile [--fix-glosses]` — pulizia riga-per-riga (glosse inglesi, voci EN, mancanti).
- `variants` (adj/noun) — genera le varianti morfologiche (genere/numero/articolo) via **Morph-it!**.
- `morphit.py` — morfologia IT da **Morph-it!** (`scripts/.tools/morph-it.txt`, gitignored;
  URL di download nel docstring) + fallback a regole. Validato 37/37 sugli aggettivi.
- **Dashboard** (`scripts/dashboard/`, Streamlit, multilingua): tab **Progresso** +
  **Generatore nomi** (anteprima offline dei RulePack, con filtro DLC, paginatore, debug regole).
  `namegen.py` = mini-motore che simula la generazione nomi.

**Contenuto (traduzioni/grammatica):**
- **Anomaly**: 40 stringhe francesi ritradotte (Precepts, UnnaturalCorpse/GoldenCube, Tales…).
- **Namer fazione ricostruiti con accordo di genere** (verificati in anteprima):
  Odyssey (Factions, Gravship: FR→IT), Core (Tribal, Pirate, Outlander), Biotech
  (OutlanderPig, PirateWaster, TribalNeanderthal). Royalty (Empire/Refugee) erano già ok.
- Metodo Namer: tracce maschile (`I/Gli`) / femminile (`Le`) + aggettivi/colori concordi;
  `di`/apposizione per il genere misto; varianti `_I/_Gli/_Le` e `_Plural_Masculine/Feminine`
  generate da `rwit variants` e cablate nel `RulePacks_Global.xml`.
- `PoliticalUnions_Tribal` completata 6→13; glosse pulite; varianti aggettivi rigenerate.
- **WordInfo (log combattimento)**: creato `plural.txt` (eteroclite: braccio→braccia, ossa,
  ginocchia, dita, labbra) + ~60 parti del corpo in `Gender/` (mano=F, pelle=F, piede=M…) +
  forme plurali eteroclite in `Female.txt` (per `ResolveGender("braccia")`=F → "le braccia").

**Docs**: nuovo `docs/RULEPACK-GRAMMAR.md` (EN, completo: condizioni `(count==N)`/genere,
pesi, log combattimento). Doc tecnici rinominati in inglese (riutilizzabili da tutti i team).

### Decisione strategica chiave — LanguageWorker: **via DATI (stile tedesco), `.cs` opzionale**

Decompilato il worker italiano **di serie**: è già capace (articoli singolari `il/lo/l'/la`,
`un/uno/una/un'` dal genere; `Pluralize` legge `WordInfo/plural.txt`). Il **tedesco non ha
`.cs`** → tutto dati WordInfo. **Decisione: andiamo data-driven.** Articoli/plurali li
controlliamo via `WordInfo` (Gender + plural.txt) e via le `rulesStrings` (articoli espliciti
+ varianti per genere). Il `.cs` migliorato (root, firme verificate contro base e spagnolo)
resta **bonus opzionale** per gli edge, da valutare per una PR upstream — **non** prerequisito.

- **Eteroclito "le braccia"**: il motore ha `LanguageWordInfo.ResolveGender(stringa)` che
  legge `WordInfo/Gender`. Setup data-only **già in place** (plural.txt + `braccia` in
  Female.txt). ⚠️ Dipende dall'ordine del grammar resolver (genere pre/post pluralizzazione)
  → **da verificare in gioco**. Domanda al team in `EXTRA/discord-languageworker-question.md`.

### PROSSIMI PASSI (domani)
1. **Inviare/attendere la domanda Discord** (conferma strategia data-driven + ordine resolver
   eteroclito). Bozza pronta in `EXTRA/`.
2. **Verifica in Dev mode** (serve il gioco): log di combattimento su pawn M/F →
   "le braccia"/"la mano"/rami `count==1/2/3`; nomi fazione e mappa generati.
3. **Namer rimanenti** (qualità minore, apposizioni di nomi-luogo perlopiù accettabili):
   Settlement (Outlander/Pirate/Tribal) e WorldFeatures.
4. **Log sociale** (Interactions) — stesso approccio dei rami `count`/genere.
5. **Reconcile residuo**: pool nomi mancanti (fallback inglese OK), altri `CORTO`; rivedere i
   fallback Morph-it! segnalati (es. `omicida`→bucket, idiomi).
6. Eventuale **`rwit wordinfo`**: generare `Gender`/`plural.txt` da *tutti* i label via Morph-it!.

**Riferimento rapido tooling**: `rwit --help`. Dashboard: `python scripts\dashboard\start.py`
(o `streamlit run scripts\dashboard\app.py`). Repo gemelli: `RimWorld-fr/de/Spanish`
(de = il più completo, modello data-driven). Decompilatore: `scripts/.tools/ilspycmd.exe`.

## 1. Contesto

Il gioco è stato aggiornato a **1.6.4850**. La cartella lingua "Italiano" dentro
l'installazione è collegata via symlink a questo repo (vedi `rwit link`), quindi il
comando **"Pulisci lingue"** dato in gioco ha riscritto i file del repo.

Generato un nuovo `docs/TranslationReport.txt`.

## 2. Cosa ha realmente cambiato il "Pulisci lingue"

Analizzato l'intero diff (43 file). Le modifiche sono **quasi tutte cosmetiche**, NON
traduzioni nuove:

1. **Correzione di refusi nell'inglese** dentro i commenti `<!-- EN: ... -->`
   (es. `fibre→fiber`, `courtesean→courtesan`, `assisant→assistant`,
   `enlightment→enlightenment`, `abilites→abilities`, `sacrified→sacrificed`,
   `succesfully→successfully`, `consumess→consumes`, `disabanded→disbanded`…).
   **Il significato inglese non cambia** → la traduzione italiana resta valida.
   **Nessuna di queste richiede ri-traduzione.**
2. **Normalizzazione whitespace** (spazi finali, ultima riga senza newline).
3. Le **4 TerrainDef "ponti antichi"** tradotte nella sessione precedente
   (`AncientBridge`, `AncientHeavyBridge`) — già a posto.
4. Una modifica IT reale già in working tree: `<Required>` da *Necessario* → *Richiesto*
   in `Core/Keyed/Misc_Gameplay.xml` (miglioria, da confermare).

> **Conclusione**: il diff del gioco è rumore (commenti EN + whitespace). Il lavoro vero
> è la **revisione qualità** e i **bug** del report, non il diff.

## 3. Stato dal TranslationReport (1.6.4850)

- **Keyed mancanti: 0** ✅
- **DefInjected mancanti: 0** ✅
- 91 load errors (backstory/def obsolete) → pulizia
- 95 keyed inutili (mai usate) → pulizia
- 109 keyed = inglese → revisione (la maggior parte va tenuta: simboli, unità, sigle)
- 9 argument mismatch → 1 bug reale + 8 legacy posizionali

## 4. Strategia di branch e commit

Per separare il rumore dal lavoro vero e rendere la review pulita:

1. **Commit "baseline"**: la rigenerazione del gioco (commenti EN + whitespace + 4 ponti).
   Messaggio: `sync: allinea commenti EN e whitespace a 1.6.4850`.
2. **Commit successivi tematici**: bug fix, revisione per DLC, pulizia.
3. Merge su `master` solo a revisione completata.

## 5. Worklist

### 5.1 Bug certi (priorità 🔴)
- [x] ~~Ternaria malformata in `LetterCatatonicMentalBreak`~~ → **FALSO POSITIVO**.
  `{0_gender ? o : a : o}` è la forma valida a **3 rami** (masch/femm/neutro-None),
  confermata sui language pack fr/de/es. La nota di handoff nel vecchio CLAUDE.md era
  errata; il warning del report era sul `{PAWN_pronoun}` reso con "Si riprenderà"
  (mismatch benigno, non un bug). Nessuna modifica.
- [x] `"Ma ai le basi adesso"` → `"Ma hai le basi adesso"` + riallineati i 5 passi
  del tutorial all'inglese aggiornato in `Core/DefInjected/InstructionDef/Instructions.xml`
  (`ChooseStoryteller.text`).
- [x] `"Sei sei sicuro"` → `"Sei sicuro"`
  in `Core/Keyed/Misc_Gameplay.xml` (`GiveGiftViaTransportPodsTradeRequestWarning`).
- [ ] Verificare gli 8 argument mismatch legacy (stile posizionale `{0}`): perlopiù ok,
  confermare che non rompano.
- [x] 🔴 **Lingua sbagliata (francese) in Anomaly** — RISOLTO. La stima "~14" era errata:
  con `rwit lang-check` (vedi sotto) trovate e ritradotte **40** stringhe FR in Anomaly:
  `Precepts_PsychicRituals.xml` (intero file, 15), `Keyed/Misc_Gameplay.xml`
  (blocco UnnaturalCorpse+GoldenCube, 23), `Tales_Double.xml` (3 label) + parole isolate
  (`cracheur`→sputatore, `noctolithe`→noctolite, refuso `difdeforme`→contorta).
  Restano 2 falsi positivi italiani (`Carne del revenant`, `una figura indistinta`).
- [x] **Lingua sbagliata per-stringa nelle altre DLC**: triage completato. I ~19 fr del
  `lang-check` per-stringa sono quasi tutti **falsi positivi italiani** (`noctolite`,
  `Carne del revenant`, `Menù principale`, `tè di psychite`…) — "revenant"/"menù" ingannano
  `lingua`. Nessuna azione.
- [ ] 🟠 **Due interi file Namer FR (Odyssey)** — workstream, NON quick-fix. Scoperti con la
  nuova modalità `rwit lang-check --files` (la per-stringa li mancava: parole brevi):
  `Odyssey/DefInjected/RulePackDef/RulePacks_Namers_Factions.xml` (96% FR) e
  `RulePacks_Namers_Gravship.xml` (99% FR). Sono **generatori di nomi** (fazioni, gravship)
  copiati da RimWorld-fr con tutta l'**impalcatura di genere/elisione francese**
  (`_feminine`/`_vowel`, prefissi `le/la/l'`). Vanno **ricostruiti per la grammatica
  italiana** (non tradotti dal francese) partendo dal sorgente EN, stile come il Namer di
  Core. ⚠️ Da **verificare in Dev mode** (nomi generati a runtime). Sorella del workstream
  log-combattimento (§5.2-ter).
  - NB: Deity_Names, Xenohumans, Genepacks, Biosignatures combaciano col FR ma sono
    **sillabe inventate neutre** (`[syl][end]`) — NON vanno toccate (confermato da `--files`).

> **TOOLING NUOVO (questa sessione)** — tutto in `scripts/rwit/`, offline, zero token LLM:
> - **`rwit lang-check`** (`langcheck.py`): rileva lingua sbagliata. Gate `lingua` +
>   conferma per match cross-repo (fr/es/de) + margine sull'italiano + policy per-lingua.
>   Report auto-sufficiente con commento EN (si traduce senza riaprire i file).
> - **`rwit ledger`** (`ledger.py`): registro versionato `scripts/dashboard/translation-ledger.csv`
>   (tracciato in git). Stato per stringa (untranslated/translated/validated/**stale**/
>   **modified**) + hash EN (baseline) e IT. `build` (merge preservando le validazioni),
>   `stats`, `validate`, `todo` (worklist per LLM esterno), `report` (dashboard HTML).
>   Rileva nel tempo: EN cambiato a monte → `stale`; IT cambiato dopo validazione → `modified`.
> - **Dashboard**: `rwit ledger report` → `reports/dashboard.html` (progresso per DLC).
>   Stato attuale: **95,2%** fatto, 1634 da tradurre/uguali-a-EN, su 34.033 stringhe.

### 5.2 Revisione ampia (decisa con il maintainer)
Passata di qualità file per file, per DLC, su naturalezza/idiomi/coerenza terminologica.
Criterio: correggere **anche le imprecisioni**, non solo gli errori
(es. "crushed" → "schiacciati", non "distrutti"). Vedi `docs/TRANSLATION-SYNTAX.md` e
`docs/CONTRIBUTING.md` per le regole.

Ordine suggerito (per impatto/visibilità):
1. `Core/Keyed` (UI sempre a schermo)
2. `Core/DefInjected` (oggetti, backstory, eventi)
3. DLC: Royalty → Ideology → Biotech → Anomaly → Odyssey

Per ogni file: variabili `[VAR]`/`{VAR}` intatte, `->` nelle rulesStrings, `\n\n`
preservati, ternaria genere valida, commenti `<!-- EN: -->` invariati.

### 5.2-bis Nomi, plurali e grammatica (workstream)
Vedi [`NAME-GENERATION-AND-GRAMMAR.md`](NAME-GENERATION-AND-GRAMMAR.md).
- [x] Decompilato `LanguageWorker_Italian` dalla DLL (esisteva già nel gioco).
- [x] **Spostato in root e migliorato** `LanguageWorker_Italian.cs`: articoli `lo`/`gli`
  (gn/ps/pn/x/y/i+vocale), articoli al plurale, plurali femminili `-ca/-ga/-cia/-gia`.
  Logica verificata con harness. ⚠️ Da deployare (PR upstream o mod) per avere effetto.
- [ ] WordInfo/Gender: inglese rimasto (vedi nota: si sistema al `.label`), generi dubbi (-e).
- [ ] **`WordInfo/plural.txt`** (nuovo, stile tedesco `singolare;plurale`): plurali irregolari.
  Auto-caricato dal motore, robusto (keyed). È ciò che usa davvero `Pluralize`.
- [ ] Strings: coerenza singolare/plurale × M/F (file posizionali — stesso conteggio righe).

**Strategia corpus**: fonte = inglese del gioco (diff IT-vs-EN per la worklist); nomi propri
`Strings/Names/` si tengono in inglese, liste-parola `Strings/Words/` si traducono;
`WordInfo` derivato dai nostri label (Morph-it!), non copiato da EN/DE.

### 5.2-ter Log generato (combattimento/sociale) — obiettivo prioritario
Vedi [`NAME-GENERATION-AND-GRAMMAR.md`](NAME-GENERATION-AND-GRAMMAR.md) §5.
Causa radice misurata: **it 1 vincolo di genere vs fr 122 / es 100 / de 95** → log con
genere/articoli sbagliati. Strategia (tutto su FILE DI TESTO, niente `.cs`): vincoli
`(X_gender==Male/Female)` + suffissi `[X_definite]` + `WordInfo/Gender` e `plural.txt`.
Funziona già col worker di serie.
- [ ] Parti del corpo in `WordInfo/Gender` (genere) e `WordInfo/plural.txt` (plurali irregolari:
  braccio→braccia, dito→dita, ginocchio→ginocchia, osso→ossa, labbro→labbra).
- [ ] Pack-template `Combat_Deflect` con i vincoli di genere (template = pack fr).
- [ ] Verifica in Dev mode (log di combattimento) su pawn M e F.
- [ ] Scalare: CombatMelee → CombatRanged → Damage → Maneuvers → Interactions sociali.
- [ ] Strings mancanti (diff IT-vs-EN, ~13 file in Core): tradurre le `Words/Adjectives|Verbs`
  reali; i pool di nomi propri si possono lasciare (fallback inglese) o copiare.
- [ ] Tooling: `rwit wordinfo` (genera Gender/plural da Morph-it!), `rwit compare`
  (it↔fr↔es↔de), `rwit validate` (lint articoli a mano + allineamento file posizionali).

### 5.3 Pulizia (priorità 🧹)
- [x] Backstory obsolete: 6 file interamente UNUSED eliminati (`Gambler_*`, `Marshal_Adult`,
  `Mate_Child`, `Sadist_*`) + voci singole `ArtSlave57`/`ModDesigner85` (~70 load error).
- [x] Inject-error di def **rimosse** (verificate assenti nei Def 1.6.4850): `SmokepopBeltRadius`,
  `GeneticChemicalDependency`, `ChooseIdeo` (Tutor.xml eliminato), `ActivateThing`,
  `CompStudiable` (chip), `left_shoulder` (Lancer).
- [ ] **Da gestire con verifica (def RINOMINATE/SPOSTATE, non rimosse → no cancellazione cieca)**:
  `NoInteraction` (ora SlaveInteractionModeDef), `CompReloadable.chargeNoun`, `CompStatEntry`,
  sensori `Bodies_Mechanoid_Light`. Candidate a `rwit clean` con conferma.
- [ ] **95 keyed inutili**: NON rimosse in blocco — alcune sono in realtà referenziate
  (es. `Credit_Translator` usato da `LanguageInfo.xml`). Richiede risoluzione DLC + cross-check
  usi → lavoro per `rwit clean`, non cancellazione di massa.
- [ ] Rivedere 109 keyed = inglese: la maggior parte va tenuta (simboli/unità/sigle).

## 6. Documentazione per i futuri sviluppatori (questa sessione)

Decisione: **CLAUDE.md tracciato e ripulito** + docs/ Claude Code compliant.
- `CLAUDE.md` (root, tracciato): istruzioni di progetto, percorsi personali rimossi,
  punta ai docs.
- `docs/CONTRIBUTING.md`: setup env, flusso di lavoro, tooling `rwit`.
- `docs/TRANSLATION-SYNTAX.md`: sintassi ammessa nelle traduzioni (ternaria genere,
  variabili, rulesStrings, `\n\n`, elisione, errori comuni).
- `docs/REFERENCES.md`: repo di riferimento (fr/es/de), strategia WordInfo, link Ludeon.
- `docs/VALIDATION.md` + `docs/VALIDATION-FILES.csv`: tracciamento validazione dei file
  (1812 dopo la pulizia) e nota di integrità (la traduzione **non** può alterare le priorità eventi:
  0 campi-peso evento nel repo; gli unici pesi sono i `(p=N)` delle rulesStrings, da
  preservare sul lato sinistro).
- `docs/UPDATE-PLAN-1.6.4850.md`: questo file.

## 7. Stato avanzamento

| Fase | Stato |
|------|-------|
| Branch `aggiornamento-1.6.4850` creato | ✅ |
| Analisi diff gioco | ✅ |
| Docs per futuri sviluppatori (6 doc + Notes) | ✅ |
| CLAUDE.md tracciato e ripulito | ✅ |
| Bug certi (2 fix reali; 1 falso positivo annullato) | ✅ |
| Workstream nomi/grammatica (LanguageWorker decompilato + doc) | ✅ |
| Pulizia load errors (backstory + inject di def rimosse) | ✅ |
| Pulizia rename/keyed inutili (→ `rwit clean`) | ⬜ tooling |
| Revisione ampia traduzioni (iterativa, per DLC) | 🔄 in corso |
| Merge su master | ⬜ a rilascio (mai push diretto) |

> Commit sul branch: tooling · docs+Notes · sync+fix · wordinfo · pulizia backstory ·
> pulizia inject-error. Working tree allineato.
