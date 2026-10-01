# Independent bounded Core Audit review

The executed candidate passed 42 assertions, including the exact embedded PostgreSQL 18.6 framed audit hash. The task originally named 36; the author had added cases before this execution. The report records actual count and input hashes rather than treating the additional cases as completed obligations. Own database: `peer_core_audit_read_84c`.

The CORE200 transport is a strict, source-derived contract distinct from unchanged experience500. Immutable audit/event bytes are inspected and hashed; the named current Secret JSON profile is separate and is not imposed on unknown historical producer bytes. Read outbox absence does not remove OPERATION_ADMITTED/STATE_CHANGED/TERMINAL applicability. Cursor, origin/filter, snapshot, completeness, provenance, and access-audit producer obligations remain open. No operation is closed by these assertions.

## Reproduced blocking response scope defect

Effective §12.54 requires accepted-before-root generation command stages to retain an audit with a typed outcome reference, without manufacturing a generation root or `generation.job.created` event. Canonical `generation-create-preroot.sql` makes `audit_event.domain_event_id` nullable and permits it only with the exact retained outcome/command link. The initial candidate instead required event/aggregate members in every AuditRecord and inner-joined `domain_event`.

Read-only inspection of the preserved actual canonical PostgreSQL fixture confirms two audit records but only one returned by that join. The missing audit is `00000000-0000-4000-8000-000000000009`, bound to the retained outcome at stateVersion 1; stored outcome bytes SHA-256 equals its canonical digest. The existing successful audit follows it and does not replace it. The candidate response mask rejects a non-event stage with `AUDIT_RECORD_MASK_INVALID`.

Global route activation is withheld until an exact discriminated command-outcome audit variant and corresponding typed SQL mapping preserve this history. Fake aggregate/event fields and silently omitting records are prohibited. A definition repair does not by itself close authenticated read, filtering or coverage producers. The historical database inspection is evidence of this physical category; it is explicitly not relabeled as a current-source complete producer fixture.
