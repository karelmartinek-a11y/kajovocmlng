# Secret profiles: approved limited choices and remaining technical activation

OWNER approved the ten named limited profiles in this continuation. This is no longer a pending product-format question. The approval does not make whole types universal, authorize arbitrary bounds, activate unchecked masks or remove mandatory browser capabilities.

| Choice | Approved profile | Impact | Remaining mandatory work |
|---|---|---|---|
| OAuth client/token | OAUTH_CLIENT_SECRET_V1 / OAUTH_BEARER_TOKEN_SET_V1 | Exact declared consumer, endpoint/client/scopes compared against authoritative binding; candidate import differs from use | Current request migration and real declared consumer/refresh/trust joins |
| TOTP / DB | TOTP_BASE32_V1 / DATABASE_USER_PASSWORD_V1 | Exact sensitive values, no unsupported normalization; consumer owns security/endpoint/algorithm policy | Current import/storage/use projections and source-bound consumers |
| Certificate / key / SSH | X509_PEM_CHAIN_V1 / PKCS8_PEM_PRIVATE_KEY_V1 / SSH_PASSWORD_V1 / SSH_OPENSSH_PRIVATE_KEY_V1 | Limited import profiles, not blanket exclusion of required other consumer formats | Exact supported algorithms and crypto/broker physical joins |
| Cookies / browser | HTTP_COOKIE_JAR_V1 / BROWSER_COOKIE_LOCAL_STORAGE_V1 | Partial declared profiles only; §13.15 remains fully mandatory | Additional BROWSER_AUTH_STATE_GRAPH_V1 exact engine/serializer/bridge/signature fixtures, retained account/tenant/epoch/CAS postconditions |

The technically authorized additional browser profile is NOT_ACTIVATED; it is required scope, not an optional future extension. No new unresolved owner choice was established in this bounded review. Missing concrete consumer policies and implementation-independent fixtures are technical blockers and must be completed independently.

Current exact candidates: `generated/resume-d362/secrets/norm-8.12.md`, `secret-profile-handoffs.schema.json`, `conversion-table.json`, `profile_reference.py` and `secret-profile-roots.sql`. Their synthetic parser and actual PostgreSQL18.6 evidence is bounded; the current create/import route must still be migrated atomically with the effective masks and authoring scripts before activation. No content guessing from legacy RAW values is permitted. Inactive root metadata edits preserve immutable historical version type; ACTIVE pointer must match ID/type/version.

Required before generation: effective import masks, exact byte conversion/pinned schemas, physical authority/transaction/consumer declarations and explicitly required PostgreSQL/crypto/browser fixtures. Reference checks now: parsing, meaningful compiled schema digest, original versus typed canonical digest, exact synthetic encrypted load identity, unsupported profile rejection and named SQL constraints. Future generated-application acceptance: live deployment vault/broker/adapter/browser behavior. Reference AES-GCM does not satisfy the canonical systemd/master-key/R17 fixture requirement and is not a cipher selection.

Create/import output and events never echo sensitive values. Explicit OWNER reveal/copy/export continues under its own §§8.5/8.6.1/8.8 contract. All fixtures use synthetic data. Ten approved names alone do not confer VERIFIED on a whole operation.
