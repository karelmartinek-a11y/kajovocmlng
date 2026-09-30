### 51.14 Queue, outbox a inbox claim přes `SKIP LOCKED`

`queue_item`, `transactional_outbox` a `transactional_inbox` jsou class H claimable-work rows s child ordinals `900`, `910` a `920`; nejsou business aggregate roots. Při doménovém commitu se vkládají po required concurrency claims, sequence allocators a všech nižších domain child rows. Při worker claimu je lze zamknout bez parent rootu pouze podle zde uvedeného protokolu, protože nesou materializovaný parent/cancellation/epoch snapshot a před external dispatch následuje fresh parent-root transakce.

`FOR UPDATE SKIP LOCKED` se používá pouze pro queue, outbox, archive outbox, retention batch a jinou explicitně unordered nebo partitioned worker distribuci. Nepoužívá se pro activation eligibility, cleanup completeness, unique active pointer, approval rozhodnutí, secret rotation ani jiné globální business rozhodnutí.

Queue eligibility je materializovaný stav. Candidate row musí mít současně:

```json
{
  "contractKind": "NORMATIVE_CONSTRAINT_DECLARATION",
  "declarationId": "SSOT-DECL-204",
  "sourceSection": "### 51.14 Queue, outbox a inbox claim přes `SKIP LOCKED`",
  "clauses": [
    "state = READY",
    "available_at <= db_now",
    "unmet_dependency_count = 0",
    "barrier_blocked = false",
    "cancellation_requested = false",
    "attempt_count < max_attempts",
    "deadline_at IS NULL OR deadline_at > db_now"
  ],
  "allClausesMandatory": true,
  "recordDefinition": "RegistryPostgres",
  "materializationRequiredBefore": "ARCHITECTURE_READINESS",
  "unknownBindingPolicy": "BLOCKED"
}
```

Dynamic dependency, parent cancellation nebo barrier rozhodnutí se promítne do těchto polí v transakci, která mění dependency/domain stav. Candidate query nesmí spoléhat na phantom-prone korelovaný `NOT EXISTS` bez zamknutého guard row.

Kanonický queue claim dodržuje class F před class H a používá neautoritativní preselection plus jednu krátkou claim transakci na zvoleného kandidáta:

1. mimo claim transakci nebo nezamykajícím prvním statementem načte bounded ordered candidate hints `id`, `state_version`, `concurrency_key_set`, `concurrency_key_set_digest`, materialized incarnation/deployment/parent snapshot; preliminary `clock_timestamp()` pouze omezuje kandidáty,
2. pro jeden candidate zahájí `WORKER_COMMIT` a pomocí `pg_try_advisory_xact_lock` získá všechny potřebné first-create locks pro concurrency keys v class A pořadí; selže-li jediný try-lock, okamžitě rollbackne candidate bez změny stavu, jinak pokračuje zamknutím platform/deployment heads class B,
3. `INSERT ... ON CONFLICT DO NOTHING` zajistí existenci persistentních `concurrency_claim` rows a všechny je zamkne v class F pořadí; výběr používá `FOR UPDATE SKIP LOCKED` a pokud nevrátí přesně celý expected key set, transakce rollbackne a worker zkusí další candidate,
4. teprve potom zamkne exact `queue_item` class H row přes `SELECT ... WHERE id = $candidate_id FOR UPDATE SKIP LOCKED`; nula rows znamená rollback této candidate transakce,
5. po všech locks načte jediný `db_now = clock_timestamp()` a znovu ověří queue eligibility, expected queue `state_version`, key-set digest, materialized parent/cancellation/barrier snapshot, incarnation, deployment epoch a deadline,
6. je-li některý concurrency claim current a neexpired pod jinou logical operation, worker claim nemění; queue row ponechá `READY`, v bounded backoff větvi posune `available_at`, zvýší queue `state_version` a uloží backoff event/audit, potom commitne bez executable claimu,
7. jsou-li všechny claims dostupné, každý claim row zvýší vlastní monotonic fence a přejde na current owner/expiry; queue row současně přejde `READY → CLAIMED`, zvýší attempt, queue fence a state version,
8. claim event, audit a případný worker wake evidence se commitnou společně. Nulový výsledek kteréhokoli final CAS znamená rollback celé executable-claim větve, takže nepersistuje ani jediný partial concurrency nebo queue claim.

Preselection pořadí je:

```sql
SELECT q.id,
       q.state_version,
       q.concurrency_key_set,
       q.concurrency_key_set_digest,
       q.platform_incarnation_id,
       q.application_deployment_epoch
FROM queue_item q
WHERE q.queue_kind = $1
  AND q.state = 'READY'
  AND q.available_at <= clock_timestamp()
  AND q.unmet_dependency_count = 0
  AND q.barrier_blocked = false
  AND q.cancellation_requested = false
  AND q.attempt_count < q.max_attempts
ORDER BY q.priority DESC,
         q.fairness_key ASC NULLS LAST,
         q.available_at,
         q.id
LIMIT $2;
```

Po class F locks se exact queue row zamkne:

```sql
SELECT q.*
FROM queue_item q
WHERE q.id = $1
FOR UPDATE SKIP LOCKED;
```

Final queue transition používá current locked row a nejméně tyto guards:

```sql
UPDATE queue_item q
SET state = 'CLAIMED',
    attempt_count = attempt_count + 1,
    lease_owner_id = $1,
    fencing_token = fencing_token + 1,
    lease_acquired_at = $2,
    last_heartbeat_at = $2,
    lease_expires_at = $2 + $3,
    platform_incarnation_id = $4,
    application_deployment_epoch = $5,
    state_version = state_version + 1
WHERE q.id = $6
  AND q.state = 'READY'
  AND q.available_at <= $2
  AND q.unmet_dependency_count = 0
  AND q.barrier_blocked = false
  AND q.cancellation_requested = false
  AND q.attempt_count < q.max_attempts
  AND (q.deadline_at IS NULL OR q.deadline_at > $2)
  AND q.platform_incarnation_id = $7
  AND q.application_deployment_epoch = $8
  AND q.state_version = $9
  AND q.concurrency_key_set_digest = $10
RETURNING q.*;
```

Je-li concurrency claim platně držen jinou operation, backoff `available_at` je nejméně `db_now + min_backoff` a nejvýše observed claim expiry plus bounded jitter. Worker nesmí v tight loopu znovu volit stále tentýž blokovaný item.

Operation contract obsahuje přesně jedno `concurrencyClaimPoint = ACCEPTANCE | WORKER_CLAIM`. `ACCEPTANCE` získá class F claims v původní doménové transakci a queue/outbox row nese jejich exact fences; delivery worker je pouze validuje. `WORKER_CLAIM` vloží READY work row bez claimu a použije výše uvedený F-before-H protokol. Generic async queue používá `WORKER_CLAIM`; odlišná volba je přípustná jen jako explicitní immutable operation contract. Jedna logical operation nesmí oba režimy smíchat ani alokovat druhý claim fence pro tentýž attempt.

Každý external `side_effect_attempt` má právě jeden canonical dispatch authority row a tím je `transactional_outbox` s purpose `SIDE_EFFECT_DISPATCH`. `queue_item` smí naplánovat interní producer/handler krok, ale nikdy neopravňuje provést tentýž external effect. Auxiliary wake/notification outbox má `is_dispatch_authority = false`. Povinné uniqueness je partial unique `(side_effect_operation_id, side_effect_attempt_sequence) WHERE purpose = 'SIDE_EFFECT_DISPATCH' AND is_dispatch_authority = true`; worker provede external request pouze z tohoto row, immutable attemptu a exact attempt-state/delivery fence.

Outbox claim bez business concurrency keys přeskočí class F a vybere class H `transactional_outbox` rows pomocí `FOR UPDATE SKIP LOCKED`, poté načte `db_now`, znovu ověří eligibility a guarded nastaví delivery lease/fence. Pokud destination contract vyžaduje concurrency key, používá stejný F-before-H protokol. Pro obyčejný event/message outbox je delivery at-least-once a duplicate řeší consumer inbox dedupe. Pro purpose `SIDE_EFFECT_DISPATCH` však claim neopravňuje k blind redelivery po možném dispatchi: po commitu attempt-state `DISPATCHING` vede timeout, crash nebo ztracený ACK do reconciliation; nový external request smí vzniknout pouze novým attemptem po `CONFIRMED_NOT_APPLIED`, nebo jako explicitně povolený retry se stejným target idempotency key podle side-effect contractu.

Outbox lifecycle je podle `purpose` přesný. Ordinary event/message delivery používá `READY|RETRY_WAIT → CLAIMED → DELIVERED|RETRY_WAIT|FAILED_FINAL`; expired `CLAIMED` lze reclaimnout vyšším delivery fence. `SIDE_EFFECT_DISPATCH` používá `READY → CLAIMED → DISPATCH_AUTHORIZED → RECONCILING|CLOSED`. Expired `CLAIMED` před D commitem lze reclaimnout, protože external authority ještě nevznikla. `DISPATCH_AUTHORIZED` se nikdy nevrací do `READY` ani `CLAIMED`; po expiry lze pouze převést reconciliation ownership na vyšší delivery fence při zachování state `DISPATCH_AUTHORIZED` nebo přejít do `RECONCILING`, přičemž nový owner smí jen retrieve/read-back/reconcile exact attempt a nesmí odeslat request. `CLOSED` vznikne až v T3 při canonical known/unknown resolution podle operation state.

Inbox processing získá xact advisory `INBOUND_EVENT`, platform/idempotency/domain heads, všechny target aggregate roots, concurrency claims a sequence allocators v classes A–G; potom zamkne všechny nižší domain child rows a nakonec `transactional_inbox` child ordinal `920`. First-create používá `INSERT ... ON CONFLICT DO NOTHING`, následovaný `SELECT ... FOR UPDATE`; unique `(consumer_scope_digest, external_event_id)` je konečný arbiter. Po locku porovná payload digest a teprve potom provede nebo replayuje domain transition a uloží canonical outcome/event/audit/outbox v jednom commitu. Stejný event ID s jiným digestem je `IDEMPOTENCY_CONFLICT` a handler se nespustí.

