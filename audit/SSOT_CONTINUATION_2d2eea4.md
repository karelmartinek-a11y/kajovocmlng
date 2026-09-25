# OWNER event decisions — continuation from 2d2eea4

Package status: **BLOCKED**. PR #2 remains draft; no merge or freeze.
This is a scoped contract repair, not completion of the semantic audit.

## Input and result identity

- Branch: `work/ssot-completion-2026-09-25`.
- Clean input HEAD: `2d2eea42533f0b4ab8ceb8b09c0cbcdc1d0c668d`.
- Input SSOT SHA-256: `8d5d6706b3ffb366b6de782af66dadb8ebb4a85f4e7db1c63110e98adabc3982`.
- Result SSOT SHA-256: `282dfdc013a37b0e3e65e87352d0b78ec501a2c4e8b02ceba8273d04248101fc`.
- Result identity is the review-branch commit containing this report; the exact
  SSOT bytes above, not an older audit result, identify its contract input.
- Continued the existing dossier rooted in e025079; no reset, new branch,
  discarded work, or change to historical evidence.

Both explicit OWNER answers of 2026-09-25 are now effective SSOT §12.44.1:
approval uses the aggregate `generation.spec.approved` event, whereas the two
immutable read operations have no generation event of their own. Read audit
is separate. This supersedes the two unanswered questions in the historical
`SSOT_CONTINUATION_664d617.md`; that report is intentionally not rewritten.

## Content changes and field provenance

Authoritative resource: `contracts/payload-contracts.json` inside SSOT.
The readable, exact three event schemas are also projected in the current
`event-final/read-boundary-evidence.json` under `generationRoutes[].event`.

| Boundary | Exact identity | Effective meaning |
|---|---|---|
| approval event | `urn:kcml:r9:route:route.0234:event` | Specialized native `SseEnvelope`; aggregate event, not operation lifecycle |
| approval payload | `urn:kcml:r9:semantic:route.0234:event-payload` | Exactly approved revision ID and canonical digest |
| revision read event | `urn:kcml:r9:route:route.0232:event` | Explicit `NOT_APPLICABLE`; `not: {}` rejects every JSON value |
| plan read event | `urn:kcml:r9:route:route.0237:event` | Explicit `NOT_APPLICABLE`; `not: {}` rejects every JSON value |

Old read payload identities are preserved as rejecting schemas in `$defs`.
They cannot be used as a permissive fallback. Neither read acquires a new
event, stream, or audit exemption. Approval request and response are unchanged.

All approval envelope fields and both payload fields are required and
non-nullable, with no additional properties:

| Field | Exact mask / domain | Provenance and relationship |
|---|---|---|
| `type` | constant `generation.spec.approved` | §12.44 SourceEnum044 and explicit OWNER choice |
| `objectId` | native `Uuid` | §12.44 stream belongs to job; §12.21 source job approval |
| `eventId` | native `Counter`, decimal string 0..9223372036854775807 | §26.15 SseEnvelope; §49.5 aggregate-local sequence allocated in state transaction |
| `emittedAt` | native `Timestamp`, validated UTC date-time with 3/6 fractional digits | §26.15 envelope; immutable persisted event redelivered under §49.5, not a new delivery timestamp |
| `payload.specificationRevisionId` | native `Uuid` | §12.21 command identity and atomic frozen approved pointer; spelling already used by exact approval command |
| `payload.specificationDigest` | native `Digest`, `sha256:` plus 64 lowercase hex digits | §12.19 canonical document digest and §12.21 frozen digest |

Technical projection/spelling follows §12.18. No extra authority ID, planning
ID, client status, model output, internal StepInput, or CommitReceipt is
invented as a public event field. Job identity is not duplicated in payload.
The chosen fields are projections of already specified persisted facts, not
new business choices. The general R9 lifecycle envelope is not evidence for a
second mandatory public lifecycle stream. No separate, explicit effective
requirement for such a stream was established in the inspected source passages.

## Concrete handoffs and recovery matrix

These are distinct semantic edges, not a relabeling of the historical 3204
inventory rows as runtime handoffs.

| Producer → consumer | Mask/identity evidence | Failure and recovery | Remaining evidence |
|---|---|---|---|
| §12.21 atomic approval snapshot + stored event → outbox publisher | exact approval event; trusted commit job, revision, digest, sequence, `ANALYZING`; actual native specification digest | no publication on precommit/unknown effect; mismatched snapshot/content rejected; postcommit retry retains exact event/timestamp | actual DB transaction must prove all six writes, audit and outbox atomically; synthetic predicate is not that proof |
| stored approval event → generation stream consumer | exact envelope; cursor/inbox scoped to the same job; next expected sequence only | duplicate with same digest ignored; changed digest conflict; gap or missing inbox history requests replay/snapshot | actual inbox persistence, Last-Event-ID, bounded replay and unavailable-range `resync.required` integration |
| approval event → revision read → immutable document consumer | request job/revision derived from event; response is native `GenerationSpecification`; trusted repository revision identity and canonical digest match | FAILED/CANCELLED/ACCEPTED yields no downstream document; changed schema-valid content rejected; exact immutable refetch accepted | real repository provenance/lookup and full read transport/error contract |
| separate `generation.spec.proposed` stream → revision read | OWNER establishes separate stream, not a read-emitted event | existing immutable read predicate still rejects wrong job/revision/digest and failure output | exact proposed-event payload and identity conversion remain technical investigation, not asserted closed |
| separate `generation.plan.created` stream → plan read | OWNER establishes separate stream; existing native plan read verifies job/plan ID and digest | failure is not a plan; immutable refetch must match persisted snapshot | exact created-event payload and identity conversion remain technical investigation, not asserted closed |

The publisher predicate takes the **approval commit snapshot**, not the latest
mutable job snapshot, which may legitimately have progressed. Trusted snapshot
provenance is a server obligation, never satisfied by a caller claiming those
values. Cancellation/disconnect after commit does not reverse approval or
planning. Command failures remain on command/response boundaries, not coerced
into `generation.spec.approved`.

Normative predicates are embedded in `scripts/ssot/ssot_control.py`:
`validate_generation_approved_event` and `generation_event_delivery_action`.
Existing approval admission and read handoff predicates are preserved.

## Counts and units

Current numbers are derived from the effective catalog and schemas by the
same continued matrix, not from a requested target count.

| Unit | 2d2eea4 input | Result | Delta |
|---|---:|---:|---:|
| unresolved operation-level request/response references | 242 | 242 | 0 |
| operations having at least one such unresolved reference | 121 | 121 | 0 |
| routes with at least one generic request/response/event boundary | 505 | 505 | 0 |
| distinct addressed generic boundary definitions, including resolved nested schemas | 1512 | 1509 | -3 |

The three removed generic definitions are one exact approval event and two
explicitly inapplicable read event contracts. **No whole route is closed or
subtracted.** The catalog still has 619 effective operations and 542 route
records; R9 payload-contracts has 509 records. These are different units.
Relative to the earlier requested 250/125/505/1512 baseline, the cumulative
change is -8/-4/0/-3; this group alone did not close another operation pair.

## Commands and evidence

Final verification was launched with:

```powershell
$env:PYTHONUTF8='1'
python scripts/close_generation_event_boundaries.py
$env:KCML_AUDIT_OUTPUT='audit/generated/continuation-2d2eea4/event-final'
python scripts/run_domain_continuation_checks.py --provider --read --events
```

The final run is recorded in `event-final/commands.json`: every expanded
command, actual and expected exit code, exact SSOT input hash (different for
historical baselines), script hash, resource versions, dependencies, stdout,
stderr and elapsed time. Baselines are expected to exit 1; current checks must
exit 0. The previous `event-integration` directory is an intermediate run with
hash `463428b7117c3ec5dd66404a20f5f1ce7836d8c27183a92399babb44338ec6c9`;
it does not certify the final SSOT, whose consumer now also checks stream job.

The event test includes exact positive payloads; original generic lifecycle
rejection; missing/null/wrong fields; forbidden server receipt/client status;
read reject-all applicability enforcement; precommit/unknown commit rejection;
snapshot/state/sequence/digest mismatch; schema-valid changed content;
cross-job cursor; duplicate conflict; gap recovery; and approval-to-read
success, failure and immutable refetch. It also verifies unchanged request and
response masks and all other R9 routes. These are contract/predicate tests,
**not** an executed database or browser/SSE deployment.

The broader run retains generation domain and operation masks, MCP read/list,
ProviderOutcome, saga handoffs, native manifest, portable manifest negatives,
the full guard regression and UI projection checks. The complete continued
matrix/dossier are regenerated in `event-final`, retaining all 130 original
operation investigations and their previously established exact bindings.

Final verification: runner exit 0; all 21 child commands have their expected
exit codes (four deliberately failing historical baselines, 17 current checks).
Current event suite: 596 checks, zero failures; 2d2eea4 baseline: 571 checks,
eight detected failures. Guard suite: 19851 checks, zero failures. The final
matrix reports no nested reference failures, schema identity conflicts,
operation reference conflicts, or unparsed resources. This does not change
the package's BLOCKED semantic status.

## Changed files and reproducible continuation

- `00_SSOT/KajovoCMLNG_SSOT.md`: §12.44.1, R9 payload-contracts, embedded native
  validator, native and R9 resource manifests. Native generation masks and
  all operation records/aliases remain unchanged. The large textual diff is
  principally deterministic compressed resource re-encoding.
- `scripts/close_generation_event_boundaries.py`: deterministic author/check.
- `scripts/verify_generation_event_boundaries.py`: targeted negative tests.
- `scripts/phase1_schema_closure.py`: fail-closed applicability enforcement
  and separate rejecting-boundary classification; no semantic PASS shortcut.
- `scripts/report_read_boundary_evidence.py`: current OWNER decisions and exact
  event projections replace the formerly unanswered alternatives in new output.
- `scripts/verify_route_guard_counters.py`: explicit expected event delta;
  comparison of unrelated fields is preserved, not disabled.
- `scripts/run_domain_continuation_checks.py`: event group, actual baseline
  input hashes, and baseline 242/121/505/1512.
- This report, `audit/generated/continuation-2d2eea4/`, and regenerated
  `PACKAGE_MANIFEST.json`, `FILE_MANIFEST_SHA256`, `FILE_MANIFEST_SHA256.json`.

Continue from `event-final/missing-operation-investigation.json` and
`event-final/current-operation-schema-matrix.json`, not older PASS files.
The next concrete work remains:

1. Exact request body/query/header transport for the three generation routes;
   approval public response and complete typed failure/recovery outcome masks.
2. Individually derive the proposed/plan-created payloads and event-to-read
   identity mappings from full effective sources. Their boundary applicability
   is now decided; missing payload investigation is not another OWNER question.
3. Actual atomic approval/outbox/inbox and replay/snapshot evidence; do not
   promote synthetic predicates to runtime or persisted-transaction proof.
4. Continue the 121 unresolved operation pairs and remaining 505 generic
   routes by the existing individual generation/runtime/domain investigations.
   These are not collectively classified as missing OWNER decisions.
5. Full semantic process audit and all mandatory integration gates remain.

No new OWNER decision is requested for the two answered applicability
questions. Both are implemented. Other unproved contract work is explicitly
left open; the package remains **BLOCKED**, not freeze-ready.
