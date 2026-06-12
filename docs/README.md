# docs/ — Documentation index

Map of the operational documentation for the **Italian translation of RimWorld**.
If you are working from the repo root, the big picture is in
[`../CLAUDE.md`](../CLAUDE.md); this file helps you find your way *inside* `docs/`.

> Note: the guides below are written in Italian (the translation team's working
> language), but this index is in English as part of the international documentation.

## Suggested reading order (new contributor/agent)

1. [`CONTRIBUTING.md`](CONTRIBUTING.md) — environment setup and workflow.
2. [`TRANSLATION-SYNTAX.md`](TRANSLATION-SYNTAX.md) — translation engine rules.
3. [`VALIDATION.md`](VALIDATION.md) — how to validate files before committing.
4. The rest as needed (advanced grammar, name generation, local tooling).

## Guides (tracked — prose to read)

| File | Contents |
|------|----------|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Environment setup, `rwit` tooling, workflow. |
| [`TRANSLATION-SYNTAX.md`](TRANSLATION-SYNTAX.md) | Engine syntax: gender ternary, `[VAR]`/`{VAR}` variables, rulesStrings, `\n\n`, elision. |
| [`RULEPACK-GRAMMAR.md`](RULEPACK-GRAMMAR.md) | Full RulePack language: `(count==N)`/gender conditions, weights `(p=N)`, indexed symbols, combat log. |
| [`NAME-GENERATION-AND-GRAMMAR.md`](NAME-GENERATION-AND-GRAMMAR.md) | How the game generates names/articles/plurals and the combat/social log (LanguageWorker + WordInfo + Strings + rulesStrings). |
| [`REFERENCES.md`](REFERENCES.md) | Other-language repos (fr/es/de), WordInfo strategy, Ludeon links. |
| [`VALIDATION.md`](VALIDATION.md) | File validation and integrity (the translation does NOT touch event priorities). |
| [`LOCAL-TOOLING.md`](LOCAL-TOOLING.md) | Strategy for local/offline tools: Morph-it! for morphology, embeddings for consistency, local LLM only as finder/triage. |

## Session plan (ephemeral — tied to the game version)

| File | Contents |
|------|----------|
| [`UPDATE-PLAN-1.6.4850.md`](UPDATE-PLAN-1.6.4850.md) | Plan for the update session to version 1.6.4850. Replaced on each new target version. |

## Artifacts / data (generated output — not prose to read)

| File | Contents |
|------|----------|
| `TranslationReport.txt` | Report generated in-game (Dev mode → Clean up translations). Source of the translation gap. |
| `VALIDATION-FILES.csv` | File-by-file validation tracking sheet. |

> ℹ️ When you add or rename a file in `docs/`, update both this index and the
> "Documentazione" section of [`../CLAUDE.md`](../CLAUDE.md).
