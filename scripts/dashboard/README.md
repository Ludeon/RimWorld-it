# Translation Progress Dashboard

A small, multilingual (EN/IT/ES/FR/DE) web dashboard to **see the state of the
translation at a glance** and find what still needs work.

It is a *viewer*. The source of truth stays the XML files and the git-tracked
ledger `translation-ledger.csv` (in this folder). The dashboard never edits anything.

## Quick start

From the repository root, with the project venv already set up
(see [`../../docs/CONTRIBUTING.md`](../../docs/CONTRIBUTING.md)):

```powershell
# 1. one-time: build the ledger (scans the repo, ~1s)
.venv\Scripts\python scripts\rwit ledger build

# 2. launch the dashboard (opens in your browser)
.venv\Scripts\streamlit run scripts\dashboard\app.py
```

Pick the UI language from the sidebar (🌐). Default is English.

## What you see

- **Completion %** and a global progress bar.
- **States** breakdown and **per-DLC** progress bars.
- A filterable **worklist** table (by DLC and status) — the strings still to do.

### Tabs

- **Progress** — completion %, per-DLC bars, filterable worklist (EN/IT).
- **Name generator** — preview the names the game would generate from any
  RulePack (factions, world/map, gravship) by simulating its grammar in Python.
  Useful to spot bad vocabulary, wrong articles/gender, or leftover foreign
  words **without launching the game**. Approximate: engine-provided symbols not
  in the pack show as `<symbol>`.

### String states

| State | Meaning |
|-------|---------|
| `untranslated` | empty, or identical to the English source |
| `translated` | translated, not yet human-validated |
| `validated` | reviewed and locked (baseline hashes recorded) |
| `stale` | the **English source changed upstream** after validation → re-translate |
| `modified` | the **Italian changed** after validation → re-validate |

`stale` and `modified` are how the ledger lets you track, over time, *which*
translations drift as the game (or a contributor) changes them.

## Is it live?

The dashboard reads the ledger CSV on every interaction — **instant (~100 ms),
no re-scan of the 34k strings.** It reflects the latest *committed* state.

To refresh the numbers after editing translations, click **🔄 Rebuild ledger**
(re-scans the repo, ~1s) — or run `rwit ledger build` from the CLI.

## How it fits the workflow

```
rwit ledger build      # refresh states + hashes
        │
        ▼
dashboard / rwit ledger todo   # see progress · export the worklist
        │
        ▼
translate the worklist (human or external LLM/tool)
        │
        ▼
rwit ledger validate --dlc <X> --yes   # lock reviewed strings as 'validated'
```

The exported worklist (`rwit ledger todo`) is plain text with the English source
next to each string, so an external LLM/tool can translate **only** what is
`untranslated` / `stale` / wrong-language — never the whole corpus.

## Wrong-language detection

The **Wrong language** metric comes from `rwit lang-check`, a deterministic,
offline detector (no LLM) that flags strings accidentally left in French/Spanish/
German. See [`../../docs/TOOLING-LOCALE.md`](../../docs/TOOLING-LOCALE.md) §3a.

## Dependencies

`streamlit` and `lingua-language-detector` (in
[`../requirements.txt`](../requirements.txt)). Everything runs locally and offline.
