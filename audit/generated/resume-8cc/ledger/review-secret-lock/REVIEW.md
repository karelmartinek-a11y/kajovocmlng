# Independent Secret acceptance lock review — defect reproduced

Pinned coordinator HEAD `451b556067cb7cdd4f411cd742ab8fcaec8a379a`. The actual source SHA, four canonical SQL resources, candidate SQL/helper hashes and statement fingerprints are in `independent-secret-lock-review.json`.

Reviewed exact corrected candidate from `resume-8cc/secrets` against actual PostgreSQL18.6 in OWN database `secret_lock_review_8cc`; only this review directory is written. Existing OWNER credential initialization cipher is explicitly opaque and the master key is an isolated generated fixture key, so this is not a credential-provisioning/systemd source proof. Native token verification is real constant-time verification; no authorized flag or PUBLIC token parameter grants authority.

## Reproduction

`/tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/ledger/review-secret-lock/verify_independent_secret.py`

Independent SQL catalog inspection confirms C0 locator and C1 idempotency have only deferred command FKs, so claims do not implicitly lock OWNER before E10. Actual native trace proves credential B → C0 locator → C1 RESERVED record → OWNER E10 → new Secret E20 → context/version/command/event/completion/outbox H → audit-head I last. After I, native code emits only the owned audit insert/head update; deferred FK checks reference already-owned roots/children. This proof does not certify arbitrary other writers or final installer grants.

Valid native domain witnesses were checked and rolled back before each independently selected mutation. Foreign context substitution rejects `SECRET_CONTEXT_SINGLE_COMMAND_REQUIRED`; changed versionState receipt, with recomputed matching receipt/event bytes and digest, rejects `SECRET_CREATE_ATOMIC_CLOSURE_INCOMPLETE`. Both leave all counts unchanged. A second real session can lock OWNER FOR UPDATE immediately before E10, demonstrating absence of early implicit FK KEY SHARE. A real rotation writer gets PostgreSQL lock timeout while credential SHARE is held. An actual isolated publication/deployment epoch1→2 retains original epoch1 replay scope/output. Exact scoped replay returns original output without new records; same key with changed native request rejects `IDEMPOTENCY_CONFLICT`.

## Actual remaining defect

**Result:14 PASS,1 FAIL across15 independently selected checks; review BLOCKED.**

The reviewer consistently replaces ONLY `domain_command.result_digest`, `create_completion.result_digest` and `domain_idempotency_record.canonical_outcome_digest` with32 zero bytes. Original request, caller, context, encrypted sensitive bytes, exact output receipt, event bytes/digests and audit remain valid. Actual deferred constraints **accept** the transaction. The original producer's response result digest remains the real SHA-256 of `semantic_result(response)` while stored result digest is zero, violating the authoritative semantic response continuity.

`create_atomic_closure_v1` compares these digest columns against one another without recomputing `canonical_digest(semantic_result(response))`. Crossrow equality is insufficient. The entire counterexample transaction is rolled back; no corrupt retained row is left.

Fix must preserve the exact immutable semantic response excluding resultDigest/idempotencyReplay (existing `scripts/create_completion_contracts.py:semantic_result`), derive/check the actual hash from those bytes and bind its route/operation/correlation/output/state/event fields to persisted context/command/root/event. An unrelated FK, invalid fixture or schema exception must not be claimed as a regression rejection. Root owns integration; this reviewer changed no author/shared files.

Other explicit gaps remain OWNER_SESSION acceptance, retention authority, restricted role installer/context, target/provider activation and broker, real credential/master-key producers, and root-status policy (separate author is addressing it). They do not negate the demonstrated corrected lock plan, and do not permit whole Secret create closure yet.
