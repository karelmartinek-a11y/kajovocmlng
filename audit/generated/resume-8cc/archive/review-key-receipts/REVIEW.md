# Independent source/key/invocation receipt review

Input HEAD 451b556067cb7cdd4f411cd742ab8fcaec8a379a; effective SSOT SHA-256 9e44b203d686ff1253133c5eb2a94ae0fc9234adafe71978fa3b437b4819363e, including the approved §8.3/§25.6 Secret-record status decision. Reviewed candidate SQL SHA-256 62e606be1d5e448503589a4c214e90e868e49eb4f9ed8520751ee55c605504a1 and helper SHA-256 8052550a13f38e2646a63d43f8ef10877a8528036f3b549b0cddfb0411a0b212.

## Actual reproduced and independently added evidence

`verify_peer_key_receipts.py` independently reproduces all 21 current author PostgreSQL assertions in a separate PostgreSQL18.6 database. It then adds 12 assertions using the established valid receipt. The narrow source-installer and invocation-publisher roles actually COMMIT source/key/invocation records; a fresh connection reads the exact matching key generation, service, source digest and key fingerprint. Valid source identity is required by both physical FKs; a changed source digest and a source bound to an unknown key reject. Empty, null-containing and multidimensional purpose lists reject the exact purpose-mask constraint. Re-inserting a changed receipt with the original invocation ID cannot overwrite its immutable primary-key record. The installer cannot publish invocation receipts, the publisher cannot register source rows, and the authentication writer cannot publish invocation receipts. Updating retained source metadata rejects immutability. The positive remains the only committed chain after negative rollback cases.

The explicit busctl address is independently exercised with a synthetic subprocess response while inherited `DBUS_SYSTEM_BUS_ADDRESS` points elsewhere. The actual argv retains `--address=unix:path=/run/dbus/system_bus_socket`; no inherited path is passed. This is a command construction reference test, not a trusted-bus provider observation.

`reproduce_manager_reference.py` reexecutes the current 28 reference assertions without writing author evidence. The earlier 27 count is historical; the exact socket-address fixture added coverage. These exercise strict typed replies, unique manager identity, exact active service and invocation continuity, receipt/key/profile/purpose checks, actual non-root source-installer denial and a real temporary read-only 32-byte key through an explicitly adapted fixture path. The module accepts no arbitrary observer callback; the static observer's unit/property calls target the established unique owner. Original author inputs/reports are preserved.

## Actual provider remains unavailable

An unpatched fresh `SystemdManagerObserver().observe()` invocation returns `SYSTEMD_MANAGER_NOT_PID1` in this environment. This remains `ENV_BLOCKED`. No root-owned encrypted systemd source, real manager bus owner, LoadCredentialEncrypted materialization or source-provider success was inferred from SQL rows, a filesystem fingerprint, temporary key bytes or patched manager replies.

## Exact unresolved producer/installation conditions

1. `SHARED.CRYPTO.SYSTEMD_SOURCE`: root installer must create and retain the actual canonical encrypted source, execute `source_installation_metadata` against the server-selected path, and persist its metadata through the restricted installer transport. The reviewed helper computes the metadata but does not itself implement that root installer→database publication transport. A trusted SQL bootstrap inserting synthetic metadata is not that producer.
2. `SHARED.CRYPTO.KEY_INVOCATION` / `GENERATION_KEY_MANAGER_PRODUCER`: real exact platform service invocation must execute the fixed-socket observer and database publisher while reading its actual read-only credential directory. Exact platform LOGIN/group membership/IPC/service-role installation is intentionally absent, not silently assumed from NOLOGIN role creation. Those actual provider/permission fixtures remain required before readiness.
3. `KEY_ROTATION_RETAINED_GENERATION_USE`: authoritative desired/effective heads, activation confirmation, dependent smoke and retained encrypted credential manifest must connect to the historical key reader. A caller `retiredForEncryption` member of a trusted internal receipt is not by itself the missing persisted rotation producer. No new retirement vocabulary, owner step, key mechanism or current-key fallback was introduced by review.
4. `SHARED.CRYPTO.GLOBAL_NONCE`: this extension supplies source and invocation identities, not the joined protected-row/nonce producer transaction. Existing generation/Secret typed metadata, invocation-selected key, reserved nonce and ciphertext authentication still require their own connected proof.

These are technical/provider obligations, not requests to reopen approved Secret product rules and not future application acceptance substitutes. No whole operation is closed. SQL FKs/immutability/typed-purpose/narrow-role boundary can be integrated after canonical-byte reproduction; the whole source→actual invocation producer cannot be marked VERIFIED here.

## Reproduction

```
PGOPTIONS='-c client_min_messages=warning' /tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/archive/review-key-receipts/verify_peer_key_receipts.py
/tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/archive/review-key-receipts/reproduce_manager_reference.py
```

Outputs bind the actual source and candidate SQL/helper hashes. They consume canonical foundation/crypto SQL plus unchanged candidate receipt SQL. Coordinator must rerun using an asserted exact embedded canonical receipt module after integration; candidate evidence must not be relabeled current canonical evidence without execution. No author/shared/canonical/Git file was changed by this independent review.
