# Translation syntax — RimWorld Italian

Reference for the syntax you can (and must) use in the translation files. Applies to
`DefInjected/`, `Keyed/` and the `rulesStrings`. Operational rules are in `CONTRIBUTING.md`;
this file documents the **RimWorld engine syntax**. Examples are in Italian (this is the
Italian pack), but the engine syntax is the same for any language.

---

## 1. File structure

Each file is a `LanguageData` XML. Two families:

- **Keyed** (`<DLC>/Keyed/*.xml`): key→text pairs for the interface.
  ```xml
  <LanguageData>
    <!-- EN: Required -->
    <Required>Richiesto</Required>
  </LanguageData>
  ```
- **DefInjected** (`<DLC>/DefInjected/<DefType>/*.xml`): translations of Def fields.
  The key is the **def path**: `DefName.field` or `DefName.sub.field`.
  ```xml
  <!-- EN: ancient bridge -->
  <AncientBridge.label>ponte antico</AncientBridge.label>
  ```

### `<!-- EN: ... -->` comments
They show the English original. **Copy them verbatim, never translate them.** When the game
updates the English, it rewrites these comments: if only an English typo changed, the Italian
translation below **must not be touched**.

### Empty tags = TODO
`<tag />` or `<tag></tag>` are to be translated: insert the translation of the preceding
`<!-- EN: -->` comment.

---

## 2. Variables — never translate the name

Two notations, both to be **left intact** in the name:

| Form | Where | Example |
|------|-------|---------|
| `[VARIABLE]` | DefInjected, rulesStrings, backstory | `[PAWN_nameDef]`, `[WEAPON_label]` |
| `{VARIABLE}` | Keyed, letters | `{PAWN_labelShort}`, `{FACTION_name}`, `{0}`, `{1}` |

Translate **only the text outside** the brackets.

```xml
<!-- EN: {0} is low on resources -->
<AlertWarqueenHasLowResources>{0} ha poche risorse</AlertWarqueenHasLowResources>
```

Common pawn variable suffixes (useful for agreement): `_nameDef`, `_nameFull`, `_labelShort`,
`_pronoun` (lui/lei), `_possessive` (suo/sua), `_objective` (lo/la), `_gender`.

> ⚠️ Positional variables `{0}`, `{1}`, `{0_label}`, `{1_gender}` must remain and keep the
> same index as the English: changing the number breaks the in-game text.

---

## 3. Gender: the ternary notation

Italian agrees adjectives/participles to gender. RimWorld offers a **ternary** with **two or
three branches**:

```
{VARIABLE_gender ? MASCULINE : FEMININE}              # 2 branches
{VARIABLE_gender ? MASCULINE : FEMININE : NEUTER}     # 3 branches
```

The engine maps gender as: **Male → 1st branch, Female → 2nd branch, None → 3rd branch**.
Gender `None` covers things **without gender**: items, buildings, animals of unknown sex
(e.g. `{CRAFTED_gender ...}`, `{0_gender ...}` of an item). That is why the 3-branch form is
**valid and common** (fr/de/es use it too).

### Three uses

**Inline, 2 branches** (single ending — the most frequent case for pawns):
```
stat{PAWN_gender ? o : a} uccis{PAWN_gender ? o : a}
→ "stato ucciso" / "stata uccisa"
```

**3 branches** (when the neuter form is needed for gender `None`):
```
è entrat{0_gender ? o : a : o}                    # masc / fem / neuter
{CRAFTED_gender ? un : una : uno} {CRAFTED_labelShort}
{PAWN_gender ? morto : morta : mortə}             # neuter with schwa
```
The 3rd branch can repeat the masculine (`o : a : o`) or use an explicit neuter form
(`o/a`, `o(a)`, `ə`, `*`). Both choices are accepted; **keep the file's style**.

**Whole word/phrase**:
```
{PAWN_gender ? un bambino : una bambina}
{PAWN_gender ? stato ucciso : stata uccisa}
```

### Which variable
Use the same root as the variable present in the text: `PAWN_gender`, `HEIR_gender`,
`CRAFTED_gender`, or the positional `{0_gender ? o : a}` when the text uses `{0}`.

### What is actually an error

| ❌ Wrong | ✅ Correct | Why |
|----------|-----------|-----|
| `entrat{0_gender ? o : a}` on a subject that can be `None` | `entrat{0_gender ? o : a : o}` | missing neuter branch: with gender `None` the engine finds no form |
| `{0_gender ? o : a : o : x}` | `{0_gender ? o : a : o}` | **four** branches: the max is 3 |
| `statoa` | `stat{PAWN_gender ? o : a}` | wrong concatenation of the branches |

> **Golden rule**: the ternary has **2 or 3 branches** separated by `:`, with **a single `?`**.
> `{ ? a : b }` and `{ ? a : b : c }` are both correct. `{ ? a : b : c : d }` is not.
> ⚠️ Do not "fix" a 3-branch ternary by removing the third: it is the neuter (None) form,
> not a bug — verified on the fr/de/es language packs.

---

## 4. rulesStrings (generative grammar)

> ⚠️ Full reference for the language (conditions `(count==N)`, gender constraints, weights,
> indexed symbols, combat log): [`RULEPACK-GRAMMAR.md`](RULEPACK-GRAMMAR.md).
> This section only covers the basics.

Rule lists the game composes to generate text (names, descriptions, stories). Each `<li>` has
the form `LEFT->RIGHT`:

```xml
<li>subject->generazione di energia da bioferrite</li>
<li>subject_story->fu addestrat{PAWN_gender ? o : a} all'uso di fonti innovative</li>
```

Rules:
- The **literal `->` arrow** (never `>`, never `-&gt;`).
- **Left side unchanged** (it is an engine identifier): translate **only the right side**.
- Same **number of `<li>`** as the original.
- Inside the right side you can use `[VARIABLES]` and gender ternaries.
- Final check: every `<li>` must contain **exactly one `->`**.
  If it is missing (`<li>introduction>…`), fix it to `<li>introduction->…`.

The `<!-- EN: -->` comments of the rulesStrings contain the multi-line English block: copy
them verbatim.

---

## 5. Line breaks and formatting

- The `\n\n` (and `\n`) sequence is **literal**: rewrite it **identically**, without actually
  breaking the line in the XML. This applies both in comments and in text.
  ```xml
  <Tutorial>Riga uno.\n\nRiga due.</Tutorial>
  ```
- Keep the original indentation and structure.
- Always return the **complete** XML, without omitting tags (even duplicated ones).

---

## 6. Articles and elision — who does what

Italian **has no cases** (unlike German): **gender** + sentence **rephrasing** are enough.
Articles and elision (`il/lo/la`, `un/uno/un'`, `l'`) are largely handled **in code**
(`LanguageWorker_Italian`) and by the data in `WordInfo/Gender/`.

When you must choose an article by hand (e.g. in name lists), quick rules:
- **l'** = singulars (m/f) starting with a vowel → *l'accento, l'idea*
- **lo** = masculine with s+consonant, z, ps, gn, x, y → *lo sguardo, lo zaino*
- **il** = masculine with another consonant
- **la** = feminine with a consonant
- Respect special lexical genders (e.g. *la fronte*).

---

## 7. Terminology (RimWorld lore)

Terms fixed for consistency:

| English | Italian |
|---------|---------|
| ideoligion | ideologia |
| scarification | incisione rituale |

Principle: fidelity **+ naturalness**. Avoid literal calques; prefer the most idiomatic and
"playable" form (e.g. a correct but stiff scientific term → a simpler version in the game
context).

---

## 8. Final checklist for each file

- [ ] Only text outside `[ ]` and `{ }` translated
- [ ] Every gender ternary has **a single `?`** and **2 or 3 branches** (`: b` or `: b : c`); the 3rd is the neuter form, not an error
- [ ] rulesStrings: `->` present in every `<li>`, left side unchanged, same number of `<li>`
- [ ] `\n\n` preserved identically
- [ ] `<!-- EN: -->` comments copied verbatim
- [ ] Well-formed XML, no missing tag
- [ ] Positional variables `{0}`, `{1}` with the same index as the English
