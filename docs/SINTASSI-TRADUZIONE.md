# Sintassi delle traduzioni — RimWorld italiano

Guida di riferimento alla sintassi che si può (e si deve) usare nei file di traduzione.
Vale per `DefInjected/`, `Keyed/` e le `rulesStrings`. Le regole di processo stanno in
`scripts/prompt.txt`; questo file documenta la **sintassi del motore di RimWorld**.

---

## 1. Struttura dei file

Ogni file è un `LanguageData` XML. Due famiglie:

- **Keyed** (`<DLC>/Keyed/*.xml`): coppie chiave→testo dell'interfaccia.
  ```xml
  <LanguageData>
    <!-- EN: Required -->
    <Required>Richiesto</Required>
  </LanguageData>
  ```
- **DefInjected** (`<DLC>/DefInjected/<DefType>/*.xml`): traduzioni di campi dei Def.
  La chiave è il **percorso del def**: `NomeDef.campo` o `NomeDef.sotto.campo`.
  ```xml
  <!-- EN: ancient bridge -->
  <AncientBridge.label>ponte antico</AncientBridge.label>
  ```

### Commenti `<!-- EN: ... -->`
Mostrano l'originale inglese. **Si copiano identici, non si traducono mai.** Quando il
gioco aggiorna l'inglese, riscrive questi commenti: se cambia solo un refuso inglese, la
traduzione italiana sottostante **non va toccata**.

### Tag vuoti = TODO
`<tag />` o `<tag></tag>` vanno trattati come da tradurre: inserire la traduzione del
commento `<!-- EN: -->` precedente.

---

## 2. Variabili — NON tradurre mai il nome

Due notazioni, entrambe da **lasciare intatte** nel nome:

| Forma | Dove | Esempio |
|-------|------|---------|
| `[VARIABILE]` | DefInjected, rulesStrings, backstory | `[PAWN_nameDef]`, `[WEAPON_label]` |
| `{VARIABILE}` | Keyed, lettere | `{PAWN_labelShort}`, `{FACTION_name}`, `{0}`, `{1}` |

Si traduce **solo il testo fuori** dalle parentesi.

```xml
<!-- EN: {0} is low on resources -->
<AlertWarqueenHasLowResources>{0} ha poche risorse</AlertWarqueenHasLowResources>
```

Suffissi comuni delle variabili pawn (utili per accordare le frasi):
`_nameDef`, `_nameFull`, `_labelShort`, `_pronoun` (lui/lei), `_possessive` (suo/sua),
`_objective` (lo/la), `_gender`.

> ⚠️ Le variabili posizionali `{0}`, `{1}`, `{0_label}`, `{1_gender}` devono restare e
> mantenere lo stesso indice dell'inglese: cambiare il numero rompe il testo in gioco.

---

## 3. Genere: la notazione ternaria

L'italiano accorda gli aggettivi/participi al genere. RimWorld offre una **ternaria** con
**due o tre rami**:

```
{VARIABILE_gender ? MASCHILE : FEMMINILE}              # 2 rami
{VARIABILE_gender ? MASCHILE : FEMMINILE : NEUTRO}     # 3 rami
```

Il motore mappa il genere così: **Maschile → 1° ramo, Femminile → 2° ramo,
Nessuno (None) → 3° ramo**. Il genere `None` riguarda cose **senza genere**: oggetti,
costruzioni, animali di sesso ignoto (es. `{CRAFTED_gender ...}`, `{0_gender ...}` di un
item). Per questo la forma a 3 rami è **valida e diffusa** (la usano anche fr/de/es).

### Tre usi

**Inline a 2 rami** (desinenza singola — caso più frequente per i pawn):
```
stat{PAWN_gender ? o : a} uccis{PAWN_gender ? o : a}
→ "stato ucciso" / "stata uccisa"
```

**A 3 rami** (quando serve la forma neutra per genere `None`):
```
è entrat{0_gender ? o : a : o}                    # masch / femm / neutro
{CRAFTED_gender ? un : una : uno} {CRAFTED_labelShort}
{PAWN_gender ? morto : morta : mortə}             # neutro con schwa
```
Il 3° ramo può ripetere il maschile (`o : a : o`) o usare una forma neutra esplicita
(`o/a`, `o(a)`, `ə`, `*`). Entrambe le scelte sono accettate; **mantieni lo stile del
file**.

**Frase/parola intera**:
```
{PAWN_gender ? un bambino : una bambina}
{PAWN_gender ? stato ucciso : stata uccisa}
```

### Quale variabile
Usa la stessa radice della variabile presente nel testo: `PAWN_gender`, `HEIR_gender`,
`CRAFTED_gender`, oppure la posizionale `{0_gender ? o : a}` quando il testo usa `{0}`.

### Cosa è davvero un errore

| ❌ Sbagliato | ✅ Corretto | Perché |
|-------------|-------------|--------|
| `entrat{0_gender ? o : a}` su un soggetto che può essere `None` | `entrat{0_gender ? o : a : o}` | manca il ramo neutro: con genere `None` il motore non trova la forma |
| `{0_gender ? o : a : o : x}` | `{0_gender ? o : a : o}` | **quattro** rami: il massimo è 3 |
| `statoa` | `stat{PAWN_gender ? o : a}` | concatenazione errata dei rami |

> **Regola d'oro**: la ternaria ha **2 o 3 rami** separati da `:`, con **un solo `?`**.
> `{ ? a : b }` e `{ ? a : b : c }` sono entrambe corrette. `{ ? a : b : c : d }` no.
> ⚠️ Non "correggere" una ternaria a 3 rami togliendo il terzo: è la forma neutra (None),
> non un bug — controllato sui language pack fr/de/es.

---

## 4. rulesStrings (grammatica generativa)

Liste di regole che il gioco compone per generare testo (nomi, descrizioni, racconti).
Ogni `<li>` ha la forma `SINISTRA->DESTRA`:

```xml
<li>subject->generazione di energia da bioferrite</li>
<li>subject_story->fu addestrat{PAWN_gender ? o : a} all'uso di fonti innovative</li>
```

Regole:
- Freccia **letterale `->`** (mai `>`, mai `-&gt;`).
- **Sinistra invariata** (è un identificatore del motore): si traduce **solo la destra**.
- Stesso **numero di `<li>`** dell'originale.
- Dentro la destra si possono usare `[VARIABILI]` e ternarie genere.
- Controllo finale: ogni `<li>` deve contenere **esattamente una `->`**.
  Se manca (`<li>introduction>…`), correggere in `<li>introduction->…`.

I commenti `<!-- EN: -->` delle rulesStrings contengono il blocco inglese multilinea: si
copiano identici.

---

## 5. A capo e formattazione

- La sequenza `\n\n` (e `\n`) è **letterale**: si riscrive **identica**, senza andare a
  capo davvero nell'XML. Vale sia nei commenti che nel testo.
  ```xml
  <Tutorial>Riga uno.\n\nRiga due.</Tutorial>
  ```
- Mantenere indentazione e struttura originali.
- Restituire sempre l'XML **completo**, senza omettere tag (anche se duplicati).

---

## 6. Articoli ed elisione — chi fa cosa

L'italiano **non ha i casi** (a differenza del tedesco): bastano **genere** +
**riformulazione** della frase. Articoli ed elisione (`il/lo/la`, `un/uno/un'`, `l'`)
sono in gran parte gestiti **dal codice** (`LanguageWorker_Italian`) e dai dati in
`WordInfo/Gender/`.

Quando devi scegliere un articolo a mano (es. nelle liste nomi), regole rapide:
- **l'** = singolari (m/f) che iniziano per vocale → *l'accento, l'idea*
- **lo** = maschili con s+consonante, z, ps, gn, x, y → *lo sguardo, lo zaino*
- **il** = maschili con altra consonante
- **la** = femminili con consonante
- Rispetta i generi lessicali particolari (es. *la fronte*).

Vedi `scripts/prompt_nomi.txt` per il flusso completo sui nomi.

---

## 7. Terminologia (lore RimWorld)

Termini fissati per coerenza:

| Inglese | Italiano |
|---------|----------|
| ideoligion | ideologia |
| scarification | incisione rituale |

Principio: fedeltà **+ naturalezza**. Evitare calchi letterali; preferire la forma più
idiomatica e "giocabile" (es. un termine scientifico corretto ma rigido → versione più
semplice nel contesto di gioco). Vedi anche la lista in `scripts/prompt.txt`.

---

## 8. Checklist finale per ogni file

- [ ] Solo testo fuori da `[ ]` e `{ }` tradotto
- [ ] Ogni ternaria genere ha **un solo `?`** e **2 o 3 rami** (`: b` o `: b : c`); il 3° è la forma neutra, non un errore
- [ ] rulesStrings: `->` presente in ogni `<li>`, sinistra invariata, stesso numero di `<li>`
- [ ] `\n\n` preservati identici
- [ ] Commenti `<!-- EN: -->` copiati identici
- [ ] XML ben formato, nessun tag mancante
- [ ] Variabili posizionali `{0}`, `{1}` con lo stesso indice dell'inglese
