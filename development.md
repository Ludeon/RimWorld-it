* New keyed translations format

https://ludeon.com/forums/index.php?topic=43979.0

* Esempio Gender

```xml
<li>traverObjective(beggarCount==1)->{beggars0_gender ? lui : lei }</li>
<li>traverObjective(beggarCount>=2)->loro</li>
```

* Condizioni multiple

```xml
<li>groupLabelSingle->viaggiatore</li>
<li>groupLabelSingle(childCount>=1,priority=1)->bambino</li>
```