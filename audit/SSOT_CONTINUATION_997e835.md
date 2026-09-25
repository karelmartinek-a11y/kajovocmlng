# Pokračování od 997e835 — PR #2

Celý SSOT zůstává **BLOCKED / rozpracovaný**. Opravy z předchozího běhu jsou
zachovány. Jejich původní reporty se nepřepisují novým úspěchem; evidence tohoto
běhu je v `audit/generated/continuation-997e835`.

Větev: `work/ssot-completion-2026-09-25`; vstup `997e835`, obsahové skupiny
`5b60c8a` a `4e6ff4c`, následná oprava integrity a zdrojových výřezů je v diffu
této revize PR. Nejnovější evidence je v `native-integrity-final`, starší
podsložky jsou důkaz jen pro vlastní uvedený hash. PR zůstává draft, bez merge.

## Skupina 1: generation.candidate.publish a skutečná saga předávka

Vstup: commit `997e835`, SSOT SHA-256
`dd21d569eee6c54648414272e0405cc03b6f4ce9c29d1ac97aa27eb69431af1e`.

Výstupní SSOT SHA-256 této skupiny:
`3dadc71dde9c48dc9a8b34bec31400ce95b44c1671a6df8920caa3285450bdff`.

`generation.candidate.publish` má podle §56.9 a
`contracts/generation/integration-step-catalog.json` jedinou explicitní vazbu
S03, předchůdce S02 a výstup `CANDIDATE_RELEASE_RECEIPT`. §12.30 bod 3 určuje
„publikace candidate release metadata“. §56.9 stanovuje:
„`IntegrationStepInput` a `IntegrationStepReceipt` z 56.13 jsou hranice každého
již definovaného kroku 12.30.“

Klasifikace dvojice: **jednoznačné odvození z přesného nativního kontraktu a
explicitního katalogu**, nikoli odhad podle jména. Do
`contracts/operation-contracts.json#/$defs/generation.candidate.publish:command`
a `...:response` přibyly původně chybějící identity. Vstup je nativní
`IntegrationStepInput` omezený na S03. Výstup přebírá všechny nativní varianty
`IntegrationStepReceipt`, omezuje stepId a pro úspěch konkrétní result.kind.
Nejde o nový HTTP endpoint ani výstup modelu.

| Ukazatel | Při vstupu | Po skupině 1 | Rozdíl |
|---|---:|---:|---:|
| Nevyřešené operation schema odkazy | 252 | 250 | −2 |
| Operace s těmito odkazy | 126 | 125 | −1 |
| Obecné trasy | 505 | 505 | 0 |

### Předávka a opravený kontrolní kód

| Producent | Přenos | Konzument | Ověřená podmínka |
|---|---|---|---|
| S02 / component.revision.publish | `IntegrationStepReceipt` uložený jako `INTEGRATION_STEP_RECEIPT` | S03 / generation.candidate.publish, `predecessorReceipts` | Skutečné bajty, trusted inventory, digest, native schema, stejný job/saga, předchůdce S02, SUCCEEDED, správný druh výsledku |
| Saga MANUAL_REVIEW | `readBackEvidence` artefakty | Resume/recovery kontrola | Evidence musí být hydratovaná a validní i před vrácením neúspěšného/nepotvrzeného kroku |

Původní vložený `scripts/ssot/ssot_control.py` neměl kontrolu
`IntegrationStepInput`; `verify_saga` vracel neúspěšný stav ještě před validací
read-back artefaktů. Doplněno `validate_integration_step_input` a opraveno pořadí
hydratace. Opora: §49.16 požaduje potvrzené outputs s expected digests; §56.4
vyžaduje trusted artifact inventory; §56.9 vyžaduje predecessor receipts;
§56.12 vyžaduje skutečnou recovery evidenci.

Nový test používá reálné JSON bajty a původní `ArtifactResolver`; nahrazuje pouze
fyzické čtení souboru paměťovou mapou. Na původním commitu reprodukuje chybějící
kontrolu a přijetí poškozené read-back evidence. Po opravě prošlo 13 případů:
platná předávka, chybějící/duplicitní/jiný předchůdce, cizí job/saga, nesprávný
output kind, UNKNOWN outcome, nepodložená reference a poškozené bytes.
Regrese starého kódu má exit 1; aktuální kontrola exit 0.

Všechna dřívější generation schema negativa zůstávají v testovací sadě; navíc
se testuje S03 proti cizímu S04, záměna node/saga, chybný output kind a UNKNOWN.
Přesné příkazy, návratové kódy, hashe skriptů a úplný současný přepočet jsou v
[`generated/continuation-997e835/commands.json`](generated/continuation-997e835/commands.json).

Není tím prokázán current PostgreSQL fence, current approval/binding, postcondition
evaluator, compensation record ani skutečný runtime effect. Native reference na
`EvidenceRecord` není sama důkaz konkrétního business obsahu. Tyto samostatné
obligace zůstávají otevřené; počet vyřešených identit není počet uzavřených procesů.

## Jednotlivě prošetřené runtime hranice — další práce

Následující položky zůstávají otevřené technické šetření. Nejsou hromadně
přeznačeny na OWNER rozhodnutí. Přesné původní authority pasáže jsou u každé
operace v aktuální `missing-operation-investigation.json` tohoto běhu.

| Operace | Doložený zdroj / existující definice | Konkrétní neuzavřená vazba |
|---|---|---|
| runtime.prepare | §50.10–50.11, §56.9 S07/S08 | Integrační vstup nepopisuje celý samostatný launch/prepare protokol; nelze jej bez dalšího vydat za celou masku operace. |
| runtime.instance.start | §50.10–50.11, §56.9 S10 | Readiness commit a live pidfd jsou explicitní; chybí doložené úplné propojení standalone command/result s launch snapshotem. |
| runtime.ready.report | §50.11, §56.9 S11, RuntimeObservation | Observation není automaticky report command ani serverový receipt. Nutno dohledat HELLO/READY vazbu a přijímací odpověď. |
| runtime.invoke | §50.19 RuntimeIpcRequest, §50.20–50.21 | `payload` je JsonValue; exact input/output pochází z bindingu. Chybí ověřené propojení dynamického resolveru s oběma nativními maskami. |
| runtime.cancel | §50.25 | Sedmikrokový cancellation postup určuje chování; nedokládá sám celý command/result wire tvar. |
| runtime.stop | §50.25, §50.31 | Musí odlišit stop intent, známý efekt a cleanup completion; nelze jej nahradit obecným úspěšným receiptem. |
| runtime.cleanup.resume | §50.31 | Cleanup inventory a jedenáct kroků jsou určeny; zbývá přesná maska requestu, checkpoint/result a recovery vazby. |
| runtime.connection.inspect | §50.19 | Definice frame/header protokolu není výstup read-only inspection operace. Nutné dohledat skutečnou serverovou projekci. |
| runtime.heartbeat | §50.10 a frame HEARTBEAT v §50.19 | Runtime launch snapshot není heartbeat payload; nepoužít component heartbeat pouze kvůli názvu. |
| runtime.state.report | §50.10, §50.29, RuntimeObservation | Nutné doložit rozdíl mezi stavovým hlášením, observed readiness a serverovým přijetím evidence. |

Žádná z těchto mezer dosud není doložena jako chybějící business volba OWNERa.

## Skupina 2: přesná doména transportních guardů

Vstup skupiny: commit `5b60c8a`, SSOT hash uvedený u skupiny 1.
Výstupní SSOT SHA-256:
`93c5250de7a30199aedc404ee135b3bc525d4255ff532d90c724e66be23750c2`.

Opora: §56.3 definuje `Counter` jako desetinný řetězec v rozsahu
`0..9223372036854775807`, bez znaménka a úvodních nul; pravidlo platí také pro
`stateVersion`, `bindingSetRevision` a `activationEpoch`. Přesná existující maska:
`contracts/generation/generation-contracts.schema.json#/$defs/Counter`.

V autoritativním `contracts/payload-contracts.json` byly opraveny masky
`/records/*/requestSchema/properties/guards/properties/{expectedStateVersion,expectedBindingSetRevision,expectedActivationEpoch}`.
Původní epoch/version řetězce neměly horní mez; binding revision dovolovala
libovolný text do 256 znaků. Jde o technický nesoulad se stanoveným číselným
významem, nikoli chybějící business rozhodnutí. Opraveno **1 521 definic polí
na 507 trasách**. Dvě další trasy už měly správnou doménu z předchozího běhu.
Zachovány jsou původní required seznamy a nullable pravidla: tato skupina
nepřidává oprávnění volajícího ani neprokazuje aktuálnost DB guardu.

Test kontroluje všech **509 R9 route records × 3 guard definice × 13 hodnot =
19 851 případů**. Na commitu `997e835` reprodukuje 7 098 chybných přijetí;
aktuální masky odmítají všechny testované neplatné hodnoty. Obsah každé trasy
mimo tyto tři definice se navíc porovnává s původním záznamem. Kontroluje se
identita celé množiny tras, nikoli pouze počet. Testy zahrnují horní mez a její
překročení, nulové prefixy, znaménko, newline, text, číslo místo řetězce,
boolean a zachování nullability.

Propojení: caller-supplied optimistic guard → R9 request validator → porovnání
se serverovým Counter. Tato oprava zajišťuje shodnou číselnou doménu, **nikoli**
důkaz konkrétního DB porovnání, retry, cancellation nebo recovery implementace.
Do 505 obecných business tras se proto žádné snížení nezapočítává.
R9 payload canonicalDigest i resource manifest byly přepočítány.

Příkazy a návratové kódy jsou odděleně v
[`guard-counters/commands.json`](generated/continuation-997e835/guard-counters/commands.json).
Reprodukce v PowerShellu:

```powershell
$env:PYTHONUTF8='1'
$env:KCML_AUDIT_OUTPUT='audit/generated/continuation-997e835/guard-counters'
python scripts/run_continuation_checks.py --guard-counters
```

Jednotky základních čítačů: unresolved reference je jedna nedohledaná schema
identita konkrétní request/response hranice účinné operace; affected operation
je unikátní operationId s alespoň jednou takovou hranicí; generic route je
unikátní účinná trasa, jejíž povinná doménová maska zůstává obecná i po
tranzitivním rozlišení odkazů. 509 zde znamená záznamy R9 payload katalogu,
nikoli všech 542 efektivních tras ani počet runtime předávek.

## Skupina 3: přesná integrita nativního manifestu

Vstup skupiny: commit `4e6ff4c`. První oprava digestu vytvořila SSOT
`bea6779ec84357ff5f1a9940f803f485453b1a2b2677323cb735cee67ad8449d`.
Jeho **neúspěšný** průchod je zachován v
[`native-integrity/commands.json`](generated/continuation-997e835/native-integrity/commands.json).
Není vydáván za úspěšnou kontrolu současného dokumentu.

`contracts/execution/embedded-manifest.json` měl nesprávný rawDigest/sizeBytes
pro `scripts/ssot/audit_checks.py`: skutečný vložený soubor má 22 124 bajtů,
nikoli 22 122. Po této opravě nativní `Document.verify_manifest` odhalil ještě
neúplnost množiny: chybělo pět existujících `KCML-EMBEDDED authority="NORMATIVE"`
artefaktů `r6-final/active-manifest.json`, `r6-final/scripts/verify_deliverable.py`,
`r6-final/registries/current-route-bindings.json`,
`r6-final/registries/terminal-write-guards.json` a
`r6-final/sql/terminal-ledger-guards.sql`.

Opora opravy je existující normativní `Document.verify_manifest`: kontroluje
raw bytes, délku, authority a přesnou množinu všech nativních normativních
assets kromě sebe. Jde pouze o doplnění jejich bajtových identit; jejich obsah,
authority ani precedence se nemění. Zejména malé/prázdné R6 registry tím
nezískávají důkaz sémantické úplnosti. Historická kopie manifestu
`history/r2/embedded-manifest.json` se neopravuje zpětně.

Výsledný SSOT SHA-256:
`75d38f3b4abdf249c29eacbb075d8a6023637b7649df9aaa4a27f372696cd751`.
Závěrečná evidence této skupiny je v samostatném adresáři
`generated/continuation-997e835/native-integrity-final`; negativní testy musí
začínat z validního manifestu, jinak se jejich odmítnutí nepočítá za důkaz.
Testuje se chybějící/duplicitní záznam, jiný digest, velikost, authority a
neexistující artifact. Ani úspěch tohoto testu není package readiness.

Opraven byl také extraktor zdrojových pasáží: `## 12. Generátor…` dříve
neodpovídal regexu kvůli koncové tečce. Odkaz na kapitolu navíc musí zahrnovat
její podkapitoly, ne jen text před prvním podnadpisem. Osm regresních případů
ověřuje tečku, potomky, hranici sourozence/další kapitoly, opakované zdroje,
fyzické číslo řádku a skutečnou kapitolu 12. Nejde o nové produktové pravidlo
ani automatickou klasifikaci operací; oprava zpřístupňuje dříve vynechaný důkaz.

Úplná reprodukce dotčených kontrol této skupiny:

```powershell
$env:PYTHONUTF8='1'
$env:KCML_AUDIT_OUTPUT='audit/generated/continuation-997e835/native-integrity-final'
python scripts/run_continuation_checks.py --native-integrity --guard-counters
```

Tento běh skončil exit **0**; všechny dílčí příkazy mají očekávaný návratový
kód v `native-integrity-final/commands.json`. Baseline negativní reprodukce
záměrně končí 1, aktuální kontroly 0. Prošlo 19 851 guard případů, 669
generation mask případů, 13 saga případů, 7 manifest případů a 8 případů
extraktoru; kontrola UI projekcí a idempotentních generátorů také skončila 0.
Čerstvá matice potvrzuje **250 nevyřešených odkazů / 125 operací / 505 obecných
tras**, tedy proti `997e835` **−2 / −1 / 0**. Zpracováno 619 efektivních operací
a 542 efektivních tras; tyto počty neznamenají jejich sémantické uzavření.

## Navázání práce

Aktuální otevřený seznam je
[`generated/continuation-997e835/native-integrity-final/missing-operation-investigation.json`](generated/continuation-997e835/native-integrity-final/missing-operation-investigation.json).
Pět dvojic od počátku této větve má doložené schema bindingy; zbývá 125 dvojic.
Úplná sémantika 505 obecných tras a skutečný procesní graf zůstávají další prací.
Historických 3 204 řádků se nepovažuje za počet unikátních runtime předávek.

Další konkrétní postup (bez nové inventarizace od nuly):

1. Použít poslední dossier výše, nikoli staré prázdné výřezy §12. U zbylých
   generation operací zejména `generation.model.execute`, `generation.plan.create`,
   `generation.spec.propose`, `generation.activation.prepare` a
   `generation.activation.rollback` porovnat celé §12, §49.15–49.17, §51.18,
   §52 a §56.6–56.12 s přesnými nativními typy. `GenerationPlan` v návrhu
   IMPLEMENTATION_PLANNER není automaticky serverový výstup plan.create;
   `ModelCallDescriptor` a provider outcome vyžadují prokázanou vazbu na hranici
   model.execute, ne pouze podobný význam názvu.
2. U deseti runtime operací navázat na tabulku konkrétních mezer výše; standalone
   command/result se nezavírá tím, že existuje saga receipt S07/S08/S10/S11.
3. Zpracovat ostatní jednotlivé operace a doménové business payloady, potvrdit
   konkrétní procesní hrany včetně negativních výsledků/recovery. Počet 125
   označuje neprošetřené dvojice, nikoli 125 požadavků na OWNER rozhodnutí.
4. Opravit a regenerovat vnější `PACKAGE_MANIFEST.json` a `FILE_MANIFEST_SHA256`.
   Jsou nadále zastaralé. Stávající `update_manifests.py` pevně uvádí main a
   přebírá status historického `audit/final-audit.json` bez kontroly hashe;
   takový běh by nebyl důkazem současné integrity. Je nutné navázat manifest na
   skutečnou větev/hash a vyřešit LF reprezentaci dle `.gitattributes`, ne
   přepsat staré auditní výsledky. Opravený embedded manifest není celý balík.
   Diagnostické `python -` volající `verify_package.check_manifest()` nad
   aktuálním SSOT hashem skončilo exit 1 s 871 neshodami klíčů/bajtů v okamžiku
   kontroly. Není to počet 871 poškozených souborů: výsledky zahrnují i
   dvojice POSIX/Windows cest (`00_SSOT/KajovoCMLNG_SSOT.md` proti cestě se
   zpětnými lomítky). Přesná množina musí být po sjednocení cest přepočítána.
5. Teprve po obsahovém uzavření provést všechny povinné gates nad novým přesným
   vstupem. V tomto běhu byly spuštěny **dotčené** kontroly, nikoli úplný
   sémantický audit celého balíku. Žádný merge ani freeze není autorizován.

Závěr: **BLOCKED / technická práce pokračuje**. Dosud nebylo doloženo nové
nezbytné business rozhodnutí OWNERa; žádné se proto plošně nevyžaduje.
