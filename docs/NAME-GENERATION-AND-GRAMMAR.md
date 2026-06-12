# Name generation, plurals and grammar (Italian)

How RimWorld builds names, articles, plurals and generated text at runtime for Italian, and
what we can (and cannot) change. Three pieces working together:

```
   CODE (game DLL)               DATA (this repo)                   DATA (this repo)
   ┌───────────────────┐        ┌───────────────────┐             ┌───────────────────┐
   │ LanguageWorker_   │  uses  │ WordInfo/Gender/   │   vocab.    │ Strings/          │
   │ Italian           │◄───────┤ Male/Female/Neuter │◄────────────┤ Names/, Words/    │
   │ articles, plurals │ gender │ (noun gender)      │  assembled  │ (names, adjectives)│
   └───────────────────┘        └───────────────────┘   by ──────► └───────────────────┘
            ▲                                                  rulesStrings / RulePackDef
            └────────────────── called by the grammar engine ───────────────────┘
```

> **Data vs code — where to work.** Daily maintenance lives in the **text files** (DATA):
> `WordInfo/Gender` (the gender of each word) and the singular/plural pairs for irregulars.
> The `LanguageWorker` (CODE) **reads** that data and applies the article/plural. With the
> worker **already in the game** + the right data, most of the grammar works **without
> touching the `.cs`**.
>
> **Decision (2026-06-12): go data-driven (German style).** The shipped Italian worker is
> already capable (singular articles from gender; `Pluralize` reads `WordInfo/plural.txt`),
> and German ships no custom worker. So we drive grammar from DATA (`WordInfo/Gender` +
> `plural.txt`) and from explicit articles in the rulesStrings. The improved
> `LanguageWorker_Italian.cs` (root) is an **optional bonus** for edge cases, not daily
> maintenance. See [`UPDATE-PLAN-1.6.4850.md`](UPDATE-PLAN-1.6.4850.md) §0.

---

## 1. `LanguageWorker_Italian` (code, inside the game DLL)

It is a **C# class compiled into the game** (`Verse.LanguageWorker_Italian`). The engine
resolves it by name (`LanguageWordInfo`/`LoadedLanguage`), per language.

> The devs **already provide it**: it exists in `Assembly-CSharp.dll` next to French, German,
> Spanish… Only the **reference `.cs`** was missing from our repo. It is now in the root, in an
> **improved** version: [`LanguageWorker_Italian.cs`](../LanguageWorker_Italian.cs) (base
> decompiled from RimWorld 1.6.4850 with ILSpy).

### What the STOCK worker already does (decompiled)
- **Indefinite article** `WithIndefiniteArticle` → un / uno / una / un' (s-impure, ps/pn/z/x/y/gn).
- **Definite article** `WithDefiniteArticle` → il / lo / la / l' (singular), correctly.
- **Pluralize**: tries `TryLookupPluralForm` first (reads `WordInfo/plural.txt`), then a naive
  vowel-swap fallback (Female → -e, Male → -i).
- **Ordinals** `OrdinalNumber` → `N°`.

So **singular articles and irregular plurals are already correct via data** (gender +
plural.txt). The stock worker's gaps: plural articles `i/gli/le` (it ignores `plural`), and the
naive regular Pluralize on `-io`/`-ca`/`-ga`/`-cia`/`-gia` (which we route through `plural.txt`).

### Improved `.cs` (root) — optional
The root file adds: `lo`/`gli` for gn/ps/pn/x/y/i+vowel, mute `h`, **plural** articles
(i/gli/le, partitives dei/degli/delle), the `-io`/`-ca`/`-ga` plural fixes, and heteroclite
handling. Signatures verified against the decompiled base and `LanguageWorker_Spanish.cs`
(overrides `WithIndefiniteArticle`/`WithDefiniteArticle`/`Pluralize`/`OrdinalNumber`).

⚠️ **Being in the repo is not enough**: a language pack is data only and does NOT load `.cs`.
To make it take effect you need an **upstream PR to Ludeon** (they compile it into the game) or
a **companion mod** (Harmony patch on the methods, or a class swapped in at runtime). Since the
stock worker + data already cover most cases, this is a low priority.

---

## 2. `WordInfo/Gender/` (data — noun gender)

Lists that tell the LanguageWorker **the gender of a noun**, so it picks the right article and
plural:

| File | Content | Lines |
|------|---------|-------|
| `Male.txt` | masculine nouns | ~2070 |
| `Female.txt` | feminine nouns | ~1020 |
| `Neuter.txt` | neuter/genderless nouns | ~166 |
| `new_words.txt` | new words not yet classified (collected by the game) | 0 |

Practical rule to populate them: gender from the ending (**-o → M**, **-a → F**), with the
ambiguous **-e** ones decided by hand. The engine resolves gender by string via
`LanguageWordInfo.ResolveGender(str)` (default Male if not found) — so the **plural forms** of
heteroclite nouns (braccia, ossa…) are added to `Female.txt` so the article comes out "le".

### English entries: usually a symptom, not a gender-file bug
An English entry in `Gender/*.txt` almost always reflects a **source label untranslated
elsewhere** (the item/plant still has the English `.label`): in that case the gender entry is
*correct* and should be fixed **at the source** (the `.label` in DefInjected), not here. A
future `rwit wordinfo` tool could reconcile the gender lists with the translated `.label`s.

---

## 3. `Strings/` (data — the vocabulary for the namers)

The raw material the `rulesStrings` assemble. Two main branches:

### `Strings/Names/` — proper names
`Animal_Female.txt`, `Animal_Male.txt`, `Animal_Unisex.txt`, `Business.txt`, `Celestial.txt`,
`OutlanderTown.txt`, `WorldFeatures/`…

### `Strings/Words/` — common vocabulary
`Nouns/`, `Adjectives/`, `Verbs/`, `Misc/`, `Foreign/`. Here Italian provides the **explicit
inflected variants**, because gender/number cannot always be derived in code. Generated with
`rwit variants` (Morph-it!). Recurring scheme:

```
AnimalGroups_Singular_Feminine.txt   AnimalGroups_Plural_Feminine.txt
Badass_Plural_Feminine.txt           Badass_Plural_Masculine.txt   (adjectives)
Animals_Badass_I.txt  Animals_Badass_Le.txt   (nouns, bucketed by article)
```

### ⚠️ The positional paired files (singular ↔ plural)
Legacy pairs like `Animals.txt` / `AnimalsPlural.txt` are NOT matched by comparing words: they
are **synchronized by line position**. Line *N* of the plural file is the plural of line *N* of
the singular. Fragile: adding/removing/reordering **one** line in only one of the two shifts all
lines below and every following animal gets the wrong plural, **silently**. The English does
**not** have `AnimalsPlural.txt` (its LanguageWorker does regular `+s`): it is an Italian-only
file, and it is **NOT** what `Pluralize` uses (see below). Prefer the keyed `plural.txt`.

### ✅ The real plural mechanism: `WordInfo/plural.txt` (keyed, generic)
Decompiling the base `LanguageWorker` shows that `Pluralize → TryLookupPluralForm` reads a
**keyed dictionary**, not the positional files:
```csharp
var table = LanguageDatabase.activeLanguage.WordInfo.GetLookupTable("plural"); // WordInfo/plural.txt
string key = str.ToLower();           // lookup BY WORD, not by position
plural = table[key][1];
```
- It is **generic** (works with the stock worker, any language) and **robust** (key→value: it
  cannot drift like the positional files).
- Format (like German): `Singular;Plural` lines, with `//` comments.
- **Status (2026-06-12): `WordInfo/plural.txt` now EXISTS** for Italian, with the heteroclite
  body-part plurals (braccio→braccia, osso→ossa, ginocchio→ginocchia, dito→dita, labbro→labbra).
  A future `rwit wordinfo` (the equivalent of German's `update-wordinfo-plural.ps1`) could batch
  it from Morph-it!. No `.cs` to deploy.

### Convention: article comment at the top of a file
Name files start with a comment fixing the group's article, e.g.:
```
//la, una
moltitudine
schiera
```
Article rules (l'/lo/il/la, singular, special lexical genders) are in
[`TRANSLATION-SYNTAX.md`](TRANSLATION-SYNTAX.md) §6.

### What to translate and from where (source = English)
The **source of truth** is the game's English (`Data/<DLC>/Languages/English/Strings`): it
defines *which* files/symbols exist. The worklist comes from a **diff IT-vs-EN** (tools:
`rwit strings-diff`, `rwit reconcile`). By list type:
- **Proper names** (`Strings/Names/`: animals, people, towns, celestial) = **pool**: kept in
  English (Abby, Akira…). Not translated; at most curated/enriched.
- **Word lists** (`Strings/Words/`: Adjectives, Verbs, Nouns, colors…) = **translated**
  (red→rosso): assembled into Italian sentences.
- **`WordInfo/Gender` and `plural.txt`** = Italian-specific, derived from **our** translated
  labels (ideally Morph-it!), **not** copied from EN/DE.
- **German** = model of the **mechanism** (it has `WordInfo/plural.txt`), not a source of names.

---

## 4. `rulesStrings` / `RulePackDef` — the grammar that assembles everything

Full reference of the rule language in [`RULEPACK-GRAMMAR.md`](RULEPACK-GRAMMAR.md). In
`DefInjected/RulePackDef/` the `<li>left->right</li>` rules compose the pieces above using
`[references]` and weights `(p=N)`:

```xml
<li>title(p=2)->[mapType] [mapNoun] di [subject]</li>
```
- `[mapType]`, `[subject]` → drawn from other rules / `Strings/` lists.
- `(p=2)` → this variant is chosen with **weight 2** (more likely). It is on the left side, copy
  it verbatim.

### How a `Strings/` file becomes available: `<rulesFiles>`
A `rulePack` has two lists: `<rulesStrings>` (inline rules) and **`<rulesFiles>`**, which
**mounts a `Strings/` file under a symbol**:
```xml
<rulePack>
  <rulesFiles>
    <li>tribal_word_file->Words/Foreign/Tribal</li>   <!-- → Strings/Words/Foreign/Tribal.txt -->
    <li>place_end->WordParts/PlaceEndings</li>          <!-- → Strings/WordParts/PlaceEndings.txt -->
  </rulesFiles>
</rulePack>
```
- Syntax: `<li>symbol->RelativePath</li>`, **relative to `Strings/`, without `.txt`**. Then
  `[symbol]` in the rulesStrings draws a random line from that file.
- ⚠️ **Key difference**: **`Strings/`** files must be registered with `rulesFiles`; **`WordInfo/`**
  files (`Gender/`, `plural.txt`) must NOT — the engine auto-loads them per language. So
  `WordInfo/plural.txt` needs nothing in the XML.

---

## 5. Generated-log grammar (combat/social) — the historical problem

Combat logs and social interactions are **generated** by the rulesStrings (`RulePacks_Combat*`,
`RulePacks_Damage*`, `RulePacks_Maneuvers`, `Interactions_*`). Historically the **most wrong**
part of the Italian translation.

### Root cause (measured)
The engine offers a gender mechanism; Italian almost never used it. `_gender==Male/Female`
constraints in the combat rulesStrings:

| Language | Gender constraints |
|----------|-------------------|
| French | 122 |
| Spanish | 100 |
| German | 95 |
| **Italian** | **1** |

Italian rules have **fixed** articles/participles (`nella [recipient_part0_label]`, `colpito`)
correct for one gender only → sentences like "X ha colpito Y nella braccio" or masculine
participles for feminine subjects. Also, body parts were largely **missing from
`WordInfo/Gender`** — now **added** (~60, incl. mano=F, pelle=F), so the automatic
`[part_definite]` path can place the right article.

### The engine's two tools to fix it
1. **Gender constraint on the rule** (left side), as French does:
   ```xml
   <li>r_logentry(p=0.1,RECIPIENT_gender==Male)->[INITIATOR_definite] [damaged_past] nel [recipient_part0_label] ...</li>
   <li>r_logentry(p=0.1,RECIPIENT_gender==Female)->[INITIATOR_definite] [damaged_past] nella [recipient_part0_label] ...</li>
   ```
   Syntax: `ruleName(p=WEIGHT, SYMBOL_gender==Male|Female)`. The resolver picks the variant
   matching the resolved entity's gender.
2. **`[X_definite]` / `[X_indefinite]` suffixes**: the engine applies the correct article via
   `LanguageWorker` + `WordInfo/Gender`. E.g. `[recipient_part0_definite]` → "il braccio" /
   "la gamba" automatically, **if** the part is in WordInfo with the right gender.

### Fix strategy
- Replace hand-written articles before `[X_label]` with `[X_definite]`/`[X_indefinite]`.
- Where participle/adjective agreement is needed, split the rule with `(SYMBOL_gender==Male/Female)`
  constraints — **template = the French/Spanish packs** (same symbols).
- Populate `WordInfo/Gender` with the body parts and nouns used in the logs (done).
- Verify **in game** (Dev mode: combat-log / interaction generators) on a male and a female pawn.
- Order by impact: CombatMelee → CombatRanged → Damage → DamageEvent → Maneuvers → social
  Interactions → Battles/Tales.

The count branches (`recipient_part_count==1/2/3`) are already translated correctly (`e`, no
Oxford comma). See [`RULEPACK-GRAMMAR.md`](RULEPACK-GRAMMAR.md) §4.

## 6. Review plan for this area

- [ ] Keep `LanguageWorker_Italian.cs` (root) updated each game version; evaluate deploy (upstream
  PR or companion mod) only if data-driven proves insufficient.
- [ ] **Generated log**: apply the §5 fix strategy (gender constraints + `[X_definite]`), starting
  from a template pack (e.g. `Combat_Deflect`) verified in game.
- [ ] **WordInfo/Gender**: translate any remaining English, check doubtful (-e) genders, empty
  `new_words.txt` by reclassifying.
- [ ] **Strings**: keep singular/plural × masculine/feminine consistent; align lists to the game's
  English (`rwit reconcile`).
- [ ] **rulesStrings**: left side and `(p=N)` weights unchanged (guaranteed by validation).
- [ ] (Tooling) `rwit wordinfo` for gender auto-maintenance; `rwit compare` to compare the same
  rulesStrings with fr/es/de.
