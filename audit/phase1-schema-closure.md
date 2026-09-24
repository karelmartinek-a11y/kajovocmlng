# Fáze 1 — PARTIAL

Fáze není uzavřena. Byly provedeny lokální opravy kontraktů a rozšířena reprodukovatelná kontrola jejich hranic. Počet chybějících schémat ani počet obecných doménových masek se těmito omezenými opravami nesnižuje. Nejde o potvrzení implementation-ready ani freeze-ready.

## Checkout a autorita

Výchozí větev: `main`. Výchozí i výsledný HEAD: `6180d9fe67dfaa5365190301dfd58cc8d9812f3d`. Výchozí `git status --short` byl prázdný. Změny zůstávají necommitnuté, bez push, merge nebo release. Nebyly nalezeny platné `AGENTS.md` v repozitáři ani kontrolovaných nadřazených adresářích. Uživatelské soubory nebyly odstraněny.

Výsledný checkout je dirty: mění SSOT, `01_UI_CONTRACT/FUNCTION_PARITY.csv`, QA, auditní závislosti, referenční validátor a regenerované auditní reporty. Nové jsou pětice `phase1_*`/`verify_phase1_contracts.py` skriptů, tři požadované předávací soubory, výchozí matice a detailní `audit/generated/phase1-*` evidence. Finální package manifesty zůstávají z předchozího stavu a nelze je vydávat za integritní potvrzení tohoto checkoutu.

Autorita vychází z README, SSOT 55.2–55.3 a `r13/contracts/effective-precedence-index.json`: konkrétní explicitní specializace, nikoli pořadí revizí. R16 explicitně povyšuje osm visual operations; `closure/contracts/operation-overlay.json#/finalOperationIds` uzavírá efektivní množinu na 619. Staré deklarace PASS v resourcech nejsou současným důkazem uzavření.

Hlavní SSOT je jediný měněný normativní soubor. Vložené resources jsou autoritativní; samostatné UI a auditní soubory jsou projekce/evidence. Historické provenance ani kapsle nebyly automaticky povýšeny na novou autoritu.

## Počty před opravami a po nich

Počty byly zjištěny z obsahu checkoutu; historické zadání nebylo použito jako testovací oracle. Stav „před“ se regeneruje přímo z výchozího commitu.

| Vlastnost | Před | Po |
|---|---:|---:|
| Efektivní operace | 619 | 619 |
| Efektivní trasy v payload katalozích a explicitní R16 promotion | 542 | 542 |
| Operace s chybějícím schema ID | 130 | 130 |
| Nerozlišené odkazy těchto operací | 260 | 260 |
| Konfliktní odkazy efektivních operací | 0 | 0 |
| Trasy s obecnou obálkou místo doložené doménové masky | 509 | 509 |
| Unikátní request/response/event definice s obecnými obálkami | 1527 | 1527 |
| Operace bez explicitního rozhodnutí o událostní hranici v této mapě | 152 | 152 |
| Další rozlišené definice vyžadující úplnou sémantickou revizi | 74 | 74 |
| Selhání rozlišení vnořených referencí dosažitelných z nalezených masek | 0 | 0 |
| Nezpracované hlavičky vložených resources | 0 | 0 |

542 = 509 R9 + 11 R11 + 8 R16 + 14 closure tras. Původní `contracts/execution/route-catalog.json` obsahuje 522 výskytů; jejich normalizace je doložena R8 route bindings a `sourceOccurrenceIds`, nikoli odstraněním operací. Matice zachovává zdroj této normalizace. „152 událostních mezer“ není tvrzení, že všech 152 operací musí emitovat event. Chybí zde prokazatelná vazba nebo výslovný kontrakt nepřítomnosti.

## Skutečně provedené opravy

1. V `contracts/payload-contracts.json` byly upraveny request masky `secret.create` (`route.0386`) a `generation.job.create` (`route.0215`): nepřipouštějí `body: null`, vyžadují alespoň jednu položku `body.values` a nepřipouštějí `guards.idempotencyKey: null`. Opora: SSOT 8.3 a akce `secret.create` v kapitole 72 vyžadují vytvoření secretu s metadaty a první hodnotou; 12.2 definuje vstupní OWNER zadání; 26.1 vyžaduje idempotency key u mutací. Nejde o plošné `minItems: 1` pro libovolná pole. Stávající struktura transportu je zachována.

   Tyto podmínky jsou pouze nutné, nikoli postačující. Neznámý slot stále může nahradit skutečný doménový obsah. Proto obě trasy nadále patří do 509 neuzavřených masek. Syntetický envelope witness v testech není označen za platný doménový příklad. Nebyla domyšlena pole, nullabilita nebo varianty jednotlivých typů secretů ani generation vstupů.

2. V `r16/contracts/r15-visual-operation-closure.json` má všech osm operací nově jednoznačné `requestSchemaRef` a `responseSchemaRef` (16 odkazů). Každý odkaz je odvozen výhradně z existujícího `requestDefinition`/`responseDefinition` a příslušných deklarovaných schema authorities. Výběr vyžaduje právě jednu odpovídající `$defs` definici; nejde o podobnost názvů. Původní pole zůstávají zachována. Přepočítány jsou `operationContractDigest` těchto osmi záznamů.

   Dotčené operace: `browser.annotation.create`, `.list`, `.tombstone`, `.reanchor`, `browser.focus.request`, `.acknowledge`, `.resolve`, `.open`. Jejich masky již existovaly před touto fází; 16 explicitních odkazů nesnižuje historických 260 chybějících ID. Oprava zpřístupňuje stejný konkrétní kontrakt běžným konzumentům `requestSchemaRef`.

3. Opraven je rozsah `scripts/verify_schema_references.py`: nyní používá stejné zdroje jako matice, zahrnuje request/command/response, route events a alternativní definice R16 a kontroluje vnořené reference s jejich skutečným rozlišovacím kontextem. Závislosti jsou povinné, JSON Schema dialekt nesmí být neznámý, formáty mají aktivní checkery. Offline registr nepřistupuje na síť. Konfliktní `$id` nejsou řešena pořadím načtení.

Nutná odvozená změna mimo vlastní masky: hash/velikost změněného payload resource v R9 `manifest.json`. Byla ověřena existující receptura `canonicalDigest` payload katalogu: kanonicky seřazený JSON s vlastním digest polem nastaveným na `null`. Obálky zachovávají gzip+base64, aktualizují bytes/SHA-256 a používají deterministickou kompresi. Globální finální integrity manifesty nebyly přepisovány; patří do další fáze.

## Reprodukce a projekce

`python scripts/phase1_repair_contracts.py` provádí výše popsanou mechanickou transformaci autoritativních zdrojů. `--check` ověřuje idempotenci; `--verify-from-baseline` nezávisle znovu odvodí přesné výsledné resource bytes z výchozího commitu a kontroluje, že jiné vložené resources nebyly změněny. Evidence je v `audit/generated/phase1-reproduction.json`.

Regenerace `python scripts/build_parity.py` promítá nové reference do `audit/generated/function-parity.json` a `01_UI_CONTRACT/FUNCTION_PARITY.csv`. Ostatní UI projekce zůstávají kontrolovány příkazem `python scripts/project_experience.py --check`. Matice, unresolved seznam a testovací fixtures jsou další odvozené výstupy. Nová přímá validační závislost `referencing==0.37.0` je připnuta v `requirements-audit.txt`.

## Ověření

Přesné příkazy, skutečné návratové kódy, stdout/stderr a SHA-256 zkontrolovaného SSOT obsahuje `audit/generated/phase1-checks.json`. Reprodukční příkaz celé sady je `python scripts/phase1_run_checks.py`; nenulový výsledek není přeznačen na PASS.

| Příkaz | Návratový kód | Skutečný význam |
|---|---:|---|
| `python scripts/phase1_schema_closure.py --baseline` | 1 | Výchozí neuzavřené hranice; nejde o selhání generování matice |
| `python scripts/phase1_schema_closure.py` | 1 | Zbývá 260 chybějících odkazů a 509 obecných tras, další review backlog |
| `python scripts/verify_schema_references.py` | 1 | Chybějící reference zůstávají FAIL; přesný počet kontrol v JSON reportu |
| `python scripts/verify_phase1_contracts.py --baseline` | 1 | 108 případů, 14 skutečných selhání |
| `python scripts/verify_phase1_contracts.py` | 1 | 108 případů, 100 PASS a 8 skutečných selhání |
| `python scripts/phase1_repair_contracts.py --check` | 0 | Žádná další změna při opakování transformace |
| `python scripts/phase1_repair_contracts.py --verify-from-baseline` | 0 | Přesné odvození změněných resource bytes z výchozího commitu |
| `python scripts/run_baseline_gates.py` | 0 | Všech pět původních bran prošlo; necertifikují doménovou úplnost |
| `python scripts/phase1_run_checks.py --embedded-r9` | 0 | Vložený R9 validátor a jeho resource manifest prošly |
| `python scripts/project_experience.py --check` | 0 | Shoda šesti kontrolovaných UI projekcí |
| `python scripts/verify_preserved_policy.py` | 0 | Zachování 40 původních Secrets/credentials sekcí |
| `python scripts/verify_experience.py` | 0 | 21 existujících statických/fixture kontrol prošlo |
| `python scripts/build_parity.py` | 0 | Regenerace 136 UI funkcí / 619 operací; není to důkaz úplné parity |
| `python scripts/audit_inventory.py` | 0 | Bez aktuálních strukturálních chyb; jedna historická chyba uchována jako provenance |
| `python scripts/phase1_search_history.py` | 0 | Hledání dokončeno ve třech revizích; žádná deklarace hledaných 260 ID, žádná nezpracovaná resource hlavička |

`git diff --check` a kompilace nových Python skriptů prošly s kódem 0. Globální `verify_package.py` ani finální package hashing nebyly v této fázi použity jako gate: aktuální celobalíkové manifesty jsou výslovně mimo její rozsah.

Testovací sada rozlišuje konkrétní R16 masky, pouhé create-envelope podmínky a otevřené doménové mezery. Platné syntetické příklady a negativní mutace jsou v `audit/generated/phase1-fixtures.json`, výsledky v `audit/generated/phase1-contract-tests.json`; varianty `-before` se odvozují z Gitu. Pokrývají chybějící povinné pole, nesprávný typ, nepovolené null, neznámé pole, neplatný discriminator, neznámý query parametr, prázdné values, vadný canonicalJson a duplicitní slot. Kontrolují také formáty, neznámý dialekt, chybějící závislost, chybějící offline referenci a obě pořadí konfliktních identit.

Osm záměrně nezamaskovaných FAIL po opravě:

- pro každou z `secret.create` a `generation.job.create` dosud projde `NOT_A_DECLARED_FILTER`, malformed `canonicalJson`, neznámý doménový slot a duplicitní slot;
- to jsou skutečná selhání požadovaného odmítnutí, nikoli očekávané PASS testu známé chyby;
- opravené invarianty neprokazují validitu celého těla, výstupu ani události.

Původní pětice bran (`run_baseline_gates.py`) prošla již před opravou navzdory těmto mezerám. Její zelený výsledek proto necertifikuje doménovou úplnost. Samostatně se kontroluje vložený R9 validátor včetně vnitřního manifestu, inventura, shoda projekcí, experience fixtures a zachování 40 původních Secrets/credentials sekcí.

## Neuzavřené práce a konkrétní blokátory

- **260 schema ID / 130 operací:** přesné operation ID, request/response role, chybějící identita, autoritativní JSON pointer a dostupné `authoritySourceRefs` jsou v `phase1-unresolved.json`. Identitní hledání v aktuálních resourcech, kapsli a inline schématech nenašlo odpovídající deklarace `$id`. To samo nedokazuje absenci jinak pojmenovaného sémantického ekvivalentu. Úplná rekonstrukce každého ze 130 kontraktů podle všech jeho doménových požadavků nebyla dokončena; není poctivé označit všech 260 případů automaticky za chybějící rozhodnutí OWNERa.
- **509 obecných tras:** chybí uzavřená vazba slot → doménové pole/schéma a u query konečný seznam jmen s typy. `semanticRules` obsahují například `DUPLICATE_SLOT_REJECT` a požadavek serverového ověření, ale samotná schémata tato pravidla nevynucují. V repozitáři není v této fázi doložena úplná konkrétní doménová validace této obálky; pouhý název pravidla nestačí.
- **`secret.create`:** 8.2–8.3 určují typy a entity, ne úplnou operaci pro všechny typované vstupní varianty v R9 slot transportu. Nalezený `SecretRequirement` popisuje výrobní/binding požadavek, nikoli vytvoření secretu s první verzí. Nelze jej přesměrovat jako ekvivalent create masky. Zbývá doložit vstupní pole versus serverová metadata, typované hodnoty, required/null pravidla, výstup a event.
- **`generation.job.create`:** 12.2 dovoluje text i další vstupní materiály. `StepInput`, `GenerationResult` ani UI solution specification nejsou automaticky ekvivalentem založení jobu. Chybí ověřené mapování těchto skutečných vstupů na sloty, varianty a výslednou odpověď/event.
- **152 událostních nejasností a 74 dalších definic:** je nutná sémantická revize a explicitní rozlišení „žádná hranice“ od „nezdokumentovaná hranice“. Žádné fiktivní event payloady nebyly přidány. Platné fixtures osmi browserových operací nenahrazují úplnou revizi všech 74 definic.

Konflikt normativních významů nebyl svévolně rozhodnut. Pro žádnou nerozlišenou referenci nebyla použita prázdná náhrada, libovolný objekt ani obecný JSON string. Stav PARTIAL zahrnuje také nedokončené sémantické prošetření; není vydáván za dokončení všech oprav požadovaných zadáním.

## Rozsah skutečně prozkoumaných podkladů

Strojově: souborová inventura balíku s explicitními výlukami `.git`, `.cache`, bytecode a instalovaných závislostí dle existujícího inventarizačního skriptu; všech 320 přímých vložených resources ze 17 rodin; 21 souborů ověřené XZ kapsle; relevantní inline JSON Schema; 402 rozlišovacích dokumentů; 34 rodin/zdrojových dokumentů s operačními výskyty. Matice eviduje i identifikátory mimo explicitně povýšenou efektivní množinu. `.git` historie není zaměněna za obsah balíku.

Hledání ve všech třech lokálně dostupných revizích SSOT a jejich dekódovaných resourcech/kapslích je reprodukovatelné příkazem `python scripts/phase1_search_history.py`; přesný rozsah, nezpracované historické hlavičky a nalezené identity jsou v `audit/generated/phase1-history-search.json`. Jde o hledání přesných identit, nikoli plnou sémantickou revizi historie. Historické provenance soubory byly zahrnuty do strukturální inventury; explicitní hledání R9 operation schema IDs v `audit/provenance` nemělo textový nález. Google Disk nebyl v této fázi použit.

Věcně byly přečteny README, QA a rozhodnutí auditu; pravidla autority 55.2–55.3, 55.20–55.22 a 56.1–56.2; relevantní části 8, 12.1–12.2, 19.3, 26.1, 42, 44.2–44.5 a 70.1–70.14; dotčená pole dvou create operací, R9 payload struktura a sémantická pravidla; definice a autoritativní odkazy osmi R16 browserových operací; čtecí, katalogové, inventarizační, referenční a reprodukční skripty a vložené R9/R16 validátory. Výpisy byly cílené, nikoli úplné přečtení všech řádků SSOT. Automatické dekódování a průchod kontrakty není lidská sémantická revize 619 operací.

## Podklady pro další fázi

Před celkovým uzavřením producent → artefakt → konzument zbývá navázat 130 interních request/response párů na skutečná doménová data, nahradit nebo konkretizovat 1527 obecných hranic a vyřešit applicability events. U dynamických payloadů je nutná verifikovatelná vazba na konkrétní schema identity/revision/digest, validace rozbaleného obsahu a jednoznačná propagace odmítnutí před handlerem. Mapování výrobních artefaktů není samo o sobě mapováním operation requestů.

Požadované předávací soubory jsou `audit/phase1-schema-closure.md`, `audit/phase1-operation-schema-matrix.json` a `audit/phase1-unresolved.json`. Výchozí matice a detailní evidence leží vedle nich, respektive v `audit/generated/phase1-*`. Další prompt by měl zachovat tento stav PARTIAL a nepředpokládat uzavření fáze 1.
