# CLAUDE.md

Guida per Claude Code (claude.ai/code) e per i contributor di questo repository.

> Questo file è **tracciato in git** e visibile a tutti i futuri sviluppatori.
> Non inserire qui percorsi personali o note di sessione: per quelli usa
> `CLAUDE.local.md` (gitignored) o `docs/`.

## Privacy — repository pubblico

Questo repository è pubblico: non committare dati personali o d'ambiente in file tracciati
(hardware, percorsi con username, email, token, contesto personale non utile alla
traduzione). Il contesto personale va in `CLAUDE.local.md` (gitignored); per i percorsi del
gioco usare meccanismi generici (`Path.home()`, `RIMWORLD_DATA`).

## Panoramica

Traduzione **italiana** di RimWorld (gioco base + DLC). È un language pack:
**solo file XML/TXT**, nessuna modifica al codice del gioco.

**Versione gioco target**: 1.6.4850.

## Documentazione

Tutta la documentazione operativa è in `docs/` (tracciata):

- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) — setup ambiente, tooling `rwit`, flusso di lavoro.
- [`docs/SINTASSI-TRADUZIONE.md`](docs/SINTASSI-TRADUZIONE.md) — sintassi del motore: ternaria genere, variabili `[VAR]`/`{VAR}`, rulesStrings, `\n\n`, elisione.
- [`docs/RULEPACK-GRAMMAR.md`](docs/RULEPACK-GRAMMAR.md) — linguaggio completo delle RulePack: condizioni `(count==N)`/genere, pesi `(p=N)`, simboli indicizzati, log di combattimento.
- [`docs/RIFERIMENTI.md`](docs/RIFERIMENTI.md) — repo di altre lingue (fr/es/de), strategia WordInfo, link Ludeon.
- [`docs/VALIDAZIONE.md`](docs/VALIDAZIONE.md) — validazione file, integrità (la traduzione NON tocca le priorità eventi), foglio `VALIDAZIONE-FILE.csv`.
- [`docs/GENERAZIONE-NOMI-E-GRAMMATICA.md`](docs/GENERAZIONE-NOMI-E-GRAMMATICA.md) — come il gioco genera nomi/articoli/plurali e il **log di combattimento/sociale** (LanguageWorker + WordInfo + Strings + rulesStrings, con la strategia di fix per il genere). Codice in [`LanguageWorker_Italian.cs`](LanguageWorker_Italian.cs) (versione migliorata, root).
- [`docs/TOOLING-LOCALE.md`](docs/TOOLING-LOCALE.md) — strategia per gli strumenti locali/offline: Morph-it! per la morfologia, embedding per la coerenza, LLM locale solo come finder/triage (mai traduttore).
- `docs/PIANO-AGGIORNAMENTO-<versione>.md` — piano della sessione di aggiornamento in corso.

Regole operative di traduzione: [`docs/SINTASSI-TRADUZIONE.md`](docs/SINTASSI-TRADUZIONE.md)
e [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md).

## Struttura del repo

```
Core/  Royalty/  Ideology/  Biotech/  Anomaly/  Odyssey/   # gioco base + DLC
scripts/                                                    # tooling rwit + regole
docs/                                                       # documentazione
```

Ogni cartella gioco/DLC contiene `DefInjected/`, `Keyed/`, `Strings/`, `WordInfo/`,
`LanguageInfo.xml`.

## Tooling

Tooling in **Python** (`scripts/rwit/`). Setup una tantum dalla radice del repo:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r scripts\requirements.txt
```

Comandi:

```powershell
.venv\Scripts\python scripts\rwit --help
.venv\Scripts\python scripts\rwit analyze    # gap reale: TranslationReport vs repo
.venv\Scripts\python scripts\rwit link        # (ri)crea i symlink Italiano nel gioco (UAC)
.venv\Scripts\python scripts\rwit unlink      # rimuove i symlink
```

Percorsi del gioco: autodeterminati; override con `--game-data` o `RIMWORLD_DATA`.
Dettagli in [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md).

## Regole di traduzione (sintesi)

1. Tradurre **solo** stringhe TODO o tag vuoti; **correggere** errori e imprecisioni nelle traduzioni esistenti (privilegiare naturalezza, evitare calchi letterali).
2. Mai tradurre il contenuto tra `[ ]` né i nomi delle variabili `{ }`.
3. Mai modificare i commenti `<!-- EN: ... -->` (si copiano identici).
4. rulesStrings: forma `<li>sinistra->destra</li>`, freccia `->` letterale, lato sinistro invariato, stesso numero di `<li>`.
5. Preservare struttura XML, indentazione e le sequenze `\n\n` (riscritte identiche, senza andare a capo).
6. Genere con ternaria: `{PAWN_gender ? o : a}` (un solo `?` e un solo `:`).

Riferimento completo: [`docs/SINTASSI-TRADUZIONE.md`](docs/SINTASSI-TRADUZIONE.md).

## Flusso di aggiornamento a una nuova versione del gioco

1. `rwit link` — ricollega le cartelle del repo dentro l'installazione.
2. In gioco (Dev mode) → lingua Italiano → *Pulisci lingue*/rigenera → produce `TranslationReport.txt`.
3. `rwit analyze` — calcola il gap reale (`reports/gap_<data>.txt`, gitignored).
4. Traduzione/revisione dei tag elencati seguendo le regole sopra.

> ⚠️ Genera SEMPRE il report con i symlink funzionanti: con link rotti il gioco carica
> zero italiano e marca tutto come "mancante" (falso positivo).
>
> Il *Pulisci lingue* riscrive i file: aggiorna i commenti `<!-- EN: -->` e normalizza il
> whitespace. Spesso sono solo **refusi inglesi corretti** → la traduzione italiana non va
> toccata. Fai sempre `git diff` per separare il rumore dalle modifiche di sostanza.

## Note di sviluppo

- Progetto di sola traduzione: nessuna modifica al codice di gioco.
- File XML usati direttamente dal gioco: nessun build necessario.
- Il DefInjected inglese non è shippato (vive nei Defs): la fonte del gap è il
  `TranslationReport` generato in gioco. Le Keyed inglesi sono in
  `Data\<DLC>\Languages\English\Keyed`.
- Gitignored: `.venv/`, `reports/`, `__pycache__/`, `dist/`, `About/`, `CLAUDE.local.md`.

## Riferimenti

- Wiki: https://rimworldwiki.com/
- Regole grammaticali Ludeon: https://ludeon.com/forums/index.php?topic=43979.0
