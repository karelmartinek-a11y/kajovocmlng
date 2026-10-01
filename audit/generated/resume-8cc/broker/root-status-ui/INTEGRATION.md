# Exact root status/detail/value UI handoff

Input is the coordinator's integrated canonical Secret read/status modules (report consumed digests are authoritative). No shared files or Git changed here.

Integrate these candidates together:

1. `secret-owner-api-value-read.sql`: additive internal `recordMetadata` (all existing physical root columns) and `recordStatus`; protected value authority also includes exact `recordStateVersion`. Existing fresh OWNER verifier and held finite root locks remain mandatory. No grants added. Metadata snapshot does not contain plaintext.
2. `secret_value_read_transport.py` + `secret-value-read.schema.json`: successful value responses require server-derived `recordStatus` INACTIVE/ACTIVE and canonical string `recordStateVersion`. DELETED value is forbidden even with explicit historical version. Type enum corrected against exact physical root: BEARER_TOKEN and WEBHOOK_SECRET preserved, previously unsupported TOKEN removed. This is a physical contract correction, not a new Secret capability.
3. `secret_metadata_status_read.py` + `secret-metadata-read.schema.json`: exact GET /secrets/{id}, no body/query, same existing OWNER_FULL permission. Actual fresh bearer verification precedes metadata or status diagnostics. Metadata can show INACTIVE/ACTIVE/DELETED roots; missing active version or unavailable encrypted value does not prevent reading valid metadata. Precise root pointer/projection integrity errors remain failures. No root status authorizes a caller.
4. UI `hydrate_status_ui` binds the status feed to the exact same root/stateVersion as any displayed immutable value response. Selected version lifecycle is not inferred as root status. Current activation pointer and revealed version are distinct; an inactive RETIRED version may be inspected without reactivation. COPY retains previously verified original bytes.

Evidence: actual PostgreSQL18.6 owner/auth/crypto/status/read chain20, metadata/UI binding16, typed value transport55. Parent baseline broadbroker29 executes only to seed private fixture; it is not a required runtime module or a canonical broker proof. Wrong source root, stale stateVersion, wrong status, DELETED value, ACTIVE+wrong bearer, status-body/caller/query injection and version vocabulary substitution are rejected specifically. First attempted run loaded the old canonical transport helper due to fixture sys.path precedence; invocation was corrected, not counted as a contract failure or PASS.

## Authority and preserved scope

- §8.3 root UUID/stable/display/description/type/purpose/target/tags/group/URL/username/notes/status/active pointer/state lock/timestamps/expiry inventory.
- §25.6 state_version and secret_activation_epoch, derived root status and immutable CREATED/ACTIVE/RETIRED versions.
- §72.21 required Secret detail, value/reveal and versions panels; UI registry page13 actions1/2 reveal/copy, exact status is a read-only server feed.

The metadata schema preserves every actual physical root field. It does not silently remove other normative fields absent from the current physical root. Explicit OPEN dependencies: SECRET.METADATA.ROTATION_POLICY_STORAGE; SECRET.METADATA.EXACT_BINDINGS_READ; SECRET.METADATA.USAGE_HISTORY_READ; SECRET.METADATA.AUDIT_HISTORY_READ. Metadata errors/global audit/access producers, OWNER-session authority, full generated UI/backend and visual review remain separate; no rerender was performed and whole UI/operation closure is not claimed. Root status is display metadata, not runtime Secret eligibility, authorization, target/purpose or expiry authority.

Tests run sequentially on own `secret_broker_8cc`; they reset only this fixture DB. Keys/tokens are synthetic, no systemd credential proof, live API or generated application.

`ui-status-proposal.json` adds the missing readonly SERVER_PROJECTION field `secret.status` to registry page13 and §72.21 displayed fields, preserving all existing fields/actions. Uses existing readonly type/TEXT_1 shape; not a required OWNER create input. The public read response status remains mandatory.
