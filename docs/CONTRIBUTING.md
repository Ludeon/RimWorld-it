# Contributing guide — Italian translation of RimWorld

Welcome. This repo contains the Italian translation of RimWorld (base game + DLC).
It is a language pack: **XML/TXT files only**, no changes to the game code.

Before translating, also read:
- [`docs/TRANSLATION-SYNTAX.md`](TRANSLATION-SYNTAX.md) — engine syntax (gender ternary, variables, rulesStrings).
- [`docs/REFERENCES.md`](REFERENCES.md) — other-language repos, WordInfo strategy, Ludeon links.

---

## 1. Repo structure

One folder per base game / DLC, in load order:

```
Core/  Royalty/  Ideology/  Biotech/  Anomaly/  Odyssey/
```

Each contains:
- `DefInjected/` — translations of Def fields (items, events, backstories…)
- `Keyed/` — interface text (key→value)
- `Strings/` — lists (names, etc.)
- `WordInfo/` — grammar data (for Italian: `Gender/` + `plural.txt`)
- `LanguageInfo.xml` — language metadata

`scripts/` holds the tooling (`rwit`) and translation rules. `docs/` holds the documentation.

---

## 2. Environment setup (once)

Requires **Python 3.11+**. From the repo root:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r scripts\requirements.txt
```

This creates the `.venv/` virtualenv (gitignored) with the tooling dependencies
(lxml, rich, typer, requests; plus lingua / flask for the QA tools and dashboard).

Check:
```powershell
.venv\Scripts\python scripts\rwit --help
```

---

## 3. The `rwit` tooling

CLI in `scripts/rwit/`. Core commands:

| Command | What it does |
|---------|--------------|
| `rwit link`   | (Re)creates the symlinks that connect this repo to the game install as the "Italiano" language. Needs admin or Windows **Developer Mode** (UAC). Redo it if you move the project folder (the symlinks use absolute paths). |
| `rwit analyze` | Compares the game's `TranslationReport.txt` with the repo and computes the **real gap** (missing/untranslated keyed, missing DefInjected by type). Excludes **phantom paths** — runtime caches the game's translator spuriously lists as missing but that aren't translatable (`unlockedRolesCachedFor`/`unlockedRituals` = a meme's runtime-cached roles/rituals, populated only when an ideoligion using that meme is active; `requiredMemeList` = a list of MemeDef *references*). Writes the detail to `reports/gap_<date>.txt`. |
| `rwit clean` | Removes dead entries the report flags. **Unused keyed**: removed only if the key is also **absent from the game's English Keyed** (genuinely orphaned — guards against false positives where the key still exists). **DefInjected load-errors**: entries the game can't inject (renamed/removed defs, moved comps, restructured body parts); reported with their repo location. Dry-run by default; `--apply-keyed` / `--apply-defs` perform the removal (single-line surgery + the adjacent `<!-- EN: -->`/`<!-- UNUSED -->` comment; needs `--yes`; **git is the safety net**). |
| `rwit unlink` | Removes the symlinks from the game (does not touch real folders). |

QA tools (offline, deterministic): `lang-check` (wrong language), `args-check` (placeholder
mismatch EN↔IT), `plural-check` (English `[Symbol]s` plural leaking on screen), `syntax-check`
(engine-breaking syntax: malformed gender ternaries + unbalanced `{}`/`[]`), `strings-diff` /
`reconcile` (align lists to the game's English), `freshness` (Words lists vs the game + gender
variants vs base), `variants` (morphological variants via Morph-it!; `variants noun-gender`
splits a noun list by gender), `ledger` (+ the **Flask** review dashboard:
`python scripts\dashboard\server.py` → http://127.0.0.1:5000 — stateless, no cache). See
[`LOCAL-TOOLING.md`](LOCAL-TOOLING.md).

Override the game paths: the `--game-data` option or the `RIMWORLD_DATA` environment variable.

```powershell
.venv\Scripts\python scripts\rwit analyze
.venv\Scripts\python scripts\rwit link
```

---

## 4. Full workflow

1. **`rwit link`** — connect the repo to the game. (Needed after each move of the project
   folder.)
2. **In game** (Dev mode on) → language **Italiano** → *Clean languages* / regenerate the
   language data. The game produces a `TranslationReport.txt`.
3. **`rwit analyze`** — computes the real gap and writes `reports/gap_<date>.txt`.
4. **Translate** the listed tags, following `docs/TRANSLATION-SYNTAX.md`.
5. **Verify** in game (restart RimWorld to reload the language).

> ⚠️ **Always generate the report with working symlinks.** With broken links the game loads
> zero Italian and marks the whole game as "missing" (false positive). `rwit analyze` recovers
> the gap by comparing with the repo anyway, but it is better to start from a correct report.

### When the game updates
The *Clean languages* command rewrites the repo files: it updates the `<!-- EN: -->` comments
to the new English and normalizes whitespace. **Often these are just corrected English typos**:
if the English meaning does not change, the Italian translation **must not be touched**. Always
`git diff` to separate the noise (comments/whitespace) from substantive changes.

A version bump also leaves **dead entries** behind: keyed whose English key was renamed/removed,
and DefInjected pointing at defs/comps/body-parts that moved. These are inert (the game logs a
load error and ignores them — no crash), but they clutter the report and hide real future
errors. Run `rwit clean` to review them and `--apply-keyed`/`--apply-defs` to remove them.
Note: a stale entry is often just a leftover **duplicate** of an already-corrected one (e.g. the
old `comps.CompReloadable.chargeNoun` next to the new `comps.CompApparelReloadable.chargeNoun`),
so removing it loses nothing.

---

## 5. Golden rules

- Translate **only** TODO strings or empty tags; do not rewrite what is already translated and
  correct (but **do fix** errors and stiffness — see below).
- Never translate the content inside `[ ]` or the variable names inside `{ }`.
- Never modify the `<!-- EN: -->` comments.
- Preserve XML structure, indentation and `\n\n`.
- rulesStrings: the `->` arrow, left side unchanged, same number of `<li>`.
- Return complete, well-formed XML.

Details and examples in [`docs/TRANSLATION-SYNTAX.md`](TRANSLATION-SYNTAX.md).

### Quality criterion
Fix **imprecisions too**, not just blatant errors: favor naturalness and fluency, avoid literal
calques from English (e.g. "crushed" → "schiacciati", not "distrutti").

---

## 6. Public repository — no personal data

Do not commit personal or environment data in tracked files (hardware, paths with usernames,
emails, tokens, personal context). Personal context goes in `CLAUDE.local.md` (gitignored). For
an automated check you can use a standard scanner (e.g. **gitleaks** via the
[pre-commit](https://pre-commit.com) framework, or GitHub **push protection**), to be configured
if/when needed.

## 7. Git and branches

- Work on a **dedicated branch** (e.g. `aggiornamento-<version>`), merge to `master` only when
  the review is complete.
- Separate "baseline" commits (game regeneration: EN comments + whitespace) from substantive
  commits (translations, bug fixes, cleanup), so the review stays readable.
- Ignored files/folders: `.venv/`, `reports/`, `__pycache__/`, `dist/`, `About/`, `EXTRA/`.
