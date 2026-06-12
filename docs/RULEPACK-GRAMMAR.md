# Linguaggio delle RulePack (grammatica generativa di RimWorld)

Riferimento del mini-linguaggio con cui RimWorld **genera testo** a runtime: nomi
(fazioni, mappa, gravship), **log di combattimento/sociale**, descrizioni di arte e
libri. Vive nelle `RulePackDef` (in gioco: `Data/<DLC>/Defs/RulePackDefs/`; da tradurre:
`<DLC>/DefInjected/RulePackDef/`).

Estende [`SINTASSI-TRADUZIONE.md §4`](SINTASSI-TRADUZIONE.md). **Leggere prima di toccare
qualsiasi `rulesStrings`**, soprattutto il log di combattimento.

## 1. Struttura

```xml
<NomeDef.rulePack.rulesFiles>          <!-- monta liste di parole come simboli -->
  <li>simbolo->Words/Nouns/Qualcosa</li>
</NomeDef.rulePack.rulesFiles>
<NomeDef.rulePack.rulesStrings>        <!-- le regole vere e proprie -->
  <li>simbolo->testo con [altro_simbolo]</li>
</NomeDef.rulePack.rulesStrings>
```

Ogni regola è `SINISTRA->DESTRA`. La **SINISTRA è codice, mai da tradurre**: nome del
simbolo + eventuale `(...)` (peso o condizione). Si traduce **solo la DESTRA**.

## 2. Simboli `[...]`

- `[simbolo]` viene espanso scegliendo una regola con quella SINISTRA (o una riga della
  lista in `rulesFiles`). Ricorsivo.
- **Simboli indicizzati**: `[recipient_part0_label]`, `[recipient_part1_label]`… — il
  numero è l'indice dell'elemento (0-based). Compaiono insieme alle condizioni di conteggio
  (§4).
- **Forme grammaticali del motore**: `[X_label]`, `[X_labelPlural]`, `[X_definite]`,
  `[X_indefinite]`, `[X_gender]`, `[X_pronoun]`, `[X_possessive]`, `[X_objective]`,
  `[X_nameDef]`… Sono fornite dal `LanguageWorker` (articoli/pronomi italiani) — **non
  inventarle**.
- I nomi dei simboli (sinistra e dentro `[...]`) **restano in inglese**: sono chiavi, non testo.

## 3. Pesi `(p=N)` — probabilità

```xml
<li>r_name(p=2)->...</li>     <!-- peso 2 -->
<li>r_name->...</li>          <!-- peso implicito 1 -->
```
Più alto = più probabile. **Vanno tarati sul numero di elementi delle liste**: se una
variante pesca da una lista di 30 voci e un'altra da una di 3, pesi uguali sbilanciano
l'output. Regola pratica: peso ∝ ricchezza/idoneità della variante, non lasciarli a caso
quando si splittano le liste per genere.

## 4. Condizioni — l'IF del linguaggio ⚠️

Una regola può avere un **vincolo** tra parentesi: viene scelta **solo se la condizione è
vera** nel contesto. È un IF/switch:

```
SINISTRA(CHIAVE OP VALORE)->DESTRA
```

**Operatori**: `==`, `!=`, `>=` (visti nel Core), e `<=`, `>`, `<` (supportati). La CHIAVE
è una **costante del contesto** fornita dal codice del gioco:

- **conteggi**: `recipient_part_count`, `recipient_part_damaged_count`,
  `recipient_part_destroyed_count`, `childCount`, `raidCount`…
- **genere**: `INITIATOR_gender==Female`, `SUBJECT_gender!=Male`…
- **tipo di carne**: `SUBJECT_flesh==Mechanoid`, `RECIPIENT_flesh!=Mechanoid`
- **booleani**: `deflected!=True`, `INITIATOR_cubeInterest==true`,
  `recipient_part_damaged0_outside==True`

### Esempio canonico — conteggio (log di combattimento)
Da `Core/Defs/RulePackDefs/RulePacks_CombatIncludes.xml`:
```xml
<li>targetlist(recipient_part_count==1)->[recipient_part0_label]</li>
<li>targetlist(recipient_part_count==2)->[recipient_part0_label] and [recipient_part1_label]</li>
<li>targetlist(recipient_part_count==3)->[recipient_part0_label], [recipient_part1_label], and [recipient_part2_label]</li>
```
Il motore sceglie la riga in base a **quante** parti del corpo sono coinvolte. In italiano:
```xml
<li>targetlist(recipient_part_count==1)->[recipient_part0_label]</li>
<li>targetlist(recipient_part_count==2)->[recipient_part0_label] e [recipient_part1_label]</li>
<li>targetlist(recipient_part_count==3)->[recipient_part0_label], [recipient_part1_label] e [recipient_part2_label]</li>
```
- `and` → **`e`**; la lista `X, Y, and Z` → **`X, Y e Z`** (niente virgola di Oxford).
- La **condizione `(...==N)` non si traduce mai**: è codice.

## 5. Regole d'oro per la traduzione

1. **Sinistra invariata, condizione inclusa**: `damaged_targets(recipient_part_damaged_count==2)`
   resta identico; si traduce solo dopo `->`.
2. **Stesso numero di `<li>` e stesse condizioni** del commento `<!-- EN: -->`: ogni ramo
   (==1/==2/==3, ==Female/!=Female, ==Mechanoid…) va mantenuto. Non fondere né eliminare rami.
3. **Accordo guidato dal conteggio**: il ramo `==1` è **singolare** (il braccio è stato
   ferito), i rami `==2/==3` sono **plurale** (le braccia sono state ferite). Verbo, articolo
   e participio nel template che usa `[targetlist]` devono concordare ramo per ramo.
4. **Plurali/articoli generati**: provengono dal `LanguageWorker` + `WordInfo/` (genere e
   `plural.txt`). I plurali irregolari delle parti del corpo (braccio→**braccia**, osso→ossa)
   vanno in `WordInfo/plural.txt`, non hardcodati nelle regole. Vedi
   [`GENERAZIONE-NOMI-E-GRAMMATICA.md`](GENERAZIONE-NOMI-E-GRAMMATICA.md).
5. **Genere nei nomi propri generati**: evitare articoli iniziali a genere fisso su liste a
   genere misto. Strategie collaudate: apposizione, complemento (`di [X]`), aggettivi in
   `-e` (invarianti), oppure **liste splittate per articolo** (il/lo/l'/la · i/gli/le) con
   pesi coerenti. Le varianti si generano con `rwit variants` (Morph-it!).
6. **`(p=N)` riscritti identici** salvo ribilanciamento consapevole legato alle dimensioni
   delle liste.

## 6. Altre direttive

- **Ternaria di genere** nel testo finale: `{X_gender ? o : a : o/a}` (vedi
  `SINTASSI-TRADUZIONE.md §3`). Diversa dalla condizione `(X_gender==Female)` sulla SINISTRA:
  la ternaria sceglie una **lettera** nel testo, la condizione sceglie una **regola**.
- **`{replace: ...}`** (usata da altre lingue, es. tedesco) per sostituzioni post-generazione.
  Rara in italiano; se presente nel commento EN, preservarla.
- **Maiuscola**: il motore mette l'iniziale maiuscola al risultato finale; le voci delle liste
  restano minuscole salvo nomi propri.

## 7. Strumenti collegati

- `rwit variants` — genera le varianti morfologiche (genere/numero/articolo) via Morph-it!.
- Anteprima offline: dashboard → tab **Generatore nomi** (`scripts/dashboard/`), o
  `scripts/rwit/namegen.py`. Mostra cosa genererebbe un rulePack senza aprire il gioco.
- `rwit strings-diff` — allinea le liste `Words/Names` all'inglese del gioco (fonte di verità).
