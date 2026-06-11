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

### 3. Triage qualità → LLM locale piccolo come *finder*
Via `Ollama`, un modello istruito 7–8B (es. `qwen2.5:7b-instruct`, `llama3.1:8b`) per compiti
a **recall**, poi verificati:
- flag di stringhe in **lingua sbagliata / non tradotte**;
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
