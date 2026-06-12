# Translation validation and integrity

Two distinct things:
1. **Track which files have been validated** (an Excel/CSV sheet).
2. **Make sure the translation did not alter game logic** — in particular the
   **event priorities/frequencies**.

---

## 1. Can the translation change event priorities? **No.**

> Concern raised: "did translating also lose or change the weights/priorities with which
> the various events appear?"

**Short answer: no, it is impossible by construction.** Verified on the repo.

### Why
RimWorld cleanly separates two things:

| What | Where it lives | In our repo? |
|------|----------------|--------------|
| Event **logic/numbers**: which incidents appear, frequency, weight, refire, conditions (`IncidentDef.baseChance`, `commonality`, `selectionWeight`, `minRefireDays`, StorytellerDef…) | in the game **Defs** (the install's `Data\` folder) | ❌ **NO** |
| **Text** shown: labels, descriptions, letter text, generated stories | in the **language pack** (`DefInjected/`, `Keyed/`) | ✅ yes |

A language pack **only injects the text fields** of the Defs. It does not — and cannot —
contain the numeric fields that govern event frequency.

### Proof on the repo
Search for event frequency/weight fields in the translation files:

```
selectionWeight | commonality | baseChance | minRefireDays | <weight> | <chance>
→ 0 real occurrences (the only hit is a word inside a UI string)
```

So: even though *Clean languages* rewrote the files, **there is no event weight to lose or
change** in this repo. Event priorities remain those of the game's English Defs, intact.

### The one exception: the `(p=N)` weights in rulesStrings
There is **only one** kind of "weight" in our files: the `(p=N)` markers in
`rulesStrings`/`RulePackDef` (e.g. `<li>title(p=2)->...`). **1456** across 79 files.

- They do not govern *which events happen*, but **which text variant** is chosen
  (e.g. which name/description among several alternatives).
- They sit on the **left side** of the `->` arrow, so they must be **copied verbatim**.
- An altered weight here would only change the probability of a *sentence*, not an event.

The per-file `(p=N)` count is in the dedicated column of `VALIDATION-FILES.csv`: files with a
high value are the ones to check most carefully (left side unchanged).

> **Rule**: in rulesStrings never touch the left side, including `(p=N)`.
> See [`TRANSLATION-SYNTAX.md`](TRANSLATION-SYNTAX.md) §4.

---

## 2. File validation sheet (`VALIDATION-FILES.csv`)

An inventory of **all** the repo's translation files, to tick off as they get validated with
Claude Code. It is a **CSV** (opens in Excel, but stays diffable in git — a binary `.xlsx`
would not).

Columns:

| Column | Meaning |
|--------|---------|
| `DLC` | Core / Royalty / Ideology / Biotech / Anomaly / Odyssey |
| `Type` | DefInjected / Keyed / Strings / WordInfo |
| `File` | relative path |
| `VariantWeights(p=N)` | how many weighted rulesStrings it contains (higher = pay more attention to the left side) |
| `Validated` | `no` / `yes` |
| `ValidationDate` | date of the check |
| `Notes` | observations (bugs found, doubts…) |

### Validation flow for a file
For each file, Claude Code checks:
- [ ] Well-formed XML, no missing/duplicated broken tag
- [ ] Variables `[VAR]` and `{VAR}` intact (name and positional index)
- [ ] Valid gender ternaries (a single `?`, 2 or 3 branches; the 3rd = neuter form, not an error)
- [ ] rulesStrings: every `<li>` has a `->`, **left side unchanged** (including `(p=N)`),
      same number of `<li>` as English
- [ ] `\n\n` preserved
- [ ] `<!-- EN: -->` comments unchanged
- [ ] Quality: naturalness, no calques, consistent terminology

Then set `Validated=yes`, `ValidationDate`, and any `Notes`.

### Regenerating the inventory
When files are added/removed (new game version), regenerate the list while keeping the ticks
already made. A candidate for a tooling command: **`rwit validate`** (see below).

---

## 3. Future tooling: `rwit validate` (proposed)

A command that automates the mechanical checks and updates the CSV:
- Well-formed XML (lxml).
- Gender ternaries: every `{... ? ...}` has a single `?` and **2 or 3 branches** (`: b` or
  `: b : c`, where the 3rd is the neuter/None form). Flag only the genuinely malformed ones
  (0 branches, 4+ branches, double `?`). ⚠️ A 3-branch ternary is **not** a bug.
- rulesStrings: every `<li>` has a single `->`; compare the **left side** (including `(p=N)`
  weights) with the game's English to catch drift.
- Variables `[VAR]`/`{N}` consistent between the EN comment and the translation.

It leaves only the **linguistic quality** part to the human/Claude. The mechanical checks
above are exactly the ones that guarantee integrity (including `(p=N)` weights).
