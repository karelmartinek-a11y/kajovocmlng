# Bounded ordering correction — candidate, not whole producer closure

Frozen original SQL and original 38-case history are untouched. `original-order-gap.json` reproduces an actual committed first intent with INSERT order H140 operation → H150 attempt → H150 state → H50 PRE checkpoint in PostgreSQL 18.6. This violates §51.6 independently of whether its final rows are atomically consistent.

Install the original unpublished producer candidate followed by `ordering-repair.sql`; `side-effect-producer.sql` contains those exact combined bytes for reproduction. This is additive preparation of fresh unpublished tables, not a safe online backfill of pre-existing immutable production rows. Root must integrate it and the explicit `lock-kind-migration.json` allocation together.

The correction separates full §49.9 checkpoint compilation from physical intent rows. A private compiler takes server-created typed operation/attempt composites, actual root/current context, actual archive content, and actual pending operations. PRE adds its precise proposed intent; POST substitutes the outcome derived by the retained fixed CAS classifier. Neither compiler accepts a validity flag or a caller-selected result. Existing non-null exact FK checks remain, with checkpoint→attempt and state→attempt deferred to COMMIT. Deferred atomic closure still requires the corresponding real rows, exact dispatch authority, counters and bytes.

After E root/F concurrency checks, both producers acquire the dedicated G checkpoint head before any H acquisition. The new H50 checkpoint INSERT and existing live H50 phase row lock are acquired in UUID order. PRE then inserts H140 operation and H150 attempt/state in actual UUID order using an automatically generated state identity. Confirmation inserts POST before prelocking H140 operation/H150 existing state; subsequent state edges update rows already held, rather than acquire new lower locks. Dispatch likewise prelocks operation H140 before state H150. The already-held G head can be updated after checkpoint creation because this is not a fresh G acquisition.

Explicit NOT NULL physical `primary_parent_uuid` columns derive from actual generation_job FK roots. State/attempt/evidence insertion rejects an inconsistent claimed parent. Generated columns are computed after PostgreSQL BEFORE triggers; the operation immutable guard excludes only this redundant computed column while preserving immutable actual parent_id. No relation name establishes ownership. The subtype `event_identity` binds exact immutable domain_event bytes to its actual operation/root. New SIDE_EFFECT_EVENT_IMMUTABLE ordinal160 is explicit, after150 and before outbox910; both existing event call sites are record_intent and confirm_cas_v1. The universal outbox parent migration remains outside this bounded change.

Reproduction:

```
/tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/ledger/order-repair/verify_original_gap.py
/tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/ledger/order-repair/verify_ordered.py
```

Run these sequentially: both use the same owned disposable PostgreSQL database. The corrected proof has 41 actual new checks, 0 failures, and separately reports 18 reused historical native-scan setup checks. It includes actual target CAS/readback, classified POST commit, typed malformed/duplicate observation negatives, rollback, strict retained replay, exact evidence-hole rejection and concurrent writer serialization. Instrumented INSERT vectors specifically prove PRE H50→H140→H150→H160 and POST H50→H160. They are **not** a full dynamic acquisition trace across every function and every hierarchy class; E/F/G and already-held update behavior are bounded source-reviewed statements.

`append_evidence` still needs a three-way UUID-sorted H150 acquisition/creation plan for immutable attempt, mutable state and new raw evidence. No whole producer ordering PASS is claimed. UNKNOWN/OWNER reconciliation, compensation, intent/outcome audit, native context-source semantics, remaining actual failure predicates and final restricted installer remain open as identified in the original delivery.
