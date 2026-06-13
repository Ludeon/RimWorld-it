# Translation Progress Dashboard

A small, multilingual (EN/IT/ES/FR/DE) web dashboard to **see the state of the
translation at a glance** and find what still needs work.

The source of truth stays the XML files and the git-tracked ledger
`translation-ledger.csv` (in this folder). The dashboard reads it for the numbers and
writes back only the **review status** (`validated`/`keep`) when you click a button.

It is a **Flask** app (`server.py`), not Streamlit. **Stateless, no cache**: it re-reads
the CSV + XML fresh on every request (and sends `Cache-Control: no-store`), so it can
NEVER show stale data — that was the whole reason for replacing the old Streamlit `app.py`
(its `@st.cache_data` kept showing old numbers). `app.py` is kept but deprecated.

## Quick start

From the repository root, with the project venv already set up
(see [`../../docs/CONTRIBUTING.md`](../../docs/CONTRIBUTING.md)):

```powershell
# 1. one-time: build the ledger (scans the repo, ~1s)
.venv\Scripts\python scripts\rwit ledger build

# 2. launch the dashboard, then open http://127.0.0.1:5000
.venv\Scripts\python scripts\dashboard\server.py
```

Pick the UI language from the selector at the top (🌐, stored in a cookie). Default is English.
Code changes auto-reload; data changes just need a page refresh (F5).

## What you see

- **Completion %** and a global progress bar.
- **States** breakdown and **per-DLC** progress bars.
- A filterable **worklist** table (by DLC and status) — the strings still to do.

### Tabs

- **Progress / review** — completion %, per-DLC bars, and a per-file table filtered by
  DLC/status. Click **✓ validate** / **keep** on a string or a whole file (writes the CSV;
  sticky across rebuilds).
- **Name generator** — preview the names the game would generate from any RulePack by
  simulating its grammar in Python. Default filter "Namer"; paginator; copyable source file;
  a **template column** showing which `[tag]` each part of a name comes from (so you don't
  delete an important tag); a **copy-for-debug** button (pack + file + names+templates). It
  resolves file-backed symbols from the base-game Defs (e.g. `celestial_name`) and runtime
  `Digit/Letter/RomanNumeral`; only true runtime person names stay as `<symbol>`. For the
  combat/social log, `namegen.generate(..., context={...})` simulates a pawn/body-part/tool to
  verify gender agreement offline.

### String states

| State | Meaning |
|-------|---------|
| `untranslated` | empty, or identical to the English source |
| `translated` | translated, not yet human-validated |
| `validated` | reviewed and locked (baseline hashes recorded) |
| `keep` | intentionally English (loanword/proper noun/format/symbol) — counts as done, sticky |
| `stale` | the **English source changed upstream** after validation → re-translate |
| `modified` | the **Italian changed** after validation → re-validate |

`stale` and `modified` are how the ledger lets you track, over time, *which*
translations drift as the game (or a contributor) changes them.

## Is it live?

Yes. The dashboard re-reads the ledger CSV (and XML for the per-file/review views) **fresh on
every request** — no cache, so it always reflects the current files on disk (not just the last
commit). After editing translations just refresh the page (F5).

To refresh the **states/hashes** after content changes (so `stale`/`modified`/`keep` are
recomputed), click **🔄 Rebuild ledger** (re-scans the repo, ~1s) — or run `rwit ledger build`.

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
German. See [`../../docs/LOCAL-TOOLING.md`](../../docs/LOCAL-TOOLING.md) §3a.

## Dependencies

`flask` and `lingua-language-detector` (in
[`../requirements.txt`](../requirements.txt)). Everything runs locally and offline.
