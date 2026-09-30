### 12.48 Create completion contracts

Tato technická specializace §12.18 stanoví native response/event masky obou
create operací v `contracts/create-operation-design.schema.json` a jejich
podmínky v `contracts/create-completion.json`. Nemění obchodní scope Secrets
ani nahrazuje otevřené typové a parent/target policies obecným allowflagem.

`generation.job.create` vrací serverový `jobId`, `state = DISCUSSING`,
`stateVersion`, `initialRequestDigest` a `createdAt` (§25.11/§49.15/§72.11).
Create command je dokončen po svém atomickém commitu; nově vytvořený job tím
není COMPLETED a jeho execution authority nevytváří klient ani model.
`secret.create` vrací `secretId`, stable name/type, `versionId`, serverem
přidělené kladné `versionNumber`, `versionState = CREATED`,
`activeVersionId = null`, `stateVersion` a `createdAt` (§25.6/§49.22.1/§72.21).
Vytvoření immutable candidate a jeho pozdější aktivace jsou různé operace.
Nenastavuje se ACTIVE ani activation epoch jen kvůli create. Tato maska
neomezuje OWNER reveal plné hodnoty podle §8.5/§8.6; receipt není reveal route.

Všechny identity, countery, časy a digests pocházejí z canonical serverového
commitu. Counter používá přesný signed-bigint decimal-string kontrakt §56.3;
root state version vychází z §51.9. Schema nestanoví novou business konstantu
počátku versionNumber. Common response obsahuje logical/correlation IDs,
stateVersion, eventSequence, activationEpoch, resultDigest a idempotencyReplay
podle §49.3. activationEpoch je null pro nově vytvořený neaktivovaný root.
SUCCEEDED má terminal=true, přesný nenullový receipt a error=null. ACCEPTED
má terminal=false, pouze durable logical-operation reference a dosud žádný
create receipt. FAILED/CANCELLED mají output=null a konkrétní error.
Retryable attempt failure s RETRY_SAME_OPERATION má terminal=false;
neterminalizuje business idempotency record (§49.4). UNKNOWN není známý rollback ani terminal failure a vyžaduje reconciliation
téže operation. CANCELLED je možné pouze pokud cancel vyhrál před commitem;
po commitu se vrací původní canonical create outcome, nevytváří se nový root.

Stable error catalog §32.6 doplňují přesné technické create codes/predicates
v `contracts/create-completion.json#/errorPredicates`. Classification,
retryDirective a HTTP status jsou pevně vázané na code a jeho predicate;
message je lokalizovatelný text, nikoli recovery autorita. Existující
IDEMPOTENCY_CONFLICT a SIDE_EFFECT_OUTCOME_UNKNOWN nemění význam. HTTP error používá `HttpCreateFailure`: operationId, serverové requestId/correlationId,
logicalOperationId=null před přijetím a pevný statusCode/error tuple; nevymýšlí
se persistovaná logical operation pro neplatný JSON. Neznámá diagnostika
se nesmí potichu mapovat na úspěch ani nesouvisející error. Parse,
auth a admission odmítnutí nevytváří doménový root ani create event. Known
transaction rollback musí mít pozitivní evidence; absence response není
takovou evidence. Neověřený povinný kontrakt vrací BLOCKED, nikdy PASS.

Event applicability obou operací je AGGREGATE_STREAM. Generation emituje
`generation.job.created` z §12.44 SourceEnum044. Secret create má typed
`OPERATION_TERMINAL` event svázaný s operationId=secret.create, canonical
writer.secret a secret_record (§49.5 a operation-contracts record546);
toto je specializace existujícího event typu, nikoli tvrzení o nezadaném
secret.created eventu. Payload je přesný create receipt a payloadDigest
je serverový digest jeho canonical JSON bytes. Immutable event UUID,
aggregateId, aggregate-local sequence, occurredAt a correlation/logical
operation jsou povinné. Event payload odpovídá frozen output, aggregate
identity a result digest relations musí ověřit serverový validator.

Root, immutable initial request nebo encrypted CREATED secret version,
canonical outcome, aggregate sequence, typed event, audit head a outbox
vzniknou v jedné transakci (§49.5/§51.12); chyba audit/outbox ruší celý commit.
Generation queue/discussion work se plánuje až z persistovaných vstupů.
Publisher smí vydat jen přesný persistovaný event po commitu. Consumer
deduplikuje immutable event ID; gap vyžaduje replay/snapshot a stejný ID
s jiným digestem je konflikt, ne nový effect. Replay nevytváří druhý event.

Stable lookup locator a frozen execution scope jsou odlišné podle §49.4:
operation family, OWNER_FULL, stable OWNER ID, stable create target namespace
a client key digest vybírají původní record. Aktuální contract/caller revision
není součást lookupu. Nalezený record připíná původní operation revision,
caller/target snapshots a executionDescriptorDigest; clientRequestDigest
se porovnává, executionDescriptorDigest se ověřuje proti uloženému descriptoru,
nikoli znovu sestavuje z current revision. Stejný key/digest vrací původní
receipt; jiný digest je konflikt; unknown outcome nejprve reconciliuje.

Response/event read selector používá serverový jobId/secretId/versionId.
Hydration ověří skutečné uložené bytes/content digest a immutable initial
request nebo version linkage, potom semantic postconditions konzumenta.
Současný read může mít vyšší stateVersion; nesmí přepsat frozen create receipt.
UI přebírá přesný serverový receipt, obnoví detail podle identity a zachová
idempotency key při transportním retry (§72.11/§72.21). Model proposal není
serverový receipt. Schema a reference-model tests nedokazují executable SQL,
skutečný backend, encryption service ani celou consumer pipeline.

Otevřené policies jsou explicitní: přesné gramatiky devíti structured/crypto
Secret typů a vlastní lifecycle admission matrix parent/target objektů.
Samotný seznam valuePolicyTypes, existence reference ani lifecycle sousedního
objektu nejsou jejich důkaz. Dokud nejsou vyřešeny, tyto varianty jsou BLOCKED
a celé create operace nelze označit sémanticky uzavřené.

