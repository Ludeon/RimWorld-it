# Local tooling / local LLM — strategy

Guidance for automating parts of the translation QA with tools that run **locally and
offline** (no external API, reproducible results). Suitable for batch jobs over the whole
corpus.

> **Status (2026-06-12): many of these tools are now REAL** in `scripts/rwit/`:
> `lang-check [--files]` (wrong language), `morphit.py` + `variants` (morphology via
> **Morph-it!**), `strings-diff` and `reconcile` (align lists to the game's English),
> `ledger` + dashboard. Still to do: embeddings for consistency and a possible `rwit wordinfo`
> (generate Gender/plural from all labels). See `RULEPACK-GRAMMAR.md` for the rule language.

## Guiding principle

> A small local LLM **is not the translator**: on hard text like RimWorld (gender, ternaries,
> rulesStrings) it introduces lore/grammar errors. Use it as a **finder/triage** whose output
> is *always verified* — never as the final translation.

Most of the value here is **deterministic**, not generative.

## Where it really pays off (in order of value)

### 1. Morphology (WordInfo gender/plurals) → lexicon, NOT an LLM
To populate `WordInfo/Gender` and the plurals (the lever that fixes the logs) the right tool
is an **Italian morphological lexicon**: **`Morph-it!`** (open source) or Wiktionary dumps.
For each lemma you *read* gender and plural instead of guessing them: deterministic, free,
exact. **Priority: the irregular body-part plurals** (braccio→braccia, dito→dita,
ginocchio→ginocchia, osso→ossa, labbro→labbra) that feed the combat log.
→ implemented as `rwit variants` / `morphit.py`; a future `rwit wordinfo` could batch it.

### 2. Terminology consistency → local embeddings
An **embedding model** (e.g. `bge-m3`, `multilingual-e5`) to find the same EN term translated
in different ways and near-duplicate strings to unify. Deterministic, lightweight.
→ future `rwit coherence`.

### 3a. Wrong language → DETERMINISTIC language detector (no LLM needed)
To find strings in the wrong language (e.g. **French** copied by mistake) the right tool is
**not** an LLM but a deterministic **language-ID**: `fastText lid.176`, `lingua`, or
`langdetect`. **Zero tokens, zero hallucinations, microseconds per string**, offline.
- Scans every translated value; flags non-`it` ones (whitelist: proper-name pools,
  symbols/units, terms kept in English).
- Real case found: **French strings in Anomaly** (`Keyed/Misc_Gameplay.xml`,
  `DefInjected/ThoughtDef/Precepts_PsychicRituals.xml`). → implemented as `rwit lang-check`.

### 3b. Fine triage → small local LLM as a *finder*
Only for nuanced cases that language-ID does not resolve (short/mixed strings). Via `Ollama`,
a 7–8B model, for **recall** and then verified:
- **round-trip** IT→EN compared with the `<!-- EN: -->` comment to flag divergences;
- **gender-disagreement** candidates in the generated logs.

Output = a list of *candidates to verify*, never direct edits.

## What NOT to do
- Do not use the LLM as the **final translator** (insufficient quality on RimWorld lore).
- Do not use it for **structural checks** (XML, `->`, variables, ternaries): the deterministic
  **linters** in `rwit validate` are better.

## Practical notes
- Locally, a **7–8B quantized** model (Q4/Q5) keeps things light; larger sizes need RAM offload
  (slower).
- Integrate everything as **`rwit` subcommands**, offline. Extra dependencies (ollama client,
  sentence-transformers) as an optional group in `scripts/requirements.txt`.

## Recommended priority
1. **Morph-it! → WordInfo** (body parts + irregulars) — unblocks the logs, deterministic. ✅ done
2. **`rwit validate`** (linter) — quality gate, no LLM.
3. **Embedding consistency** — cross-cutting terminology cleanup.
4. **LLM triage** — finder for wrong language / round-trip, with human verification.
