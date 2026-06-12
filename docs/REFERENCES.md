# References

External resources and other-language repos used as a model for translation and
grammar choices.

## Other-language repos (in `progetti/rimworld/`)

Local clones of official/community language packs, kept next to this repo as a
reference for rulesStrings, namers, and grammar strategy:

| Repo | Use |
|------|-----|
| `RimWorld-de` (German) | **Used as a reference** for structure and namers. ⚠️ German uses a **4-case declension** engine in `WordInfo/`: worth studying, but **not replicated** in Italian. It is the most complete repo and the model for the data-driven approach. |
| `RimWorld-fr` (French) | **Model** for WordInfo: like us it uses **only `Gender/`** (plus `plural.txt`). The closest reference to Italian. |
| `RimWorld-Spanish` (Spanish) | Gender + light extras (`plural.txt`, `fix_indefinite.txt`…), and a `LanguageWorker_Spanish.cs` we use as the C# reference. Borrow only when a real case calls for it. |

> The reference clones are not part of this repo; they are sibling folders in
> `progetti/rimworld/`. They are used to **compare** the same rulesStrings across languages.

## WordInfo strategy for Italian

Italian **has no grammatical cases**: correct output only needs **gender** + **sentence
rephrasing** (as already done in the namers).

- **WordInfo** → `Gender/` (noun gender) + `plural.txt` (irregular plurals). Model: French/German.
- Articles and elision (`il/lo/la`, `un/uno/un'`, `l'`) are handled **in code** by the stock
  `LanguageWorker_Italian` (already capable), so they should not be hardcoded into the text.
- The German declension system does not need to be replicated.

Practical usage details in [`docs/TRANSLATION-SYNTAX.md`](TRANSLATION-SYNTAX.md) §6 and the
data-driven decision in [`docs/UPDATE-PLAN-1.6.4850.md`](UPDATE-PLAN-1.6.4850.md) §0.

## Useful links

- **RimWorld Wiki**: https://rimworldwiki.com/ — official lore and terminology.
- **Ludeon grammar rules** (localization system, gender, namers):
  https://ludeon.com/forums/index.php?topic=43979.0
- **Target game version**: 1.6.4850.
