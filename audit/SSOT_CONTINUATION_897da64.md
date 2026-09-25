# Obsahové pokračování z 897da64 — draft PR #2

Vstup: čistá větev `work/ssot-completion-2026-09-25`, commit
`897da64efe97b8439473f714892204a7a1b37caf`, SSOT SHA-256
`75d38f3b4abdf249c29eacbb075d8a6023637b7649df9aaa4a27f372696cd751`.
Starší důkazy v `continuation-997e835` zůstávají historické. Žádný merge/freeze.

## Skupina: approval command a uložené generation dokumenty

Autoritativní opravy jsou ve vloženém `contracts/payload-contracts.json`:

| Trasa / operace | Opravená maska | Zdroj významu |
|---|---|---|
| route.0234 / generation.spec.approve | requestSchema.properties.body | §12.21: „Approval command obsahuje expected job state version, current turn ID/status, spec revision/digest, capability snapshot/digest a idempotency key.“ |
| route.0232 / generation.spec.revision.read | responseSchema.properties.output → GenerationSpecification | §12.19: „GenerationSpecification je úplný immutable funkční kontrakt“; API route GET exact revision; §56.7 zachovává všech 34 vrchních fields. |
| route.0237 / generation.plan.read | responseSchema.properties.output → GenerationPlan | §12.23: „Planner vytvoří immutable GenerationPlan jako directed acyclic graph“; API route GET exact plan; §56.8. |

Approval body má šest povinných, nenullových polí `currentTurnId` (Uuid),
`currentTurnStatus` (COMPLETED), `specificationRevisionId` (Uuid),
`specificationDigest` (Digest), `capabilitySnapshotId` (Uuid),
`capabilitySnapshotDigest` (Digest). `expectedStateVersion` (Counter) a
`idempotencyKey` zůstávají v transportních guards, nyní nenullové podle §12.21.
Pole nepředstavují nová business rozhodnutí: jejich význam je výslovně vyjmenován;
camelCase spelling je technická konkretizace dovolená §12.18. Serverové
authorityId/commit/scopeLock nejsou součástí caller body a jsou odmítnuty.
Modelový proposal ani StepInput se nepoužívá jako veřejný approval command.

Oba read outputs používají **stejnou nativní definici** jako navazující validator,
nikoli nový přejmenovaný slot. Převzaty jsou její přesné typy, required/nullability,
varianty a reference. Úspěšné čtení exact existující revision/planu nesmí vrátit
null dokument; failure větev zachovává null output. Původní obálky a ostatní
nenapravená pole se nepovažují za důkaz sémantické úplnosti.

### Hranice, které zůstávají konkrétně otevřené

| Trasa | Request | Response | Event |
|---|---|---|---|
| 0234 | business body + povinné approval guards opraveny; query/transport review není celé uzavřeno | §12.21 vyjmenovává šest změn transakce, ale ještě není doložena přesná veřejná response projekce těchto změn; obecný output se nepřejmenovává na ApprovedGenerationSpecification | §12.21 ukládá OWNER approval event/audit, ale chybí dokázaná vazba každé R9 eventType varianty na přesný domain payload |
| 0232 | exact path id/revisionId zůstává; obecný body/query nebyl prohlášen za přesný | dokument opraven; trusted revision→digest vazba se musí ověřit proti persisted snapshotu, nikoli jen z jobId | R9 event payload je stále obecný; není doloženo, zda jde o událost read operace, nebo sledovaného generation agregátu |
| 0237 | exact path id/planId zůstává; obecný body/query nebyl prohlášen za přesný | dokument a vazba jobId/planId opraveny; DAG/coverage/artifact hydration vyžadují navazující plné kontroly | stejná nerozlišená read-versus-aggregate hranice; samotné GET není důkaz NONE |

Žádná z těchto tras není vydávána za úplně uzavřenou. Zejména **505 obecných
tras se tím nesnižuje**: u každé zůstává konkrétní obecná hranice. Dílčí odstranění
slotů není celé PASS.

### Konkrétní předávky a negativní větve

Vložený normativní `scripts/ssot/ssot_control.py` nyní obsahuje
`validate_generation_read_handoff`; jeho digest/velikost jsou aktualizované v
nativním manifestu. Funkce se používá po transportní validaci a neuděluje DB práva.

| Producent | Konzument | Prokázané | Nepokrývá |
|---|---|---|---|
| uložená specification revision → route.0232 response.output | nativní GenerationSpecification validator před precheck | stejná maska, všechna required fields, shoda jobId; FAILED/CANCELLED ani ACCEPTED se nesmějí předat jako dokument | trusted revision ID/digest, source/requirement coverage a approval transakce |
| uložený immutable plan → route.0237 response.output | nativní GenerationPlan validator před execution validation | stejná maska, required fields, shoda jobId a planId; failure s podstrčeným outputem je odmítnut | skutečné DAG, hydratační a runtime gates |
| OWNER approval body → server admission | R9 request validator + validate_generation_approval_handoff | explicitní snapshots a completed turn claim, shoda se separátními serverovými vstupy, skutečný specification digest | původ serverových vstupů z current DB snapshotu, fence, full precheck, atomic commit/outbox a jejich recovery |

Pending/failed read vrací z handoff kontroly false: žádný následný validator
nedostane fiktivní success. Nové čtení/recovery musí dodat skutečný potvrzený
dokument. Není to důkaz fungující retry smyčky nebo runtime implementace.

## Individuální šetření devíti generation operací

Následující tabulka zaznamenává konkrétní prověřené významy a chybějící vazby,
nikoli hromadné OWNER rozhodnutí. Samotná absence schema ID není důvod blokace.

| Operace | Přesný zdroj / relevantní definice | Co konkrétně brání navázání celé dvojice |
|---|---|---|
| generation.model.execute | §12.10–12.15, §52.4–52.7, §56.6; ModelCallDescriptor / ProviderOutcome | §12.11 říká „Timeout, connection error nebo worker crash po DISPATCH_STARTED bez uloženého response ID je MODEL_SUBMIT_OUTCOME_UNKNOWN“. ProviderOutcome vyžaduje rawResponse a nemá UNKNOWN localStatus; nelze jím pokrýt tuto větev ani před-submit failure. Vstupní vada acceptedOutput u REFUSED/INCOMPLETE/FAILED byla následně opravena ve skupině ProviderOutcome níže; není to OWNER volba ani uzavření celé operace. |
| generation.plan.create | §12.23, §49.16, §56.8 a §56.10; GenerationPlan / IMPLEMENTATION_PLANNERProposal | §56.10 zakazuje modelu vytvářet serverové commit receipt/current identity. Nativní plan je dokument/proposal, nikoli doložená create receipt pro všechny success/failure/replay varianty. Chybí konkrétní vazba přidělených plan/job IDs a persistence potvrzení k této operaci. |
| generation.spec.propose | §12.15, §12.19–12.21, §56.7/56.10; GenerationSpecification | §12.20: „Neúplná specifikace zůstává proposal a nemůže být schválena.“ Samotná schema-validní specification není serverový receipt přijaté nové immutable revision. Ještě není prokázáno celé uložení/rejection rozhraní této vnitřní operace. |
| generation.activation.prepare | §49.17: DRAFT→READY vyžaduje membership, previous/candidate snapshots, rollback, gates a preflight; ActivationPlan | Plán není potvrzení provedeného barrier/admission prepare. Nutno určit konkrétní command snapshot a serverový výstup stavu READY včetně stale/blocked větví; S07/S08 připravují runtime, nikoli celý activation set. |
| generation.activation.rollback | §49.17, §51.18; RollbackPlan / ActivationReceipt | „Rollback nikdy nesnižuje epoch“ a obnovuje frozen previous snapshot nebo ABSENT. ACTIVATE forward receipt ani rollback plán nejsou samy přesnou reverse-switch/result maskou včetně MANUAL_REVIEW a pending cleanup. |
| generation.blocker.open | §12.18, §49.15; Problem / Question | §49.15 vyžaduje BLOCKED s resumeState, resumePhase, checkpoint ID, context digest a blocker. Samotný Problem/Question neobsahuje dokázané přiřazení všech těchto polí ani serverovou persisted blocker identity; technická rekonstrukce zůstává otevřená. |
| generation.job.complete | §49.15 a §49.34; ClosureReport | COMPLETED je terminal job outcome, ale ClosureReport/evidence není command měnící job pointer ani jeho commit. Nestačí připojit closure dokument jako obě masky; zbývá concrete command→protected closure commit→receipt/error vazba. |
| generation.phase.start | §49.15: „Nový attempt má vyšší attempt sequence a vznikne až po terminalizaci předchozího.“ | Phase enum ani serverově sestavený StepInput nepokrývá start admission/attempt reservation a jeho response. Nutno propojit přesnou phase identity, parent authority, predecessor terminal a at-most-one active attempt. |
| generation.turn.interrupt | §12.8, §49.15 completion-versus-steer race | §12.8 vyžaduje persist nové OWNER zprávy a successor reservation; §49.15 dovoluje pozdní completion jen jako evidence. Runtime CANCEL frame nepokrývá clientMessageId/digest, turn fence ani persisted successor outcome. |

## Individuální šetření deseti runtime operací

Přečteny byly celé příslušné účinné §50.10, 50.11, 50.19–50.21, 50.25,
50.29 a 50.31 z aktuálního dossieru. Žádná níže uvedená mezera sama
neprokazuje nezbytné business rozhodnutí OWNERa.

| Operace | Přesná opora | Konkrétní chybějící maska/vazba |
|---|---|---|
| runtime.prepare | §50.10: immutable start snapshot je „read-only launch input, nikoli bearer credential“; §56.9 S07/S08 | Launch manifest ani IntegrationStepInput nepokrývá standalone prepare command/result a jejich chyby; nelze zavést authority z manifestu. |
| runtime.instance.start | §50.11: „Autoritativní start linearizační bod je commit readiness evidence odpovídající stejné runtime generation a živému pidfd.“ | Start request a readiness receipt nejsou totožné; runtime snapshot/observation postrádají dokázanou vazbu na všechny pending/failed start výsledky. |
| runtime.ready.report | §50.11 kroky 13–15 (HELLO/READY digests, conformance test, guarded evidence) | RuntimeObservation není wire HELLO/READY ani server acceptance ACK; potřebné je konkrétní mapování těchto hranic a stale odmítnutí. |
| runtime.invoke | §50.19 RuntimeIpcRequest; §50.20 exact input/output; §50.21 alias→jeden exact target operation/digest | JsonValue payload se musí validovat podle resolved bindingu. Bez konkrétního resolveru masky/error a current context nelze obecný request prohlásit za přesný celý invoke kontrakt. |
| runtime.cancel | §50.25 sedm cancellation kroků; „terminalizuje pouze podle známých outcomes“ | CANCEL frame command není potvrzený cancellation outcome; chybí úplná vazba cancellation version, reconciliation a result/error payloadu. |
| runtime.stop | §50.25 a §50.31; nejprve draining, reconciliation, potom process-tree termination a cleanup | SHUTDOWN frame ani RuntimeReceipt nevypovídá o dokončeném stop+cleanup; není doložena přesná standalone pending/failure/known-terminal maska. |
| runtime.cleanup.resume | §50.31 explicitní inventory a jedenáct kroků, konec „store final evidence a mark COMPLETE“ | Existuje obsah cleanup inventory, ale nikoli prokázaná celá resume request/checkpoint/result vazba a nullable pravidla částečného cleanupu. |
| runtime.connection.inspect | §50.19 16-byte header / canonical frame types | Header codec není inspection response. Není doložena projekce živé connection evidence a jejích nepřítomných/stale stavů pro tuto operaci. |
| runtime.heartbeat | §50.19 HEARTBEAT=12; §50.29 „old heartbeat ... je stale evidence“ | Typ frame nedává JSON payload ani ACK. ComponentHeartbeat patří jinému control transportu; bez transformace a identity proof se nepřebírá. |
| runtime.state.report | §50.29 ActivationRuntimeSnapshot a stale state report; §50.10 server instance identity | Snapshot není state report command, RuntimeObservation popisuje readiness; chybí přesné domain state payload→server acceptance/rejection mapování. |

## Navazující skupina: approval snapshot a ProviderOutcome

První publikovaná skupina je commit `3047f07`. Další evidence je oddělená:
`approval-handoff/commands.json` patří jen k mezivstupu
`fe6fd48f8d6fe6c112cd6727da3c1a7ee120985d53574e4b68ded02afa17c0b7`.
Nejnovější dotčený průchod je v
`generated/continuation-897da64/provider-outcome/commands.json` nad SSOT
`98dfcebd89aee508982a87847fd347ec89307fe54d2662d7b8c8b64c251f548f`.
Tento nový průchod skončil exit 0. Dílčí aktuální kontroly skončily 0, oba
baseline reproduktory očekávaně 1. Prošlo 109 domain/handoff, 22 ProviderOutcome,
669 generation mask, 13 saga, 7 native-manifest a 12 portable-manifest případů;
UI projekce odpovídají. Matice znovu potvrzuje 250 / 125 / 505 a 1512 obecných
hranic, bez schema identity konfliktů a bez nedohledaných vnořených refs.

### Approval: skutečné porovnání s current snapshotem

Vložený `validate_generation_approval_handoff` podle §12.19–12.21 porovnává
public command s oddělenými serverovými hodnotami job/turn/spec/capability.
Vyžaduje DISCUSSING, COMPLETED turn, exact stateVersion a všechny identity/digests,
stejný job dokumentu, žádné openQuestions a skutečný canonical digest předaného
specification dokumentu. Nestačí porovnat dva nepodložené digest řetězce.

109 aktuálních doménových testů zahrnuje změněný, stále schema-validní business
obsah se starým digestem; stale turn/revision/capability/verzi; otázku i při
matching digestu; cizí job/plan a failure document injection. Recovery případ
znovu ověří čerstvý snapshot s novým command idempotency key — nepředstírá
bezpečné opakování starého klíče nad změněným commandem.

Server musí vstupy získat pod skutečnými locks/fences v jednom authoritative
snapshotu. Predicate nevytváří approval authority ani commit receipt. Full
precheck, idempotency ledger a atomický zápis pointer/event/outbox stále vyžadují
implementaci a důkaz. Předání callerem dodaných hodnot za serverový snapshot
není povoleno. Event a veřejná response maska approval zůstávají otevřené.

Současně zůstaly zachovány původní identity
`urn:kcml:r9:semantic:route.0232:output` a `...:route.0237:output` jako odkazy na
skutečné nativní doménové definice. Test přes tyto identity ověřuje přímo nový
payload; nejde o přesunutí původního `values` za ref.

### ProviderOutcome: odmítnutý výsledek není structured success

§12.14 stanovuje: „Refusal, incomplete a provider failure se nezkoušejí parseovat
jako požadovaný structured success.“ Pole `acceptedOutput` v
`contracts/generation/generation-contracts.schema.json#/$defs/ProviderOutcome`
proto při `localStatus` REFUSED, INCOMPLETE nebo FAILED musí být null.
Původní maska dovolovala neprázdný artifact ve všech těchto větvích.

Opravena je autoritativní nativní definice, její aktivní R5 SOURCE_CONTRACT kopie
stejného path/identity i R5 `project-registry.schema.json#/$defs/ProviderOutcome`.
Jejich schéma texty jsou konzistentní a metadata/digests i native manifest byly
přepočteny. `history/r2` a historické auditní výsledky se nepřepisují.

Předávka je normalizovaný serverový provider receipt → konzument přijatého
structured artifactu. REFUSED/INCOMPLETE/FAILED nesmějí předat accepted artifact;
rawResponse, orderedItems, problems a server commit se nadále zachovávají.
COMPLETED/NO_OUTPUT není nově zakázán. Baseline nad 897da64 prokazuje šest
chybných přijetí (tři stavy × native/projection), nikoli chybějící testovací fixture.
Po opravě prošlo všech 22 případů. UNKNOWN nebo missing rawResponse/commit
nadále není platný potvrzený receipt. Neznámý submit vyžaduje samostatnou
recovery větev podle §12.11/52; nefalšuje se doplněním UNKNOWN do tohoto receiptu.

## Vnější manifesty

`package_integrity.py` a aktualizovaný `update_manifests.py` používají skutečnou
větev, současný SSOT hash, POSIX cesty a explicitně verzovanou reprezentaci
UTF-8 textu CRLF→LF; binární bytes se nemění. Obě strany kontroly používají
stejnou definici bytes/hash. Inventář se porovnává jako množina; duplicity,
vynechaný/přidaný soubor, změna obsahu, chybná větev a nový SSOT jsou vady.
Historický `audit/final-audit.json` není autoritou pro status. Manifest výslovně
zůstává BLOCKED/INVENTORY_ONLY; jeho integrita není sémantické PASS.
Zachován je také CLI vstup `package_integrity.py --generate` / `--receipt`.
Plain `FILE_MANIFEST_SHA256` a JSON varianta obsahují stejný ověřovaný soupis;
nevytvářejí cyklus vzájemného hashování. Výjimky jsou explicitní a ověřované,
post-hash receipt není vstupní autoritou. Manifesty hashují i aktuální reporty
a skripty; jejich výsledné bytes váže Git commit.
Dodatečný závěrečný test v `generated/continuation-897da64/package-final`
ověřil 13 manifest případů včetně zákazu rozšíření exclusion policy (exit 0).
Ve stejné složce je posledních 109 domain/handoff případů s rozdílnými turn,
specification revision a capability snapshot IDs, aby se záměna rolí neschovala
za shodné fixture hodnoty (exit 0). Tyto doplňující testy nemění SSOT hash.

## Evidence, počty a pokračování

Výsledek první skupiny: SSOT SHA-256
`6c66b8faf0979e36158699caf7e461b429922eaf761b39bfe49c6a484aed99c9`.
Spuštěný `run_domain_continuation_checks.py` skončil exit 0: aktuálních 92
doménových/handoff případů prošlo, baseline reprodukce skončila očekávaně 1.
Prošly i dotčené generation/saga/native integrity kontroly a UI projection check.
Guard regrese byla zopakována jednou kvůli změně approval guard nullability.
Po sjednocení obou vnějších hash manifestů bylo navíc spuštěno 12 portable
manifest případů (exit 0); jejich report uvádí hashe implementačních modulů.

| Ukazatel | 897da64 | Po skupině | Rozdíl |
|---|---:|---:|---:|
| Nedohledané operation schema odkazy | 250 | 250 | 0 |
| Operace s nedohledanými odkazy | 125 | 125 | 0 |
| Obecné trasy | 505 | 505 | 0 |
| Obecné request/response/event definice | 1515 | 1512 | −3 |

Příkazy první skupiny jsou v
`generated/continuation-897da64/generation-domain/commands.json`. Nejnovější
příkazy, matice a dossier jsou v `generated/continuation-897da64/provider-outcome`.
Reprodukce do nové složky, aby nepřepsala historickou evidenci:

```powershell
$env:PYTHONUTF8='1'
$env:KCML_AUDIT_OUTPUT='audit/generated/continuation-897da64/recheck'
python scripts/run_domain_continuation_checks.py --focused --provider
python scripts/update_manifests.py
python scripts/package_integrity.py
```

Jednotky: nevyřešený odkaz = jedna request/response schema identita operace;
dotčená operace = unikátní operationId s takovým odkazem; obecná trasa = unikátní
efektivní route s alespoň jednou obecnou hranicí, včetně tranzitivních refs.
Opravená dílčí maska není uzavřená trasa. 3 204 historických matičních řádků
nepředstavuje počet unikátních runtime předávek.

Závěr zůstává **BLOCKED**: 125 dvojic operací není uzavřených, event hranice
této skupiny zůstávají obecné, schvalovací DB/recovery vazby nejsou prokázané a
celý balík neprošel úplným sémantickým auditem. Žádná technická mezera není
přeznačena na plošné OWNER rozhodnutí.
