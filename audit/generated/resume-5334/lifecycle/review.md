# Targeted six-field continuation review

Input: HEAD `5334d8caa1b284cb1b4857f51aef2d431b571427`, SSOT `2086c1594100e125cae4714a62371f608835c3346feff66a9f5dab99db6b22aa`. This review consumes the earlier lifecycle-review/field-review.json; it does not repeat the complete audit.

## A — Required before generation: normative meaning and technical projection

The current six fields are still open string masks. A current-resource scan found these exact property names only in closure/contracts/operation-payloads.json; there is no existing server enum dictionary for them. §12.18 permits technical naming, schemas, queues and retries to be derived automatically. Accordingly the attached masks are **technical proposals requiring normative integration**, not existing effective enums and not owner-approved new product behavior.

### owner.mfa.reset.enrollmentState

Own source: closure/contracts/operation-overlay.json#/operations/0/linearizationPoint:

> MFA reset epoch increment + prior factor invalidation + enrollment challenge creation in one DB transaction

Own purpose:

> Reset existing OWNER MFA only after current-session reauthentication, invalidate prior MFA/recovery material and enter bounded enrollment state.

Own recovery:

> Replay committed reset outcome by idempotency key; stale reauth or stateVersion requires refresh/new command.

§21.3:

> Až jeho úspěšné ověření atomicky aktivuje MFA, označí relaci jako MFA-ověřenou ... před dokončením enrollmentu nesmí relace volat MFA-chráněné endpointy.

**Derivable postcondition:** the reset commit creates a bounded challenge and requires fresh factor enrollment. It cannot certify an already completed fresh enrollment, old-factor validity or full MFA authentication.

**Not yet defined in SSOT:** whether enrollmentState returns the immutable reset-commit postcondition or the current enrollment object's lifecycle at read/replay time. The word `enrollmentState` alone does not answer this. §72.9's UI states do not establish this response field's semantics.

**Technical proposed field definition:** “enrollmentState is the reset receipt's as-committed enrollment requirement, not current enrollment progress.” With this explicitly authored meaning the exact mask is `{"type":"string","const":"ENROLLMENT_REQUIRED"}`. The spelling is independently chosen under §12.18; it is not projected from the UI enum. A later separate verify/expire/renew changes enrollment progress without changing the committed reset receipt. Without that normative field definition, the constant must not be integrated as a silently inferred existing enum.

This closes only that response field's receipt meaning. It does not define the enrollment entity's full lifecycle, seed reveal, verification/import or the entire reset operation.

### chat.turn.steer.checkpointDisposition

Own source: closure/contracts/operation-overlay.json#/operations/1:

> Append an OWNER steering instruction to one nonterminal chat turn without replacing authority lineage or silently restarting side effects.

> steering message + successor checkpoint/interrupt intent + audit/outbox commit

> Steering instruction is durably ordered and linked to the exact turn/checkpoint.

> Same key replays the same steering outcome; stale/terminal turn is conflict, never a new implicit turn.

§11.24 explicitly makes central chat a canonical platform agent using the same approval, guardrails, session and audit contracts; proposals are not authority. §49.15 describes **generation discussion** completion/steer races and does not define the central SYSTEM_CHAT_CONVERSATION field.

**Derivable postconditions:** steering is durable, ordered and bound to an exact turn/checkpoint; stale/terminal turn conflicts; no implicit restart or authority replacement; child cancellation must use its own contract. These do not enumerate checkpointDisposition. The slash `successor checkpoint/interrupt intent` does not define whether this field describes an existing checkpoint, a newly reserved successor, a pending interrupt intent or completed child reconciliation.

**Technical gap (not automatically an owner question):** define a central-chat steering checkpoint receipt dictionary with distinct persistent facts and precise conditions. Options requiring technical authoring review are (a) a single `STEERING_COMMITTED` receipt value describing durable instruction/intent only, with no claims that side effects were cancelled, or (b) distinct `INTERRUPT_INTENT_COMMITTED` and `SUCCESSOR_CHECKPOINT_COMMITTED` values plus an explicit, own-central-chat predicate deciding between them. Option (b) cannot be completed from the slash alone. No mask is emitted for this field and it remains BLOCKED_TECHNICAL_MISSING_FIELD_MEANING. Ask OWNER only if investigation reveals different required functional steering behavior, not merely a naming/schema question.

### acceptance.run.start.state and acceptance.run.cancel state/cleanupStatus/reconciliationStatus

Own sources: closure/contracts/operation-overlay.json#/operations/12–13, §25.14 production_acceptance_run, §29.5; §49.4 known outcomes/replay/manual review; §49.5 atomic audit/outbox.

Start linearization:

> production_acceptance_run insert + immutable test plan/profile digest + queue/outbox reservation

Cancel linearization:

> cancel intent/version commit; terminal CANCELLED only after required cleanup/reconciliation

Cancel terminal closure:

> Run is CANCELLED only with zero required pending cleanup/unknown fixture effect; otherwise remains reconciliation/manual-review.

Start closure:

> All required checks have terminal evidence, fixtures cleaned, no unknown effect/orphan, audit/outbox closed and run terminal.

**Technical proposed projection:** define start `state=QUEUED` as an immutable admission receipt at the queue-reservation commit. Separately define the run's current state dictionary and its read endpoint; a current worker run state is not that receipt. Define cancellation response as the current authoritative cancellation-stage snapshot taken under the cancel/run lock, with own values `CANCEL_REQUESTED`, `RECONCILING`, `MANUAL_REVIEW`, `CANCELLED`; cleanup `PENDING`, `COMPLETE`, `FAILED`; reconciliation `PENDING`, `COMPLETE`, `UNKNOWN`, `MANUAL_REVIEW`. This is a newly materialized technical dictionary, not an enum found elsewhere.

The minimal cancellation dictionaries distinguish pending cleanup, a known cleanup failure, unknown external outcome and recorded manual review. COMPLETE requires a positively verified server-owned inventory; an absent inventory is never empty. CANCELLED requires COMPLETE cleanup and reconciliation plus terminal evidence of all required checks. The corresponding proposed reference predicates reject pending or unknown effects and stale fences before terminal cancellation. Failed cleanup is preserved and cannot be recast as success. A cancellation request may remain pending even when inventories are clean until its canonical finalization transaction commits.

A complete run dictionary and worker edges are proposed in technical-proposals.json. They cannot be installed merely by changing six response enum masks. Their own data persistence and exact-run source binding must also be authored. No additional fixture privilege, external mutation, actor or acceptance waiver is introduced.

## B — Reference design proof

`verify_reference.py` passes 79 exact checks over proposed receipt masks/predicates. Each negative mutation starts from its own positive witness and checks the specific expected diagnostic. It includes null/wrong-type/unknown-value rejection, omitted commit prerequisites, stale fence, unverified inventory, pending cleanup, unknown effects, nonterminal checks and manual-review terminalization. Synthetic booleans/counts represent authoritative transaction facts; this is not actual SQL or worker evidence.

This proof does not establish that the proposed field dictionaries are already effective SSOT. It must be rerun and rebound after canonical integration and supplemented with actual transport/error/event/consumer contracts for operation closure.

## C — Implementation acceptance

NOT_EVALUATED. No application, database transaction, queue worker, UI lifecycle or external cleanup/reconciliation execution was evaluated.
