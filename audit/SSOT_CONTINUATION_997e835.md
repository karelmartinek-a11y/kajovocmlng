# Pokračování od 997e835 — PR #2

Celý SSOT zůstává **BLOCKED / rozpracovaný**. Opravy z předchozího běhu jsou
zachovány. Jejich původní reporty se nepřepisují novým úspěchem; evidence tohoto
běhu je v `audit/generated/continuation-997e835`.

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

## Navázání práce

Aktuální otevřený seznam je
[`generated/continuation-997e835/guard-counters/missing-operation-investigation.json`](generated/continuation-997e835/guard-counters/missing-operation-investigation.json).
Pět dvojic od počátku této větve má doložené schema bindingy; zbývá 125 dvojic.
Úplná sémantika 505 obecných tras a skutečný procesní graf zůstávají další prací.
Historických 3 204 řádků se nepovažuje za počet unikátních runtime předávek.
