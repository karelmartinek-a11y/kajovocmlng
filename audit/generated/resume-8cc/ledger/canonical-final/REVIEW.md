# Current canonical SQL reproduction

Fresh execution loads `database/generation-effect-ledger-producer.sql` directly from the effective canonical SSOT embedded resource. No author candidate SQL substitutes for it. Executed bytes are saved as executed-canonical-producer.sql; their SHA-256 is 4ce2e51d7d98e6234a617928ce6db19cb3199db56d1364a60094e879f91eb274.

Input HEAD d6f6ccefc27f03af3855c0bc31c1ef5f46609c4e, SSOT SHA-256 2577dacf6024e4666ba98b11eb9c7ffa6e7f225e60630697db740129615cc536. SSOT was unchanged during execution. Exact canonical foundation, locked RETRY and frozen archive installed bytes are fingerprinted, as are proof helper and checkpoint schema fixture. Historical scaffolding dependency fingerprints are separate and explicitly recorded after execution.

PostgreSQL 18.6: **48 checks PASS, zero failures**. The 18 historical setup checks are separately reported. Actual target CAS/readback, strict raw observation classification, PRE/POST commit, exact retained replay, concurrent raw writer serialization, allocation rollback, scoped parent/fence/cancellation negatives, UUID order vectors, evidence holes, malformed/duplicate JSON, immutable scope, deferred head/state projection equality, native publication and frozen seal guards were reproduced against actual canonical bytes.

Command:

```
/tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/ledger/canonical-final/verify_canonical_pg.py
```

This is a bounded pre-generation PostgreSQL proof, not full generation.job.create closure or runtime acceptance. Baseline authentication remains a synthetic historical scaffold; archived checkpoint graph/binding/budget source fixtures remain synthetic. Their existence does not establish native semantic authority. Parent producer IDs remain OPEN for audit/reconciliation/compensation/failure universes, restricted installation, authoritative native checkpoint sources and the independently required complete authenticated consumer chain.
