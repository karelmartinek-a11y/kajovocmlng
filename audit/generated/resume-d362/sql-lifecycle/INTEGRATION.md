# Ready integration: six own receipt fields

Pinned input d362487999bd795d4723c2a930e93fc7aa8aa295; SSOT 22256baa17729b7577ca4e2498b74b7dfc2b3e6bab57f3b88c338a059557a0ee. `field-patch.json` additionally pins all actually consumed canonical resource bytes. Locate records again by operationId before applying; each patch carries oldValue so a changed field fails review rather than overwrites it.

Integrate `state-definitions.md` as a new normative technical subsection under the effective operation overlay, and apply its six patches to `closure/contracts/operation-payloads.json`. The concrete response masks for these final closure operations exist only there: no baseline native-generation definitions or operation-contract records declare them. Preserve response required arrays and nullable sibling fields. No invented baseline route/operation record is needed. Overlay request/responseSchemaRef pointers already bind these concrete native masks and remain unchanged.

Exact fields:
- records/0 responseSchema/properties/enrollmentState (owner.mfa.reset), const ENROLLMENT_REQUIRED;
- records/1 responseSchema/properties/checkpointDisposition (chat.turn.steer), const STEERING_COMMITTED;
- records/12 responseSchema/properties/state (acceptance.run.start), const QUEUED;
- records/13 responseSchema/properties/state, cleanupStatus, reconciliationStatus (acceptance.run.cancel), own dictionaries and inventory predicates.

Run `/tmp/ssot-audit-venv/bin/python audit/generated/resume-d362/sql-lifecycle/verify_states.py`: 65 checks PASS, with every negative mutation beginning from its own positive schema/inventory witness. This reference consumes actual inventory entries/digests and exact expected obligation sets, not `valid=true` or count summaries. Missing/duplicate identity, conflicting digests, unknown effects, failed/pending cleanup, pending checks, orphan entries and forged receipt state have specific rejection diagnostics.

The normative field meaning and these masks close six bounded response definitions after review/integration. They do **not** close four whole operations. Other operation boundaries and real SQL worker execution remain separate obligations. Actual required Postgres transaction fixtures are not replaced by this Python proof. Inventory trusted origin is an explicit prerequisite, not a claim proven by this reference. After canonical integration rerun/rebind evidence against current source hash; this original input proof remains historical.

The previous 79-check proof was proposal-only and used boolean/count transaction facts. This new 65-check proof provides concrete inventory projection and adds central-chat receipt semantics; do not sum the two as operation completion.

# SQL follow-on, deliberately separate

The four common helpers have 262 call sites each; the current operation-functions resource is unchanged relative to the earlier scoped SQL review. `kcml_operation_context_v1` remains missing from canonical executable SQL. The descriptor/recovery/root-lock helpers require the exact trusted-context definition and retained-replay lookup produced by the persistence/event work. The generic apply helper cannot turn 262 descriptive physical plans into executable domains. An exact generation.job.create wrapper/dispatcher may close that operation's bounded SQL path once roots/context/event contract agree, but does not define all remaining 261 operation handlers. No unconditional-success or generic-json interpreter stubs are supplied.

No owner decision was identified for these technical receipt vocabularies. No PostgreSQL installation was duplicated; the persistence agent owns the isolated PostgreSQL 18 environment and its genuine fixture evidence.

## Independent-review correction

Evidence lookup now loads actual canonical bytes, verifies digest, and requires full run/release/plan/fixture/item/family/outcome binding. Numeric item IDs and duplicate JSON keys are rejected. Terminal projection accepts a retained finalization record ID only: it resolves typed actual finalization bytes, committed transaction record and event/outbox/audit records with matching logical operation, transaction, inventory digest and fence. The former caller-supplied finalization boolean no longer exists. These semantic record joins remain a reference test, not proof that a server actually persisted or trusted the records.
