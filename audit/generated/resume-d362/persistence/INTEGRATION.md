# generation.job.create physical roots and trusted context

Input: `d362487999bd795d4723c2a930e93fc7aa8aa295`, canonical SHA256
`22256baa17729b7577ca4e2498b74b7dfc2b3e6bab57f3b88c338a059557a0ee`.
No Git operations, canonical SSOT/projection/checkpoint writes or recursive agents.

## Candidate technical materializations

- `generation-root-proposed.sql`: all 17 §25.11 field groups projected into 39
  actual columns; exact own 11 lifecycle states and 15 producer target kinds.
  Immutable request/OWNER/context/kind/target identity, exact state-version
  increment, server counters and deferred `(job_id,snapshot_id,content_digest)`
  FK bind retained request bytes to the root. Source-authority inventory is
  `generation-root-field-authorities.json`. This does not close the external
  child/target FK or current-phase mapping dependencies.
- `trusted-generation-context-proposed.sql`: immutable server authentication
  acceptance and a constructor that uses actual persisted OWNER session/API
  credential data, current incarnation/deployment heads and exact stored
  descriptor bytes. Session epoch, ownership, lookup digest, revoke and expiry
  are checked. API credential version and fingerprint are checked; no API MFA
  requirement, artificial credential expiry, business role or scope is added.
- `generation-context-role-bindings.sql`: infrastructure NOLOGIN groups. Only
  authentication writer inserts authentication acceptance; domain writer has
  EXECUTE on the reviewed constructor, cannot directly forge context/receipt or
  assume builder role. Builder reads only needed metadata columns, cannot LOGIN.
  Controlled installation schema is captured; `pg_temp` explicitly LAST prevents
  relation shadowing in SECURITY DEFINER. PUBLIC EXECUTE and schema CREATE revoked.
- `generation-root-context-bindings.sql`: deferred root/context/OWNER/channel FK.

The authentication acceptance writer must verify actual token material using the
canonical authentication service and completed interactive-auth/session issuance
contract (including its required MFA when applicable). An INSERT grant does not
prove that verifier. There is no `authenticated = true` shortcut. The isolated
fixture tables deliberately contain only the source-owned columns required by
these guards, not counterfeit complete production authentication roots.

## Actual isolated PostgreSQL proof

Downloaded official PostgreSQL `REL_18_6` source via the allowed codeload host,
built and installed exclusively under `/tmp`. Debian build tools extracted under
`/tmp`; no host package installation. Actual server reports **18.6** and listens
only on a private Unix socket, with TCP disabled. Source/package checksums and
configuration are in `postgres-fixture-environment.json`.

- `verify_postgres_root.py`: **24 PASS / 0 FAIL**, actual PostgreSQL constraints,
  deferred digest/identity joins, immutable metadata, CAS counter step, malformed
  enum/type-null cases, replay duplicate and failed-COMMIT rollback. Root/snapshot
  witnesses start from typed valid synthetic domain input. Ciphertext is an opaque
  synthetic SQL carrier: this is not a cryptographic proof.
- `verify_postgres_context.py`: **24 PASS / 0 FAIL**, actual current session/API
  record checks, controlled caller EXECUTE, direct row forgery denial, builder
  role denial and temporary relation forgery denial. Authentication token verifier
  and generated application acceptance are explicitly not claimed.
- `combined_foundations.py` exports dependency-ordered exact candidate SQL for the
  event agent's separate fresh PUBLIC-schema combined fixture. The event agent
  owns domain_command, idempotency, event/outbox/audit and command consistency.

Fixture connection:
`/tmp/kcml-pg18/bin/psql -h /tmp/kcml-pg18-socket -p 55432 -d postgres`.
Use a separate schema/database. The existing server is synthetic and disposable.

## Remaining mandatory design/fixture dependencies

A. Before generation: exact descriptor mask and immutable contract-pin registry
binding; complete canonical authentication/entity/child/target DDL and infrastructure
login-role installation; current-phase own dictionary and same-job child FKs;
protected input crypto algorithm/nonce/AAD profile bound to §8.4/§50.30; own
UPDATE/RETRY/REPAIR selectors/admission; event/outbox/audit full transaction bridge.
Do not mark all-root/context readiness from these primitive proofs.

B. Design/reference proof: all above exact masks, pointers, transitions, joins,
role/ACL and PostgreSQL18.6 fixture guards can be tested before an application
exists. Required fixture evidence is not deferred to future application acceptance.

C. Future implementation: deployed canonical authentication token verifier and
session issuance, real service-login grants/pool reset, systemd master-key material,
generated UI/provider/browser/model execution. `IMPLEMENTATION_PRODUCTION_ACCEPTANCE`
remains `NOT_EVALUATED`. The whole operation remains OPEN; there is no new product
question identified in this persistence scope.

## Physical singleton correction

Independent event review identified §51.11 precedence over symbolic §25.3 labels.
Physical column `singleton_key` is SMALLINT, DEFAULT1, NOTNULL, UNIQUE/CHECK=1.
OWNER/OWNER_API are logical identifiers, not stored text-key variants. Constructor
uses integer1 for owner/API/platform/deployment heads. Four valid-witness mutations
key1→key2 are rejected specifically by PG18.6 CHECK (SQLSTATE23514).
Both root24 and context24 tests reran against current canonical SHA256 9bf5510b189ef4f71216d56bf293599ac129d200ec92e90ff7c2c22f6b15e57b.

## Follow-on: source pin and complete needed authentication storage

Input HEAD `6ac0e89921ad73e1dae7054ef78d0d4880c67e60`, canonical source
`9bf5510b189ef4f71216d56bf293599ac129d200ec92e90ff7c2c22f6b15e57b`.

`authentication-roots-proposed.sql` now supplies complete needed source-owned
OWNER/session/API columns and platform/deployment heads (56 columns). It uses
actual citext1.8 storage plus exact COLLATE C username CHECK, fixed singleton
identity/DELETE guards, server state/counter/epoch defaults and no business roles.
`authentication-root-field-authorities.json` documents the field meanings and
explicitly distinguishes an opaque stored verifier encoding from its still-required
verifier codec/profile. Metadata text is literal descriptive/projection text, not
JSON hidden in a string and never authority.

`generation_descriptor_registry.py` freezes a single actual canonical-source
snapshot, selects native generation.job.create operation/revision and route/body
by operationId, and produces exact registry bytes/hashes. The persisted deployment-
epoch pin stores those actual consumed contract/route/domain-schema bytes, with
DB digest/record consistency CHECKs. It cannot be installed by a domain writer.
The seven-field descriptor matches the existing frozen replay scope; constructor
validates exact registry revision, fixedOWNER identity, operation/root/caller
semantics and exact canonical UTF8 bytes. Arbitrary matching caller digest, extra
field, different revision, duplicate keys, invalidUTF8/JSON and noncanonical bytes
are rejected. Context has a composite FK to the actual epoch+contract-digest pin.
`generation-snapshot-pin-links.sql` additionally binds snapshot schema ID/digest to
that context's retained actual domain schema (must be included in combined proof).

Updated actual PostgreSQL18.6 proofs:

- `postgres-context-proof.json`: **46 PASS**, full needed auth DDL, actual native
  contract-pin fixture, restricted producer ACLs and exact descriptor validators.
- `owner-api-secret-links-proof.json`: **6 PASS**, full actual Secret candidate DDL
  joined to reserved OWNER API credential using deferred same-secret/version FK
  and stable-name/currentACTIVE/fingerprint guards. Valid witness performs lawful
  CREATED→ACTIVE transition, not a forbidden ACTIVE insert. Opaque ciphertext and
  open Secret record-status/creator-context are explicitly outside this proof.
- `postgres-extension-proof.json`: **7 PASS**, actual pgcrypto1.4 +citext1.8,
  SHA256/HMAC known answers and synthetic bcrypt positive/negative. Fixture cost4
  is not a production password profile. These are extension primitive checks,
  not canonical authenticated-encryption/master-key or wholeR17 PASS.

`context_fixture_exports.py` provides read-only valid full-auth insert templates,
actual pin insertion and exact descriptor/context call to independent reviewers.
`combined_foundations.py` now includes full auth roots, pin table and snapshot pin
joins; downstream combined proofs must refresh their old generic descriptor and
request-schema digest fixtures rather than weaken the new validator.

§51.20 explicitly requires bounded constant-time API material verification under
B3 credential FOR SHARE in the same command-acceptance transaction. Receipt plus
version/fingerprint recheck is not claimed as a complete substitute. The canonical
verifier codec/profile, actual token/MFA session issuance and full acceptance
transaction bridge remain explicit obligations. Actual deployed verifier/service
is future implementation acceptance; its exact design and mandatory crypto/SQL
fixture are pre-generation requirements. No application-generation cycle is added.
