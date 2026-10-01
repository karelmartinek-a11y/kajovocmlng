# Independent exact-AAD repair verification

Effective source `4ac6fe00df084e910a90093485b12172866be73db94f66b6815200556c35be06`.

`verify_peer_key_fixed.py` and `peer-key-fixed-proof.json`: **18 PASS**, actual PostgreSQL **18.6**, exact current embedded typed-link SQL (`d3362763a573d1dbef8eaf53aa8ad4d91eb288047cebe987f2e38baf0b977fb1`) plus actual canonical root authentication/crypto helpers. This reruns all fifteen prior bounded peer scenarios and three independently derived byte-level counterexamples against the integrated repair:

- whitespace reencoding of the correct metadata, with recomputed matching metadata digest;
- noncanonical top-level key order preserving every value and field;
- integer epoch encoded as equivalent numeric `1.0` rather than required canonical integer `1`.

Each starts from the valid full producer fixture and retains actual valid ciphertext/nonce/context/schema/identities. Each now fails exactly `GENERATION_PROTECTED_TYPED_AAD_INVALID`. Valid canonical bytes still pass actual authenticated opening and commit, observed from a fresh connection. This demonstrates the original semantic-jsonb-only acceptance is repaired at the integrated SQL boundary.

`aad-byte-counterexample-before-fix.json`, `peer-key-proof-before-fix.json` and `verify_peer_key_before_fix.py` preserve the historical reproduced defect and prior proof; no history is rewritten as current PASS. The earlier `REVIEW.md` describes that historical faulty source, not the current repaired source.

`peer-environment-proof.json` is a fresh independent read-only current-source check: systemd manager remains offline, PID1 tail, UID1000, no manager/system-bus socket. Authentic root-owned encrypted credential source and read-only invocation materialization remain **ENVIRONMENT BLOCKED**. Service/key registration authority and Secret typed producer/broker joins are separate OPEN contracts, not inferred from isolated synthetic fixture registry rows.

For the actual connected auth→crypto→archive→root/event/outbox/audit/locator→fresh-read→consumer proof, see sibling `review-joined/joined-chain-proof.json` (**8 PASS**). Counts overlap and must not be added as completion percentages. No whole-operation or production-runtime acceptance claim.

Final canonical reproduction installs the unchanged successful archive and new canonical pre-root archive extension too. Current reports are from real execution at this final source; earlier source reports are not relabeled PASS.
