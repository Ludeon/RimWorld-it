# RimWorld RulePack grammar (generative text language)

Reference for the small language RimWorld uses to **generate text** at runtime: names
(factions, world/map, gravship), the **combat & social log**, art and book descriptions.
It lives in `RulePackDef`s (in the game: `Data/<DLC>/Defs/RulePackDefs/`; the translatable
side: `<DLC>/DefInjected/RulePackDef/`).

This is **language-agnostic engine documentation** — useful to every language pack. Read it
before editing any `rulesStrings`, especially the combat log. Language-specific notes use
Italian as an example, but the principles apply to any language.

## 1. Structure

```xml
<SomeDef.rulePack.rulesFiles>          <!-- mounts word lists as symbols -->
  <li>symbol->Words/Nouns/Something</li>
</SomeDef.rulePack.rulesFiles>
<SomeDef.rulePack.rulesStrings>        <!-- the actual rules -->
  <li>symbol->text with [other_symbol]</li>
</SomeDef.rulePack.rulesStrings>
```

Every rule is `LEFT->RIGHT`. The **LEFT side is code, never translate it**: the symbol name
plus an optional `(...)` (weight or condition). Translate **only the RIGHT side**.

## 2. Symbols `[...]`

- `[symbol]` is expanded by picking a rule with that LEFT side (or a line from the list in
  `rulesFiles`). Recursive.
- **Indexed symbols**: `[recipient_part0_label]`, `[recipient_part1_label]`… — the number is
  the 0-based index of the element. They appear together with count conditions (§4).
- **Engine grammatical forms**: `[X_label]`, `[X_labelPlural]`, `[X_definite]`,
  `[X_indefinite]`, `[X_gender]`, `[X_pronoun]`, `[X_possessive]`, `[X_objective]`,
  `[X_nameDef]`… These are produced by the `LanguageWorker` (your language's articles /
  pronouns) — **do not invent them**.
- Symbol names (on the left and inside `[...]`) **stay in English**: they are keys, not text.

## 3. Weights `(p=N)` — probability

```xml
<li>r_name(p=2)->...</li>     <!-- weight 2 -->
<li>r_name->...</li>          <!-- implicit weight 1 -->
```
Higher = more likely. **Tune them to the size of the lists**: if one variant draws from a
30-item list and another from a 3-item list, equal weights skew the output. Rule of thumb:
weight ∝ the variant's richness/suitability — don't leave them arbitrary when you split lists
by gender/number.

## 4. Conditions — the language's IF ⚠️

A rule may carry a **constraint** in parentheses: it is chosen **only if the condition holds**
in the current context. It is an IF/switch:

```
LEFT(KEY OP VALUE)->RIGHT
```

**Operators**: `==`, `!=`, `>=` (seen in Core), plus `<=`, `>`, `<` (supported). The KEY is a
**context constant** supplied by the game code:

- **counts**: `recipient_part_count`, `recipient_part_damaged_count`,
  `recipient_part_destroyed_count`, `childCount`, `raidCount`…
- **gender**: `INITIATOR_gender==Female`, `SUBJECT_gender!=Male`…
- **flesh type**: `SUBJECT_flesh==Mechanoid`, `RECIPIENT_flesh!=Mechanoid`
- **booleans**: `deflected!=True`, `INITIATOR_cubeInterest==true`,
  `recipient_part_damaged0_outside==True`

### Canonical example — count (combat log)
From `Core/Defs/RulePackDefs/RulePacks_CombatIncludes.xml`:
```xml
<li>targetlist(recipient_part_count==1)->[recipient_part0_label]</li>
<li>targetlist(recipient_part_count==2)->[recipient_part0_label] and [recipient_part1_label]</li>
<li>targetlist(recipient_part_count==3)->[recipient_part0_label], [recipient_part1_label], and [recipient_part2_label]</li>
```
The engine selects the row by **how many** body parts are involved. In Italian, for example:
```xml
<li>targetlist(recipient_part_count==1)->[recipient_part0_label]</li>
<li>targetlist(recipient_part_count==2)->[recipient_part0_label] e [recipient_part1_label]</li>
<li>targetlist(recipient_part_count==3)->[recipient_part0_label], [recipient_part1_label] e [recipient_part2_label]</li>
```
- `and` → the language's conjunction (Italian `e`); the list `X, Y, and Z` → `X, Y e Z`
  (Italian uses no Oxford comma — adjust to your language).
- The condition `(...==N)` is **never translated**: it is code.

## 5. Golden rules for translators

1. **Left side invariant, condition included**: `damaged_targets(recipient_part_damaged_count==2)`
   stays identical; translate only after `->`.
2. **Same number of `<li>` and same conditions** as the `<!-- EN: -->` comment: every branch
   (==1/==2/==3, ==Female/!=Female, ==Mechanoid…) must be kept. Do not merge or drop branches.
3. **Count-driven agreement**: the `==1` branch is **singular**, the `==2/==3` branches are
   **plural**. The verb, article and participle in the template that consumes `[targetlist]`
   must agree branch by branch.
4. **Generated plurals/articles** come from the `LanguageWorker` + `WordInfo/` (gender and
   `plural.txt`). Irregular noun plurals go in `WordInfo/plural.txt`, not hardcoded into the
   rules (Italian example: braccio→**braccia**, osso→ossa). See
   [`NAME-GENERATION-AND-GRAMMAR.md`](NAME-GENERATION-AND-GRAMMAR.md).
5. **Gender in generated proper names**: avoid a fixed-gender leading article in front of a
   mixed-gender list. Robust strategies: apposition, a complement (`of [X]`), gender-invariant
   adjectives, or **lists split by article/gender/number** with coherent weights. (For Italian
   these variants are produced with `rwit variants` via Morph-it!.)
6. **`(p=N)` rewritten identically** unless you deliberately rebalance against list sizes.

## 6. Other directives

- **Gender ternary** inside the final text: `{X_gender ? male : female : neutral}` — picks a
  **letter/word** in the text. Different from the `(X_gender==Female)` condition on the LEFT,
  which picks a **rule**. (Italian usage: see `TRANSLATION-SYNTAX.md §3`.)
- **`{replace: ...}` / `{lookup: ...}`** — string operations applied **after** a sub-rule is
  resolved (see §8 for the full syntax). Used heavily by German for its case system. Rare;
  if present in the EN comment, preserve it.
- **Capitalization**: the engine capitalizes the first letter of the final result; list entries
  stay lowercase except proper nouns.

## 7. Articles in generated text — the entity-bridge pattern ⚠️

`[X_definite]` / `[X_indefinite]` add the article (`il/lo/la/l'`, `un/uno/una/un'`) **only when
`X` is a real grammatical entity** that carries gender. Two kinds of symbol look alike but
behave differently:

| Symbol | What it is | Has gender → article? |
|--------|-----------|-----------------------|
| `[WEAPON_…]`, `[PROJECTILE_…]`, `[INITIATOR_…]`, `[RECIPIENT_…]` (UPPERCASE) | a full entity from the game code (`GrammarUtility.RulesForDef`): label **plus** `_gender`, `_definite`, `_indefinite`, `_possessive`… | **yes** — gender resolved from the def + `WordInfo/Gender`, article correct |
| `[projectile]`, `[implement]`… (lowercase) | a **convenience symbol** defined *inside the rulePack* (`projectile->[WEAPON_projectile_label]`), usually just a **label string** | **no** — no `_gender`, so `[projectile_definite]` falls back to the bare label with **no article** |

So writing `[projectile_definite]` does **not** auto-produce an article: if the rulePack only
defines `projectile` (the label), the `_definite` suffix has no gender to work with and you get
the bare word (`Proiettile di X ha colpito…` instead of `Il proiettile di X…`).

**Fix (the French model): bridge the lowercase symbol to the UPPERCASE entity** for every form
you use. In `Combat_RangedBase`:

```xml
<li>projectile(WEAPON_missing==True, p=3)->[PROJECTILE_label]</li>
<li>projectile_definite(WEAPON_missing==True, p=3)->[PROJECTILE_definite]</li>
<li>projectile_indefinite(WEAPON_missing==True, p=3)->[PROJECTILE_indefinite]</li>
<li>projectile->[WEAPON_projectile_label]</li>
<li>projectile_definite->[WEAPON_projectile_definite]</li>
<li>projectile_indefinite->[WEAPON_projectile_indefinite]</li>
```

Now `[projectile_definite]` resolves through the entity, which picks the article from the
projectile's gender (`il proiettile` / `la freccia`; `un proiettile` / `una granata`). For this
to be correct the head-noun of each label must have the right gender in `WordInfo/Gender`
(Italian example: `freccia` belongs in `Female.txt`, or you get `il freccia`). The
`WEAPON_missing==True` branch covers shots that have a projectile def but no weapon (e.g. bows
vs thrown).

> **Why not the German `{replace:}` trick?** German needs to bend the noun through four
> grammatical **cases** (Nominativ/Akkusativ/Dativ/Genitiv), which the article suffixes can't
> express, so it post-processes the resolved string (§8). Italian (like French/Spanish) only
> needs the **article**, which the engine already provides via the UPPERCASE entity — so the
> bridge above is enough; the `{replace:}`/`{lookup:}` machinery is unnecessary here.

## 8. The German string operations `{replace:}` / `{lookup:}` (reference)

You will see these in the German pack and occasionally in EN comments. They run **after** the
inner symbols are resolved, operating on the produced string. Italian does not use them, but
recognize them so you can preserve them verbatim when copying EN comments:

- **`{replace: TEXT; "find"-"replace"; …}`** — resolve `TEXT`, then apply literal
  find→replace substitutions. German uses it to repair contractions/forms after assembly, e.g.
  `{replace: [INITIATOR_label]'s [blast]; "Feuer's Explosion"-"Eine durch Feuer ausgelöste Explosion"}`.
- **`{lookup: [SYMBOL]; decline; CASE}`** — resolve `[SYMBOL]`, then **decline** it to a
  grammatical case via the language's declension table (`CASE`: `1`=Nom, `2`=Gen, `3`=Dat,
  `4`=Akk). This is the core of German's case handling; Italian has no equivalent need.

**Rule for us**: never *add* these to Italian rules (we solve agreement with gender conditions,
`[X_definite]`, the entity bridge above, and `WordInfo`); only **preserve** them unchanged if
they appear inside a `<!-- EN: -->` comment.

## 9. Related tools (this repo)

- `rwit variants` — generates morphological variants (gender/number/article) via Morph-it!.
- Offline preview: dashboard → **Name generator** tab (`scripts/dashboard/`), or
  `scripts/rwit/namegen.py`. Shows what a rulePack would generate without launching the game.
- `rwit strings-diff` — aligns `Words/Names` lists with the game's English (the source of truth).
