### 25.3 Fixed OWNER authentication entities

#### `owner_identity`

- `id`
- `singleton_key = OWNER`, primary/unique a check constraint
- `username = KRMAR78`, citext unique a check constraint
- `password_hash`
- `password_changed_at`
- `mfa_enabled`
- `mfa_secret_ciphertext`
- `deployment_managed`
- `session_epoch`
- `created_at`, `updated_at`
- `password_source = GITHUB_ACTIONS_PASS`

Tabulka neobsahuje role, status, ownership, permission ani soft-delete. Constraint dovoluje nejvýše jeden řádek; bootstrap a readiness gate vyžadují právě jeden.

#### `owner_session`

- `id`, `owner_identity_id`
- `lookup_digest`, `session_hash`
- `created_at`, `last_seen_at`, `expires_at`, `revoked_at`
- `reauthenticated_at`
- `session_epoch`
- device/IP/user-agent metadata

#### `owner_login_throttle`

- attempt key digest
- failure count
- first/last failure
- locked until

#### `owner_recovery_code`

- owner identity ID
- code hash
- created/consumed timestamps

#### `owner_mfa_enrollment`

- owner identity ID
- enrollment token digest
- encrypted seed
- expiresAt
- verifiedAt

#### `owner_api_credential`

- `singleton_key = OWNER_API`, primary/unique a check constraint
- `secret_id` a `secret_version_id` pro stable name `KCML_OWNER_API_KEY`
- `verifier_hash`, `fingerprint`, `credential_version`
- `state_version` a credential activation epoch
- poslední rotate logical operation a outcome digest
- `created_at`, `rotated_at`, `last_used_at`
- `last_usage_metadata`, `audit_correlation_id`

Existuje právě jeden řádek a jedna active Secret version. Tabulka neobsahuje account relation, principal, role, scope, label, expiry ani collection lifecycle. Rotace pod singleton row lockem a expected state version atomicky nahradí active Secret version, verifier, credential version a epoch; předchozí klíč přestane platit v témže commitu. Retry stejné rotate logical operation vrací stejný canonical outcome.

