# CLAUDE.md

Guide for Claude Code (claude.ai/code) and for contributors to this repository.

> This file is **tracked in git** and visible to all future developers.
> Do not put personal paths or session notes here: for those use
> `CLAUDE.local.md` (gitignored) or `docs/`.

## Privacy — public repository

This repository is public: do not commit personal or environment data into tracked files
(hardware, paths with usernames, email, tokens, personal context not useful to the
translation). Personal context goes in `CLAUDE.local.md` (gitignored); for game paths use
generic mechanisms (`Path.home()`, `RIMWORLD_DATA`).

## Overview

**Italian** translation of RimWorld (base game + DLC). It is a language pack:
**XML/TXT files only**, no changes to the game code.

**Target game version**: 1.6.4850.

## Documentation

All operational documentation is in `docs/` (tracked):

- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) — environment setup, `rwit` tooling, workflow.
- [`docs/TRANSLATION-SYNTAX.md`](docs/TRANSLATION-SYNTAX.md) — engine syntax: gender ternary, `[VAR]`/`{VAR}` variables, rulesStrings, `\n\n`, elision.
- [`docs/RULEPACK-GRAMMAR.md`](docs/RULEPACK-GRAMMAR.md) — full RulePack language: `(count==N)`/gender conditions, weights `(p=N)`, indexed symbols, combat log.
- [`docs/REFERENCES.md`](docs/REFERENCES.md) — other-language repos (fr/es/de), WordInfo strategy, Ludeon links.
- [`docs/VALIDATION.md`](docs/VALIDATION.md) — file validation, integrity (the translation does NOT touch event priorities), `VALIDATION-FILES.csv` sheet.
- [`docs/NAME-GENERATION-AND-GRAMMAR.md`](docs/NAME-GENERATION-AND-GRAMMAR.md) — how the game generates names/articles/plurals and the **combat/social log** (LanguageWorker + WordInfo + Strings + rulesStrings, with the gender-fix strategy). Code in [`LanguageWorker_Italian.cs`](LanguageWorker_Italian.cs) (improved version, root).
- [`docs/LOCAL-TOOLING.md`](docs/LOCAL-TOOLING.md) — strategy for local/offline tools: Morph-it! for morphology, embeddings for consistency, local LLM only as finder/triage (never as translator).
- `docs/UPDATE-PLAN-<version>.md` — plan for the in-progress update session.

Operational translation rules: [`docs/TRANSLATION-SYNTAX.md`](docs/TRANSLATION-SYNTAX.md)
and [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md).

## Repo structure

```
Core/  Royalty/  Ideology/  Biotech/  Anomaly/  Odyssey/   # base game + DLC
scripts/                                                    # rwit tooling + rules
docs/                                                       # documentation
```

Each game/DLC folder contains `DefInjected/`, `Keyed/`, `Strings/`, `WordInfo/`,
`LanguageInfo.xml`.

## Tooling

Tooling in **Python** (`scripts/rwit/`). One-time setup from the repo root:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r scripts\requirements.txt
```

Commands:

```powershell
.venv\Scripts\python scripts\rwit --help
.venv\Scripts\python scripts\rwit analyze    # real gap: TranslationReport vs repo
.venv\Scripts\python scripts\rwit link        # (re)create the Italian symlinks in the game (UAC)
.venv\Scripts\python scripts\rwit unlink      # remove the symlinks
```

Game paths: auto-detected; override with `--game-data` or `RIMWORLD_DATA`.
Details in [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md).

### Live reload while testing (RimLiveTongue)

Optional companion **dev mod** for previewing edits without restarting the game:
[**RimLiveTongue**](https://github.com/b4p3p/RimLiveTongue) (`packageId: b4p3p.rimlivetongue`, RimWorld 1.6).
On a file change it does a *language-only* reload through the engine's native loading path
(Keyed + Strings + DefInjected), so edits to this repo show up live. Point its **watch folder**
(Options → Mod settings → RimLiveTongue) at the active language folder — with the `rwit link` symlink
setup that is this repo root. It can also be triggered by touching a `.rimlivetongue-reload` sentinel
file in the watch folder. Dev tool only: it is **not** shipped inside the translation pack.

## Translation rules (summary)

1. Translate **only** TODO strings or empty tags; **fix** errors and inaccuracies in existing translations (favor naturalness, avoid literal calques).
2. Never translate the content inside `[ ]` nor the names of `{ }` variables.
3. Never modify the `<!-- EN: ... -->` comments (copy them verbatim).
4. rulesStrings: form `<li>left->right</li>`, literal `->` arrow, left side unchanged, same number of `<li>`.
5. Preserve XML structure, indentation and the `\n\n` sequences (rewritten identically, without line breaks).
6. Gender via ternary: `{PAWN_gender ? o : a}` (exactly one `?` and one `:`).

Full reference: [`docs/TRANSLATION-SYNTAX.md`](docs/TRANSLATION-SYNTAX.md).

## Update flow to a new game version

1. `rwit link` — re-link the repo folders inside the installation.
2. In game (Dev mode) → language Italian → *Clean up translations*/regenerate → produces `TranslationReport.txt`.
3. `rwit analyze` — compute the real gap (`reports/gap_<date>.txt`, gitignored).
4. Translate/review the listed tags following the rules above.

> ⚠️ ALWAYS generate the report with working symlinks: with broken links the game loads
> zero Italian and marks everything as "missing" (false positive).
>
> *Clean up translations* rewrites the files: it updates the `<!-- EN: -->` comments and
> normalizes whitespace. Often these are just **corrected English typos** → the Italian
> translation must not be touched. Always run `git diff` to separate the noise from the
> substantive changes.

## Development notes

- Translation-only project: no changes to the game code.
- XML files used directly by the game: no build needed.
- The English DefInjected is not shipped (it lives in the Defs): the source of the gap is the
  `TranslationReport` generated in game. The English Keyed files are in
  `Data\<DLC>\Languages\English\Keyed`.
- Gitignored: `.venv/`, `reports/`, `__pycache__/`, `dist/`, `About/`, `CLAUDE.local.md`.

## References

- Wiki: https://rimworldwiki.com/
- Ludeon grammar rules: https://ludeon.com/forums/index.php?topic=43979.0
- RimLiveTongue (live-reload dev mod): https://github.com/b4p3p/RimLiveTongue
