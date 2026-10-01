# Accepted-before-root frozen archive and exact successful transfer

Input pushed HEAD `32a63a9e3447bd4ed9a7dc4638cadc113071a8b7`; canonical SSOT SHA-256 `a2bdb08ec729881087e59d7a3fd31053c1e0989bb5b3c640a65cf698a75af4b5`.

## Authority and additive repair

§12.54 requires actual frozen schema/domain-policy bytes and declared dependency closure at hydration, no current-policy/network substitute. Its pre-root retention clauses require accepted input/outcome identity to remain immutable and later success to transfer identical protected snapshot fields. §12.55 materializes successful exact archive snapshot/command/schema/policy bindings while explicitly leaving pre-root archive transfer open. §49.4 retention, §51.10 immutable history and §51.12 frozen idempotency support this technical extension; no new kind/state/product policy is introduced.

`generation-preroot-frozen-archive.sql` installs AFTER the unchanged canonical foundation, preroot and successful-archive resources. It adds a separate immutable `generation_preroot_frozen_policy_binding_v1` with actual FK to the accepted pre-root snapshot (not a fabricated generation root), FK to the admitted command, and schema/policy byte-address FKs to the existing immutable bundle store. Its deferred guards require exact snapshot/command/schema identity, complete policy authority/implementation bytes and declared schema closure before accepted pre-root COMMIT. Current successful archive table, FK, required snapshot guard and validator remain unchanged.

When success is created later, its existing mandatory successful binding must equal the retained pre-root binding in every command/schema/policy/dependency member. A symmetric guard prevents late insertion of a different pre-root binding after success. The same protected snapshot already remains subject to canonical pre-root transfer/global crypto authority guards. Retained pre-root archive and pending outcome are not updated or deleted. Failed transfer rolls back its candidate root/event/command changes and extra bundle publications; accepted immutable history remains intact. Dedicated `kcml_preroot_archive_read_v1(snapshot,command)` returns actual exact archive bytes without requiring/creating a root.

The producer must publish authentic available frozen bytes under actual accepted service authority; this SQL adds no request/model ability to claim registry authority and PUBLIC table/function access is revoked. Authentic unavailable legacy archived content remains BLOCKED; no digest-only/current backfill is authorized.

## Actual connected proof

`verify_preroot_archive_transfer.py` / `preroot-archive-transfer-proof.json`: **25 PASS**, PostgreSQL **18.6**, disposable own `archive_preroot_transfer_905`. Exact canonical foundation/auth/preroot/global crypto registry/fixed typed protected-row link/successful archive/read resources execute unchanged, with candidate extension added separately. Proof and candidate hashes are explicit.

The fixture verifies a real isolated OWNER bearer through ROOT verifier/context constructor, performs actual canonical AES-GCM encryption, reserves the exact global nonce/protected row, retains a valid native ACCEPTED command outcome plus audit/locator/idempotency and exact archive BEFORE any job/event/outbox exists. Later a real successful transaction uses the SAME command/context/ciphertext/nonce/schema/content/policy/closure, adds exactly one root/event/outbox and second audit, and retains the prior outcome bytes. Actual transferred ciphertext opens under ROOT crypto and the archived request policy.

Four valid-positive-derived pre-root negative families: missing archive binding; missing schema bytes (specific named FK); available digest-valid wrong schema; missing declared dependency bytes. Each rejects its exact guard and leaves no partial command/snapshot/nonce/archive binding.

Four failed-success families: omitted required successful archive; same schema with DIFFERENT available policy digest; DIFFERENT available dependency closure; changed ciphertext. Policy/closure substitutions reject `FROZEN_PREROOT_ARCHIVE_TRANSFER_MISMATCH`. Ciphertext substitution rejects the earlier canonical global nonce/ciphertext binding guard, not a claim of directly isolating the later pre-root byte comparator. Every rollback checks no new root/event/successful archive, command remains ACCEPTED, and the original pending archive AND outcome remain byte-identical. Original successful archive FK is preserved.

## Development diagnostics and limits

Initial invocation extracted the wrong historical `checks=[]` marker and did not load the pure outcome function; corrected targeted source extraction, not counted as negative PASS. An auto-generated PostgreSQL FK name was truncated; candidate now names schema/policy FKs explicitly. A ciphertext mutation hit the existing stronger global protected reservation guard before the pre-root comparator; the negative now accurately names/checks that exact boundary. No unrelated exception is counted.

This closes bounded **GENERATION.ARCHIVE.PREROOT** retention/transfer after canonical integration and independent reproduction. It does NOT close full admission/kind/execution policy archives, failure/cancel/UNKNOWN/reconciliation decision producers or public pending/read/UI hydration. Credentials and key registry provisioning are isolated synthetic; actual root-owned encrypted systemd source remains ENVIRONMENT BLOCKED. No whole operation/runtime acceptance claim.

## Final canonical reproduction

Current effective source SHA-256 `4ac6fe00df084e910a90093485b12172866be73db94f66b6815200556c35be06`.
Canonical `database/generation-preroot-frozen-archive.sql` executes unchanged; verifier asserts bytes equal the original frozen candidate `40a2fce25eaa50d582228463df86bfbf0ffb30f9facb1f1e84a2907bef3705ef` and reports `canonicalExtensionBytesExecuted=true`. Fresh actual run: **25 PASS**. Original candidate/input narrative above remains historical provenance; this is the current proof, not a source-hash relabel.
