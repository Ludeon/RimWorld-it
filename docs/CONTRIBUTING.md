# Guida al contributo — Traduzione italiana di RimWorld

Benvenuto. Questo repo contiene la traduzione italiana di RimWorld (gioco base + DLC).
È un language pack: **solo file XML/TXT**, nessuna modifica al codice del gioco.

Prima di tradurre, leggi anche:
- [`docs/TRANSLATION-SYNTAX.md`](TRANSLATION-SYNTAX.md) — sintassi del motore (ternaria genere, variabili, rulesStrings).
- [`docs/REFERENCES.md`](REFERENCES.md) — repo di altre lingue, strategia WordInfo, link Ludeon.

---

## 1. Struttura del repo

Una cartella per gioco base / DLC, nell'ordine di caricamento:

```
Core/  Royalty/  Ideology/  Biotech/  Anomaly/  Odyssey/
```

Ognuna contiene:
- `DefInjected/` — traduzioni dei campi dei Def (oggetti, eventi, backstory…)
- `Keyed/` — testo di interfaccia (chiave→valore)
- `Strings/` — liste (nomi, ecc.)
- `WordInfo/` — dati grammaticali (per l'italiano: solo `Gender/`)
- `LanguageInfo.xml` — metadati lingua

`scripts/` contiene il tooling (`rwit`) e le regole di traduzione. `docs/` la documentazione.

---

## 2. Setup dell'ambiente (una volta)

Serve **Python 3.11+**. Dalla radice del repo:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r scripts\requirements.txt
```

Questo crea il virtualenv `.venv/` (gitignored) con le dipendenze del tooling
(lxml, rich, typer, requests).

Verifica:
```powershell
.venv\Scripts\python scripts\rwit --help
```

---

## 3. Il tooling `rwit`

CLI in `scripts/rwit/`. Tre comandi:

| Comando | Cosa fa |
|---------|---------|
| `rwit link`   | (Ri)crea i symlink che collegano questo repo all'installazione del gioco come lingua "Italiano". Serve admin o **Modalità sviluppatore** di Windows (UAC). Da rifare se sposti la cartella del progetto (i symlink hanno il percorso assoluto). |
| `rwit analyze` | Confronta il `TranslationReport.txt` del gioco con il repo e calcola il **gap reale** (keyed mancanti/non tradotte, DefInjected mancanti per tipo). Scrive il dettaglio in `reports/gap_<data>.txt`. |
| `rwit unlink` | Rimuove i symlink dal gioco (non tocca cartelle reali). |

Override dei percorsi del gioco: opzione `--game-data` o variabile d'ambiente `RIMWORLD_DATA`.

```powershell
.venv\Scripts\python scripts\rwit analyze
.venv\Scripts\python scripts\rwit link
```

---

## 4. Flusso di lavoro completo

1. **`rwit link`** — collega il repo al gioco. (Necessario dopo ogni spostamento della
   cartella del progetto.)
2. **In gioco** (Dev mode attiva) → lingua **Italiano** → *Pulisci lingue* / rigenera i
   dati di lingua. Il gioco produce un `TranslationReport.txt`.
3. **`rwit analyze`** — calcola il gap reale e scrive `reports/gap_<data>.txt`.
4. **Traduci** i tag elencati, seguendo `docs/TRANSLATION-SYNTAX.md`.
5. **Verifica** in gioco (riavvia RimWorld per rileggere la lingua).

> ⚠️ **Genera SEMPRE il report con i symlink funzionanti.** Con link rotti il gioco carica
> zero italiano e segna l'intero gioco come "mancante" (falso positivo). `rwit analyze`
> recupera comunque il gap confrontando col repo, ma è meglio partire da un report corretto.

### Quando il gioco si aggiorna
Il comando *Pulisci lingue* riscrive i file del repo: aggiorna i commenti `<!-- EN: -->`
all'inglese nuovo e normalizza il whitespace. **Spesso sono solo refusi inglesi corretti**:
se il significato inglese non cambia, la traduzione italiana **non va toccata**. Fai sempre
un `git diff` per distinguere il rumore (commenti/whitespace) dalle modifiche di sostanza.

---

## 5. Regole d'oro

- Tradurre **solo** stringhe TODO o tag vuoti; non riscrivere ciò che è già tradotto e
  corretto (ma **correggere** errori e rigidità — vedi sotto).
- Mai tradurre il contenuto tra `[ ]` e i nomi delle variabili `{ }`.
- Mai modificare i commenti `<!-- EN: -->`.
- Preservare struttura XML, indentazione e `\n\n`.
- rulesStrings: freccia `->`, lato sinistro invariato, stesso numero di `<li>`.
- Restituire XML completo e ben formato.

Dettagli ed esempi in [`docs/TRANSLATION-SYNTAX.md`](TRANSLATION-SYNTAX.md).

### Criterio di qualità
Correggere **anche le imprecisioni**, non solo gli errori palesi: privilegiare
naturalezza e fluidità, evitare i calchi letterali dall'inglese
(es. "crushed" → "schiacciati", non "distrutti").

---

## 6. Repository pubblico — niente dati personali

Non committare dati personali o d'ambiente in file tracciati (hardware, percorsi con
username, email, token, contesto personale). Il contesto personale va in `CLAUDE.local.md`
(gitignored). Per un controllo automatico si può usare uno scanner standard (es. **gitleaks**
via il framework [pre-commit](https://pre-commit.com), o la **push protection** di GitHub),
da configurare se/quando serve.

## 7. Git e branch

- Si lavora su un **branch dedicato** (es. `aggiornamento-<versione>`), si fonde su
  `master` solo a revisione completata.
- Separare i commit "baseline" (rigenerazione del gioco: commenti EN + whitespace) dai
  commit di sostanza (traduzioni, bug fix, pulizia), così la review resta leggibile.
- File/cartelle ignorati: `.venv/`, `reports/`, `__pycache__/`, `dist/`, `About/`.
