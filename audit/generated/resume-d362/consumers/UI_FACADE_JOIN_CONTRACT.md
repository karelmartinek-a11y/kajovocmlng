# Staged OWNER UI intent bridge: exact joins and remaining gates

This supplements the narrow first-wave selector proposals. Input is pinned to d362487; masks use unchanged effective UI/spec resources. Parent must bind integrated evidence to final actual resource hashes.

## Native proposals supplied

`ui-facade-native-inputs.proposed.json` contains explicit closed inputs for dashboard.start, dashboard.stop and gen.editSpec. No schemaId/value bag or arbitrary patch path is used. Runtime actions have their own START/STOP discriminator and existing-runtime selector. Specification input has OWNER_TEXT (exact submitted text) or SPECIFICATION_CANDIDATE (complete native GenerationSpecification), a current job/version and precise immutable revision/digest precondition. A candidate remains OWNER input, not a server-owned approved specification, verified fact, execution authority or proposal receipt. The server must independently verify source provenance and reconstruct all server-authority-bearing fields before publishing a DRAFT revision.

The specification candidate is a technical complete-document editor representation. It must not be bound directly to the historical four sample form fields: the actual form/editor must implement every required native field or use the OWNER_TEXT path explicitly. Silent reconstruction from those four examples is forbidden.

## Required pipeline and concrete sources

| Boundary | Exact contract | Source | Completion condition |
|---|---|---|---|
| UI → OWNER API | Closed action-specific mask, no query, reject duplicates and extras; authenticated OWNER channel outside JSON | UI registry actions; §49.3 | Native facade route/operation catalog authored with exact decoder and transport |
| OWNER authentication → trusted context | Server authentication acceptance, current session/API generation and platform/deployment heads; request+contract+descriptor digests | §§26.1,49.4,51.5–6 | Exact facade-specific context constructor and role-bound physical auth joins |
| Selected runtime → frozen intent | Existing exact component/runtime pair, state/generation/activation CAS; typed §50.10 actual launch manifest bytes/digest and registry/active-head checks | §§50.10–11,49.3 | Reference currently checks typed bytes and selector identity; actual active-head/profile/pidfd checks remain required |
| Selected spec → frozen input | Same-job current revision, actual valid native spec JSON, exact canonical digest, OWNER text/candidate retained independently | §§43.3,25.11,49.15 | Same-job physical FK and current revision lock; no duplicate identical canonical candidate |
| Intent → domain_command | Canonical operation/request/idempotency locator, immutable exact arguments/context, sole server writer | §§49.3–4 | Command/context physical joins and exact privileged writer installed; stable locator replay precedes fresh admission |
| Commit → response/event/outbox/audit | ACCEPTED intent receipt; never runtime READY or DRAFT-published claim yet; durable links include exact request/intent/event digests | §49.5 | Full own response/error/event masks, aggregate sequence and audit chain SQL transaction fixture |
| Outbox → worker dispatch | Dispatcher verifies committed command/outbox digest and current target; constructs bounded AUTOMATED or INTERNAL context from server authority | §§49.4–5,50.10–11 | Exact worker-context constructor/operation argument schemas and CAS registry pin; no reuse of OWNER or generation.create context |
| runtime.start → success | Actual same-generation live pidfd plus committed guarded readiness evidence | §50.11 | Readiness receipt belongs to exact runtime generation/launch snapshot; mere process start is not success |
| runtime.stop → success | Own persistent drain/cancel/cleanup inventory, pending effect reconciliation, verified absence of current pointers | §§50.25,50.31 | Cleanup COMPLETE evidence actual inventory and known effects; EOF/transport success insufficient |
| spec input → new DRAFT | New server revision on changed input, immutable prior approval/execution; exact diff/requirement coverage and source provenance | §43.3, UI live-experience specification/edit | Canonical orchestrator publishes native spec-proposed receipt/event after same-job persistence; no duplicate canonical revision |
| worker outcome → original UI intent | Child command+parent logical operation join, precise canonical response/errors and unknown reconciliation | §§49.3–5,50.25 | Pending/UNKNOWN never reported as effect success; retry same stable locator |
| UI hydration | Original logical operation by ID, current selected root/revision by exact server identity and retained immutable byte links | §25.11; UI live-experience | Full typed read masks, current action guards and authenticated producer identity |

## What the executable reference proves

`ui_facade_pipeline_reference.py` is a scoped atomic **reference repository**, not the PostgreSQL or auth implementation. It checks actual typed launch/spec JSON bytes, identity/CAS/digest constraints, distinct OWNER candidate representation, a stored server context scoped to exact request, stable-locator replay/conflict, all-or-none command/receipt/event/outbox/audit reference links, and readback tamper rejection. There is no caller `valid` or `authenticated` boolean. A stored fixture context does not prove real authentication acceptance; that remains a mandatory independently verified join.

Its ACCEPTED receipt intentionally has runtimeReady=false and createdRevisionId=null. Those fields cannot be changed to claim completion without verified worker outcomes. The reference's event digest checks are not a substitute for the full aggregate sequence/audit-chain SQL implementation. The new OWNER facade operations are not active in the shared catalog: assigning direct INTERNAL/AUTOMATED exposure would weaken the trust boundary.

## Exact unresolved A obligations

1. Facade-specific server context constructor and typed frozen descriptor, linked to actual source authentication tables/roles. The generation.create context constructor is operation-scoped and cannot be repurposed silently.
2. Domain_command/native operation rows, concrete transport routes, full response/error/event dictionaries, parent-child result joins and catalog/schema pins for the three facade operations.
3. Start launch current eligibility and immutable release/profile/handler registries, bounded worker context, actual readiness receipt hydration; start-new-runtime allocation distinct from selected-existing-runtime actions.
4. Stop own cleanup operation selector/guards, effect reconciliation and terminal cleanup receipt; no invented adjacent lifecycle enum.
5. Specification OWNER input preservation, canonical reviewed new-DRAFT reconstruction, source/provenance validity, immutable revision physical FK, diff/coverage and exact typed revision read.
6. PostgreSQL event/outbox/audit-chain atomicity and concurrency fixture for this facade bridge, not just generation.create fixture.

No newly necessary business choice was demonstrated. These six groups are technical completion requirements with normative sources; the three UI exposures remain BLOCKED until they are integrated. Actual deployed UI/TLS/session/runtime process/cleanup integration is future implementation acceptance, while obligatory isolated SQL fixtures remain before-generation under their own gate.
