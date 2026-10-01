# Independent bounded OWNER rotation review

Actual PostgreSQL 18.6 reproduced all 49 current author assertions in a separate database (`peer_owner_rotate_archive_8cc`), including actual current token authentication, both state CAS checks, B3 SHARE/UPDATE races, retained replay, rollback, and canonical AEAD opening of persisted synthetic new-version bytes. Count 49 is current bounded fixture coverage, not 49 requirements or full rotation closure. The earlier prompt's 26 assertions preceded added request parser/schema coverage.

Consumed source: `3edb2dafec4d93370d0f8ece759fee5b9d84cf50f59f28f89eb54498612ae247`; candidate SQL `dc2d36f5b6442396aa78e08b738d330a84b948dfc2c8802f588d8c729ed8a457`; helper `e9eea9a05e4fa8b9c16e2d31df77366135d74e819d3be23d4796ebbbcd6324e0`. Report records byte equality throughout the run and actual root crypto helper path. No production key or account was used.

## Five independently reproduced closure defects

Each mutation starts with the same authenticated valid request and valid current heads. Only the named event or audit field changes. Actual all-deferred-constraints checking accepts wrong event type, aggregate kind, event schema ID, zero event schema digest, and an audit afterDigest changed to zero with correctly recomputed canonical audit bytes/hash. Transactions were deliberately rolled back; no bad artifact was committed. This proves missing candidate SQL semantic joins, not failed crypto authentication. The prior positive fixture is valid and all original assertions remain PASS.

Relevant authority: §49.22.1 atomic Secret/credential transitions; §51.20 retained rotation outcome and invalidation consequences; author proposed exact rotation output/event schema and closure. These bounded semantic defects do not propose a new event product contract. Required repair is exact approved/proposed artifact binding appropriate to this bounded candidate. Do not activate it as the effective full generic rotation contract.

Zero semantic result digest fails the actual table digest CHECK; altered semantic operation ID with its recomputed digest fails `OWNER_ROTATION_SEMANTIC_RESULT_MISMATCH`. Public adapter rejects explicit empty invalidation inventory with `OWNER_ROTATION_EFFECTIVE_INVALIDATION_INVENTORY_UNRESOLVED`; no false empty-inventory completion claim.

## Physical boundary and limitations

Catalog evidence confirms completion's event+command+Secret FK is DEFERRABLE INITIALLY DEFERRED; immutable update/delete trigger exists. Table is owned by fixture superuser `agent`; `kcml_domain_writer` has no INSERT/UPDATE/DELETE. Thus the actual commit fixture proves physical mechanics, not a deployed narrow-role completion producer. A canonical writer/ordinal authority still needs explicit coordinator integration; do not infer one from table name or fixture superuser privilege.

Provider/genesis, global key/nonce authority, complete dependent invalidation inventory/events, HTTP/OWNER_SESSION, durable credential/session recovery and future generated application remain excluded. `wholeRotationClosed=false`; implementation acceptance NOT_EVALUATED.

Reproduce:
`PYTHONDONTWRITEBYTECODE=1 /tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/archive/review-secret-rotation/verify_rotation_peer.py`

`history/` preserves first counterexample evidence; final proof is not relabeled historical evidence. Await author correction and independently rerun exact repaired bytes before claiming the scoped defects closed.
