# Generation event decisions and explicit read errors — current review

**BLOCKED**: semantic completion remains open. PR #2 stays draft, no merge and
no freeze. Both OWNER event-applicability answers have been implemented; they
are no longer unanswered OWNER questions.

## Exact input/result

Branch `work/ssot-completion-2026-09-25`.
This second group starts at published commit
`5d72ccd4a20ce6d65020d176d95531c387bc31fd`, following the event group from
`2d2eea42533f0b4ab8ceb8b09c0cbcdc1d0c668d`.

- Group input SSOT SHA-256: `282dfdc013a37b0e3e65e87352d0b78ec501a2c4e8b02ceba8273d04248101fc`.
- Current result SSOT SHA-256: `709cd67a7f4d131d2fd0ff482a38e61105453febaa0793f7a456581bbcea15e4`.
- Result is the review-branch commit containing this report. No reset or
  historical evidence rewrite. Exact prior event field provenance is retained
  in `audit/SSOT_CONTINUATION_2d2eea4.md`; its old test hash does not certify the
  new SSOT. Event, read and other affected tests are rerun on the current hash.

## Implemented content

1. Effective SSOT §12.44.1 records both OWNER decisions. Approval event is
   aggregate `generation.spec.approved`; the two reads do not emit generation
   events. Audit remains separate; no invented second public lifecycle stream.
2. R9 `route.0234/eventSchema` is a precise native-SSE specialization:
   `eventId: Counter`, `type: const generation.spec.approved`, `objectId: Uuid`,
   `emittedAt: Timestamp`, and exactly two payload fields,
   `specificationRevisionId: Uuid` and `specificationDigest: Digest`.
   All are required/non-null; extra fields are prohibited. Sources are
   §12.19/12.21 frozen revision/digest, §12.44 job stream, §26.15 envelope and
   §49.5 same-commit sequence/outbox. Technical derivation follows §12.18.
3. R9 `route.0232/eventSchema` and `route.0237/eventSchema` explicitly reject
   every payload (`not: {}`) and declare `NOT_APPLICABLE`. Their old payload
   identities also resolve to reject-all schemas. Matrix validation rejects a
   purported NOT_APPLICABLE boundary that is missing or still permissive.
4. **New independent response repair**: both read response masks now require
   an error object on `FAILED` and `CANCELLED`. The previous schemas allowed
   both statuses with `output: null, error: null`. This contradicts the OWNER
   requirement, recorded in §12.44.1, that a read return the exact requested
   immutable document or an explicit error. No OWNER choice was necessary.

The precise response correction is one added conditional per read:

```json
{
  "if": {"properties": {"status": {"enum": ["FAILED", "CANCELLED"]}}},
  "then": {"properties": {"error": {"type": "object"}}}
}
```

This composes with the existing error schema, not a new arbitrary object:
`stableCode`, `classification`, `retryDirective`, `message`, `detailsDigest`
remain required, with their existing types/enums/nullability and no extra
fields. Existing failure output must still be null. Success still requires
the exact native `GenerationSpecification` / `GenerationPlan` and null error.
The repair does **not** claim that arbitrary stableCode/classification/retry
combinations are semantically correct; exact domain error applicability and
HTTP mapping remain unclosed. It does not silently decide the remaining
public ACCEPTED/terminal semantics of the general R9 response envelope.

Exact resource addresses:

- `contracts/payload-contracts.json`, record `route.0232`, `responseSchema`,
  identity `urn:kcml:r9:route:route.0232:response`.
- Same resource, record `route.0237`, `responseSchema`, identity
  `urn:kcml:r9:route:route.0237:response`.
- Native success masks remain
  `urn:kcml:generation-contracts:2#/$defs/GenerationSpecification` and
  `urn:kcml:generation-contracts:2#/$defs/GenerationPlan`.

## Concrete handoffs, failure and recovery

| Producer → consumer | Current evidence | Failure/recovery | Still not proved |
|---|---|---|---|
| approval commit snapshot/stored event → publisher | exact event equals persisted bytes; job/revision/digest/sequence and commit state ANALYZING match; actual specification digest checked | no precommit or unknown-effect publication; same outbox event redelivered after commit | real atomic DB evidence for all six §12.21 writes and outbox |
| generation SSE → client | cursor/inbox job matches objectId; only next sequence applied | identical duplicate ignored; changed duplicate conflicts; gap/missing history requires replay/snapshot | actual inbox persistence, Last-Event-ID bounded replay, resync.required |
| approval event → revision read → specification consumer | event job/revision/digest selects trusted persisted revision and exact native content | failure/cancel supplies no document; exact immutable refetch recovers | repository provenance and complete transport/error mappings |
| immutable specification/plan repository → read response → native document consumer | existing trusted job/document ID/canonical digest predicate plus complete response-schema failure checks | FAILED/CANCELLED cannot have null error or document output; required error fields enforced; confirmed matching refetch accepted | full error-code/classification/retry mapping, HTTP statuses, pending/terminal semantics |
| proposed / plan.created stream → immutable read | separate stream applicability is now decided; reads themselves have reject-all event schemas | wrong persisted identity/digest is still rejected by the read predicate | exact upstream payloads and source-to-target identity conversion require further technical investigation |

These are individual semantic edges, not 3204 claimed unique runtime handoffs.
Synthetic fixtures verify contracts and predicates; they do not execute a DB,
queue, deployed SSE endpoint or browser consumer. No whole route is certified.

## Counts, definitions and actual delta

| Unit | Before this turn (2d2eea4) | After event group (5d72ccd) | Current |
|---|---:|---:|---:|
| unresolved operation request/response schema references | 242 | 242 | 242 |
| operations with at least one unresolved reference | 121 | 121 | 121 |
| routes with any generic boundary | 505 | 505 | 505 |
| distinct addressed generic boundary definitions, including resolved nested refs | 1512 | 1509 | 1509 |

This second group delta is **0 / 0 / 0 / 0**. The full turn delta is
**0 / 0 / 0 / -3**; cumulative versus the earlier 250/125/505/1512 baseline is
**-8 / -4 / 0 / -3**. Three event definitions were fixed, not three whole routes.
The effective universe remains 619 operations and 542 route records, with
509 records in the R9 payload resource. Counts are derived, not an oracle.

## Commands and results

```powershell
$env:PYTHONUTF8='1'
python scripts/close_generation_domain_payloads.py
$env:KCML_AUDIT_OUTPUT='audit/generated/continuation-5d72ccd/read-errors'
python scripts/run_domain_continuation_checks.py --provider --read --events --read-errors
```

`audit/generated/continuation-5d72ccd/read-errors/commands.json` contains every
expanded command, actual/expected exit code, SSOT input hash (including exact
historical baseline hashes), script hashes, resource versions, dependencies,
stdout/stderr and durations. Current read-error tests have **87 checks, zero
failures**; the 5d72ccd baseline has five failures (four null-error cases and
the exact-delta assertion). Current event tests have 596 checks, zero failures.
The response tests exercise both reads, both failure statuses, missing/null/
malformed errors, all required error fields, wrong enum/type, forbidden failure
document, positive exact document and immutable refetch handoff.

Final runner exit code: **0**. All 23 expanded commands returned their expected
codes: five deliberately failing historical baselines and 18 current checks.
The current full guard suite passed 19851 checks. The regenerated matrix has
zero nested reference failures, conflicting schema identities, conflicting
operation references and unparsed resources; 108 concrete boundary definitions
still require semantic review, and 152 operation event applicability entries
remain unspecified elsewhere. These structural results do not certify the
remaining semantic scope or change the package's BLOCKED status.

The guard suite's unrelated-field comparison is preserved via explicit authored
deltas; no exception waives domain checks. Historical baseline failures and
prior results remain at their original paths/hashes.

## Changed files and continuation

New group changes: canonical SSOT R9 payload resource and digest manifest;
`scripts/close_generation_domain_payloads.py`;
`scripts/verify_generation_read_errors.py`;
`scripts/verify_generation_event_boundaries.py` (explicit expected read-error
delta, not disabling preservation checks);
`scripts/run_domain_continuation_checks.py` (new baseline/group);
this report; `audit/generated/continuation-5d72ccd/read-errors/`; regenerated
`PACKAGE_MANIFEST.json`, `FILE_MANIFEST_SHA256`, `FILE_MANIFEST_SHA256.json`.
The self-excluded `audit/generated/integrity-receipt.json` records current
package integrity only; it does not assert semantic completion.
Native schemas, predicates and all unrelated route records are unchanged from
5d72ccd and checked by the targeted test.

Current continuation sources are the new directory's
`missing-operation-investigation.json`, `current-operation-schema-matrix.json`
and `read-boundary-evidence.json`. Continue, without reinventorying from an old
ZIP or audit PASS, with:

1. The three generation routes' exact request body/query/header transport;
   approval public outcome; complete error mapping and public pending/terminal
   response semantics. The null-error defect is fixed, not the entire taxonomy.
2. Exact `generation.spec.proposed` and `generation.plan.created` payloads and
   stream-to-read identity mapping, using the now-decided separate-stream rule.
3. Actual approval transaction, outbox/inbox, replay/snapshot integration proof.
4. The remaining 121 operation pairs and 505 generic routes, using their
   existing individual generation/runtime/domain investigations. They are not
   collectively reclassified as OWNER decisions.
5. Complete semantic process audit and all mandatory gates before any PASS.

No new OWNER question is asserted by this group. The two answered decisions
are implemented, while the specifically listed technical/integration work
remains open. Conclusion: **BLOCKED**, draft PR, no merge, no freeze.
