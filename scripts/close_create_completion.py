"""Author precise create output/error/event contracts and their technical provenance."""
import argparse,hashlib,json,re
from ssot_sources import SSOT,resources,resource_index
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
from create_completion_contracts import PATH,ERRORS,contract

TEXT='''### 12.48 Create completion contracts

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
`recordStatus = INACTIVE`, `activeVersionId = null`, `stateVersion` a `createdAt` (§25.6/§49.22.1/§72.21).
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

Otevřené policies jsou explicitní: úplný browser
kontrakt a celá serverová policy/producer/consumer předávka. Vlastní generation
selectors a native validators podle §12.51 již existují, úplná fyzická source
projection a child-commit coupling zůstávají povinné.
Samotný seznam valuePolicyTypes, existence reference ani lifecycle sousedního
objektu nejsou jejich důkaz. Dokud nejsou vyřešeny, tyto varianty jsou BLOCKED
a celé create operace nelze označit sémanticky uzavřené.

### 12.49 FOLLOW_UP immutable admission

Schválené produktové pravidlo OWNER (2026-09-30, podmínky 1–7) dovoluje
nezávislou FOLLOW_UP větev před terminalitou source jobu. §12.41 nadále
vyžaduje vlastní discussion/specification a následnou execution authority;
§25.11 terminal immutability zdrojového jobu není zákaz nové větve. Frozen
podklad sám nepovoluje execution ani nenahrazuje požadovaný finální výsledek.
Nezavádí se plošný terminal-state guard ani lifecycle převzatý od jiného kindu.

FOLLOW_UP vyžaduje parentJobId a followUpBasis s jednoznačným basisKind:
INITIAL_REQUEST (expectedDigest), SPECIFICATION_REVISION (revisionId,
expectedDigest), PUBLISHED_FINAL_OUTPUT (artifactId, expectedDigest).
To jsou pouze klientské selektory/preconditions, nikdy trusted receipts.
Každá uzavřená varianta má vlastní přesnou masku bez extra/null polí.
INITIAL_REQUEST znamená původní immutable request konkrétního parent jobu,
nikoli current obsah. Revision/artifact UUID musí vybírat přesně identifikovaný
persistovaný neměnný podklad. Chybějící/nepublikovaný potřebný finální output
se odmítá konkrétním FOLLOW_UP_BASIS_UNAVAILABLE nebo
FOLLOW_UP_FINAL_OUTPUT_UNPUBLISHED; chybějící závazný COMMITTED publication
receipt je FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED.

Matice kind × source state × dostupnost je contracts/follow-up-admission.json.
FOLLOW_UP ve všech jedenácti vlastních stavech generation_job dovoluje pouze
AVAILABLE_IMMUTABLE podklad: owned, konzistentní, dostatečný pro vybraný druh,
se skutečně načtenými bytes a přepočteným digestem. Pro finální output musí
odpovídat závazný publication receipt. MISSING, INCONSISTENT, INSUFFICIENT,
UNPUBLISHED jsou odmítnutí; jiné kinds mají vlastní §12.41 dependencies a
nepřebírají toto povolení. Jejich neuzavřené policies zůstávají OPEN.

Admission atomicky autentizuje OWNER, ověří parent ownership, přesný
snapshot/revision/artifact, bytes a obsahovou způsobilost pod příslušnými
locks. Neověřená atomicita je BLOCKED. Server persistuje frozenBasis:
sourceJobId, snapshotId, basisKind, contentDigest, lineageDigest a podle
varianty revisionId nebo artifactId/publicationReceiptId. Descriptor nikdy
neobsahuje plaintext podkladu, current pointer ani důvěryhodnost dodanou
modelem. Lineage digest pokrývá přesný descriptor bez samotného lineageDigest.
GenerationCreated a generation.job.created obsahují stejný kind/frozenBasis;
pro ostatní kinds je frozenBasis=null. Descriptor, nový child root, initial
request, canonical outcome, audit a outbox se commitnou společně (§49.5).
Source inputs/plan/state/artifacts/control se nemění. Jeho pozdější update,
failure nebo cancel nemění zmrazené vstupy child jobu. Hydration z uloženého
snapshotId ověřuje actual bytes, content/lineage digest a případný publication
receipt, nikdy current state source jobu. Consumer používá tento frozen podklad.

Idempotency lookup §49.4 předchází nové způsobilostní kontrole: stejný stable
locator/request digest vrací původní frozen receipt, změněný selector/digest
se stejným klíčem je IDEMPOTENCY_CONFLICT, UNKNOWN vyžaduje reconciliation
původního commitu. Souběžná změna relevantních locked zdrojů vede k novému
ověření před jedním commitem, nikoli k přijetí pohyblivého podkladu. Nový key
má vlastní child identity/běh. Sdílené prostředky a side effects nadále
podléhají existující isolation/coordination; FOLLOW_UP není jejich výjimka.

Referenční model netvrdí skutečné SQL locks ani runtime sufficiency.
Serverové consistent/sufficient výsledky musí pocházet z konkrétního
validatoru daného podkladu; boolean dodaný klientem/modelovým proposalem
nestačí. Tyto implementační a ostatní kind policies jsou samostatné povinnosti.

'''

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 text=SSOT.read_text();items=list(resources(text));rs=resource_index(items)
 raw=(json.dumps(contract(),ensure_ascii=False,indent=2)+'\n').encode()
 gen_path='contracts/generation/generation-contracts.schema.json';gen=json.loads(rs[gen_path]['raw'])
 codes=gen['$defs']['SourceEnum110']['enum']
 for error in ERRORS:
  if error['stableCode'] not in codes:codes.append(error['stableCode'])
 gen_raw=encoded(gen,rs[gen_path]['raw'])
 manifest=json.loads(rs['manifest.json']['raw'])
 entry=manifest['resources'].setdefault(PATH,{'kind':'JSON'});entry.update(sizeBytes=len(raw),sha256='sha256:'+hashlib.sha256(raw).hexdigest())
 follow_path='contracts/follow-up-admission.json'
 from follow_up_contracts import matrix,AUTHORITY
 follow_raw=(json.dumps({'authority':AUTHORITY,'status':'APPROVED_FOLLOW_UP_RULE','runtimeAcceptance':'NOT_EVALUATED','matrix':matrix()},ensure_ascii=False,indent=2)+'\n').encode()
 manifest['resources'][follow_path]={'kind':'JSON','sizeBytes':len(follow_raw),'sha256':'sha256:'+hashlib.sha256(follow_raw).hexdigest()}
 updates={PATH:raw,gen_path:gen_raw,follow_path:follow_raw,'manifest.json':encoded(manifest,rs['manifest.json']['raw'])}
 native_path='contracts/execution/embedded-manifest.json'
 native=json.loads(rs[native_path]['raw'])
 matches=[e for e in native['files'] if e['path']==gen_path]
 if len(matches)!=1:raise ValueError('CREATE_NATIVE_MANIFEST_ENTRY_MISSING_OR_DUPLICATE')
 matches[0].update(sizeBytes=len(gen_raw),rawDigest='sha256:'+hashlib.sha256(gen_raw).hexdigest())
 updates[native_path]=encoded(native,rs[native_path]['raw'])
 pending=[k for k,v in updates.items() if k not in rs or rs[k]['raw']!=v]
 if a.check:
  exact=not pending and text.count(TEXT)==1
  print(json.dumps({'status':'PASS' if exact else 'BLOCKED','pending':pending,'normativeTextExact':text.count(TEXT)==1}));return int(not exact)
 text=rewrite(text,items,updates)
 if '### 12.48 Create completion contracts' in text:
  start=text.index('### 12.48 Create completion contracts');end=re.search(r'^### 12\.(?:[5-9]\d|\d{3,}) |^## 13\.',text[start:],re.M)
  if not end:raise ValueError('CREATE_COMPLETION_SECTION_END_MISSING')
  text=text[:start]+TEXT+text[start+end.start():]
 if '### 12.48 Create completion contracts' not in text:
  match=re.search(r'^## 13\.',text,re.M)
  if not match:raise ValueError('GENERATION_SECTION_END_MISSING')
  text=text[:match.start()]+TEXT+text[match.start():]
 SSOT.write_text(text,encoding='utf8',newline='\n')
 print(json.dumps({'authored':PATH,'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest()}));return 0
if __name__=='__main__':raise SystemExit(main())
