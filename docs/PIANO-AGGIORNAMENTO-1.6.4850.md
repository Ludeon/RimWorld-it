# Piano di aggiornamento traduzione — RimWorld 1.6.4850

> Branch di lavoro: **`aggiornamento-1.6.4850`** (separato da `master`, si fonde solo a rilascio pronto).
> Documento di sessione. Stato e decisioni aggiornati man mano.

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

### 5.2 Revisione ampia (decisa con il maintainer)
Passata di qualità file per file, per DLC, su naturalezza/idiomi/coerenza terminologica.
Criterio: correggere **anche le imprecisioni**, non solo gli errori
(es. "crushed" → "schiacciati", non "distrutti"). Vedi `docs/SINTASSI-TRADUZIONE.md`
per le regole formali e `scripts/prompt.txt` per le regole di traduzione.

Ordine suggerito (per impatto/visibilità):
1. `Core/Keyed` (UI sempre a schermo)
2. `Core/DefInjected` (oggetti, backstory, eventi)
3. DLC: Royalty → Ideology → Biotech → Anomaly → Odyssey

Per ogni file: variabili `[VAR]`/`{VAR}` intatte, `->` nelle rulesStrings, `\n\n`
preservati, ternaria genere valida, commenti `<!-- EN: -->` invariati.

### 5.2-bis Nomi, plurali e grammatica (nuovo workstream)
Vedi [`GENERAZIONE-NOMI-E-GRAMMATICA.md`](GENERAZIONE-NOMI-E-GRAMMATICA.md).
- [x] Decompilato e salvato il riferimento `Notes/LanguageWorker_Italian.cs` (esisteva già
  nella DLL del gioco; mancava solo il `.cs` come per fr/es).
- [ ] WordInfo/Gender: tradurre inglese rimasto (`anima grass/tree`, `psychic shock lance`,
  `psylink neuroformer`), verificare generi dubbi (-e), gestire `new_words.txt`.
- [ ] Strings: coerenza singolare/plurale × M/F e commenti `//articolo`.
- [ ] Valutare PR upstream/mod per i limiti del worker (articolo `lo` per gn/ps/x/y,
  plurali `-ca/-ga/-co/-go`).

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
