# scripts/ — strumenti di traduzione (rwit)

Tool in Python (`scripts/rwit/`) per gestire la traduzione italiana di RimWorld 1.6.
Sostituisce i vecchi script PowerShell/Node.

## Setup (una volta)

Dalla radice del repo:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r scripts\requirements.txt
```

## Uso

```powershell
.venv\Scripts\python scripts\rwit --help
.venv\Scripts\python scripts\rwit analyze      # gap reale vs TranslationReport del Desktop
.venv\Scripts\python scripts\rwit link         # (ri)crea i symlink nel gioco (UAC)
.venv\Scripts\python scripts\rwit unlink       # rimuove i symlink
```

## Flusso di lavoro

1. **`link`** — collega le cartelle del repo dentro l'installazione del gioco come
   lingua "Italiano". Va rifatto se sposti la cartella del progetto (i symlink
   contengono il percorso assoluto). Serve admin o Modalita sviluppatore di Windows.
2. **In gioco** (Dev mode) — imposta lingua Italiano e rigenera i dati di lingua;
   il gioco scrive un `TranslationReport.txt` sul Desktop.
3. **`analyze`** — confronta quel report col repo e calcola il **gap reale**
   (Keyed mancanti/non tradotte, DefInjected mancanti per tipo). Scrive il dettaglio
   in `reports/gap_<data>.txt` (cartella gitignored).
4. **Traduzione** — si lavora sui tag elencati, rispettando le regole Ludeon
   (vedi `scripts/prompt.txt`): variabili `[VAR]` e `{PAWN_...}` intatte, frecce `->`
   nelle rulesStrings, `\n\n` preservati, commenti `<!-- EN: ... -->` invariati.

## Note

- Il report e affidabile solo se i symlink funzionano: con link rotti il gioco carica
  zero italiano e segna come "mancante" l'intero gioco. `analyze` recupera comunque il
  gap reale confrontando col repo, ma e meglio rigenerare con i link a posto.
- I percorsi del gioco si autodeterminano; override con `--game-data` o `RIMWORLD_DATA`.
