### 49.5 Události, pořadí, audit a transactional outbox

Každý aggregate root obsahuje vlastní poslední `eventSequence`. Následující sequence se alokuje změnou root řádku v téže transakci jako stav. Tím vzniká bezmezerové pořadí commitnutých doménových eventů v rámci agregátu. PostgreSQL sequence objekt se pro tento bezmezerový aggregate-local čítač nepoužívá.

Globální auditní hash chain alokuje `chainSequence` pod row lockem singletonu `audit_head`. Doménová transakce, která vyžaduje audit, současně uloží audit event, nový hash a nový audit head. Pokud audit write selže, doménová změna se necommitne.

Cross-aggregate globální business pořadí se nepředstírá. Vztah mezi různými agregáty vyjadřují `correlationId`, `causationId`, logical operation ID, activation epoch a transactional commit evidence. Časové razítko není concurrency guard.

Každý event určený pro SSE, queue, webhook delivery, cache invalidaci, runtime reconcile nebo jiného consumera má ve stejné transakci `transactional_outbox` řádek. Publisher používá at-least-once delivery. Consumer deduplikuje podle immutable event ID a pro jeden stream přijímá pouze následující expected sequence; duplicate ignoruje, gap vyvolá snapshot/replay nebo `SEQUENCE_GAP`, nikoli tiché přeskočení.

`LISTEN/NOTIFY`, condition variable, in-memory signal a socket wakeup jsou pouze optimalizace. Worker vždy polluje persistentní queue/outbox podle `availableAt`, takže ztracená notification nezpůsobí lost wakeup.

Event se publikuje až po commitu. Crash po commitu a před publikací zanechá outbox row k pozdějšímu doručení. Crash po publikaci a před označením delivery může způsobit duplicate delivery, nikoli ztrátu eventu.

PULSE, webhook, provider callback a jiný at-least-once inbound event používá `transactional_inbox`. Consumer v jedné transakci vloží unique `(consumerScope,eventId)`, ověří payload/schema/sequence digest, provede doménovou změnu a uloží outcome/event/audit/outbox. Duplicate stejného eventu vrátí původní outcome; stejné event ID s jiným digestem je protocol conflict.

PULSE stream s ordered delivery udržuje source stream ID a expected sequence. Event vyšší než expected se nedispatchne mimo pořadí; uloží se jako pending gap, vyžádá replay/snapshot nebo přejde do dead letter podle port contractu. Unordered port stále deduplikuje event ID a nesmí stejný event aplikovat dvakrát.

