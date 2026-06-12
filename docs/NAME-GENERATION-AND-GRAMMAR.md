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

> **Dati vs codice — dove lavorare.** La manutenzione quotidiana sta nei **file di testo**
> (DATI): `WordInfo/Gender` (il genere di ogni parola) e le coppie singolare/plurale per gli
> irregolari. Il `LanguageWorker` (CODICE) **legge** quei dati e applica articolo/plurale;
> da genere + ortografia decide solo il caso `lo`/`il` che i dati da soli non possono
> risolvere. Col worker **già nel gioco** + i dati giusti, gran parte della grammatica
> funziona **senza toccare il `.cs`** (che resta una proposta upstream, non manutenzione
> quotidiana).

---

## 1. `LanguageWorker_Italian` (codice, dentro la DLL del gioco)

È una **classe C# compilata nel gioco** (`Verse.LanguageWorker_Italian`), dichiarata in
`Core/LanguageInfo.xml` → `<languageWorkerClass>LanguageWorker_Italian</languageWorkerClass>`.

> Gli sviluppatori **l'hanno fornita**: esiste nell'`Assembly-CSharp.dll` accanto a
> French, German, Spanish… Mancava solo il **file `.cs` di riferimento** nel nostro repo.
> Ora c'è, in versione **migliorata**, nella root: [`LanguageWorker_Italian.cs`](../LanguageWorker_Italian.cs)
> (base decompilata da RimWorld 1.6.4850 con ILSpy).

### Versione migliorata (root del repo) e come deployarla
Il file in root (aggiornato 2026-06-12) corregge i limiti del worker di serie:
- articolo `lo`/`gli` anche per gn, ps, pn, x, y, i+vocale (lo gnomo, lo psicologo);
- **h muta** trattata come vocale per l'elisione (l'hotel, un'hostess, gli hotel);
- articoli al **plurale** (i/gli/le, partitivi dei/degli/delle) — il worker di serie li ignorava;
- **fix bug**: plurali `-io` ora collassano a `-i` (figlio→figli, occhio→occhi; prima "figlii");
- plurali maschili `-ca/-ga→-chi/-ghi` (duca→duchi, collega→colleghi);
- plurali femminili `-ca→-che`, `-ga→-ghe`, `-cia/-gia→-cie/-gie | -ce/-ge`.

Tutto verificato con harness di test C# (16/16 casi ok).

⚠️ **Non basta che stia nel repo**: un language pack è solo dati e NON carica `.cs`. Per
farlo valere serve una **PR upstream a Ludeon** (lo compilano nel gioco) oppure un **mod
companion** (patch Harmony sui metodi, o classe con nome diverso in `languageWorkerClass`).
Logica verificata con un harness di test (articoli e plurali corretti).

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

### Voci in inglese: di solito sono conseguenze, non bug del file gender
Una voce inglese in `Gender/*.txt` riflette quasi sempre un'**etichetta di origine non
tradotta altrove** (l'oggetto/pianta ha ancora il `.label` inglese): in quel caso la voce
gender è *corretta* e va sistemata **alla fonte** (il `.label` nel DefInjected), non qui.
Casi visti:
- `Female.txt`: `anima grass`, `anima tree` → verificare/tradurre il `.label` della pianta
  (Ideology); la voce gender seguirà.
- `Neuter.txt`: `psylink neuroformer` → idem (item Royalty).
- ✅ Rimosso `psychic shock lance` da `Neuter.txt`: residuo morto, l'italiano corretto
  `lancia di shock psichico` è già in `Female.txt` (l'item Core è tradotto).
- `Male.txt`: `jump-pack` è l'etichetta reale tenuta in inglese (`Apparel_PackJump`) → ok.

Candidato a un tool `rwit wordinfo` che riconcili le liste gender con i `.label` tradotti.

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

### ⚠️ I file accoppiati sono POSIZIONALI (singolare ↔ plurale)
Le coppie come `Animals.txt` / `AnimalsPlural.txt` (e `..._Singular_*` / `..._Plural_*`) NON
vengono accoppiate confrontando le parole: sono **sincronizzate per posizione di riga**.
La riga *N* del file plurale è il plurale della riga *N* del singolare.

```
Animals.txt        riga 1: muffalo   riga 24: ape   riga 67: oca
AnimalsPlural.txt  riga 1: muffali   riga 24: api   riga 67: oche
```

Conseguenze pratiche:
- I due file **devono avere lo stesso numero di righe** (escl. commenti/vuote); da noi
  178 = 178. Verificato: nessun disallineamento.
- **Fragilità**: se aggiungi/rimuovi/riordini **una** riga in un solo file dei due, tutte
  le righe sotto **scalano** e ogni animale successivo prende il plurale sbagliato
  (muffalo→"api"), **in silenzio**. Modifica sempre entrambi i file alla stessa posizione.
- L'inglese **non ha** `AnimalsPlural.txt` (il plurale regolare `+s` lo fa il suo
  LanguageWorker): è un file **solo italiano**. Serve alla resa dei simboli plurali nelle
  rulesStrings, ma **NON** è ciò che usa `Pluralize` (vedi sotto).
- Candidato a controllo `rwit validate`: stesso conteggio righe e coerenza delle coppie.

### ✅ Il vero meccanismo dei plurali: `WordInfo/plural.txt` (keyed, generico)
Decompilando il `LanguageWorker` di base si vede che `Pluralize → TryLookupPluralForm`
legge un **dizionario keyed**, non i file posizionali:
```csharp
var table = LanguageDatabase.activeLanguage.WordInfo.GetLookupTable("plural"); // WordInfo/plural.txt
string key = str.ToLower();           // lookup PER PAROLA, non per posizione
plural = table[key][1];
```
- È **generico** (funziona col worker di serie, per qualsiasi lingua) e **robusto**
  (chiave→valore: non si disallinea come i file posizionali).
- Formato (come il tedesco): righe `Singolare;Plurale`, con commenti `//`. Es. tedesco:
  ```
  // Ingame pluralization use this file automatically.
  Ladung;Ladungen
  ```
- **Stato**: il tedesco ha `WordInfo/plural.txt` (+ `plural_decline.txt`), autogenerato.
  **L'italiano NON ce l'ha** (solo `Gender/`) → oggi il nostro `Pluralize` cade sempre
  sull'euristica del `.cs`.
- **Raccomandazione**: gli irregolari italiani (incl. parti del corpo: braccio→braccia,
  dito→dita, ginocchio→ginocchia, osso→ossa, labbra…) vanno messi in un
  **`WordInfo/plural.txt`** keyed (modello tedesco), non nel fragile `AnimalsPlural.txt`.
  Da generare con `rwit wordinfo` (l'equivalente di `update-wordinfo-plural.ps1` tedesco),
  idealmente da Morph-it!. Nessun `.cs` da deployare.

### Convenzione: commento-articolo a inizio file
I file di nomi iniziano con un commento che fissa l'articolo del gruppo, es.:
```
//la, una
moltitudine
schiera
```
Le regole degli articoli (l'/lo/il/la, singolare, generi lessicali particolari) sono in
[`SINTASSI-TRADUZIONE.md`](SINTASSI-TRADUZIONE.md) §6.

### Cosa tradurre e da dove (fonte = inglese)
La **fonte di verità** è l'inglese del gioco (`Data/<DLC>/Languages/English/Strings`):
definisce *quali* file/simboli esistono. La worklist si ricava per **diff IT-vs-EN** (se un
file manca nella nostra lingua, il gioco usa l'inglese → può trapelare). Per tipo di lista:
- **Nomi propri** (`Strings/Names/`: animali, persone, città, celestiali) = **pool**:
  si **tengono in inglese** (Abby, Akira…). Non si traducono; al più si cura/arricchisce.
- **Liste-parola** (`Strings/Words/`: Adjectives, Verbs, Nouns, colori…) = **si traducono**
  (red→rosso): vengono assemblate in frasi italiane.
- **`WordInfo/Gender` e `plural.txt`** = specifici dell'italiano, derivati dai **nostri**
  label tradotti (ideale: Morph-it!), **non** copiati da EN/DE.
- **Tedesco** = modello del **meccanismo** (ha `WordInfo/plural.txt`), non fonte dei nomi.

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

### Come un file `Strings/` diventa disponibile: `<rulesFiles>`
Un `rulePack` ha due liste: `<rulesStrings>` (regole inline) e **`<rulesFiles>`**, che
**monta un file di `Strings/` sotto un simbolo**. Esempio dai Def del gioco
(`Core/Defs/RulePackDefs/RulePacks_Common.xml`):
```xml
<rulePack>
  <rulesFiles>
    <li>tribal_word_file->Words/Foreign/Tribal</li>   <!-- → Strings/Words/Foreign/Tribal.txt -->
    <li>place_end->WordParts/PlaceEndings</li>          <!-- → Strings/WordParts/PlaceEndings.txt -->
  </rulesFiles>
</rulePack>
```
- Sintassi: `<li>simbolo->PercorsoRelativo</li>`, **relativo a `Strings/`, senza `.txt`**.
  Poi `[simbolo]` nelle rulesStrings pesca una riga a caso da quel file.
- Nelle traduzioni si può **ridichiarare** `rulesFiles` in DefInjected per puntare ai file
  `Strings/` italiani (es. `Odyssey/.../Script_SpaceSites.xml`).
- ⚠️ **Differenza chiave**: i file di **`Strings/`** vanno registrati con `rulesFiles`; i
  file di **`WordInfo/`** (`Gender/`, `plural.txt`) NO — li carica il motore in automatico
  per lingua. Quindi il futuro `WordInfo/plural.txt` non richiede nulla negli XML.

### Esempio end-to-end (descrizione di una mappa)
1. Una `RulePackDef` ha `title->[mapType] [mapNoun] di [subject]`.
2. `[mapType]` risolve a "deserto", `[mapNoun]` a "distese", `[subject]` a "Vetro".
3. Il motore chiama il LanguageWorker per articoli/elisioni → "le distese di Vetro".
4. Il genere di "distese" arriva da `WordInfo/Gender/` per scegliere "le/i".

---

## 5. Grammatica del log generato (combattimento/sociale) — il problema storico

I log di combattimento e le interazioni sociali sono **generati** dalle `rulesStrings`
(`RulePacks_Combat*`, `RulePacks_Damage*`, `RulePacks_Maneuvers`, `Interactions_*`).
È la parte storicamente **più sbagliata** della traduzione italiana.

### Causa radice (misurata)
Il motore offre un meccanismo per il genere; l'italiano non l'ha quasi mai usato. Vincoli
`_gender==Male/Female` nelle rulesStrings di combattimento:

| Lingua | Vincoli di genere |
|--------|-------------------|
| Francese | 122 |
| Spagnolo | 100 |
| Tedesco | 95 |
| **Italiano** | **1** |

Le regole italiane hanno articoli/participi **fissi** (`nella [recipient_part0_label]`,
`colpito`) giusti solo per un genere → frasi come "X ha colpito Y nella braccio" o
participi al maschile per soggetti femminili. In più **`WordInfo/Gender` non ha quasi
nessuna parte del corpo** (braccio, gamba, mano… assenti), quindi neppure la via
automatica `[parte_definite]` può mettere l'articolo giusto.

### I due strumenti del motore per risolvere
1. **Vincolo di genere sulla regola** (lato sinistro), come fa il francese:
   ```xml
   <li>r_logentry(p=0.1,RECIPIENT_gender==Male)->[INITIATOR_definite] [damaged_past] nel [recipient_part0_label] ...</li>
   <li>r_logentry(p=0.1,RECIPIENT_gender==Female)->[INITIATOR_definite] [damaged_past] nella [recipient_part0_label] ...</li>
   ```
   Sintassi: `nomeRegola(p=PESO, SIMBOLO_gender==Male|Female)`. Il resolver sceglie la
   variante che combacia col genere dell'entità risolta.
2. **Suffissi `[X_definite]` / `[X_indefinite]`**: il motore applica l'articolo corretto
   via `LanguageWorker` + `WordInfo/Gender`. Es. `[recipient_part0_definite]` → "il braccio"
   / "la gamba" automaticamente, **se** la parte è nel WordInfo col genere giusto.
   (L'italiano usa 456 di questi suffissi, il francese 617: c'è margine.)

### Strategia di fix
- Sostituire gli articoli scritti a mano davanti a `[X_label]` con `[X_definite]`/`[X_indefinite]`.
- Dove serve accordo di participio/aggettivo, sdoppiare la regola con i vincoli
  `(SIMBOLO_gender==Male/Female)` — **template = i pack francese/spagnolo** (stessi simboli).
- Popolare `WordInfo/Gender` con le parti del corpo e i nomi usati nei log.
- Verificare **in gioco** (Dev mode: generatori del log di combattimento/interazioni) su
  un pawn maschio e uno femmina.
- Ordine per impatto: CombatMelee → CombatRanged → Damage → DamageEvent → Maneuvers →
  Interactions sociali → Battles/Tales.

Tooling di supporto previsto: `rwit compare` (affianca it/fr/es/de sulle stesse rulesStrings),
`rwit validate` (lint: niente articolo a mano prima di `[X_label]`, vincoli ben formati).

## 6. Piano di revisione di quest'area

- [ ] Aggiornare `LanguageWorker_Italian.cs` (root) a ogni versione del gioco; valutarne
  il deploy (PR upstream o mod companion) per attivare le migliorie.
- [ ] **Log generato**: applicare la strategia di fix §5 (vincoli di genere + `[X_definite]`),
  partendo da un pack-template (es. `Combat_Deflect`) verificato in gioco.
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
