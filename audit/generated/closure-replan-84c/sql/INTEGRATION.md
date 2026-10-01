# Scoped four-helper definition package (not dispatch activation)

Pinned initial input: `84c41ba`, SSOT `2577dacf6024e4666ba98b11eb9c7ffa6e7f225e60630697db740129615cc536`. The fresh reference proof consumed current SSOT `8fe5e74f10197a45e55053d50f8fc0b4340d84d8d59dba706af90d080168cb6c`; the exact operation wrapper resource remained unchanged. Current registry bindings are regenerated independently from the current source, rather than relabelling historical evidence.

The exact two existing embedded wrappers `ownerApiKey.read` and `ownerApiKey.reveal` execute all four original helper calls against actual canonical OWNER/API credential and Secret root/version rows in PostgreSQL 18.6 UTF8. `owner-query-helpers.sql` supplies the four missing definitions, a UUID-domain context handle and two narrowly scoped private functions. It does not interpret generic fieldUpdatePlan strings or arbitrary model JSON. The exact decoded static plans are checked in full before explicit physical projections. All 260 other wrapper operations fail closed with `SQL_OPERATION_TYPED_HANDLER_UNRESOLVED`.

## Authoritative interpretation and applicable callsites

- §7.2: verified OWNER session or reserved current OWNER API key yields the same constant OWNER_FULL; every OWNER catalog operation is available. Dedicated `ownerApiKey.reveal` therefore supports both mechanisms. The earlier SESSION-only proposed rule was a source-scope defect and was removed. The canonical general Secret API value reader's reserved-key rejection is a different route and remains unchanged.
- §25.3: the concrete source columns are `owner_identity`, `owner_session`, and `owner_api_credential`; the reserved singleton points at the canonical immutable Secret version, not a caller-supplied target.
- §§7.2/8.5/51.20: OWNER reveal remains explicit, and response-loss must permit subsequent reveal; it must not expose verifier hashes. Returning internal encrypted hydration input is not the public reveal result.
- §51.2: CONSISTENT_READ is REPEATABLE READ READ ONLY, with the 3000ms lock, 60s statement and 60s idle-in-transaction settings. No mutation/E-root FOR UPDATE is inserted into this read profile. Current authority, credential, and session state are verified in the same snapshot. This bounded proposal does not redefine mutating lock ordinals.
- §51.2: pool state must be reset and no previous-request TEMP authority may be reused. The candidate fresh private TEMP relation is owned by `kcml_authentication_writer`, checked by owner OID, backend PID and actual xid; its creation happens before entering READ ONLY because PostgreSQL correctly forbids CREATE TABLE inside that transaction. It is explicitly dropped after the request. The live runtime ownership, TEMP/SET ROLE capability and trusted verifier service integration remain unactivated prerequisites, not proven session authorization deployment.

`operation-helper-callsite-registry.json` covers exactly 262 wrappers / 1,048 mandatory calls in the current embedded resource. Each row contains its operation ID, physical function, descriptor, source line, four helper names and literal arguments, typed handler status, dispatch status and missing IDs. This is not a list of every SSOT operation. Its overall status MUST remain BLOCKED: two reference-implemented wrappers have shared dispatch prerequisites, and 260 have no typed implementation. Definition presence is a distinct fact from callsite coverage and must not make verify_operation_sql_literals PASS for executable closure.

## Proposed resource installation

Coordinator may embed `owner-query-helpers.sql` as `database/operation-helper-owner-query.sql` with applicability limited to these two IDs. Do not silently activate its SESSION verifier profile or connect it as a public dispatcher. Keep `database/operation-functions.sql` wrapper bytes/literals unchanged. `owner-query-original-wrappers.sql` is the extracted reference subset, not a replacement of all 262 functions.

Prerequisites: canonical core roots/platform/deployment, OWNER auth tables/roles, canonical Secret roots/version/status/owner-binding and reserved credential-to-Secret FK constraints, plus their actual data authorities. The standalone fixture uses `native_auth_factory.Factory` and `credential_root_fixture.install_current_credential_secret` only to install those unchanged embedded resources and valid isolated data in its own database. The fixture issuer deliberately seeds a synthetic session and isolated cryptographic material; it does not prove login/MFA/API exchange or root-owned systemd key source.

For reference reproduction:

```
/tmp/ssot-audit-venv/bin/python audit/generated/closure-replan-84c/sql/verify_owner_query_family_pg.py
```

It uses only `helper_owner_queries_utf8_84c`, requiring PostgreSQL 18.6 socket `/tmp/kcml-pg18-socket`, port 55432. The helper SQL revokes PUBLIC EXECUTE. Original wrapper bytes contain no REVOKE; install `owner-query-install-acl.sql` after the helpers and wrappers in the same privileged installation transaction, before any runtime grant. Its exact two REVOKEs match the independently verified fixture sequence; fixture migration privilege is not a runtime grant recipe. Preserve the existing canonical authority checks. An independent reviewer must use a separate database/output directory.

## Results and remaining exact IDs

`owner-query-postgres-proof.json`: ten actual tests PASS on PostgreSQL 18.6 UTF8. Two SESSION positive wrappers, actual API metadata and dedicated reveal positives, unknown context, wrong raw session/API bytes, operation/descriptor substitution, exact-plan extra field and persisted session revocation. Every negative is derived from a valid positive context and requires its exact diagnostic. Earlier failures from hardcoded wrong session epoch, SQL_ASCII Unicode JSON cast, and CREATE TEMP in READ ONLY were invocation/environment/design defects, not successful negative contract proofs.

- `SQL.OWNER_QUERY.TRUSTED_ISSUER`: actual interactive/MFA/API-exchange session issuer, precise verifier profile, gateway extraction and transport ceiling authority; no model auth flag accepted. The API reference verifier uses exact raw bytes, the effective verifier hash profile, constant-time digest comparison, current fingerprint and reserved physical root. It introduces no numeric token-size limit. The separate genuine gateway extraction/transport-policy producer remains required before deployment.
- `SQL.OWNER_QUERY.RUNTIME_CAPABILITY`: least-privileged trusted service/role grants, fresh private context lifecycle and pool reset; no user-created TEMP row may produce authority.
- `SQL.OWNER_QUERY.AUDIT_HYDRATION`: request/read attribution, authenticated canonical key/nonce hydration and exact public OWNER reveal result/consumer. No plaintext, verifier, token or cookie appears in reports. Internal encrypted fields must not be exported as the public response.
- `SQL.TYPED_HANDLER.<operationId>`: each of the remaining 260 wrappers requires its own physical domain implementation and source-specific plan; four definition names cannot satisfy these callsites.

Design-stage definitions and parser/static literal evidence are available. Scoped PostgreSQL reference execution is available. Runtime service acceptance and whole OWNER query operation closure are NOT verified. No create operation is closed by this package and no product choice is needed to correct dedicated reveal's channel scope.
