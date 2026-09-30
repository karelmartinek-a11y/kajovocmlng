# Technical materialization for §§7.2/8.4/49.4/50.30/51.20

This proposal selects explicit technical primitive/codec details absent from the
current canonical resources. It does not claim the historical SSOT already named
AES or a verifier codec. Root reviews and authors it into effective normative
sections and embedded resources. No new OWNER authority, role, scope, expiry or
manual credential step is introduced.

## OWNER API verifier and acceptance

`KCML_OWNER_API_SHA256_V1:<64 lowercase hexadecimal SHA256 digits>` represents
SHA256 of the exact bearer-token bytes. The token is cryptographically random with
at least 256 bits of entropy (§7.2); fixture/new issuance may encode 32 random bytes
as unpadded Base64URL ASCII, but verification MUST NOT reinterpret existing token
bytes, trim, normalize, decode a guessed format or impose that issuance format on
legacy immutable values. Profile absence/mismatch is an explicit error, never a
fallback. Current fingerprint is the first16 lowercase SHA256 hexadecimal digits;
it is display/coherence data, not an authentication substitute.

The public gateway requires exactly one Authorization header with case-insensitive
Bearer scheme and RFC6750 token68 bytes; scheme case is transport syntax, while
token bytes are never normalized. Duplicate/header injection/wrong scheme fails
explicitly, without a silent alternate-auth fallback.

The effective gateway authorization-header transport ceiling MUST be consumed
from the actual server transport contract. This check precedes bounded SHA256 and
`hmac.compare_digest` of the complete32byte expected/actual digests. Fixture4096
is an isolated declared fixture transport limit, not a newly authorized product
limit. Unsupported/missing effective transport policy is BLOCKED.

The authentication service owns the live PostgreSQL command-acceptance transaction.
It reads platform/deployment heads FOR SHARE, current credential B3 FOR SHARE,
performs actual token verification without external I/O, then resolves the fixed
OWNER singleton and writes a fresh immutable receipt. No account FK, expiry,
permission lookup, scope, MFA policy for machine bearer or secret copy is added.
The same credential SHARE lock remains held until the complete command, queue,
event/audit/locator acceptance COMMIT; an authentication-only precommit followed by
an unlocked command transaction is prohibited. Rotation requires B3 FOR UPDATE.
Accepted pre-rotation commands retain their frozen authority; every new transport
request and replay authenticates current material again.

Receipt `authenticated_request_digest`, `authenticated_descriptor_digest` and
`api_credential_activation_epoch` bind exact server-decoded request bytes/digest,
frozen seven-field scope (including clientKeyDigest), and current API generation.
The descriptor is the actual pinned server contract descriptor, not a request's
authority declaration. One receipt creates at most one context (physical UNIQUE
on authentication_acceptance_id). Context insertion requires exact digest matches
and current API epoch; historical unbound receipts stay immutable/readable but
cannot authorize new contexts. OWNER session issuance retains its own existing
MFA/expiry/revocation/session-epoch contract and binds the same exact request and
descriptor fields after actual session verification. Existing expiration checks
are not removed. No receipt IDs or authenticated flags enter the public body.

Only canonical public OWNER gateway consumes Authorization. It strips bearer
material before internal dispatch (§16/50); body credential is a business input
and never caller authority. OWNER_SESSION/OWNER_API_KEY authentication channel and
UI/CHAT/API initiating surface must remain distinct projections of actual server
routing; a public request cannot invent internal, target or consumer purpose.
Current seven-field descriptor resolves operation and new-root target identity;
referenced target eligibility remains its own actual admission policy.

## Protected input technical profile

`KCML_PROTECTED_INPUT_AES256_GCM_V1` uses AES-256-GCM: exactly32key bytes,
12random nonce bytes and16authentication tag bytes appended to ciphertext.
The only production key source remains the root-owned encrypted systemd credential
source and exact-service read-only per-invocation materialization (§8.4/50.30).
No plaintext host-key file, new environment variable, null-key encryption,
manual user step or alternate production key provider is introduced.

A persisted server registry maps immutable keyID/generation to exact key
fingerprint, authorized service/purpose and existing credential source. Loading
checks actual effective invocation/credential generation/fingerprint against that
server authority. Registry absence, wrong invocation/service, unavailable key,
stale generation or wrong keyID fails closed. Rotation follows all §50.30 steps;
retained ciphertext loads its retained keyID and cannot silently use the current
key. Existing R17/bootstrap/recovery requirements still apply.

Nonce uniqueness is required globally per key across generation snapshots AND
Secret versions. A canonical immutable reservation registry must bind
(keyID,nonce) to exactly one protected object/purpose and ciphertext digest in the
same transaction as ciphertext persistence. Separate per-table uniqueness is
insufficient. Key registry also has UNIQUE(key fingerprint) so duplicate IDs cannot
reuse the same physical master-key bytes under separate nonce namespaces. A nonce collision aborts that candidate encryption/transaction;
plaintext is not published, the producer creates a fresh nonce before retry under
the same immutable command semantics. Duplicate retained object replay returns
original ciphertext/receipt, never reencrypts it.

AAD is exact UTF8 sorted compact JSON emitted by the versioned canonical profile:
`{"identity":<exact typed persisted metadata>,"keyId":<exact retained server keyID>,"profile":<actual profile object>,"purpose":<explicit purpose>}`.
Sorted compact means keys sorted lexicographically, no whitespace, UTF8 strings,
no nonfinite numbers, and no duplicate keys. Profile bytes and digest are pinned
from the actual embedded contract. No caller may substitute metadata/digest.

For GENERATION_INITIAL_REQUEST all fields are required/non-null: ownerId,jobId,
snapshotId,logicalOperationId,requestSchemaId,requestSchemaDigest,contentDigest,
trustedContextId,platformIncarnationId,applicationDeploymentEpoch,
executionDescriptorDigest,initiatingAccessChannel. IdentityUUIDs are canonical
UUID text; epoch is nonnegative integer; all digests are sha256:64lowerhex.
The protected plaintext is exact canonical native create-body bytes, validated
against the actual retained schema bytes and actual admission/consumer policy.
It is not the entire HTTP Authorization header or a model receipt.

For SECRET_IMMUTABLE_VERSION all fields are required: ownerId,secretId,
secretVersionId,secretType,representation,profileId,schemaId,schemaDigest,
plaintextByteLength,originalImportBytesDigest,canonicalValueDigest,trustedContextId,
logicalOperationId. RAW_UTF8/RAW_BINARY have profileId/schemaId/schemaDigest all
null; PROFILE_JSON_V1 has allthree exact retained non-null profile/schema values.
RAW_BINARY means decoded legacy BASE64 bytes, not guessed JSON or text. Typed
profile consumers additionally check their actual profile mask/semantics, exact
canonicalValueDigest, byte length and version selector. Encryption never rewrites
original sensitive bytes.

Read/hydration derives identity metadata from the actual joined protected row,
root, command binding and immutable trusted context. Verify exact algorithm,
profile digest/keyID/nonce lengths and authenticated AAD before interpreting bytes;
then check exact plaintext digest and actual native/profile consumer validation.
Wrong context/identity/key, corrupted nonce/ciphertext or swapped source yields an
explicit diagnostic without plaintext or cryptographic material in response,
event, audit or logs. No content-valid Boolean stands in for actual bytes.

Plaintext is scoped to authorized consumer work, never public create/error/event
receipts, logging, audit or persistent plaintext caches. Managed buffers are
cleared on success and every exception. The Python reference test clears its
managed bytearray but cannot assert erasure of temporary immutable decrypt/parser
copies or all runtime heaps. A generated production implementation must enforce
its applicable memory/lifetime policy and actual systemd invocation authority;
reference AES success is not evidence of that production service mechanism.
Existing explicit OWNER Secret reveal remains governed by its separate contract.
