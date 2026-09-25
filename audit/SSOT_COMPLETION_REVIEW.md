# Opravy masek: pokračování z e025079

> Tento report zachycuje výsledek commitu `997e835`. Další obsahové opravy,
> nové hashe a počty jsou v [SSOT_CONTINUATION_997e835.md](SSOT_CONTINUATION_997e835.md).

Stav celého zadání: **BLOCKED — obsahová práce pokračuje**. Tento balík změn
neuzavírá všech 130 operací ani zbývající obecné trasy. Neobsahuje rozhodnutí,
že dosud neprošetřené operace musí rozhodnout OWNER.

Větev: `work/ssot-completion-2026-09-25`. Výchozí commit `e025079`.
Devět změněných auditních souborů přítomných při vstupu bylo zachováno samostatným
commitem `821c6d6` (jeden soubor měl pouze rozdíl konců řádků). Jsou to historické
výstupy předchozího běhu; nové kontroly mají vlastní soubory a hash vstupu.

Vstupní SHA-256 SSOT:
`4ee82539e50ce3b538f58d18b03206aef28ab7607201e878f15a61e8cb783450`.

Výsledný SHA-256 SSOT:
`dd21d569eee6c54648414272e0405cc03b6f4ce9c29d1ac97aa27eb69431af1e`.

## Opravené autoritativní kontrakty

Zdroj: aktuální `00_SSOT/KajovoCMLNG_SSOT.md`, §55.2, §56.8–56.9,
`contracts/generation/step-catalog.json`, `contracts/generation/integration-step-catalog.json`
a definice v `contracts/generation/generation-contracts.schema.json`.

§56.8 výslovně stanovuje: „Runtime `StepInput` sestavuje server.“ a
„`StepOutput` je serverový receipt po validaci a guarded commitu; nikdy přímý
strukturovaný výstup modelu.“ Následující tabulka téhož oddílu jmenuje operace,
node kinds i obě konkrétní definice. Nové vazby přebírají celé definice přes
absolutní `$ref`, včetně jejich required/nullable pravidel a failure větví.

| Operace | Klasifikace dvojice masek | Přesné převzaté definice |
|---|---|---|
| `generation.workspace.patch` | Jednoznačné odvození z explicitního katalogu | `MCP_IMPLEMENT`, `AGENT_COMPILE`, `UI_IMPLEMENT`, `SCHEMA_GENERATE`, `TEST_GENERATE`, vždy `Input`/`Output`; disjunktní `oneOf` |
| `generation.workspace.validate` | Přesná definice existuje | `BUILDInput` / `BUILDOutput` |
| `generation.activation.switch` | Přesná definice existuje | `ACTIVATEInput` / `ACTIVATEOutput` |
| `generation.integration.step` | Jednoznačné odvození z explicitních katalogů | Šest node kinds §56.8 a oddělené `IntegrationStepInput` / `IntegrationStepReceipt` pro S04, S06, S09, S12, S13, S14 podle §56.9 |

Definice jsou v R9 `contracts/operation-contracts.json#/$defs/<operation>:command`
a `.../<operation>:response`. Zachovávají již deklarované identity
`urn:kcml:r9:operation:<operation>:command` a `...:response`.
Převzaté nativní definice mají adresu `urn:kcml:generation-contracts:2#/$defs/<definition>`.
Původně neexistovalo ani osm příslušných cílových schémat; nyní reference rozlišuje
aktuální inventář. Počet operací, business funkcí a tras se tím nemění.

§56.9 stanovuje: „Jednotlivé S-kroky jsou vnitřní saga kroky v existujících node
kinds, ne nové node kinds nebo nové endpoints.“ Proto dispatcher rozlišuje celý
node a vnitřní krok jejich existujícími nativními tvary. Response každého S-kroku
omezuje úspěšný `result.kind` na konkrétní `outputKind` katalogu; odmítá krok
patřící jiné operaci. Nebyla vytvořena nová HTTP trasa ani domnělý modelový výstup.

## Control enable/disable: skutečná chyba doménových typů

§56.3 určuje: „`Counter` je regexem i numerickým rozsahem uzavřený string `0` až
`9223372036854775807`, bez znaménka a leading zero.“ Výslovně zahrnuje
`stateVersion`, `activationEpoch` a `bindingSetRevision`.

Na `route.0000` / `component.control.enable` a `route.0001` /
`component.control.disable` měl `bindingSetRevision` typ obecného `Id`; ostatní
control čítače neměly horní mez. Opraveny jsou request guards, business body,
response result i totožná event payload definice. Materializační skript používá
přímo nativní `Counter`, `Uuid`, `Digest`, `Id` a `Timestamp` z §56.13.
Testovací hodnota `binding-1` byla opravena na platný čítač `1`.

Negativní test reprodukuje na `e025079` **48 selhání z 272 případů** (exit 1).
Stejná sada nad opraveným SSOT má **272 případů bez selhání** (exit 0).
Změna neuzavírá všechny ostatní guards a životní cyklus control operací.

## Validátor a rozsah důkazu

`Inventory.boundary()` nyní hledá obecný `values`/`canonicalJson` také za
tranzitivním `$ref`. Pouhé zavedení odkazového schématu tak nesmí skrýt obecnou
doménovou masku. Samostatná regrese ověřuje přímý obecný slot, jeden i dva
odkazy, přesnou kontrolní masku a chybějící tranzitivní definici.

Sada generation testů má **658 případů**: 13 konkrétních node variants a šest
saga kroků, success/failure/unknown, povinná pole, null, wrong artifact kind,
záměna vstupu/výstupu, záměna dispatch varianty, chybějící commit a recovery.
Syntetické payloady jsou uložené v reportu; nejsou vydávané za runtime provedení.

Přesné příkazy, návratové kódy, doby, hash vstupu a hash testovacího skriptu:
[`generated/completion-group-checks.json`](generated/completion-group-checks.json).
Reprodukce: `python scripts/run_completion_group_checks.py`.

## Počty a otevřená práce

Aktuální přepočet je v
[`generated/current-operation-schema-matrix.json`](generated/current-operation-schema-matrix.json).

| Jednotka | Aktuální počet | Význam |
|---|---:|---|
| Efektivní operace | 619 | Unikátní operation IDs z účinných katalogů |
| Trasy | 542 | Trasy spojené inventářem s operacemi; různé zdrojové katalogy |
| Nerozlišené operation schema odkazy | 252 | Chybějící request/response schema identity; dříve 260 |
| Operace s těmito odkazy | 126 | Unikátní operation IDs; dříve 130 |
| Obecné trasy | 505 | Trasy obsahující obecnou hranici; v tomto běhu nebyla nová obecná trasa uzavřena |
| Obecné route hranice | 1 515 | Request/response/event definice obecných tras |
| Neurčená event applicability | 152 | Inventář neurčuje, zda/podle jaké masky operace emituje event |

Údaj 509 v předchozím checkpointu byl převzat ze starší matice. Čtyři komponentové
trasy byly materializovány již před `e025079`; změnu 509 → 505 nelze přičítat
tomuto běhu. Původní historické zprávy zůstávají zachované.

Všech 130 původních dvojic má záznam v
[`generated/missing-operation-investigation.json`](generated/missing-operation-investigation.json):
původní chybějící odkazy, současné hranice, route lookup, přesné pasáže deklarované
autority, textové výskyty operation ID a explicitní node/saga vazby. Čtyři dvojice
jsou klasifikované výše. **Zbývajících 126 má `INVESTIGATION_OPEN`**. Automatické
dohledání pasáží není dokončené sémantické šetření; nelze je hromadně zařadit do
kategorie chybějícího business rozhodnutí. `ownerDecisionRequired:null` znamená
dosud nerozhodnuto, ne implicitní požadavek na OWNERa.

## Předávky a pokračování

V generation test reportu je šest konkrétních saga boundary řádků s canonical
operation, node kind, step ID, predecessor step IDs, input/output schema,
output artifact kind, postcondition a compensation ID. Tyto vztahy pocházejí
z autoritativního katalogu. Je ověřen přípustný tvar a diskriminace výsledků.

Nadále je třeba ověřit hydratovaný obsah artefaktů, přesnou lineage producenta
a konzumenta, current snapshot, skutečný commit, cancellation, retry a recovery
v každé procesní větvi. Schema identity ani správný `kind` nejsou tento důkaz.
Historických 3 204 inventarizačních řádků zde není přejmenováno na unikátní
runtime hrany a jejich runtime kompatibilita není prohlášena za prokázanou.

Další práce:

1. Dokončit jednotlivá šetření 126 položek `INVESTIGATION_OPEN`, začít dalšími
   generation/runtime vazbami v §56.9; nesuplovat celý obecný runtime protokol
   pouze vstupem jednoho generation saga kroku.
2. Projít 505 obecných tras po doménách; veřejný API body není serverový
   `StepInput`. Nepřenést do caller body serverový snapshot, fence či commit.
3. Uzavřít skutečné artefaktové a eventové předávky, včetně R11 hydratace,
   stavových slovníků, dispatchů a UI mapování.
4. Po dalších obsahových opravách regenerovat aktuální matice a opakovat
   dotčené testy. Úplné package gates a freeze podmínky dosud nejsou splněné.

Žádná otázka OWNERovi není tímto reportem předložena jako prokázaný blokátor.
