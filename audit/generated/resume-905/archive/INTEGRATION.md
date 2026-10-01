# Frozen archive integration candidate

Pinned HEAD `905555e47f3547516439a699e262df62cbbec229`, SSOT SHA-256 `df3de1b9d3411c9c410f2d7e4274d9d15ff41ec912ee901833bbc124a79ed691`. Own outputs only this directory. No Git/shared changes.

## Authority and precise repair

- §12.54 read clause 7 (canonical lines 4701–4705): preserve actual frozen schema/policy bytes and declared closure; instantiate compiler per `(schemaId,bundleDigest,definition)`; reject unavailable archive, no current/network fallback. The prior current-mask-only `generation_read_hydration.py` guard contradicted the required historical consumer.
- §12.47 (4251–4284): exact request schema plus nonempty intent and duplicate domain references. This candidate retains the **request-hydration** domain semantics; it does not assert a full immutable admission-policy dispatcher for every kind.
- §49.4 retention and §51.10 immutable rows/no deletion while frozen reference exists; §51.5/51.12 atomic command/root/idempotency retention.

`generation-frozen-archive.sql` is a separate extension installed after unchanged canonical generation foundations. It has immutable content-addressed SCHEMA/DOMAIN_POLICY/AUTHORITY/POLICY_IMPLEMENTATION bytes, exact server provenance identity/source digest, immutable snapshot↔command/schema/policy binding, and explicit closure. Deferred triggers require each successful initial snapshot to have its archive in the **same** transaction and bind exact schema/command identities. Missing schema/dependency/authority/code bytes or invalid closure rejects rather than leaving a digest-only snapshot. Frozen bytes/bindings reject UPDATE/DELETE. Same `$id` with different digest coexists. Publish replay must preserve actual bytes and provenance; PUBLIC table/function use is revoked, SECURITY INVOKER never creates auth authority.

`kcml_archive_read_v1(snapshot,command)` returns only the exact selected binding and its actual declared bytes. These schema/policy contents contain no Secret/input plaintext; protected request bytes remain in canonical protected snapshot storage. Runtime invocation must still use authenticated selected job/command read context.

`generation_frozen_archive.py` dispatches frozen request schema and **real archived source bytes** of `generation_request_policy_v1.py` with exact authority bytes. The V1 handler is a statically trusted loaded revision, never `eval`/`exec` of arbitrary archived code. Unknown implementation/revision is explicitly BLOCKED. Supported historical d362 schema is validated with retained d362 authority/policy, not today's schema. No JSON caller flag proves policy validity.

`generation_create_consumer_archive.py` changes only consumer signature + request validator use: no current request validator when archive missing. `generation_read_hydration_archive.py` replaces current-mask lookup with exact bound archived compiler/handler; all existing retained receipt/root/event joins, digest checks, and sensitive-output protections stay intact. Coordinator can apply these small changes to canonical helpers rather than copy broad historical fixtures.

## Actual proof

`verify_archive.py` / `archive-proof.json`: **32 PASS**, PostgreSQL **18.6**, disposable own `archive_905` database. Exactly the current embedded `database/generation-create-foundations.sql` and `database/generation-create-read.sql` bytes execute; the extension is clearly candidate SQL, not yet canonical.

The producer publishes exact schema/policy/authority/code bytes, creates root/command/event/outbox/audit/locator and the archive binding in one real COMMIT, reads actual archive bytes from SQL, and consumes the actual root/event/receipt/protected-input byte fixture through frozen policy. Missing archive proves whole-transaction rollback (0 command/root/event); missing dependency rejects exact expected diagnostic. A wrong command points at a real existing non-generation command (rather than an absent FK), and digest-valid available alternate schema bytes point at the wrong snapshot: both reject the specific archive binding diagnostic. Identical concurrent publication waits under the actual unique-index lock and retains one exact row; conflicting source cannot replace retained provenance. An initial negative-test fixture used an absent command, which hit its FK instead of the target binding guard; this was corrected to an existing command and was not counted as a successful guard proof. Same bytes/provenance replay succeeds, changed provenance fails. Actual historical d362 mask accepts its valid UPDATE witness, current mask rejects it, with exact historical bytes also persisted in PostgreSQL. Synthetic same-ID distinct revisions independently reject wrong value. No unavailable archive/implementation fallback succeeds.

The existing root fixture uses synthetic trusted context and returns real body bytes from its opener; these are **not** proof of OWNER credentials, authenticated systemd key opening, or future backend service acceptance. SQL archive ownership grants/producer invocation must be bound by coordinator to actual service accepted context, not exposed to model/OWNER HTTP inputs.

## Exact remaining IDs

- **GENERATION.ARCHIVE.SUCCESS**: this candidate closes bounded durable successful snapshot schema/request-domain-policy bytes plus historical read if integrated/reproduced/reviewed. Root must embed SQL + authoring and integrate helper changes; candidate evidence alone is not VERIFIED.
- **GENERATION.ARCHIVE.PREROOT**: accepted pre-root snapshot must freeze the same archive before pending/failure retention, then transfer exact binding to successful snapshot. This candidate currently covers successful snapshot only; do not invent root for pre-root failure.
- **GENERATION.ARCHIVE.KIND_POLICY**: full selector/admission/eligibility/execution policy implementation revisions and all native dependencies need their own archived producer/dispatcher. V1 request hydration rules do not replace those policies.
- **GENERATION.ARCHIVE.AUTHORITY**: trusted deployment/service role/context publishes normative current package and binds it under actual admission locks. Fixture superuser/source assertions are not the production auth verifier.
- **GENERATION.ARCHIVE.REVIEW**: independent reproduction on integrated canonical SQL/helper bytes required.

Whole operation closure remains 0; implementation acceptance NOT_EVALUATED. No new product decision found.
