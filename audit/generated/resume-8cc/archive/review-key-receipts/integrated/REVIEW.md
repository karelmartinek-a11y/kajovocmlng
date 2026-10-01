# Activated key-only reproduction

At effective SSOT SHA-256 c754c27e744434588ee17e3074d1750003077149a6193efcccefbd05f88103a3, reexecuted the independent review using asserted exact canonical `database/canonical-key-invocation-receipts.sql` bytes and the actual imported `/workspace/kajovocmlng/scripts/systemd_key_authority.py`. Both were byte-compared with their reviewed candidate; the historical candidate reports in the parent directory were preserved.

PostgreSQL18.6: 21 author assertions independently reproduced; 12 additional peer assertions PASS, 0 FAIL. Root helper: 28 reference assertions PASS. Unpatched actual provider probe still `SYSTEMD_MANAGER_NOT_PID1`; provider stays ENV_BLOCKED. These counts describe bounded fixture coverage, not operation completeness.

The source installer→database transport, exact live service role/membership, actual encrypted source→systemd read-only materialization, desired/effective rotation authority and retained source availability remain explicit unmet conditions from the parent review. Neither SQL rows nor patched reference replies certify provider authority. This review changes none of the approved Secret status rules and introduces no new product decision.
