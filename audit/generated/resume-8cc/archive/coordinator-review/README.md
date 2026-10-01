# Fresh canonical bounded handoff rerun launcher

Owned files only; no shared/Git changes. `bounded_spec.json` covers exactly the eight original `scripts/verify_producer_archive_handoffs.py` labels: joined, retry, archive, aad, secret, ui, preroot, retry-stage. It lists the original script and report identity for each family. Secret comprises four original fixture scripts and a newly generated aggregate whose source/report hashes are computed only after their actual execution.

After coordinator freezes effective SSOT **and consumed helper/resource files**, run:

```
PYTHONDONTWRITEBYTECODE=1 /tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/archive/coordinator-review/run_all.py --run-id final-<source-prefix> --expected-source <exact-full-current-SSOT-SHA256>
```

Use a new run ID; existing output directories are rejected to prevent accidentally mixing stale reports. Each family has its own output tree and original fixture database names prefixed with a label-specific `cr8_` namespace. Unknown/unisolated database connections are rejected before opening libpq/psql. Original script paths and inputs are preserved; only enumerated database identity strings in the fixture Python and audit write destinations change. Business schemas, canonical SQL, fixture witnesses, negative assertions, historical sources and helper logic are not patched. Executed source transformation hashes and all redirected audit write hashes are recorded. Original evidence is never overwritten or assigned a new source hash.

`run-state.json` is saved between families, with exact exit code, timeout status, proof/manifest/log paths. Timeout terminates only that fixture's new process group, including its isolated psql holders; later families can continue. Source changes are an error. A complete eight-label attempt calls the **actual current** checker, including explicit missing/failed evidence paths with the complete eight-label evidence map; partial `--only` smoke runs return PARTIAL and never run or claim the universe gate. Failures remain BLOCKED with their original log/diagnostic, not contract PASS.

## Output and root integration

`runs/<id>/EVIDENCE_MAPPING.json` contains actual newly generated proof paths. The launcher invokes the canonical checker after overriding its `PROOFS` with this exact complete map in that process. Root's subsequent full/resumable runner must also consume this map, rather than unchanged historical hardcoded paths. Root alone owns any shared checker/configuration change. A supported override must reject missing/extra labels and preserve all existing checker conditions. Alternatively, root may point its eight existing paths at these fixed completed output paths. The map contains no self-commit SHA or circular hash requirement.

The archive proof checker expects its exact `verify_archive.py` source alongside the report; the launcher copies the original bytes there without altering them. Other support paths remain the original files actually consumed, and the checker verifies their current hashes.

Historical fixture inputs remain historical. In particular, Secret publication uses the existing `secret-native-review.json` as explicit structural/publication fixture data; its own declared historical source identity is retained. A new SQL publication test does **not** certify that historical artifact as a current semantic profile review. The publication subreport records its real old review source and exact artifact digest. Root-status/import/OWNER authority changes can invalidate an old positive fixture; such incompatibilities remain a visible failed command requiring an explicit fixture migration, not an automatic change in expected rejection.

The joined/AAD/preroot/retry fixtures retain their original bounded authentication, crypto and producer limitations. This launcher does not join the newly ordered native producer, certify real systemd source, close Secret/browser/broker policies, or close either create operation.

## Preparation smoke evidence

- Original UI fixture: actual 12 assertions executed in isolated output tree. Its initial preparation runner intentionally did not run the full universe; it must not be presented as full readiness.
- Original exact-AAD fixture: actual 18 PostgreSQL assertions executed in an isolated `cr8_aad_…` database; run status PARTIAL. This tests real nested fixture database/output isolation.
- Both original author report paths and fixtures remained unchanged. These preparation runs retain their actual source hashes; final execution must use a new run ID after source freeze.
