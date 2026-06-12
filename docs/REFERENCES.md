# Riferimenti

Risorse esterne e repo di altre lingue usati come modello per le scelte di traduzione e
grammatica.

## Repo di altre lingue (in `progetti/rimworld/`)

Cloni locali di language pack ufficiali/community, tenuti accanto a questo repo come
riferimento per rulesStrings, namer e strategia grammaticale:

| Repo | Uso |
|------|-----|
| `RimWorld-de` (tedesco) | **Preso a riferimento** per struttura e namer. ⚠️ Il tedesco usa un motore di **declinazione per i 4 casi** in `WordInfo/`: utile da studiare, ma **non si replica** in italiano. |
| `RimWorld-fr` (francese) | **Modello** per WordInfo: come noi usa **solo `Gender/`**. È il riferimento più vicino all'italiano. |
| `RimWorld-Spanish` (spagnolo) | Gender + extra leggeri (`plural.txt`, `fix_indefinite.txt`…). Prendere solo se serve un caso reale. |

> I cloni di riferimento non fanno parte di questo repo; sono cartelle sorelle in
> `progetti/rimworld/`. Servono per **confrontare** le stesse rulesStrings tra lingue.

## Strategia WordInfo per l'italiano

L'italiano **non ha casi grammaticali**: per una resa corretta bastano
**genere** + **riformulazione delle frasi** (come già fatto nei namer, es. `Namer_Tome`).

- **WordInfo** → solo `Gender/` (genere dei sostantivi). Modello: francese.
- Articoli ed elisione (`il/lo/la`, `un/uno/un'`, `l'`) sono gestiti **lato codice** da
  `LanguageWorker_Italian`, non vanno codificati a mano nei testi.
- Non serve replicare il sistema di declinazione tedesco.

Dettagli sull'uso pratico in [`docs/TRANSLATION-SYNTAX.md`](TRANSLATION-SYNTAX.md) §6.

## Link utili

- **Wiki RimWorld**: https://rimworldwiki.com/ — lore e terminologia ufficiale.
- **Regole grammaticali Ludeon** (sistema di localizzazione, genere, namer):
  https://ludeon.com/forums/index.php?topic=43979.0
- **Versione gioco target**: 1.6.4850.
