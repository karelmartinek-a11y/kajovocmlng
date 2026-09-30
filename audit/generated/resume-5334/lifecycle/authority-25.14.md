### 25.14 Release a deployment entities

#### `application_release`

- release ID, source commit, build ID
- manifest/artifact/signature digests
- immutable release state/evidence
- created/deployed timestamps
- previous release

#### `deployment_run`

- release/environment a logical operation
- state podle 49.24 a state version
- platform incarnation a application deployment epoch before/candidate
- controller lease/fence
- step timings/results/checkpoints
- backup/migration/symlink/database epoch/process effective evidence
- error/rollback/manual review

#### `deployment_step`

- run a stable ordered step key/attempt
- state, intent, expected before/after digests
- side-effect operation a outcome/reconciliation
- started/completed, duration, result, evidence

#### `backup_record`

- database/files/config
- digest, location, createdAt, verification, retention

#### `production_acceptance_run`

- expected SHA/release
- checks, results, timing
- created/completed

