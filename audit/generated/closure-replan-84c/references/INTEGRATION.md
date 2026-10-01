# MCP resources/read + prompts/get native reference package

This package resolves exactly four pre-existing absent operation-schema identities. It does not close two operations, their event applicability, or the MCP runtime pipeline.

## Exact authority and consumed boundaries

Both operations are already PUBLIC_PROTOCOL operations in `contracts/operation-contracts.json`. Their request/response references are absent; native revision 2026-07-28 is already vendored inside the same document under `$defs/mcp.native.2026-07-28` and independently pinned by `contracts/mcp-native-schema-artifact.json`.

`source-provenance.json` records exact native field pointers and §10.3, §10.4, §10.10, §10.11, §10.14, §10.16.1 text/line/hash evidence. No similarly named entity or HTTP platform operation envelope is substituted for a native JSON-RPC message. No native artifact bytes change.

The authored command aliases select exact GetPromptRequest / ReadResourceRequest. They bind method, request ID and native params. Unknown command/params members are rejected; bounded untrusted vendor extensions remain confined to native `_meta`. Prompt arguments retain their exact native string-map representation, and a separate declared immutable prompt revision schema must reject missing/unknown arguments; they are not arbitrary trusted domain authority.

Responses distinguish complete, input_required, and JSON-RPC error. A complete resource read contains the mandatory native contents/cacheScope/ttlMs fields. The native complete prompt result contains messages. Native complete and input_required result `_meta` is optional for both methods, with its native type checked whenever present. §10.14 platform-rendered completion requires diagnostic server identity metadata; this producer specialization is supplied separately, remains UNBOUND for integration review, and does not strengthen optional serverInfo in raw external-native replies. MRTR is retained for both methods under §10.11, including at least one of inputRequests/requestState. Task responses are rejected for these methods because §10.16.1 restricts task augmentation to tools/call. Cross-message ID identity uses exact JSON type/value; schema validation alone cannot establish it.

Server/client self-reported metadata is diagnostic and never credential, routing or identity authority. Fixtures without serverInfo do not claim a valid deployed server-identity publisher or client capability negotiation.

## Coordinator integration

1. Preserve concurrent changes. Import `author_native_read_refs.apply(current_text)` to author canonical resource bytes. Preconditions bind the exact selected native artifact and two operation records, not unrelated catalog records. Identical publication is idempotent; incompatible aliases or selected source changes fail closed. The exact prior published alias content and digest authorize the narrow optional-metadata correction. Standalone authoring writes only a temporary patched resource in this audit directory; `--check` checks publication and cannot silently overwrite a changed mask.
2. Integrate the reusable `native_byte_format.py` checker in the audit schema-format entrypoint. The normal audit environment lacks native MCP `format=byte`; without registration, the inventory correctly reports UNAVAILABLE_FORMAT_CHECKER. The checker validates native RFC4648 base64 bytes without trimming or decode/re-encode normalization. Preserve the native format assertion. This is a reproduced checker availability issue exposed by additional schema coverage, not a new business contract defect.
3. Run `verify_native_read_refs.py` (78 reference checks) and `verify_authoring.py` (6 exact consumption/publication checks). `verify_inventory_delta.py` confirms the four aliases and nested references in the real Inventory resolver, using the checker. Before/after unresolved references are 242 → 238 for the pinned 242-reference universe. Generic routes/masks and event applicability counts are unchanged by this package.
4. Obtain independent review on the integrated canonical aliases and format checker. Refresh proofs against consumed selected sources; do not relabel historical whole-SSOT hashes.

## Explicit limitations and remaining IDs

No semantic operation closure is asserted. The following existing boundaries remain OPEN:

- `MCP.READ.TRANSPORT_ACCESS`: HTTP singleton routing headers/body binding, authenticated exact source/access context and request capabilities; §10.3–10.4.
- `MCP.READ.REVISION_CONSUMPTION`: actual immutable prompt argument contract publisher; resource access/URI/MIME contract and content hydration; §10.14.
- `MCP.READ.MRTR_PERSISTENCE`: protected persistent exchange, actual continuation authority, capability-specific input requests, atomic consume/resume and replay; §10.11.
- `MCP.READ.LIFECYCLE_ATOMICITY`: operation/root/event/outbox/audit and reconciliation according to each existing operation record; §49.13.1 and its own catalog authority.
- `MCP.READ.CONSUMER_ACCEPTANCE`: future generated-runtime renderer/resource consumer, no live external APIs or accounts used.

These labels describe existing authoritative boundaries, not proposed additional architecture. The original audit-event list (OPERATION_ADMITTED, OPERATION_STATE_CHANGED, OPERATION_TERMINAL) is preserved. No event is marked NOT_APPLICABLE just to reduce blockers.

The prompt revision schema/digest example is synthetic, precisely labelled reference validation. Base64 decoder, actual duplicate-key JSON decoder, exact-ID guard and real scoped Inventory resolver are exercised. They are not an access registry publisher, runtime broker, MRTR cryptographic state, external MCP server, or complete operation evidence.

`unresolved-family-packages.json` groups all 242 existing missing references into actual operation-catalog families with operation pointers and authority references. Its inventory is not a semantic review of those remaining families.
