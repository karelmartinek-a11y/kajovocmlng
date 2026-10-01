# Restricted key observer, source and invocation receipts

Pinned input: commit `8cc19fbc69fb839ea88597b736da03d8b3eaecd4`, SSOT `4ac6fe00df084e910a90093485b12172866be73db94f66b6815200556c35be06`.
Owned paths: only this directory. No shared edits, Git operations or recursive agents.

## Integratable technical changes

`systemd_key_authority.py` implements an actual restricted local system-bus observer. It rejects a non-systemd PID1; validates a root-owned Unix socket and root SO_PEERCRED; resolves and pins systemd's unique bus owner, checks its UID0/PID1, and sends all subsequent unit/property queries to that exact unique owner using explicit busctl --address=unix:path=/run/dbus/system_bus_socket. The verified Unix peer and all CLI calls therefore use the same socket; inherited DBUS_SYSTEM_BUS_ADDRESS cannot redirect calls. Installed busctl supports --address. It resolves the server's exact unit ID, active state, InvocationID, MainPID and monotonic process start timestamp. Two InvocationID reads detect a restart during observation. This is not a request callback, client receipt, authorized Boolean or model-provided mapping.

The source installer function runs only as root. It reads the exact server installation source using O_NOFOLLOW, requires regular root-owned0600 source, hashes encrypted bytes in bounded chunks without exposing their content, and detects concurrent file mutation. It does not claim that filesystem properties alone prove encryption: actual systemd LoadCredentialEncrypted and observed plaintext fingerprint are mandatory.

`publish_current_invocation` obtains exact key/service/generation/fingerprint/profile and source receipt from actual database rows, requires an open DB transaction, observes the manager's actual process identity, reads the actual service credential directory and verifies the key fingerprint. It publishes an immutable invocation receipt and compares every retained identity/fingerprint/source/purpose member on replay. Its internal key selector must come from locked server current/retained authority, never public request fields. No client path or supplied invocation mapping enters this producer.

`key-invocation-receipts.sql` stores immutable encrypted-source and confirmed invocation records under physical key-generation/service and encrypted-source FKs. It checks the actual observed key fingerprint against the canonical key registry. Purpose arrays have exact enum, dimensions, lower bound and uniqueness constraints; an offset array cannot bypass duplicate checks. Restricted NOLOGIN/NOINHERIT source installer and invocation publisher roles receive only their narrow table permissions; dangerous pre-existing role attributes block installation rather than being rewritten. Exact platform LOGIN membership/IPC/service installation is deliberately not invented by this candidate. Historical versions remain encrypted under the existing canonical systemd mechanism; no ENV key, plaintext archive, new owner step or key-ID alias namespace is introduced.

`key-authority-contract.json` identifies all producers, exact source→invocation chain, same-transaction global nonce producer order, retained historical source requirement, and remaining mandatory conditions. It is a technical candidate awaiting review/provider fixture, not a production receipt or whole-operation verification.

## Actual evidence and its limits

- `manager-adapter-reference-proof.json`: 28 PASS. Parser/guard tests use explicitly patched manager replies, plus actual temporary readonly key bytes through a fixture-only path adapter and actual non-root installer denial. A valid reference witness precedes receipt mutations. This does not attest the manager/source provider.
- `key-receipts-postgres-proof.json`: 21 PASS, actual PostgreSQL18.6. Exact canonical registry/foundations plus named candidate; FK/mask/immutability/restricted-role checks and real publisher-code→DB idempotent handoff. The source metadata, manager replies and temporary key path are synthetic. This is not root/systemd/rotation proof.
- `review-stage/integrated-stage-proof.json`: 12 PASS on the actual integrated root module. Source §12.51.2, actual declared synthetic classifier bytes. Valid CONFIRMED_APPLIED/FAILED_FINAL discussion witnesses preserve effect/final result, execution retains the exact old rejection codes, and corrupt actual scan/classifier bytes reject specifically. No PostgreSQL lock/completeness claim is attached to this byte/stage proof. Historical candidate proof is retained separately.
- Existing canonical exact-AAD and preroot-transfer proofs are preserved; this task does not redo their authoring or replace their successful boundaries.

## Environment obstruction and reproduction

`environment-capabilities.json` records UID1000, PID1 `tail`, absent system/system-user manager/bus sockets, and an actual new observer diagnostic `SYSTEMD_MANAGER_NOT_PID1`. Managed Docker28.4.0 responds but has no cached images; the current policy does not list Docker Hub. No privileged host mount/network bypass/unapproved registry pull was attempted. The previous unsupported encrypt attempt is preserved and was not repeated unchanged.

`run_systemd_isolated_fixture.sh`/`systemd_fixture_worker.py` are syntax-checked, automatically create synthetic32-byte material, use systemd-creds host encryption, retain root-owned0600 encrypted source, and invoke an exact non-root unit via LoadCredentialEncrypted in a disposable root-systemd VM. They are NOT_RUN here. To extend the provider fixture, run the actual observer from that exact service process, persist the installer/source/key/invocation receipt through the restricted DB roles, restart the unit and confirm changed InvocationID with unchanged key fingerprint, rotate an automatically generated encrypted key version with desired/effective confirmation and dependent smoke, keep the old encrypted version in the server-authored credential manifest, and open retained generation and Secret rows under their own retained key IDs. Verify stale invocation/source/epoch, unsafe writer roles, missing old materialization and mixed desired/effective generations reject; verify immutable replay does not reserve/reseal another nonce. No production credentials or live accounts are involved.

## Precise remaining obligations

- `SHARED.CRYPTO.SYSTEMD_SOURCE`: actual root encrypted source → read-only exact systemd invocation fixture. ENV_BLOCKED.
- `SHARED.CRYPTO.KEY_INVOCATION` / `GENERATION_KEY_MANAGER_PRODUCER`: execute the real observer/installer→restricted publication path under actual service identity and confirm invocation/generation/fingerprint; verify exact role membership and generated handlers cannot access directory/registry writer. ENV_BLOCKED for real producer; technical adapter/SQL available.
- `KEY_ROTATION_RETAINED_GENERATION_USE`: actual desired/effective head, credential restart/smoke/old-connection retirement, retained encrypted version availability and retained-generation read. Requires actual systemd and platform rotation producer; no caller `retired` flag alone is authority. ENV_BLOCKED provider, missing mutable-head/rotation transaction remains explicit technical work.
- `SHARED.CRYPTO.GLOBAL_NONCE`: canonical exact-AAD/preroot reservation integrity is already covered. End-to-end producer ordering still depends on confirmed real key invocation, restricted source publication and generation/Secret transaction producers; global uniqueness alone does not close this obligation.

No new product decision was found. These are mandatory A/B design/fixture obligations; none is moved to future application acceptance C. Whole operations remain OPEN and implementation acceptance NOT_EVALUATED.

## Diagnosed invocations

The initial PG test expectations used guessed autogenerated constraint names. PostgreSQL rejected the intended defects correctly; the candidate now uses explicit stable FK/purpose constraint names and all reruns pass. No unrelated exception was counted as a negative PASS. Prior proof files describe their own consumed hashes rather than current provider certification.

## Exact installation and reproduction commands

Install in one controlled transaction, in this order:
1. Unchanged embedded `database/generation-create-foundations.sql` (physical crypto consumers and SHA256/database prerequisites).
2. Unchanged embedded `database/canonical-crypto-registry.sql` (profile/key/global nonce tables and immutable trigger).
3. Reviewed candidate `key-invocation-receipts.sql` (source/invocation FKs, fingerprint guard, immutable records and restricted roles).
4. Existing canonical protected-row/AAD/preroot and Secret-row modules according to their existing installation order; this candidate does not replace them.
5. Exact platform service identity/role membership and trusted installer/bus transport, then actual provider fixtures before activating provider readiness. No application LOGIN, password, production source or caller authority is created by step3.

Required local versions: audit Python3.12 with current requirements-audit and cryptography50.0.0; PostgreSQL18.6 on the existing isolated Unix socket55432; systemd257/busctl for the real provider. Candidate uses only stdlib plus existing canonical crypto helper; no new third-party dependency or gateway authentication mechanism is added.

Run bounded proofs:
```
/tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/key/verify_manager_adapter.py
/tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/key/verify_key_receipts_pg.py
/tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/key/review-stage/verify_named_stage.py
```
Use `bash -n audit/generated/resume-8cc/key/run_systemd_isolated_fixture.sh` here. Execute that script only in the disposable root systemd VM, never here or on production. Current audit outputs contain no plaintext credentials; temporary random reference key files are scoped to automatically removed TemporaryDirectory fixtures. No synthetic provider observation is promoted to actual systemd evidence.

Normative technical clauses for root review/integration: verified unique system-manager owner and exact active unit process; root-owned encrypted source receipt; immutable versioned key/source/invocation identity; exact retained-key reads; same-key global nonce producer order; no caller-supplied service/path/purpose/fingerprint/authorized flag; invocation/source absence is ENV_BLOCKED; no new owner step/provider; all desired/effective-head/rotation/actual role-identity fixtures stay before-generation requirements. The source/key registration and rotation producers are not declared fully verified by this bounded adapter.

## Independent OWNER value-read review

`review-owner-value/owner-value-read-tests.json` reproduces token lock → immutable version/nonce AAD → canonical byte opening/profile, OWNER-session-only API credential reveal and credential rotation race: 17 PASS in a separate PostgreSQL18.6 database. Five peer cases mutate a valid positive's context, nonce, owner, original-value digest or ciphertext digest. Sibling broker28 also passes.

The original physical crypto-profile misbinding counterexample is preserved in `profile-binding-counterexample/profile-binding-counterexample-before-fix.json`. No immutable trigger was disabled. The repaired SQL returns actual registry crypto-profile digest and exact profile bytes; both owner-read and sibling broker consumers compare them to their supported canonical profile before opening. `profile-binding-fix-proof.json` reruns the SAME physical counterexample and rejects precisely SECRET_KEY_CRYPTO_PROFILE_MISMATCH. Candidate repair is independently reproduced; root canonical integration/reproduction is a separate step. Actual systemd source and whole Secret remain unverified.
