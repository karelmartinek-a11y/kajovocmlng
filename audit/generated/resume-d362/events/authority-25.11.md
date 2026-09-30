### 25.11 Generation entities

#### `generation_job`

- `id`, fixed OWNER actor a initiating access channel/execution context
- kind `CREATE`, `UPDATE`, `FOLLOW_UP`, `RETRY`, `REPAIR`
- target kind a volitelný target object
- lifecycle state a current phase
- `state_version` a aggregate event sequence
- immutable initial request a digest
- parent/source job
- current/approved spec pointers a approved digest
- execution authority ID
- current capability snapshot a plan ID
- active phase run a latest checkpoint
- previous/candidate release a activation set
- cancellation version, blocker a error
- coordinator lease owner/fencing token/expiry/heartbeat
- coordinator platform incarnation a application deployment epoch
- created/started/completed timestamps
- client request ID a latest command logical operation

Constraints:

- jeden `client request ID` na OWNER idempotency scope,
- nejvýše jeden non-terminal coordinator lease na job,
- approved spec patří stejnému jobu,
- terminal state je immutable,
- current phase odpovídá state transition mapě,
- každý lifecycle command používá expected state version a current coordinator fence podle typu operace.

#### `generation_source`

- job
- source kind `TEXT`, `FILE`, `IMAGE`, `URL`, `API_DOC`, `CREDENTIAL_REF`, `OBJECT_REF`
- original name/locator a MIME
- content/storage reference a digest
- status
- parser version a normalized text reference
- sensitivity a retention
- created/parsed/verified/superseded timestamps

#### `generation_fact`

- job a source
- stable fact key
- classification
- statement a canonical value
- source locator
- verification method a confidence classification
- observedAt, supersededAt
- fact digest

#### `generation_owner_decision`

- job a OWNER message
- decision key a affected specification paths
- exact text a structured value
- digest
- createdAt a supersededBy

#### `generation_message`

- job, monotonic sequence, role
- content a attachments
- status
- client message ID
- turn ID
- created/completed/interrupted timestamps
- content digest

#### `generation_turn`

- job, input message a monotonic turn sequence
- status a `state_version`
- worker lease owner/fencing token/expiry/heartbeat
- platform incarnation a application deployment epoch
- active model call a provider response ID
- successor relation a unique successor slot
- interruption/cancellation version, intent a reason
- latest checkpoint a pending side-effect set
- error a terminal outcome digest
- timestamps

Completion versus steer/interrupt používá jeden job/turn row-lock commit; vznikne právě jeden terminal turn outcome a nejvýše jeden successor.

#### `generation_spec_revision`

- job a revision number
- schema version
- canonical JSON
- rendered Markdown
- digest
- parent revision
- capability snapshot/digest
- conformance precheck state a report
- createdAt

Revision je immutable a unique podle `(job_id, revision_number)` i `(job_id, digest)`.

#### `generation_execution_authority`

- job
- kind `OWNER_APPROVED` nebo `INHERITED_TECHNICAL`
- source job/spec/revision/digest
- OWNER approval event
- target identities snapshot
- lineage digest
- frozenAt

#### `generation_capability_snapshot`

- job a specification revision
- normalized requirement digest
- catalog epoch
- snapshot payload a digest
- createdAt a staleAt

#### `generation_capability_match`

- snapshot a requirement ID
- matched object/component/revision/contract
- behavior coverage
- schema compatibility
- runtime/binding eligibility
- decision `FULL_REUSE`, `PARTIAL_REUSE`, `NEW_CAPABILITY_REQUIRED`
- evidence a score

#### `generation_plan`

- job, authority a specification
- schema version
- canonical DAG JSON a digest
- validation state a report
- createdAt

#### `generation_plan_node`

- plan a stable node key
- kind a purpose
- requirement IDs
- input artifact refs/digests
- output schema/digest
- execution role
- side-effect/retry/idempotency
- timeout a budget
- checkpoint/compensation policy
- state a result artifact

#### `generation_plan_edge`

- plan
- source node a target node
- edge kind `DATA`, `CONTROL`, `ACTIVATION`, `COMPENSATION`
- required artifact/schema
- digest

Graph constraints blokují self-edge, neexistující node a cyklus v execution edges.

#### `generation_phase_run`

- job, phase a attempt
- state a `state_version`
- worker pool, lease owner/fencing token/expiry/heartbeat
- platform incarnation a application deployment epoch
- plan node range
- input checkpoint a output checkpoint
- cancellation version a pending side-effect set
- started/completed timestamps
- result summary a digest
- blocker/error/manual-review relation

Partial unique constraint povoluje nejvýše jeden active phase run na job. Phase terminal write, job transition, event/audit a enqueue další fáze jsou jedna transakce.

#### `generation_checkpoint`

- job, phase run a monotonic sequence
- checkpoint kind
- expected parent/job/phase state versions
- platform incarnation, application deployment epoch a lease fencing token
- authoritative pointer snapshot
- pending operation/side-effect/cancellation snapshot
- workspace, candidate a activation references
- provider handles
- previous checkpoint ID/digest
- canonical payload a digest
- createdAt

Checkpoint je immutable, jeho sequence je contiguous a current pointer se přepne compare-and-swap ve stejné transakci jako související state mutation.

#### `generation_tool_event`

- job/turn/phase/model call
- tool key a provider call ID
- state `STARTED`, `PROGRESS`, `COMPLETED`, `FAILED`, `CANCELLED`
- canonical args/result payload a digests
- domain operation a side-effect classification
- correlation/audit
- timestamps

#### `generation_workspace_revision`

- job a revision number
- parent revision
- source tree digest
- artifact manifest draft digest
- createdBy model call/worker
- createdAt

#### `generation_workspace_file`

- workspace revision
- canonical relative path
- MIME/type a executable flag
- content storage/reference
- size a digest
- source classification

#### `generation_workspace_patch`

- job, phase run a model call
- base workspace revision/digest
- ordered operations payload a digest
- apply state
- conflict/error
- resulting workspace revision
- created/applied timestamps

#### `generation_artifact_manifest`

- job, workspace a candidate release
- specification/authority/plan digests
- canonical manifest JSON a digest
- completeness state
- createdAt

#### `generation_artifact`

- job/workspace/release/manifest
- path/type/digest/size
- content/storage reference
- requirement IDs
- evidence references
- retention a sensitivity

#### `generation_contract_candidate`

- job a target graph node
- kind `COMPONENT`, `MCP_SERVER`, `MCP_TOOL`, `MCP_RESOURCE`, `MCP_PROMPT`, `AI_AGENT`, `AUTOMATION`
- proposed stable identity
- revision payload a digest
- source specification paths
- validation/verification state
- published object/revision relation

#### `generation_validation_run`

- job, phase run, workspace/candidate/activation set
- gate catalog version
- state
- started/completed timestamps
- blocking summary
- evidence digest

#### `generation_validation_result`

- validation run a gate key
- evaluator version
- status `PASS`, `FAIL`, `NOT_APPLICABLE`
- inputs, expected a actual
- diagnostics a artifacts
- logs/correlation
- duration a result digest

#### `generation_repair_iteration`

- job, phase a iteration number
- diagnostics cluster/digest
- input workspace revision
- model call a patch
- output workspace revision
- progress signature
- result a duration

#### `generation_blocker`

- job, phase a plan node
- stable code a classification
- title/detail
- affected requirement IDs
- evidence
- required resolution a input schema
- resume phase/checkpoint
- state
- created/resolved timestamps a resolver

#### `generation_activation_set`

- job a authority
- immutable membership digest a mutable state version
- state `DRAFT`, `READY`, `SWITCHING`, `VERIFYING`, `ACTIVE`, `ROLLING_BACK`, `ROLLBACK_VERIFYING`, `ROLLED_BACK`, `FAILED`, `MANUAL_REVIEW`
- controller lease/fence, platform incarnation a application deployment epoch
- activation domains a barrier relation
- activation/switch/rollback epochs
- previous pointer snapshot a digest
- candidate pointer snapshot a digest
- preflight/postflight/effective-ack evidence
- rollback a cleanup evidence/state
- created/switched/activated/rolled-back timestamps

`ROLLED_BACK` a `FAILED` jsou terminal pro konkrétní set. `ACTIVE` je stable successful stav, který může přejít do rollbacku pouze dokud je set current podle `activation_head` a exact candidate snapshotu; historický superseded set je kvůli current-head a snapshot guards immutable evidence. `MANUAL_REVIEW` používá exact resolution hrany 49.17.

#### `generation_activation_member`

- activation set
- object kind/ID
- previous revision/release/binding-set revision
- candidate revision/release/binding-set revision
- activation order key
- state a evidence

#### `generation_event`

- job a monotonic sequence
- event type, emittedAt a persistedAt
- payload a digest
- message/turn/phase/model/spec/plan/workspace/candidate/activation references
- correlation/causation/trace

Event sequence je unique per job a je autoritou pro SSE replay.

