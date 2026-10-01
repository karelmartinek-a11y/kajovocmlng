# Independent Secret publication / reserved OWNER binding review

Independent from the Secret designer; only this review directory changed. Exact authored candidate bytes were copied, not semantically rewritten for the reproduction. Separate PostgreSQL 18.6 databases `secret_publication_review_905` and `secret_owner_review_905` avoided designer fixture collisions. Exact canonical embedded Secret roots and exact canonical OWNER credential table statement were executed; candidate extension bytes were then installed. These reports do NOT yet assert that the extension is canonical or current after coordinator integration.

- Reproduced publication **23 PASS** and OWNER binding **6 PASS**.
- Independently derived **7 PASS**: genuine positive baseline; wrong Secret root composite parent/version FK; wrong root type own active-version parent/type FK; changed immutable version type; wrong active pointer parent/version FK; version lifecycle retired while selected OWNER head remains ACTIVE; baseline unchanged after rejected transactions.
- Initial extra-test invocations expected the deferred OWNER diagnostic for three mutations where a stricter immediate physical FK/immutability constraint rejected the exact tested defect first. Expectations were corrected to the precise actual relevant constraint. Those failed invocations were test expectation errors, never counted as PASS.

## Actual reproduced defect and correction

The publisher installer silently accepted a pre-existing reserved role with LOGIN or BYPASSRLS. Both defects were reproduced by modifying that synthetic fixture role within one transaction, executing the exact installer statement, observing the unsafe role still accepted, then rolling back. No login, credential or persistent global role modification occurred. `publication-role-defects.json` preserves both counterexamples.

`secret-profile-publication-safe-role.proposed.sql` is the concrete correction. Fresh role explicitly forbids replication and bypass-RLS, preserving existing NOLOGIN/NOSUPERUSER/NOCREATEDB/NOCREATEROLE/NOINHERIT. Existing reserved role must satisfy that whole safe profile before grants or installer continuation; otherwise `SECRET_PROFILE_PUBLISHER_ROLE_UNSAFE` aborts.

`safe-role-tests.json`: **8 PASS**, exact corrected installer rejects each of seven unsafe profiles, accepts genuine existing safe role. These tests execute only the installer statement: full corrected extension installation and canonical source reproduction remain mandatory coordinator checks.

## Precise remaining producer obligation

The bounded OWNER identity trigger accepts arbitrary credential_version and credential_activation_epoch changes. `additional-tests.json` records both as **OPEN producer observations**, not successful rotation proof. This is expected in the candidate's explicitly limited identity guard, but §51.20's deferred consistency and authenticated atomic rotation requirement is still unimplemented. Do not invent a simple equality between credential_version and Secret version_number: §51.20 permits reactivation of an old immutable Secret version. The exact independent head version/epoch producer and authenticated verifier-fingerprint derivation must enforce the real atomic transition.

These fixtures provide no actual verifier derivation, authenticated locked acceptance, canonical crypto/key source, broker target/activation or whole `secret.create` closure. SQL schema/review byte archive materialization does not prove that its archived review evidence semantically approves the publication. Re-run against coordinator-integrated exact canonical extension bytes before binding current-source evidence.

## Current corrected candidate reproduction

Designer incorporated both safe-role guards, exact registry read hydration and unique-index first-publication serialization. Reproduced exact current candidate bytes afresh in independent databases: **36 publication + 6 OWNER binding + 7 independently derived identity/lifecycle + 16 both-role installer checks PASS**. The original unsafe installer counterexamples are preserved as historical defect evidence. Current candidate extension remains distinct from canonical integration; re-run exact integrated bytes after root authoring.

## Integrated canonical reproduction

At frozen SSOT `4f9d657357b3623ab5fa7b5f39b8b635476556733207cadc62d16d9a7a12736e`, own verifiers assert candidate bytes equal exact embedded publication/OWNER binding resources before running. Fresh actual PostgreSQL18.6 **36 publication, 6 OWNER binding, 16 installer, 7 derived negatives PASS**. `canonical-independent-review.json` binds reports and resource hashes. Two credential producer observations remain OPEN. This supersedes candidate-only limitations for exact bounded SQL materialization, without extending proof to whole authentication/broker/rotation.

Final-source refresh at `a2bdb08ec729881087e59d7a3fd31053c1e0989bb5b3c640a65cf698a75af4b5`: all four canonical SQL suites re-executed, same 36/6/16/7 results. Chromium14 cookie proof is explicitly reused after exact recorded helper/schema/resource hashes and current engine version checks; historical execution source remains df3de1b9, no new fixture/rerender.
