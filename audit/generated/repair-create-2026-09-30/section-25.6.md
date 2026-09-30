### 25.6 Secret entities

#### `secret_record`

- ID, stable name, display name, description, type
- purpose kind a volitelný target object ID
- status
- active version ID a secret activation epoch
- `state_version`
- tags/group/metadata
- expiry/rotation policy
- latest rotation logical operation a outcome digest
- created/updated/deleted

Stable name je unique a nerecykluje se přes soft delete. Active version pointer, secret activation epoch, state version, dependent invalidation outbox a audit se mění v jedné transakci.

#### `secret_version`

- secret ID, immutable version number
- ciphertext, nonce, algorithm, key ID
- fingerprint a canonical value digest podle typu
- lifecycle `CREATED`, `ACTIVE`, `RETIRED`
- created/activated/retired
- creator a activation logical operation

Unique `(secret_id, version_number)` a immutable ciphertext brání ABA. V jednom secretu existuje nejvýše jedna `ACTIVE` verze.

#### `secret_binding`

- secret ID a exact source object/revision
- exact usage purpose a volitelný target/account relation
- version selector a resolved-version policy
- binding revision, state version a binding digest
- activation set a activation epoch
- lifecycle, expiry a invalidation policy
- created/retired/audit metadata

Wildcard source a all-secrets binding nejsou přípustné. Active binding je unique v exact source/target/purpose scope. Rotation nemění binding revision, pokud se nemění contract; mění resolved secret epoch a invaliduje závislý session/cache stav podle policy.

#### `secret_resolution`

- source execution context a logical operation
- secret/binding ID, binding revision a binding digest
- requested stable name/purpose/target
- resolved exact secret version a secret activation epoch
- source/target revision a activation epoch snapshot
- state `RESERVED`, `RESOLVED`, `REJECTED`, `EXPIRED`
- result fingerprint, created/expires/consumed timestamps
- correlation a audit event

Runtime používá pouze `RESOLVED` záznam odpovídající current execution snapshotu. Retry stejné logical operation nemůže potichu přejít na jinou secret version uprostřed jednoho side effectu.

#### `secret_access_event`

- secret/version/source execution context/binding
- purpose, operation, correlation
- success, timestamp, runtime/job/run

