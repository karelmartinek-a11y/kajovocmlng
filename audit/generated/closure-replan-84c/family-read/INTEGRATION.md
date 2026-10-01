# Six-route history read family — exact proposed boundaries, finite gaps

Pinned input `84c41ba`, SSOT `2577dacf6024e4666ba98b11eb9c7ffa6e7f225e60630697db740129615cc536`. Owned outputs only; no canonical/Git/runtime changes.

Family: audit.event.list on component/generation/global paths, audit.event.read exact UUID, generation.job.events.read, agent.run.events.read: **4 operations /6 routes /18 route boundaries**. New schema+authorable delta provides exact request and success-output masks using the normative shared query/result/item definitions and49 per-field exact source pointers (includes the second active strict history query). Existing admission/guards/status/error transport envelopes are preserved. Proposed technical error predicates separate bad request from invalid server/native producer bytes. Event schemas/application are unchanged because READ_ONLY is not authority to prohibit operation audit/events.

`history_read_reference.py` /66 tests cover all6 route transport positives, unknown/duplicate parameters, forbidden GET JSON body, UUID/path shape, arrays/types/ranges/UTC/IANA interval, same-domain component/run binding, actual native summary JSON bytes and exact duplicate-key/encoding/syntax rejection, event identity collision, recordedAt/eventId binary ordering, bounds and explicit COMPLETE/PARTIAL/UNAVAILABLE, exact interval and summary-only UI projection. Every negative derives from a valid positive; no unrelated exception counts. Reading payloadReference is never claimed to hydrate payload bytes. The COMPLETE fixture demonstrates result invariants only, not an authentic continuous archive publisher.

## Profile compatibility and activation hold

The source exposes two distinct active schemas: experience-history-query:1 (fromInclusive/timezone, max500), history-query:1 (from/recordKinds/sort, max200). The exact operation allow-list and Dashboard/chat text do not resolve which URI/consumer uses which profile or declare a trusted profile selector. Neither strict schema is weakened or replaced.

`profile-binding-proposal.json` authors explicit technical queryProfile variants, each own exact input mask, no format guessing or permission change.11 parser checks preserve both500 and200 bounds, old required sort/recordKinds, reject missing/unknown/duplicate discriminator and cross-profile fields. This is **NOT_ACTIVATED**; old-profile execution/result-sort/classification binding remains a named gap. No new owner business decision is assumed or requested. The six-route experience delta is marked activationReady=false: coordinator must resolve normative URI/consumer/profile binding before applying a universal route capability. The narrow global audit read/list can consume a declared profile once this technical handoff is authored/reviewed.

## Measured structural comparison

`verify_family_inventory.py` applies the proposal only to in-memory SSOT and runs the real resolver/inventory. Canonical bytes remain unchanged.

| Same family metric | Pinned | Virtual proposal |
|---|---:|---:|
| Generic request boundaries |6|0|
| Generic response boundaries |6|0|
| Generic event boundaries |6|6|
| Generic routes |6|6|
| Unresolved route refs |0|0|
| Unresolved selected operation refs |0|0|
| Whole operations semantically closed |0|0|

The12 fewer generic masks are a structural property, not12 completed semantic requirements or an improvement in the unrelated242-reference count. All6 routes still have a generic event boundary. No global project readiness change is claimed.

## Exact remaining authorities and verification methods

- HISTORY.ROUTE_CONSUMER_PROFILE_BINDING: current observability operations/schemaBinding lists4 operations but does not pin the6 route variants to declared source profiles/consumer producer. Author explicit routing and test both consumers; do not assume500 applies everywhere.
- HISTORY.AUTHENTICATED_SCOPE_PRODUCER: actual current OWNER/caller/channel context and scoped persisted root read. A valid request schema or source label creates no server authority. Test actual context under required lock/snapshot.
- HISTORY.SNAPSHOT_CURSOR_PRODUCER: persist opaque cursor filters/order/authorization/watermark, exact retention/expiry and replay; changed filter/expired cursor returns normative HISTORY_CURSOR_INVALID and explicit restart. No in-memory token/hash substitute supplied.
- HISTORY.CONTINUOUS_COVERAGE_PRODUCER: authenticated source manifests/bytes demonstrate continuous resolved interval/snapshot coverage; source gaps cannot become COMPLETE merely from a supplied flag.
- HISTORY.GENERATION_JOB_MEMBERSHIP_PRODUCER: Item only has runId; generation job path must join actual immutable run/job membership, not job==run. The reference raises a precise missing producer diagnostic for the two job routes.
- HISTORY.CHANNEL_CLASSIFICATION_PRODUCER: Item lacks channel; never infer channel from free source/eventType. Actual canonical record origin/classification must supply it. Non-ALL filter is held pending that producer.
- HISTORY.LEGACY_RESULT_SORT_CLASSIFICATION_PRODUCER: source history-query:1 recordKinds/result/sort/clientRef requires its exact result/record origin projection and null/tie semantics. Parsing strict200 does not close these duties.
- HISTORY.ACCESS_AUDIT_APPEND: actual existing history-access producer retains actor execution context, UI/chat origin, normalized filters, watermark, returned IDs/completeness under existing retention/OWNER/Secrets rules. No invented new audit authority.
- HISTORY.PAYLOAD_PROVENANCE_HYDRATION: persisted reference→actual archived bytes/schema/digests→typed content consumer; nonempty strings or valid JSON do not prove it. Summary-only consumer explicitly does not request a payload.
- HISTORY.OPERATION_EVENT_APPLICABILITY: preserve required existing OPERATION_ADMITTED/STATE_CHANGED/TERMINAL audit types and establish exact emitted-operation event mask or sourced prohibition. Do not infer NOT_APPLICABLE from no external effect.

`error-predicate-review.json` reviews10 family predicates with exact source/proposal status; global258 predicates and159 provenance detector hits are not reviewed by count. Shared producers are mandatory pre-generation A; parser/format/summary fixtures are B; generated endpoint/UI/runtime acceptance C remains NOT_EVALUATED. Entire family is PARTIAL; SSOT readiness remains BLOCKED. No renders/browser fixtures or lifecycle family work duplicated.
