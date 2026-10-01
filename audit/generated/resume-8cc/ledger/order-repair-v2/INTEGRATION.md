# Exact append-evidence ordering correction

This extends the frozen 41-case v1 candidate without changing its files. `frozen-v1.sql` retains its exact bytes. Use the combined `side-effect-producer.sql`, or install v1 then additive `evidence-order-repair.sql`. No native call signature or native projection bytes changed.

The original violation is reproduced in `original-append-order-gap.json` on actual PostgreSQL18.6. At a test-only BEFORE evidence INSERT pause, the new evidence UUID is lower than the actual immutable state UUID. An independent session's state FOR UPDATE NOWAIT fails: frozen append already held the higher H150 state row before inserting the lower H150 evidence row. The corrected exact-byte candidate at the same pause allows that independent state lock. This is a physical row-lock counterexample and reproduction; the pause is fixture instrumentation only and not part of canonical producer behavior.

The corrected append holds actual E generation root and F concurrency fencing authority first. It reads typed physical operation/attempt/state identity while that root serializes conforming producers. A dedicated G evidence_head allocator, with NOT NULL primary_parent_uuid from the canonical root and exact deferred attempt FK, is claimed/locked before H. Source watermark and actual contiguous evidence are checked before initializing it. The authoritative counter increments by one under FOR UPDATE; rollback consumes no sequence. Both allocator and state have deferred exact projection equality checks, preventing a privileged contiguous evidence/state advance from bypassing G.

The producer knows three real H150 UUIDs: immutable attempt, existing mutable state, and the new raw evidence. It sorts all three, taking attempt FOR KEY SHARE, state FOR UPDATE, and exact immutable evidence INSERT in that order. Exact evidence→attempt FK is DEFERRABLE INITIALLY DEFERRED so a lower-UUID new evidence INSERT does not implicitly acquire the higher attempt key ahead of the explicit sorted slot. The later state counter update affects the already-held row. Primary-parent metadata, raw bytes/digest, actual fence/incarnation and state version rules remain enforced.

Same evidence identity plus identical operation/attempt/kind/bytes/digest/fence/incarnation returns the retained original sequence without consuming another counter. A changed replay rejects EFFECT_EVIDENCE_REPLAY_CONFLICT. This is not ON CONFLICT DO NOTHING. Invalid kind after allocation rolls back G/state/evidence. Head identity mutation, head/state mismatch, count-equivalent evidence holes and concurrent counter writers reject their actual relevant violations.

Commands, sequential because full proof and fixed vector share an owned disposable database:

```
/tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/ledger/order-repair-v2/verify_original_append_gap.py
/tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/ledger/order-repair-v2/verify_ordered.py
/tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/ledger/order-repair-v2/verify_fixed_append_vector.py
```

48 meaningful actual PG checks PASS; 18 reused setup checks are separately counted. The original/fixed row-lock vectors bind exact candidate and SSOT hashes. The full proof binds exact executed canonical foundation, locked-retry and archive bytes and asserts SSOT unchanged during execution. Candidate approval and integration remain coordinator-owned. A reviewer must reproduce it independently before activation.

This closes the known bounded append ordering defect. It does not certify native publication/phase sealing/failure producer order, audit producers, all UNKNOWN/OWNER/compensation paths, native checkpoint source semantics, final roles, or actual key installation. The broader parent producer IDs remain IN_PROGRESS.
