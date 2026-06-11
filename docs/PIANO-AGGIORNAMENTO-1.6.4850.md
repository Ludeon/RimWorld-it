# Piano di aggiornamento traduzione — RimWorld 1.6.4850

> Branch di lavoro: **`aggiornamento-1.6.4850`** (separato da `master`, si fonde solo a rilascio pronto).
> Documento di sessione. Stato e decisioni aggiornati man mano.

## 0. RIPARTENZA — riprendere da qui (ultimo aggiornamento 2026-06-12)

**Branch attivo**: `aggiornamento-1.6.4850` (mai pushare su master). Working tree pulito,
tutto committato. Per riprendere: `git checkout aggiornamento-1.6.4850`.

**Fatto finora (committato)**:
1. Tooling Python `rwit` (sostituisce i vecchi script); vecchi prompt GPT-3.5 eliminati
   (regole ora nei docs).
2. Docs per contributor (`docs/`) + `CLAUDE.md` tracciato e ripulito + policy "repo pubblico,
   niente dati personali" (il personale sta in `CLAUDE.local.md`, gitignored).
3. Sync 1.6.4850 (commenti EN + whitespace) + 2 bug fix reali.
4. `LanguageWorker_Italian.cs` in **root**, decompilato e **migliorato** (articoli lo/gli,
   h muta, plurali -io/-ca/-ga; 16/16 test). Commenti in inglese (pronto per PR upstream).
5. Pulizia load-error (backstory obsolete + inject di def rimosse).

**Come funziona la grammatica (capito in questa sessione — vedi GENERAZIONE-NOMI…)**:
- Articoli/plurali a runtime = **`LanguageWorker`** (codice) che **legge i DATI**:
  `WordInfo/Gender/` (genere) e `WordInfo/plural.txt` (plurali, lookup keyed `parola;plurale`).
- `WordInfo/` è **auto-caricato** (nessuna registrazione XML). I file `Strings/` invece
  vanno montati con **`<rulesFiles>`** (`simbolo->PercorsoRelativo`) per essere usati come
  `[simbolo]` nelle rulesStrings.
- Italiano: **manca `WordInfo/plural.txt`** (ce l'ha il tedesco, auto-generato) → oggi i
  plurali cadono sull'euristica del `.cs`. Il file posizionale `AnimalsPlural.txt` è cosa
  diversa (e fragile) e NON è ciò che usa `Pluralize`.

**Strategia corpus (fonte e cosa tradurre)**:
- **Fonte di verità = INGLESE del gioco** (`Data/<DLC>/Languages/English/Strings`): definisce
  *cosa* esiste; la worklist si ricava per **diff IT-vs-EN**.
- **Nomi propri** (`Strings/Names/`) = pool: si **tengono in inglese** (già fatto, contenuti
  identici). **Liste-parola** (`Strings/Words/` Adjectives/Verbs/Nouns) = si **traducono**.
- **`WordInfo/Gender` + `plural.txt`** = specifici dell'italiano, derivati dai **nostri**
  label tradotti (ideale: Morph-it!), NON copiati da EN/DE.
- **Tedesco = modello del meccanismo** (plural.txt, dati), non fonte dei nomi.

**PROSSIMO PASSO (deciso) — tutto lavoro su FILE DI TESTO, niente `.cs`**:
1. **`WordInfo/Gender`**: aggiungere le **parti del corpo** (braccio M, gamba F, mano F…).
2. **`WordInfo/plural.txt`** (nuovo, stile tedesco `singolare;plurale`): plurali irregolari,
   prima le parti del corpo (braccio→braccia, dito→dita, ginocchio→ginocchia, osso→ossa,
   labbro→labbra). Auto-caricato, robusto, niente XML.
3. **Pack-template `Combat_Deflect`**: vincoli di genere `(X_gender==Male/Female)` + suffissi
   `[X_definite]`, modello = `RimWorld-fr/Core/DefInjected/RulePackDef/RulePacks_CombatMelee.xml`.
4. **L'utente verifica in Dev mode** (log di combattimento su pawn M e F).
5. Se regge → scalare: CombatMelee → CombatRanged → Damage → Maneuvers → Interactions sociali.
6. **Strings mancanti**: diff IT-vs-EN dà ~13 file assenti in Core (pool nomi + alcune
   `Words/Adjectives|Verbs`). Verificare per file se è gap reale (inglese che trapela) o
   ristrutturato in varianti di genere; tradurre le liste-parola mancanti.

**Lavoro aperto minore** (task tracciati): `rwit clean` (rename + 95 keyed inutili),
revisione ampia iterativa, valutare PR upstream del worker, costruire `rwit wordinfo`
(genera `WordInfo/plural.txt`/`Gender` da Morph-it!) e `rwit validate`.

**Repo di riferimento** (cartelle sorelle, `origin` = ufficiale Ludeon, **tutti allineati**):
`RimWorld-fr` (apr), `RimWorld-de` (giu — il più completo, ha `WordInfo/plural.txt`),
`RimWorld-Spanish` (mag). Decompilatore: `scripts/.tools/ilspycmd.exe` (gitignored).
Report del gioco: `docs/TranslationReport.txt`.

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
- [ ] 🔴 **Lingua sbagliata (francese)**: ~14 stringhe in **Anomaly** (copia dal repo FR):
  `Anomaly/Keyed/Misc_Gameplay.xml` (×10) e `Anomaly/DefInjected/ThoughtDef/Precepts_PsychicRituals.xml`
  (×4). Da ritradurre in italiano (fonte: commento `<!-- EN: -->` / inglese del gioco).
  Nessuno spagnolo rilevato. Trovare il resto con un language-ID (`rwit lang-check`, vedi
  [`TOOLING-LOCALE.md`](TOOLING-LOCALE.md) §3a).

### 5.2 Revisione ampia (decisa con il maintainer)
Passata di qualità file per file, per DLC, su naturalezza/idiomi/coerenza terminologica.
Criterio: correggere **anche le imprecisioni**, non solo gli errori
(es. "crushed" → "schiacciati", non "distrutti"). Vedi `docs/SINTASSI-TRADUZIONE.md` e
`docs/CONTRIBUTING.md` per le regole.

Ordine suggerito (per impatto/visibilità):
1. `Core/Keyed` (UI sempre a schermo)
2. `Core/DefInjected` (oggetti, backstory, eventi)
3. DLC: Royalty → Ideology → Biotech → Anomaly → Odyssey

Per ogni file: variabili `[VAR]`/`{VAR}` intatte, `->` nelle rulesStrings, `\n\n`
preservati, ternaria genere valida, commenti `<!-- EN: -->` invariati.

### 5.2-bis Nomi, plurali e grammatica (workstream)
Vedi [`GENERAZIONE-NOMI-E-GRAMMATICA.md`](GENERAZIONE-NOMI-E-GRAMMATICA.md).
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
Vedi [`GENERAZIONE-NOMI-E-GRAMMATICA.md`](GENERAZIONE-NOMI-E-GRAMMATICA.md) §5.
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
- `docs/SINTASSI-TRADUZIONE.md`: sintassi ammessa nelle traduzioni (ternaria genere,
  variabili, rulesStrings, `\n\n`, elisione, errori comuni).
- `docs/RIFERIMENTI.md`: repo di riferimento (fr/es/de), strategia WordInfo, link Ludeon.
- `docs/VALIDAZIONE.md` + `docs/VALIDAZIONE-FILE.csv`: tracciamento validazione dei file
  (1812 dopo la pulizia) e nota di integrità (la traduzione **non** può alterare le priorità eventi:
  0 campi-peso evento nel repo; gli unici pesi sono i `(p=N)` delle rulesStrings, da
  preservare sul lato sinistro).
- `docs/PIANO-AGGIORNAMENTO-1.6.4850.md`: questo file.

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
