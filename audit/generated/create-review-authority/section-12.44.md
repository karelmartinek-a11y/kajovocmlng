### 12.44 Generation events a SSE

Každý job má monotonic event sequence. Eventy zahrnují:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "urn:kcml:generation-contracts:2#/$defs/SourceEnum044"
}
```

SSE publikuje až persistované events. Reconnect používá `Last-Event-ID`, replay a snapshot. Klientská delta není autoritativní bez server event sequence.

#### 12.44.1 OWNER rozhodnutí 2026-09-25: approval a immutable reads

Veřejná event hranice `generation.spec.approve` je agregátová událost
`generation.spec.approved` v generation streamu jobu. Vzniká ve stejné
autoritativní transakci jako šest zápisů §12.21 a publikuje se až po commitu
prostřednictvím outboxu (§49.5). Používá `SseEnvelope`, monotonic sequence,
`Last-Event-ID`, replay a snapshot podle §26.15. Obecné R9 lifecycle hodnoty
`ACCEPTED/PROGRESS/WAITING_FOR_INPUT/RECONCILING/TERMINAL` nejsou touto událostí
ani neukládají druhý veřejný lifecycle stream. Command outcome a interní stav
operace zůstávají na vlastních hranicích.

Technická specializace masky podle §12.18: `type` je přesně
`generation.spec.approved`; `objectId` je UUID jobu; `eventId` je jeho
commitnutá aggregate-local sequence typu `Counter`; `emittedAt` je uložený
čas události typu `Timestamp`, nikoli čas nového pokusu o delivery.
`payload` má právě dvě povinná nenullová pole: `specificationRevisionId`
typu `Uuid` a `specificationDigest` typu `Digest`. Jde o immutable pointer
a canonical digest zmrazené bodem 3 §12.21, ne o klientský návrh. Job je
identifikován `objectId`, proto se v payloadu neduplikuje. Envelope má právě
pět povinných nenullových polí `SseEnvelope`; jiné payload/envelope klíče
nejsou přípustné. Konkrétní maska je R9 `route.0234/eventSchema`.

Publikující server porovná událost s persistovaným eventem a snapshotem
jejího approval commitu: job, schválená revision/digest, event sequence a stav
`ANALYZING`. Snapshot novějšího stavu jobu nesmí být zaměněn za tento commit
snapshot. Read dané revision vrací dokument stejného jobu a canonical
digestu; samotný `GenerationSpecification` neobsahuje revision ID, proto
musí identita pocházet z trusted immutable repository pointeru (§12.19).
Crash před commitem nesmí publikovat; crash po commitu opakuje delivery
stejného uloženého eventu. Duplicate se neaplikuje podruhé, gap vyžaduje
replay/snapshot; nedostupný replay range vede na `resync.required` (§26.15).
SSE disconnect/cancellation neruší již commitnuté approval ani planning.

`generation.spec.revision.read` a `generation.plan.read` mají veřejně jen
request/response. Samy neemitují persistovaný generation event ani vlastní
replayable SSE událost. Jejich R9 event hranice je výslovně nepoužitelná:
`eventApplicability=NOT_APPLICABLE`, `eventSchema` odmítá každý payload.
Audit čtení podle obecných auditních pravidel je oddělený a není generation
eventem. Klient sleduje změny v samostatném generation streamu pomocí
`generation.spec.proposed`, `generation.spec.approved` a
`generation.plan.created` a následně načte konkrétní immutable revision či
plan. Read vrátí přesně požadovaný dokument, nebo jednoznačnou chybu; chyba
není dokumentem pro navazující krok. Toto rozhodnutí neurčuje dosud
nedoložené payloady `generation.spec.proposed` a `generation.plan.created`.

#### 12.44.2 Přesné předání immutable dokumentu ze streamu do readu

Technická projekce podle §12.18, §12.19, §12.23, §26.15 a §49.5 je vložena
v `contracts/generation/document-events.schema.json`. Event
`generation.spec.proposed` má `SseEnvelope` s `objectId` jobu a payloadem
obsahujícím právě povinné nenullové `specificationRevisionId: Uuid` a
`specificationDigest: Digest`. Jde o serverem persistovanou immutable revision
a její canonical digest, nikoli o modelový návrh prohlášený za receipt.
Blocking questions mohou v proposal existovat; jejich nepřítomnost je guard
approval, nikoli podmínka existence proposal eventu.

`generation.plan.created` má stejnou obálku s payloadem právě
`planId: Uuid`, `planDigest: Digest`, `specificationDigest: Digest`, vše povinné
a nenullové. `planId` a `specificationDigest` jsou totožné s poli uloženého
`GenerationPlan`; druhý digest se rovná také
`scopeLock.approvedSpecificationDigest`. `planDigest` je SHA-256 canonical
UTF-8 JSON celého immutable plánu podle stejných encoding pravidel §56.3.
Event neprohlašuje neplatný DAG za validní ani nepovoluje IMPLEMENTING;
plan conformance guard §12.23 zůstává samostatný.

Specifikace i plán používají serverem vytvořenou identitu, immutable parent
ownership a ochranu obsahu podle §51.10. Uložení dokumentu, aggregate sequence,
eventu a outboxu tvoří jeden commit (§49.5, §51.5 a §51.13). Před commitem se
nepublikuje nic; po commitu se doručuje přesně uložená obálka. Publisher
ověří job, document ID, actual canonical digest, sequence a u plánu i approved
specification digest proti trusted snapshotu tohoto commitu, ne proti pozdější
mutable projekci jobu. Jméno obálky je přesně příslušný event type; jiné
payload/envelope klíče jsou zakázány.

Consumer převede `objectId` na path `id`; u spec eventů převede
`specificationRevisionId` na path `revisionId`, u plánu `planId` na path
`planId`. Digest drží jako expected immutable identity a porovná jej se
skutečnými canonical bytes read outputu a trusted repository pointerem.
Přečtení current/latest pointeru místo konkrétní ID není tento převod.
Neexistující dokument nebo rozdílná identita/digest nesmějí dodat downstream
dokument. Read lze znovu provést pro stejnou immutable identitu; nesmí tiše
nahradit revision jinou. Stream sequence/dedup/replay a snapshot se řídí
§12.44.1 a §26.15; timeout/disconnect readu nevytváří generation event ani
neruší již commitnutou publikaci. Audit čtení zůstává oddělený.

Interní serverová projekce `PlanAllocation` ve stejném vloženém kontraktu
obsahuje právě povinné nenullové `jobId: Uuid`, `planId: Uuid` a
`scopeLock: ScopeLock`. Jde o projekci persistované alokace/frozen scope podle
§12.22 a §56.10, nikoli o veřejný command ani modelovou authority. Přijatý
`GenerationPlan` musí mít všechny tři hodnoty shodné s touto serverovou
projekcí; porovnává se celý scope lock, ne pouze approved digest.
`specificationDigest` musí navíc odpovídat approved digestu scope locku.
`generation.plan.create` je producent immutable plánu a jeho eventu,
`generation.spec.propose` producent revision a proposed eventu. Oba emitují
až z potvrzeného serverového commitu. Model může pouze citovat předem
alokované identity. Validace této předávky nenahrazuje DAG, hydrataci
artefaktů ani zbývající command/result/error kontrakt těchto operací.

#### 12.44.3 HTTP specializace approval a immutable readů

`contracts/generation/http-design.schema.json` materializuje podle §12.18
technický HTTP kontrakt `generation.spec.approve`,
`generation.spec.revision.read` a `generation.plan.read`. Přesné wire masks
jsou jeho `$defs/ApprovalWireRequest`, `SpecificationReadWireRequest` a
`PlanReadWireRequest`; nejsou interním `StepInput`. `transportBindings`
adresují normalizované R9 request/response masks a přesné HTTP status/body
varianty. Root tohoto schema bundle není payload a odmítá instanci; používá
se konkrétní definice.

Oba reads vybírají immutable dokument pouze exact UUID path parametry §26.7.
Nemají business body ani query; absent body se normalizuje na JSON null a
prázdný query na prázdný seznam R9. Nepřijímají caller CAS/idempotency guards.
R9 guard fields se pro read odvodí jako null, kromě serverem vypočteného
`clientRequestDigest`; klient je nezasílá. Úspěšný read není durable mutation
ani nová generation událost. Request trace `commandId` a `logicalOperationId`
v success meta §26.1 nevytvářejí `domain_command` ani mutující idempotency row.

Approval wire body obsahuje šest polí §12.21 a volitelný
`expectedStateVersion: Counter`. CAS se předá tímto polem nebo `If-Match`
se silným quoted decimal Counter; při současném předání se obě hodnoty musí
shodovat. Povinný `Idempotency-Key` je header. Gateway vyjme body CAS do R9
`guards.expectedStateVersion`; zbývajících šest business polí zachová beze
změny. `clientRequestDigest` vytváří server z canonical objektu obsahujícího
operation ID, exact path parameters, šest business polí a expected version,
nikoli z credentialu, attempt ID nebo nového server contextu (§49.4).
Caller nesmí poslat authority, lineage, commit receipt ani další server pole.

Autentizace zůstává jediná OWNER session nebo jediný OWNER bearer key
(§7.2, §21.2, §26.1). Technické názvy cookie `__Host-kcml-owner` a CSRF headeru
`X-CSRF-Token` konkretizují §21.2; mutation přes cookie vyžaduje platný CSRF,
key path vyžaduje platný aktuální bearer credential. Cookie má Secure,
HttpOnly, Path=/, bez Domain; další bezpečnostní a expiry pravidla §21 a §30
zůstávají v platnosti. Přítomnost headeru není autentizace. Kontrakt přijímá
právě jeden auth mechanismus. Relevantní application headers se převádějí na
lowercase singleton mapu; duplicitní relevantní header a duplicitní JSON key
jsou chyby před handlerem. HTTP framing headers nepatří do business masky.

Veřejná response obsahuje success `meta` přesně podle
`ApiConcurrencyEnvelope` (§26.1/§49.27). `logicalOperationId`, `correlationId`
a `resultDigest` v R9 a meta se musí shodovat. Digest výsledku je SHA-256
canonical `{status, output, error}`; mutable response čas/correlation a replay
flag nejsou součástí frozen business výsledku. Digest immutable dokumentu je
samostatný SHA-256 jeho canonical bytes. Read čte dokument, job metadata a
activation epoch v jednom `CONSISTENT_READ` snapshotu (§51.2); tento snapshot
není oprávněním k pozdější mutaci. Read `meta.eventSequence` samo neopravňuje
přeskočit jiné stream události.

Approval je pro tuto trasu synchronní lokální command: HTTP 200/SUCCEEDED
potvrzuje pouze commit §12.21, nikoli dokončení planningu nebo jobu. Výstup
`ApprovalReceipt` má právě povinné nenullové `jobId`,
`specificationRevisionId`, `specificationDigest`, `executionAuthorityId`,
`planningPhaseRunId` a `jobState=ANALYZING`. UUID pocházejí z téhož approval
commitu; žádnou z těchto serverových identit nevytváří model ani volající.
Planning phase patří generation jobu, ne novému caller-created runtime.
Při replay se vrací frozen receipt a frozen operation metadata; čerstvá
autentizace, response correlation/time a `idempotencyReplay` se odlišují od
frozen outcome (§49.27). Nové CAS/deadline/current-revision admission nesmí
zamítnout již commitnutý terminal replay.

Chybové varianty adresují přesné `errorBindings` stejného resource. §32
zůstává zdrojem classification/retry významů; nové REST code names jsou
technická pojmenování konkrétních již požadovaných podmínek, ne nové business
akce. Chybějící auth je 401, chybná wire maska včetně chybějícího key/CAS je
400, neexistující exact target 404; stale version/digest/idempotency conflict
zachovávají 409 podle §49.27. Not-approvable precheck je 422. Konflikty
state/spec/capability nesou exact current snapshot, ne pouze jeho digest.
Stabilní code, classification, retry directive a next action mají pevnou
vazbu v errorBindings; lokalizovaný message ji nemění. Detail má přesnou
masku field paths/reason a ověřený canonical digest. Doporučená next action
není nová capability ani oprávnění přeskočit precheck.

Read timeout má 504/RETRY_SAME_OPERATION pro stejný selector, read cancellation
409/DO_NOT_RETRY. Poškozený nebo digestově odlišný immutable dokument má
500/DO_NOT_RETRY a nesmí být vrácen jako success. Potvrzený rollback nebo
read-only storage failure lze opakovat bounded profilem §32.9; capacity error
neznamená ACCEPTED (§32.7). Neověřený výsledek approval commitu je zvláštní
503 `API_COMMIT_UNCONFIRMED`, public status `UNCONFIRMED`, `terminal=false`,
directive `RECONCILE_THEN_RETRY`: smí se pouze vyhledat původní locator a
zjistit committed/rolled-back outcome. Není to automaticky neznámý external
side effect. Timeout či ztracená HTTP odpověď neruší command, nevytváří nový
key a není důkazem rollbacku. Po confirmed commit se vrátí původní receipt;
nové provedení je možné pouze po důkazu rollbacku a opětovném ověření guards.
§49.4 tombstone se nikdy nerecykluje; nedostupný retained result používá
`IDEMPOTENCY_CONFLICT` s reason `RESULT_RETAINED_AS_TOMBSTONE`.

Samotná tato specializace neprohlašuje celý generation proces za uzavřený:
pokrytí fyzických guards, error/recovery dispatchu a procesních hranic musí
prokázat návrhové gates §55.21.1. Jejich produkční provedení je samostatná brána.

`CurrentSnapshot` vždy pochází z autorizovaného repository čtení: revision a
digest, capability ID a digest i turn ID a status jsou páry, které jsou buď oba
ne-null, nebo oba null. Conflict snapshot není frozen receipt. U
`IDEMPOTENCY_CONFLICT` je null přípustné jen pro nedostupný retained outcome s
`details.reason = RESULT_RETAINED_AS_TOMBSTONE`; locator se ani tehdy nerecykluje.
Povolení `RETRY_SAME_OPERATION` se ověřuje proti serverovému pozorování
`READ_ONLY`, `CONFIRMED_ROLLBACK` nebo `NO_DISPATCH`, nikoli proti HTTP statusu
nebo textu chyby. `PLATFORM_RECOVERY_IN_PROGRESS` dovoluje tuto větev jen před
dispatch a s `NO_DISPATCH`. `UNKNOWN_COMMIT` vyžaduje
`API_COMMIT_UNCONFIRMED` a lookup původního locatoru. Čtení nemůže vykázat
mutující effect. Úspěšný read má `idempotencyReplay=false`, jeho celé `meta`
pochází z téhož CONSISTENT_READ snapshotu jako immutable dokument; přesnou
identitu a digest dokumentu dále ověřuje §12.44.2. Tyto kontroly doplňují,
nikoli nahrazují úplné mapování interních coordinator/phase/checkpoint chyb.

#### 12.44.4 Approval a předchozí discussion phase

Technické složení §12.3–12.5, §12.21, §49.15, §51.16 a §51.31:
completed discussion **turn** není terminal evidence discussion **phase**.
Approval commit současně uzavře aktuální DISCUSSING phase run do `SUCCEEDED`,
uloží jeho úplný výstupní checkpoint a terminal evidence, přesune job/current
phase pointer a vytvoří jediný ANALYZING planning phase run s queue/outbox.
Nesmí commitnout dva aktivní phase runs; `QUEUED` nástupce je již aktivní pro
partial unique index. Povolené cesty předchůdce jsou `RUNNING → SUCCEEDED`,
`REPAIRING → SUCCEEDED` nebo `WAITING_FOR_OWNER → RUNNING → SUCCEEDED`;
poslední cesta nesmí zavést nepovolenou přímou hranu WAITING_FOR_OWNER→SUCCEEDED.
Guards obou přechodů a jejich evidence jsou součástí téže transakce.

Coordinator server ověřuje current incarnation/recovery epoch, vlastní platný
lease/fence, phase state/version/fence, cancellation version a complete output
checkpoint. Tyto hodnoty klient nemůže dodat místo serverové authority.
Preapproval nepřítomnost approved authority/planu nesmí vést k požadavku na
již existující budoucí planning artefakty: authority a approved pointer vznikají
právě tímto commitem, plan až následnou planning operací. Ostatní applicable
guards §12.5 zůstávají povinné; tato specializace není blanket výjimkou.
Chybějící phase evidence nebo stale fence blokují commit celé šestice §12.21,
nikoli pouze založení nástupce. Replay již commitnutého výsledku při nové
autentizaci neprovádí čerstvou admission ani druhé uzavření phase (§49.4).

