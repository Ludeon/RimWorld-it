# Strumenti locali / LLM locale — strategia

Indicazioni per chi vuole automatizzare parti della QA della traduzione con strumenti che
girano **in locale e offline** (nessuna API esterna, risultati riproducibili). Adatto a
job batch sull'intero corpus.

## Principio guida

> Un LLM locale di piccola taglia **non è il traduttore**: su un testo difficile come
> RimWorld (genere, ternarie, rulesStrings) introduce errori di lore/grammatica. Va usato
> come **finder/triage** il cui output è *sempre verificato* — mai come traduzione finale.

La maggior parte del valore qui è **deterministico**, non generativo.

## Dove conviene davvero (in ordine di valore)

### 1. Morfologia (genere/plurali WordInfo) → lessico, NON LLM
Per popolare `WordInfo/Gender` e i plurali (la leva che sistema i log) lo strumento giusto
è un **lessico morfologico italiano**: **`Morph-it!`** (open source) o i dump di Wiktionary.
Per ogni lemma si *legge* genere e plurale invece di indovinarli: deterministico, gratuito,
esatto. **Priorità: i plurali irregolari delle parti del corpo** (braccio→braccia,
dito→dita, ginocchio→ginocchia, osso→ossa, labbro→labbra) che alimentano il log di
combattimento. → futuro `rwit wordinfo`.

### 2. Coerenza terminologica → embedding locali
Un **embedding model** (es. `bge-m3`, `multilingual-e5`) per trovare lo stesso termine EN
tradotto in modi diversi e le stringhe quasi-duplicate da uniformare. Deterministico, leggero.
→ futuro `rwit coherence`.

### 3a. Lingua sbagliata → rilevatore di lingua DETERMINISTICO (non serve LLM)
Per trovare stringhe in lingua sbagliata (es. **francese** copiato per errore) lo strumento
giusto **non è un LLM** ma un **language-ID** deterministico: `fastText lid.176`, `lingua`,
o `langdetect`. **Zero token, zero allucinazioni, microsecondi a stringa**, offline.
- Scansiona ogni valore tradotto; segnala quelli non `it` (whitelist: pool di nomi propri,
  simboli/unità, termini tenuti in inglese).
- Caso reale trovato: **~14 stringhe francesi in Anomaly** (`Keyed/Misc_Gameplay.xml`,
  `DefInjected/ThoughtDef/Precepts_PsychicRituals.xml`). → futuro `rwit lang-check`.

### 3b. Triage fine → LLM locale piccolo come *finder*
Solo per casi sfumati che il language-ID non risolve (stringhe corte/miste). Via `Ollama`,
modello 7–8B, a **recall** e poi verificato:
- **round-trip** IT→EN con confronto al commento `<!-- EN: -->` per segnalare divergenze;
- candidati di **disaccordo di genere** nei log generati.

Output = lista di *candidati da verificare*, mai modifiche dirette.

## Cosa NON fare
- Non usare l'LLM come **traduttore finale** (qualità insufficiente sul lore RimWorld).
- Non usarlo per **controlli strutturali** (XML, `->`, variabili, ternarie): meglio i
  **linter deterministici** in `rwit validate`.

## Note pratiche
- In locale conviene un modello **7–8B quantizzato** (Q4/Q5) per restare leggeri; taglie
  maggiori richiedono offload su RAM (più lente).
- Integrare tutto come **sottocomandi `rwit`**, offline. Le dipendenze extra (client ollama,
  sentence-transformers) come gruppo opzionale in `scripts/requirements.txt`.

## Priorità consigliata
1. **Morph-it! → WordInfo** (parti del corpo + irregolari) — sblocca i log, deterministico.
2. **`rwit validate`** (linter) — gate qualità, nessun LLM.
3. **Embedding coerenza** — pulizia terminologica trasversale.
4. **LLM triage** — finder per lingua sbagliata / round-trip, a verifica umana.
