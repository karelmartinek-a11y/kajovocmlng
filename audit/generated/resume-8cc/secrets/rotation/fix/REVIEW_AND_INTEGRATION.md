# Corrected bounded OWNER rotation projection

The parent `rotation/` candidate and its 49 author tests remain historical: independent PostgreSQL review found five real deferred-closure substitutions that committed. They must not be reported as verified.

This additive correction binds event type `OPERATION_TERMINAL`, aggregate kind `SECRET_RECORD`, authoritative operation-specific event schema identity and the exact compiled projection digest. It additionally binds event canonical payload bytes/hash to the exact closed response receipt and reconstructs the canonical audit bytes, including after-image digest, from that receipt and the transaction's authoritative identities. Existing semantic-result recomputation remains required. No `jsonb::text` serializer or arbitrary hash equality substitutes for the canonical encoder.

The operation-specific event projection is proposed for coordinator integration: derive it from the effective ownerApiKey.rotate event schema, preserve its closed envelope/operation/route identity, substitute the exact response payload and restrict eventType to TERMINAL. This does not silently claim that the old generic projection already accepts the new event. `source-projection-bindings.json` records compilation input; the independent peer rebuilt it from final source 2577dacf and found byte-equivalent compiled schema despite unrelated full payload-catalog changes.

Actual isolated PostgreSQL 18.6: corrected baseline 49 PASS; own 11 corrective regressions PASS. Independent archive peer reproduced baseline 49 and 11 independent tests PASS. All original five violations reject specifically. Tests also reject a valid foreign schema digest, a genuine earlier same-root event receipt with matching SHA, and a genuine earlier audit after-image digest with correctly recomputed authentic audit bytes. The earlier timestamp-column invocation error is recorded separately and is not a contract test result.

Independent peer proof: `audit/generated/resume-8cc/archive/review-secret-rotation/fixed/`. Original counterexamples: sibling peer directory, retained unchanged.

This is bounded structural/semantic projection closure. Effective invalidation inventory, real credential/nonce source, deployment capability grants, full retained outcomes and complete OWNER session/browser consumers remain explicit dependencies. The public adapter stays fail-closed; no whole rotation or Secret create completion is claimed.
