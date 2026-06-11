# Generazione di nomi, plurali e grammatica (italiano)

Come RimWorld costruisce a runtime nomi, articoli, plurali e testi generati per
l'italiano, e cosa possiamo (e non possiamo) modificare. Tre pezzi che lavorano insieme:

```
   CODICE (DLL del gioco)        DATI (questo repo)                 DATI (questo repo)
   ┌───────────────────┐        ┌───────────────────┐             ┌───────────────────┐
   │ LanguageWorker_   │  usa   │ WordInfo/Gender/   │   vocab.    │ Strings/          │
   │ Italian           │◄───────┤ Male/Female/Neuter │◄────────────┤ Names/, Words/    │
   │ articoli, plurali │ genere │ (genere dei nomi)  │  assemblati │ (nomi, aggettivi) │
   └───────────────────┘        └───────────────────┘   da ──────► └───────────────────┘
            ▲                                                  rulesStrings / RulePackDef
            └────────────────── chiamato dal motore di grammatica ──────────────┘
```

---

## 1. `LanguageWorker_Italian` (codice, dentro la DLL del gioco)

È una **classe C# compilata nel gioco** (`Verse.LanguageWorker_Italian`), dichiarata in
`Core/LanguageInfo.xml` → `<languageWorkerClass>LanguageWorker_Italian</languageWorkerClass>`.

> Gli sviluppatori **l'hanno fornita**: esiste nell'`Assembly-CSharp.dll` accanto a
> French, German, Spanish… Mancava solo il **file `.cs` di riferimento** nel nostro repo.
> Ora c'è: [`Notes/LanguageWorker_Italian.cs`](../Notes/LanguageWorker_Italian.cs)
> (decompilato da RimWorld 1.6.4850 con ILSpy, come i `.cs` di fr/es).

### Cosa fa
- **Articolo indeterminativo** `WithIndefiniteArticle` → un / uno / una / un'
  - Femm. + vocale → **un'** (un'arma) · Femm. + consonante → **una**
  - Masch. + s+consonante → **uno** (uno sgabello) · Masch. + ps/pn/z/x/y/gn → **uno**
    (uno psicologo, uno zaino) · altrimenti → **un**
- **Articolo determinativo** `WithDefiniteArticle` → il / lo / la / l'
  - Femm. + vocale → **l'** · Femm. + consonante → **la**
  - Masch. + z → **lo** · Masch. + s+consonante → **lo** · Masch. + vocale → **l'**
    · altrimenti → **il**
- **Plurale** `Pluralize`:
  1. prova prima `TryLookupPluralForm` (forme esplicite nei dati / `count`),
  2. se l'ultima lettera **non** è vocale → invariato (parole straniere: "cobra"→"cobra"),
  3. Femm. che finisce in vocale → ultima lettera **→ e** (mela→mele),
  4. Masch. che finisce in vocale → ultima lettera **→ i** (gatto→gatti).
- **Ordinali** `OrdinalNumber` → `N°` (1°, 2°, …).
- **IsVowel** considera solo `a e i o u` (niente accentate, niente `h`).

### Limiti noti (candidati a miglioramento)
Questi sono limiti del **codice del gioco**, non dei nostri dati:
- **`il psicologo` invece di `lo psicologo`**: l'articolo *determinativo* NON gestisce
  gn/ps/x/y/pn (l'indeterminativo sì). Incoerenza reale.
- **Plurali `-ca/-ga/-co/-go`** non gestiti: "amica" → "amice" anziché "amiche".
  Mitigato dalle liste di plurale esplicite e dal lookup WordInfo.
- **IsVowel** senza vocali accentate/`h`: casi marginali in italiano.

### ⚠️ Come modificarlo davvero
Un language pack è **solo dati**: non può sostituire o ricompilare un LanguageWorker.
Per cambiarne il comportamento ci sono due strade:
1. **PR upstream a Ludeon** (mantengono loro questi worker) — la via "pulita" per la
   traduzione ufficiale.
2. **Mod companion** con assembly compilato (es. patch Harmony che fa override dei metodi).
Il file in `Notes/` resta comunque utile come riferimento e base per entrambe.

---

## 2. `WordInfo/Gender/` (dati — il genere dei nomi)

Tre liste che dicono al LanguageWorker **di che genere è un nome**, così sceglie l'articolo
e il plurale giusti:

| File | Contenuto | Righe |
|------|-----------|-------|
| `Male.txt` | nomi maschili | ~2043 |
| `Female.txt` | nomi femminili | ~988 |
| `Neuter.txt` | nomi neutri/senza genere | ~166 |
| `new_words.txt` | parole nuove non ancora classificate (raccolte dal gioco) | 0 |

Regola pratica per popolarle: genere dalla desinenza (**-o → M**, **-a → F**), con i **-e**
ambigui da decidere a mano. Candidato per un tool `rwit wordinfo` (auto-manutenzione).

### Bug dati già individuati (da correggere in revisione)
- `Female.txt`: **`anima grass`**, **`anima tree`** → inglese non tradotto ("anima
  d'erba"/"anima d'albero"? Da verificare il termine corretto in gioco).
- `Neuter.txt`: **`psychic shock lance`**, **`psylink neuroformer`** → inglese non tradotto.

---

## 3. `Strings/` (dati — il vocabolario per i namer)

Il materiale grezzo che le `rulesStrings` assemblano. Due rami principali:

### `Strings/Names/` — nomi propri
`Animal_Female.txt`, `Animal_Male.txt`, `Animal_Unisex.txt` (nomi di animali),
`Business.txt`, `Celestial.txt` (+ `CelestialPrefix/Suffix`), `OutlanderTown.txt`,
`WorldFeatures/`…

### `Strings/Words/` — vocabolario comune
`Nouns/`, `Adjectives/`, `Verbs/`, `Misc/`, `Foreign/`. Qui l'italiano fornisce le
**varianti flesse esplicite**, perché il genere/numero non si può dedurre sempre a
codice. Schema ricorrente:

```
AnimalGroups_Singular_Feminine.txt   AnimalGroups_Plural_Feminine.txt
AnimalGroups_Singular_Masculine.txt  AnimalGroups_Plural_Masculine.txt
Animals.txt                          AnimalsPlural.txt
Badass_Plural_Feminine.txt           Badass_Plural_Masculine.txt   (aggettivi)
```

Così "muffalo→muffali", "cobra→cobra" vengono da `AnimalsPlural.txt` (lookup), non
dall'euristica del codice.

### Convenzione: commento-articolo a inizio file
I file di nomi iniziano con un commento che fissa l'articolo del gruppo, es.:
```
//la, una
moltitudine
schiera
```
Vedi le regole in [`scripts/prompt_nomi.txt`](../scripts/prompt_nomi.txt) (l'/lo/il/la,
singolare, generi lessicali particolari).

---

## 4. `rulesStrings` / `RulePackDef` — la grammatica che assembla tutto

Nei `DefInjected/RulePackDef/` (e affini) le regole `<li>sinistra->destra</li>` compongono
i pezzi sopra usando `[riferimenti]` e pesi `(p=N)`:

```xml
<li>title(p=2)->[mapType] [mapNoun] di [subject]</li>
```
- `[mapType]`, `[subject]` → pescati da altre regole / liste di `Strings/`.
- `(p=2)` → questa variante è scelta con **peso 2** (più probabile). Sta sul lato sinistro,
  va **copiato identico** (vedi [`SINTASSI-TRADUZIONE.md`](SINTASSI-TRADUZIONE.md) §4 e la
  nota integrità in [`VALIDAZIONE.md`](VALIDAZIONE.md)).

### Esempio end-to-end (descrizione di una mappa)
1. Una `RulePackDef` ha `title->[mapType] [mapNoun] di [subject]`.
2. `[mapType]` risolve a "deserto", `[mapNoun]` a "distese", `[subject]` a "Vetro".
3. Il motore chiama il LanguageWorker per articoli/elisioni → "le distese di Vetro".
4. Il genere di "distese" arriva da `WordInfo/Gender/` per scegliere "le/i".

---

## 5. Piano di revisione di quest'area

- [ ] Salvare/aggiornare il riferimento `Notes/LanguageWorker_Italian.cs` a ogni versione.
- [ ] **WordInfo/Gender**: tradurre l'inglese rimasto (`anima grass/tree`, `psychic shock
  lance`, `psylink neuroformer`), verificare i generi dubbi (-e), svuotare `new_words.txt`
  riclassificando.
- [ ] **Strings**: controllare coerenza singolare/plurale × maschile/femminile e i commenti
  `//articolo` a inizio file.
- [ ] **rulesStrings**: lato sinistro e pesi `(p=N)` invariati (lo garantisce la validazione).
- [ ] Valutare una **PR upstream**/mod per i limiti del worker (articolo `lo` per gn/ps/x/y,
  plurali `-ca/-ga/-co/-go`).
- [ ] (Tooling) `rwit wordinfo` per auto-manutenzione del genere; `rwit compare` per
  confrontare le stesse rulesStrings con fr/es/de.
