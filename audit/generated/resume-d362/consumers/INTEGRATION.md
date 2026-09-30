# Generation consumer and UI bridge review

Pinned input: d362487999bd795d4723c2a930e93fc7aa8aa295, SSOT SHA-256 22256baa17729b7577ca4e2498b74b7dfc2b3e6bab57f3b88c338a059557a0ee.

## Concrete bounded repair

`consumer-projections.proposed.json#/createReadProjection` is a closed, exact **create-consumer projection**, not a replacement for the complete generation entity. It includes server job identity, current own lifecycle state/counters, immutable creation timestamp/kind/request digest/frozen FOLLOW_UP basis and the persisted initial request reference. The reference has a server-owned snapshot UUID, exact actual-byte content SHA-256 and JSON media type. The initial request semantic digest is independently recomputed from strictly decoded and domain-mask-valid JSON. Byte content digest and semantic canonical digest have distinct purposes; neither substitutes for the other.

`generation_consumer_reference.py#consume` checks a valid exact create receipt first, then validates the own job read projection and producer operation/selected identity. A model payload cannot supply the producer provenance. The integrating API must derive producer provenance from authenticated transport/repository handling; this reference tuple is **not a proof of TLS or a runtime session**. Actual immutable request bytes are supplied only at an internal trusted repository hydration boundary, never echoed into the public UI return or evidence. The raw source is strictly decoded and validated against the active generation request body. A caller-provided `valid` flag is never accepted.

The projection binds immutable creation fields while permitting current own job state/version to advance. It rejects current version/event sequence regressions and terminal-state rewrites. The return authorizes no execution or activation merely because create admission succeeded. Failure/UNKNOWN reconciliation retains the original logical operation and idempotency key rather than issuing another create.

26 reference checks PASS in `consumer-reference-tests.json`. Each semantic mutation starts from the valid same domain witness. Duplicate/malformed JSON tests update the byte digest before rejection, so they specifically exercise the actual decoder rather than failing on an unrelated digest mismatch. No application, backend or live account was invoked.

## Exact field/source mapping

| Projection field | Authority | Meaning and origin |
|---|---|---|
| jobId | §25.11 generation_job.id; create output mask | Server-created root UUID; read must select this exact root |
| kind | §12.41, §25.11; create output | Immutable approved kind dictionary, never inferred from state |
| state | own generation lifecycle dictionary already referenced by `follow_up_contracts.STATES` | Current server snapshot; DISCUSSING in frozen create receipt may legitimately advance |
| stateVersion | §49.3, §25.11 | Server bigint represented as exact decimal string, cannot regress |
| eventSequence | §49.5, §25.11 | Aggregate-local current contiguous sequence; cannot regress |
| createdAt | §25.11; create output | Immutable server timestamp |
| initialRequestDigest | §25.11; §12.48 create receipt | Canonical semantic digest of the retained typed request, independently checked |
| frozenBasis | §12.49, approved FOLLOW_UP rule | Frozen server lineage descriptor; never substituted by latest source |
| initialRequestRef.snapshotId/contentDigest/mediaType | §25.11 immutable initial request; §49.4 frozen descriptors | Exact persisted bytes address/digest; internal bytes verified independently |

All fields are required, non-null except frozenBasis exactly null outside FOLLOW_UP. The reference schema explicitly rejects extras. Counters inherit the active bounded bigint representation; no speculative field-size business cap was added.

### Still required to close the whole read/consumer operation (A)

1. Complete job/snapshot projection for every §25.11 field: target and parent pointers, phase, current/approved specification, execution authority, capability/plan, checkpoint/phase-run, releases/activation, cancel/error, coordinator leases/fences/incarnation/epochs/timestamps and command locator. The proposed narrow projection must **not discard these mandatory relationships** or silently redefine existing job.read as this subset.
2. SQL repository query must prove same-snapshot identity and owner authorization with the actual physical root/source tables. The reference does not supply the missing DB helper or accepted trusted context.
3. UI current selected-job read transport must consume the exact projection and apply own state→visible action rules. A create receipt is not the whole read output.
4. Initial request encrypted storage/decryption/retention must use existing Secrets mechanism for embedded credentials. Internal hydration may validate sensitive bytes, but public read/UI must not reveal credentials automatically.
5. Current read response/errors/transport masks remain generic in payload records217/218 and must be authored together with this complete schema.

B: reference negative tests can prove the above exact identities, bytes/schema/digest/retry relationships once the complete contracts exist. C: real authenticated API, actual browser rendering of server snapshots, PostgreSQL consistency, actual crypto/repository execution and dispatch are implementation acceptance or required isolated fixture evidence according to their own gates. They are not proved by this module.

## Three UI exposure blockers: technical bridge, not permission relabel

Current source still binds dashboard.start → runtime.instance.start (AUTOMATED_MAINTENANCE), dashboard.stop → runtime.stop (same), gen.editSpec → generation.spec.propose (INTERNAL_PROTOCOL). Authenticated OWNER cannot directly impersonate these writer contexts. §49.3 requires a canonical domain_command for UI mutations, §49.4 stable locator/CAS, §49.5 server-owned context and publication. §43.3 requires OWNER input after proposal to produce a new immutable revision without changing old approval/execution.

The proposed START/STOP **selected-existing-runtime** intent masks contain only explicit action/schema discriminator, component UUID, expected component state version, runtime UUID/generation and activation epoch. Unknown client context/authority fields are rejected. They preserve separate server runtime operation dispatch. These are useful closed selector proposals, **not complete facade contracts**: first launch/runtime allocation semantics and exact current launch snapshot resolution must be materialized from §§50.10–50.11. The masks cannot be used as authority for launch or current activation.

Do not add these proposal IDs to the catalog until domain_command/response/errors/event/freshness/resolver rules are integrated. Full launch snapshot requires source revision, exact release/artifact/runtime/dependency/profile/schema digests, binding-set revision, deployment/incarnation, unit/class, cleanup inventory and handler entrypoint; omitting these server dependencies cannot be justified by the selector being precise.

For gen.editSpec, safe request entry is an explicit OWNER-input facade, not direct INTERNAL_PROTOCOL proposal. Text input must retain exact OWNER bytes; form input needs a closed semantic patch mapped to authoritative GenerationSpecification fields. The four reference form fields goal/role/input/output are examples and are **not enough authority to invent the complete patch semantics**. `generation.message.append` is a possible existing entry point but remains generic; rebinding alone would not close submission→new DRAFT revision→diff/coverage→read/UI.

No additional product decision was identified. These are mandatory technical materialization/source-consistency gaps. No exposure is declared closed merely by supplying a facade sketch. Current context-menu enable/disable and dashboard start/stop have different effects and must not be silently aliased.

## Visual scope

The current renderer compatibility was already repaired and fresh 96/128 matrices exist. No source or rendering concern in this bounded review justified rerendering, so none was run. Existing 4/96 manual screenshot inspection is limited layout review; the remaining manual/font/glyph and complete UI semantic conditions remain distinct from automated no-overflow/interaction PASS. No screenshot proves the missing typed producer/read/dispatch boundary.

## Complete root composition received from persistence review

`generation-full-root-read.proposed.json` maps all 39 candidate physical root columns to required wire fields and preserves every nullable pointer. UUIDs remain canonical identities, bigint values use exact decimal strings, 32-byte digests become `sha256:` lowercase hex, timestamps use RFC3339. It is reproducible with `build_full_read_shape.py` and bound to the exact candidate SQL bytes. This full row shape is a **review artifact**, not an active complete read mask: own currentPhase/access-channel/error dictionaries, public visibility of internal context/leases, same-job/FK relationships and child hydration still need exact authority. Schema-only strings cannot hide those unresolved semantics.

## Second-wave review correction

The original retry helper accepted disconnected status/classification strings. That defect was confirmed and corrected: it now validates the **entire effective generation.job.create canonical response mask**, exact stable-code/classification/retry relations, output/terminal conditions and recomputed resultDigest before deriving an action. Unknown statuses/classes and contradictory pairs are rejected with UI_CREATE_OUTCOME_SCHEMA_INVALID; a correct-schema corrupted receipt digest produces UI_CREATE_OUTCOME_DIGEST_MISMATCH. The updated consumer suite has **35 checks PASS**, superseding the initial 26-count suite.

`UI_FACADE_JOIN_CONTRACT.md`, `ui-facade-native-inputs.proposed.json`, `ui-facade-native-patch.proposed.json` and the separate pipeline reference provide the next concrete bridge. Its **32 checks PASS** cover typed actual launch/spec bytes, same-domain CAS, reference atomicity/replay/rollback, digest-valid wrong-identity and duplicate-JSON decoder violations, event/outbox/audit readback and exact OWNER text preservation. These are bounded design results, not closure of the three exposure blockers or production auth/worker evidence. The six mandatory integration groups are enumerated explicitly in the join contract.
