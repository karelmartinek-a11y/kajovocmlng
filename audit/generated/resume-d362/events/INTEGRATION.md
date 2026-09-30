# generation.job.create atomic publication and replay slice

Pinned input: `d362487999bd795d4723c2a930e93fc7aa8aa295`, canonical SSOT SHA-256 `22256baa17729b7577ca4e2498b74b7dfc2b3e6bab57f3b88c338a059557a0ee`.

This is a technical authoring proposal, not an active canonical resource. Parent owns integration. Native response/event masks remain authoritative; no new event type or product scope is invented. Independent reviewer uses separate files and fresh rollback-only PostgreSQL mutants.

## Concrete materialization

`generation-event-storage-proposed.sql` defines the previously missing domain command/idempotency physical rows; event byte/digest and sequence columns; ordinary event delivery outbox; singleton audit head, immutable canonical audit events and conditional archive outbox. It preserves the existing locator declaration (read from `database/explicit-entities.sql`) instead of creating a competing locator. `generation-command-links-proposed.sql` adds real FK/deferred links to the independently authored trusted context and protected initial snapshot. Its combined execution is recorded separately; unrelated authentication root tables remain explicitly fixture prerequisites.

The command is **not** given the idempotency lifecycle: its `state` is the existing create response status (`ACCEPTED|SUCCEEDED|FAILED|CANCELLED`) and `terminal` is separate. `domain_idempotency_record` retains its own authoritative §25.11/49.4 eight-state lifecycle. No source-job terminal guard is introduced here.

The exact command column meanings come from §25.11 `domain_command` and §49.3: stable command/logical identities; pinned contract revision; trusted channel/context and target; immutable protected canonical-argument snapshot reference; caller request digest distinct from frozen descriptor digest; scope/key digests; nullable CREATE CAS fields (no invented client authority); optional deadline; correlation/causation; created/accepted/terminal timestamps and canonical result/error digests. Native create terminality and the idempotency lifecycle must not be conflated.

Deferred creation closure binds completion → exact event ID/operation/root → exact payload bytes/digest → domain outbox row → audit bytes with exact actor/object/operation/event/digest/chain identity → actual current audit head. Required locator and domain-idempotency rows must agree with canonical request/key/scope/result. Every missing required join rolls back the initial transaction. A valid hash on audit bytes about the wrong object is rejected.

Postcommit protection is separate from initial closure: events/audits are immutable; terminal command and idempotency rows are immutable; locator identity/digests are frozen; outbox event/consumer/purpose/operation/root/payload are frozen. Ordinary delivery uses its own §51.14 states and guarded live lease/fence transitions, while mutable delivery version/lease/state can advance. Deletion of the delivery obligation requires an explicit retention authority; none is silently fabricated.

## Audit encoding technical addition

§51.25 requires a versioned immutable `kcml_audit_hash` with vectors but does not define an exact binary preimage in the inspected input. Proposed format 1 is SHA-256 over ASCII `KCML-AUDIT-CHAIN`, unsigned 32-bit big-endian version 1, 32-byte previous hash, positive signed 64-bit big-endian sequence, signed 64-bit big-endian canonical-byte length, and exact canonical bytes. No text encoding or JSON reserialization occurs inside the hash function. PostgreSQL and independently encoded Python vectors agree for ASCII, UTF-8 and maximum bigint sequence. This technical definition needs normative materialization; vectors alone do not activate it.

## Actual evidence

`event-storage-proof.json`: PostgreSQL **18.6**, isolated Unix-socket-only database `generation_events_fixture`, no production/account/API calls. Forty checks passed. `combined-generation-proof.json` adds fourteen executed PostgreSQL checks over the full proposed generation root, exact command/context/snapshot links and publication tables, including two concurrent fresh same-key claim transactions resolving to one observable outcome. Includes executed DDL and PL/pgSQL, exact native positive response/event masks, independent hash vectors, four missing-join rollback mutants, hash-valid wrong audit identity, wrong audit-head hash, frozen command/idempotency/locator violations, postcommit delivery retarget/digest/delete/state violations, valid fenced claim/delivery, two-process locator row-lock replay, conflicting request comparison, and reconciliation of a lost transport response against the original committed receipt. No SQLite substitutes.

The fixture's `generation_job` and completion table are explicitly **minimal FK dependency fixtures**, not the complete physical roots. This script therefore proves the publication slice, not whole operation closure or production implementation acceptance. It does not prove database role grants/authentication, encrypted initial request cryptography, external archive availability, the full queue/side-effect outbox schema, general multi-key/revision idempotency races, canonical authentication table closure, or the actual cryptographic profile. The separate combined proof covers the particular fresh same-key race and context/snapshot links.

Reproduce only against a disposable fixture database after creating it:

```sh
KCML_EVENT_PSQL_COMMAND='["/tmp/kcml-pg18/bin/psql","-h","/tmp/kcml-pg18-socket","-p55432","-d","generation_events_fixture"]' /tmp/ssot-audit-venv/bin/python audit/generated/resume-d362/events/verify_event_storage.py
```

The script expects a newly empty database; it intentionally does not erase tables or arbitrary databases. The parent's disposable fixture lifecycle must recreate its own named database between runs.

## Transaction and recovery obligations

1. Authenticate and freeze real server context; acquire class A/B heads, then stable locator and revision-pinned idempotency class C. Lookup precedes fresh target admission on replay (§49.4/51.12).
2. New claim uses `INSERT ... ON CONFLICT DO NOTHING`, then exact `SELECT ... FOR UPDATE`; compare caller digest. Existing terminal record returns the original frozen scope/result without target/activation locks. Different digest rejects before root mutation. The combined proof exercises one fresh same-key race using this algorithm; opposite-order/multi-key/revision races remain distinct mandatory fixture cases.
3. Verify admission under correct actual target/namespace/root locks; no provider/browser/network I/O inside transaction (§51.5–8).
4. Create job/snapshot/context/command and canonical receipt; root event sequence is allocated on the locked root, not a PostgreSQL sequence/MAX (§49.5/51.13).
5. Insert event and required outbox before audit-head lock. Domain and payload digests must already be final. Lock audit head last, append canonical event, update head, append archive-outbox only if actual pinned policy requires it. Do not mutate previously existing A–H rows afterward (§51.25).
6. One COMMIT linearizes root/result/event/outbox/audit. Delivery occurs afterward and is at-least-once. Consumer deduplicates immutable event ID and checks sequence/digest; delivery lease is not business outcome authority (§49.5/51.14).
7. Known rollback is retryable under the same business key. Unknown connection/commit outcome queries the same locator; it must not be labeled failure or rolled back and must not create another root (§49.25/12.48). The fixture exercises lost transport after a known commit; broader injected unknown timing remains mandatory.

## Remaining before whole operation readiness

- **A — normative/design before generation:** activate reviewed exact resources and hash-format definition; complete owner/platform/context FKs and trusted writer grants; resolve exact new-scope claim/queue integration; active audit-retention policy binding and authorized retention/tombstone materialization; side-effect/other-purpose outbox extensions remain outside this bounded slice.
- **B — required isolated fixture:** execute combined physical roots+protected snapshots+trusted context+publication SQL; retain the executed fresh same-key creation proof; test opposite-order lock contention/deadlock/backoff and failure injection at every durable stage. Confirm canonical encrypted bytes using selected real crypto profile rather than synthetic AEAD.
- **C — later generated implementation acceptance:** real authenticated HTTP/UI consumers, workers/publisher/inbox delivery, archive integration, restart recovery, and production startup verification.

No requirement is moved from A/B into C merely to obtain a PASS. Whole operation and SSOT readiness remain BLOCKED until the actual mandatory universe is closed.

## Source conflict requiring resolution

The initial combined context fixture exposed TEXT singleton keys (`OWNER`, `CURRENT`, `OWNER_API`) where §51.11 requires physical SMALLINT key 1. The persistence agent corrected its constructor and fixture foundation using the physical precedence; symbolic names remain logical identities. The final combined proof was re-executed against the corrected SMALLINT foundation and passed. No owner product decision was needed. Full authentication DDL/service verification remains separate from this corrected key binding.
