# Independent protected registry-link review

Input effective SSOT `4f9d657357b3623ab5fa7b5f39b8b635476556733207cadc62d16d9a7a12736e`. Writes only this review directory, own disposable PostgreSQL databases. No shared/Git writes.

`verify_peer_key.py`: **15 PASS**, actual PostgreSQL18.6, exact embedded `database/generation-protected-registry-link.sql`, canonical foundation/authentication/preroot/registry bytes, ROOT authentication and crypto helpers. Reproduces original12 cases and adds purpose substitution plus independently derived post-SQL valid-positive AEAD context and ciphertext-envelope substitutions. Actual successful COMMIT is visible from independent SQL connection with root/reservation/command/outbox/audit. Missing reservation/purpose mismatch fails exact required guard; SQL identity/cipher/nonce substitutions fail their own expected guards. Crypto substitutions first pass unchanged valid SQL storage and then fail actual authenticated opening, not an unrelated invalid fixture exception.

## Reproduced defect — exact AAD bytes

`verify_aad_counterexample.py` and `aad-byte-counterexample.json`: **DEFECT_REPRODUCED**. Derived from the same valid positive, encode the correct complete metadata/profile/purpose/key JSON object with whitespace, retain all identical values, recompute its exact metadata digest, and store it in the reservation. SQL semantic-jsonb equality accepts it; actual root crypto consumer opens the ciphertext (generated with canonical compact AAD) successfully. Therefore the row named authenticated_metadata_bytes contains bytes DIFFERENT from those actually authenticated by GCM. §12.54 explicitly requires exact UTF8 sorted compact bytes/no whitespace. The current typed-link guard verifies values but loses required byte identity. This is a technical repair, not a new product decision. Fix must compare canonical actual AAD bytes or bind verified exact emitted bytes through the typed producer; merely adding another jsonb equality condition does not fix it. Then rerun this real counterexample and all valid positives.

## Separate authority/environment gaps

`peer-environment-proof.json`: PID1 tail, UID1000, no systemd private/system bus socket; systemctl offline. Actual root-owned encrypted credential and read-only systemd invocation source remain **BLOCKED / ENVIRONMENT**, not product ambiguity.

The SQL proof explicitly inserts registry/service/key rows in a disposable fixture using synthetic random keys. It does not verify who may register an authorized service, how actual systemd invocation supplies trusted context, or Secret typed-row/broker joins. PUBLIC revocation and identity FK/value checks are useful constraints but not proof of those producer/authority contracts. They remain separate OPEN A/B obligations; whole operation is not closed and production acceptance remains NOT_EVALUATED.
