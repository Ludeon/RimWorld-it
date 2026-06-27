---
name: valida-file
description: >-
  Procedura di validazione qualità di UN file di traduzione (promuove translated→validated nel
  ledger). Usala quando l'utente dice "riprendiamo da <file>", "valida <file>", "passiamo al
  prossimo file" o simili durante la fase di revisione (roadmap §5.4 di docs/UPDATE-PLAN-1.6.4850.md).
---

# Validazione di un file di traduzione

Segui questi passi **in ordine** per il file indicato dall'utente (`$ARGUMENTS`, p.es.
`Solid_Child.xml` o un percorso completo). Se manca il nome, chiedi quale file o proponi il
prossimo della fase corrente leggendo il RESUME in `docs/UPDATE-PLAN-1.6.4850.md`.

## 0. Contesto
- Branch di lavoro: **`aggiornamento-1.6.4850`** (MAI push su `master`). Verifica con `git status`.
- Dashboard Flask attiva: `.venv\Scripts\python scripts\dashboard\server.py` → http://127.0.0.1:5000
  (avviala solo se non già in esecuzione; è stateless, rilegge CSV+XML a ogni richiesta).
- Roadmap e fasi: §5.4 di `docs/UPDATE-PLAN-1.6.4850.md`. Ordine di validazione = ordine dei file
  in `docs/VALIDATION-FILES.csv` (file order); i `RulePackDef` si rivedono nella tab Name generator.

## 1. Inquadra il file
- Risolvi il percorso reale (di solito `<DLC>/DefInjected/<DefType>/<file>` o `<DLC>/Keyed/...`).
- 🔑 **Usa il path ESATTAMENTE come fornito in `$ARGUMENTS`** in tutti i comandi `rwit ledger ... --file`.
  La dashboard copia il path completo DLC-qualified (es. `Core\Keyed\Dialogs_Various.xml`): passalo
  verbatim, **non ridurlo mai al solo nome file** (`Dialogs_Various.xml`). `--file` è una sottostringa
  sul path e molti file sono omonimi tra DLC → il solo nome file validerebbe le copie di TUTTI i DLC.
- **Se è un `RulePackDef/*.xml`** (name generator: namer, log combat/social, descrizioni): NON si
  valida leggendo l'XML grezzo → si rivede nella tab **Name generator** della dashboard
  (anteprima dei nomi/frasi generati), poi si valida da lì. Ferma qui la parte "prosa" sotto.
- Altrimenti è prosa/etichette: prosegui.

## 2. Lint automatico PRIMA della review (leva, pochi token)
**Solo BackstoryDef** — rimuovi prima le iniezioni MORTE `*.baseDesc` (il gioco 1.6 legge solo
`<description>`; `baseDesc` non è più un campo del Def):
```powershell
.venv\Scripts\python scripts\rwit strip-basedesc            # DRY-RUN: mostra cosa rimuoverebbe
.venv\Scripts\python scripts\rwit strip-basedesc --apply    # applica
.venv\Scripts\python scripts\rwit ledger build              # AGGIORNA i contatori dopo lo strip
```
> Regola generale: ogni volta che **elimini/rinomini righe XML** (strip, pulizia) i numeri della
> dashboard NON cambiano da soli → rilancia `rwit ledger build` (preserva `validated`/`keep` per
> chiave; declassa a `modified`/`stale` solo le righe il cui testo IT/EN è cambiato).

Poi esegui i linter sul file (o sull'intera DLC) e correggi SOLO i veri hit:
```powershell
.venv\Scripts\python scripts\rwit gender-check   # articolo/aggettivo fisso davanti a {gender ? o:a}
.venv\Scripts\python scripts\rwit syntax-check    # ternarie malformate, {}/[ ] sbilanciate
.venv\Scripts\python scripts\rwit args-check       # segnaposto {N}/{VAR} discordanti EN↔IT
.venv\Scripts\python scripts\rwit lang-check       # residui FR/ES/DE
```
- I report finiscono in `reports/` (gitignored). Triage ogni hit: distingui bug reali da falsi
  positivi (prestiti, nomi propri, indici `{N_gender}` validati).
- **Backstory — campo vivo = `<description>`**: i fix di concordanza vanno fatti SOLO sulla
  `.description` (il `baseDesc` è morto, rimosso da `strip-basedesc`). Forma corretta: articolo
  DENTRO la ternaria, `{PAWN_gender ? un guerriero:una guerriera}`. Non sprecare modifiche sui baseDesc.

## 3. Review prosa a blocchi
**Riprendi dal non-validato.** Non rileggere ciò che è già a posto: elenca le voci ancora da fare
con `.venv\Scripts\python scripts\rwit ledger validate --file "$ARGUMENTS" --list` (mostra le
righe `translated`/`modified`; salta `validated`/`keep`) e rivedi solo quelle, a blocchi (~20 voci).

**REGOLA N.1 — il commento `<!-- EN: ... -->` è la GUIDA (fonte del significato).** Per OGNI voce,
leggi prima l'EN sopra e verifica che l'italiano renda **lo stesso senso**: soggetto, azione,
causa/effetto, sfumatura. Una frase può essere italiano perfetto e aver comunque **tradito il
significato** dell'inglese (omissioni, ribaltamenti causa→effetto, falsi amici, dettagli inventati o
persi) → quello è l'errore più grave da correggere. Confronta IT↔EN, non controllare solo l'italiano
in sé. NON validare una voce il cui senso diverge dall'EN: prima allineala.

Poi cura forma e naturalezza, rispettando `docs/TRANSLATION-SYNTAX.md`:
- NON tradurre il contenuto dentro `[ ]` né i nomi delle variabili `{ }`.
- NON modificare i commenti `<!-- EN: ... -->` (copiali verbatim — sono la guida, non si toccano).
- rulesStrings `<li>sx->dx</li>`: freccia `->` letterale, lato sinistro invariato, stesso numero di `<li>`.
- Preserva struttura XML, indentazione e le sequenze `\n\n` (riscritte identiche, senza a-capo).
- Genere via ternaria: `{PAWN_gender ? o : a}` (esattamente un `?` e uno/due `:`).
- Favorisci la naturalezza, evita calchi letterali; correggi anche le imprecisioni, non solo gli errori.
Dopo ogni modifica verifica che l'XML resti valido (`ET.parse`).

## 4. Validazione — LA FA LA SKILL via CLI (l'utente NON clicca nulla)
A fine file (o a fine di ogni blocco rivisto) promuovi a `validated` **da CLI** le sole voci che
hai EFFETTIVAMENTE riletto/corretto in §2-3:
```powershell
# intero file rivisto (path completo come fornito in $ARGUMENTS):
.venv\Scripts\python scripts\rwit ledger validate --file "$ARGUMENTS" --yes
# solo alcune voci/blocchi (--tag = sottostringa del tag, ripetibile):
.venv\Scripts\python scripts\rwit ledger validate --file "$ARGUMENTS" --tag <Tag1> --tag <Tag2> --yes
```
- `--file`/`--tag` sono sottostringhe case-insensitive; valida le righe `translated`/`modified`
  che combaciano (`set_status_keys`), ri-fissando gli hash → diventano sticky. Senza `--yes`
  stampa solo l'anteprima del conteggio; con `--list` elenca le voci ancora da validare.
- ⚠️ **`--file` è una SOTTOSTRINGA sul path, non un nome esatto** → passa il path completo di `$ARGUMENTS`
  (vedi §1), mai il solo nome file. Molti file sono omonimi tra DLC (`Dialogs_Various.xml`,
  `Misc_Gameplay.xml`, `Letters.xml` esistono in Core/Royalty/Ideology/Biotech/Anomaly/Odyssey):
  col solo nome file valideresti le copie di TUTTI i DLC. **Sanity check**: il conteggio di `--list`
  deve combaciare con le voci del tuo file; se è molto più alto, stai per timbrare file non letti →
  ferma. Recupero se è già successo: `git checkout HEAD -- scripts/dashboard/translation-ledger.csv`
  e rivalida col path completo.
- **Ignora già `validated`/`keep`** (idempotente): puoi rilanciarla senza ri-toccare il fatto.
- **Valida per VOCE intera, non per singolo tag**: usa `--tag <NomeVoce>` (es. `--tag Cadet96`),
  non `--tag Cadet96.description` → così validi anche `.title/.titleFemale/.titleShort...` ed eviti
  i "buchi" (voce con la sola description validata e i titoli ancora `translated`).
- Voci da NON tradurre (prestiti, nomi propri, sigle, format) → `keep` (dalla dashboard o
  `rwit ledger keep`), NON validated.
- Verifica: `.venv\Scripts\python scripts\rwit ledger stats` — `validated` sale del numero di voci
  validate. La dashboard è stateless: i numeri nuovi compaiono al reload, **senza** `ledger build`
  (la validazione scrive già il CSV).

**REGOLA**: valida solo ciò che hai DAVVERO rivisto in questa sessione — la validazione è il
sign-off di qualità, non un timbro automatico su un file non letto. Sui backstory il campo da
validare è `<description>` (il `baseDesc` è morto, già rimosso in §2).

## 5. Commit
- `git add` **esplicito** dei soli file toccati (MAI `git add -A`: una seconda sessione può
  lavorare in parallelo).
- Messaggi separati per natura: `content(<dlc>): ...` per i fix di traduzione,
  `tooling(...)`/`tooling(dashboard): ...` per CSV/strumenti.
- NON aggiungere il trailer "Co-Authored-By: Claude".

## 6. NON loggare il progresso per-file nel piano
Lo stato `validated` è tracciato dal ledger CSV (`scripts/dashboard/translation-ledger.csv`) +
dashboard: è quella la fonte di verità del progresso. **Non** aggiungere righe "file X validato,
N voci" in `docs/UPDATE-PLAN-1.6.4850.md` — il piano contiene solo piani/decisioni generali, non
un log di sessione. Tocca il piano SOLO se cambia qualcosa di generale (una nuova fase, una
decisione di strategia, una regola che vale per tutti i file).

> Riferimenti: `docs/VALIDATION.md`, `docs/NAME-GENERATION-AND-GRAMMAR.md`,
> `docs/RULEPACK-GRAMMAR.md`. Stato/conteggi: `.venv\Scripts\python scripts\rwit ledger stats`.
