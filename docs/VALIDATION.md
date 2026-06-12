# Validazione e integrità della traduzione

Due cose distinte:
1. **Tracciare quali file sono stati validati** (foglio Excel/CSV).
2. **Garantire che la traduzione non abbia alterato la logica di gioco** — in particolare
   le **priorità/frequenze degli eventi**.

---

## 1. La traduzione può cambiare le priorità degli eventi? **No.**

> Dubbio sollevato: "con la traduzione si saranno persi o modificati anche i pesi/priorità
> con cui compaiono i vari eventi?"

**Risposta breve: no, è impossibile per costruzione.** Verificato sul repo.

### Perché
RimWorld separa nettamente due cose:

| Cosa | Dove vive | Nel nostro repo? |
|------|-----------|------------------|
| **Logica/numeri** degli eventi: quali incidenti compaiono, con che frequenza, peso, refire, condizioni (`IncidentDef.baseChance`, `commonality`, `selectionWeight`, `minRefireDays`, StorytellerDef…) | nei **Def del gioco** (cartella `Data\` dell'installazione) | ❌ **NO** |
| **Testo** mostrato: etichette, descrizioni, testo delle lettere, racconti generati | nei **language pack** (`DefInjected/`, `Keyed/`) | ✅ sì |

Un language pack **inietta solo i campi di testo** dei Def. Non contiene — e non può
contenere — i campi numerici che governano la frequenza degli eventi.

### Prova sul repo
Ricerca di campi di frequenza/peso evento nei file di traduzione:

```
selectionWeight | commonality | baseChance | minRefireDays | <weight> | <chance>
→ 0 occorrenze reali (l'unico hit è una parola dentro una stringa di UI)
```

Quindi: anche se *Pulisci lingue* ha riscritto i file, **non c'è nessun peso-evento da
perdere o modificare** in questo repo. Le priorità degli eventi restano quelle dei Def
inglesi del gioco, intatte.

### L'unica eccezione: i pesi `(p=N)` delle rulesStrings
Esiste **un solo** tipo di "peso" nei nostri file: i marcatori `(p=N)` nelle
`rulesStrings`/`RulePackDef` (es. `<li>title(p=2)->...`). **1456** in 79 file.

- Non governano *quali eventi accadono*, ma **quale variante di testo** viene scelta
  (es. quale nome/descrizione tra più alternative).
- Stanno sul **lato sinistro** della freccia `->`, quindi vanno **copiati identici**.
- Un peso alterato qui cambierebbe solo la probabilità di una *frase*, non di un evento.

Il conteggio `(p=N)` per file è nella colonna apposita di `VALIDATION-FILES.csv`: i file
con valore alto sono quelli da controllare con più attenzione (left side invariato).

> **Regola**: nelle rulesStrings non toccare mai il lato sinistro, compreso `(p=N)`.
> Vedi [`TRANSLATION-SYNTAX.md`](TRANSLATION-SYNTAX.md) §4.

---

## 2. Foglio di validazione file (`VALIDATION-FILES.csv`)

Inventario di **tutti** i file di traduzione del repo, da spuntare man mano che vengono
validati con Claude Code. È un **CSV** (si apre in Excel, ma resta diffabile in git — un
`.xlsx` binario no).

Colonne:

| Colonna | Significato |
|---------|-------------|
| `DLC` | Core / Royalty / Ideology / Biotech / Anomaly / Odyssey |
| `Tipo` | DefInjected / Keyed / Strings / WordInfo |
| `File` | percorso relativo |
| `PesiVarianti(p=N)` | quante rulesStrings pesate contiene (più alto = più attenzione al left side) |
| `Validato` | `no` / `sì` |
| `DataValidazione` | data del controllo |
| `Note` | osservazioni (bug trovati, dubbi…) |

### Flusso di validazione di un file
Per ogni file, Claude Code verifica:
- [ ] XML ben formato, nessun tag mancante/duplicato rotto
- [ ] Variabili `[VAR]` e `{VAR}` intatte (nome e indice posizionale)
- [ ] Ternarie genere valide (un solo `?`, 2 o 3 rami; il 3° = forma neutra, non un errore)
- [ ] rulesStrings: ogni `<li>` ha una `->`, **left side invariato** (inclusi `(p=N)`),
      stesso numero di `<li>` dell'inglese
- [ ] `\n\n` preservati
- [ ] Commenti `<!-- EN: -->` invariati
- [ ] Qualità: naturalezza, niente calchi, terminologia coerente

Poi imposta `Validato=sì`, `DataValidazione`, ed eventuali `Note`.

### Rigenerare l'inventario
Quando si aggiungono/rimuovono file (nuova versione del gioco), rigenerare l'elenco
mantenendo le spunte già fatte. Candidato per un comando di tooling:
**`rwit validate`** (vedi sotto).

---

## 3. Tooling futuro: `rwit validate` (proposto)

Comando che automatizza i controlli meccanici e aggiorna il CSV:
- XML ben formato (lxml).
- Ternarie genere: ogni `{... ? ...}` ha un solo `?` e **2 o 3 rami** (`: b` oppure
  `: b : c`, dove il 3° è la forma neutra/None). Segnala solo le malformate vere
  (0 rami, 4+ rami, `?` doppio). ⚠️ Una ternaria a 3 rami **non** è un bug.
- rulesStrings: ogni `<li>` ha una sola `->`; confronto del **left side** (inclusi pesi
  `(p=N)`) con l'inglese del gioco per intercettare derive.
- Variabili `[VAR]`/`{N}` coerenti tra commento EN e traduzione.

Lascia all'umano/Claude solo la parte di **qualità linguistica**. I controlli meccanici
sopra sono esattamente quelli che danno garanzia sull'integrità (pesi `(p=N)` inclusi).
