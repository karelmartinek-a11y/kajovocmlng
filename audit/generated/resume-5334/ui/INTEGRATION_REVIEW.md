# UI/reference integration review at 5334d8c

Canonical input SHA-256: `2086c1594100e125cae4714a62371f608835c3346feff66a9f5dab99db6b22aa`.
Only files under this review directory were written. No Git operation, canonical authoring, projection, manifest or checkpoint write was performed.

## Concrete renderer correction

Preferred renderer integration now uses `render_reference.proposed.py` at
`scripts/render_reference.py` and `render_reference.wrapper.proposed.mjs` at
`scripts/render_reference.mjs`. The earlier direct Node proposal is superseded:
Node Playwright is 1.62.1 in this environment whereas requirements-audit pins
Python Playwright 1.63.0. The thin wrapper uses only Node child_process with
shell=false and requires AUDIT_PYTHON. The Python renderer verifies the full
pinned audit package inventory and uses explicit CHROMIUM_PATH. Two environment
negative diagnostics are independently verified in launcher-environment-tests.json;
this preparation has not rerendered changing canonical sources.

After source freeze, an isolated review invocation is:

    AUDIT_PYTHON=/tmp/ssot-audit-venv/bin/python CHROMIUM_PATH=/usr/bin/chromium REFERENCE_OUTPUT_ROOT=<isolated-output-root> node scripts/render_reference.mjs

Omit REFERENCE_OUTPUT_ROOT only for coordinator-authorized canonical exports.
The renderer writes 96 primary renders for the current declared matrix and
separate derivative dashboard screenshot copies. cs preserves workspace-*.png;
en writes en/<viewport>/workspace-*-en.png. It never overwrites generation.png
with the live specification editor. Actual served asset hashes, source/resource/
helper hashes, interpreter/API/browser versions and pending manual inspection
are recorded. Missing environment is BLOCKED; invalid/missing reference layout
is a presentation check failure, and unexpected tool exceptions are identified.

`current-reference-checks.json` proves current presentation compatibility using installed Chromium (`/usr/bin/chromium`) and the audit Playwright dependency: **1,170 checks, zero failures, 96 renders** = 12 effective `ui/contracts/live-experience.json#/views` × four declared viewports × cs/en. These are fresh current HTML/CSS/JS bytes, no external HTTP request and no backend. All actual consumed local files are hashed. `test_current_reference.py` reproduces this scoped result and writes exclusively here.

Historical `scripts/render_reference.mjs` waits for `[data-ready=true]` on dashboard query states. Current dashboard has `data-demo=true`, `data-view=dashboard`, `data-state=ACTIVE`, and `assets/live.js`; it never emits historical `data-ready`. Most query strings now simply return the same dashboard. Current specification view is `pages/live-specification.html`, whereas `pages/generation.html` is a distinct administrative reference using `assets/ui.js`.

Integration proposals:

1. Historical Node-only prototype: `render_reference.proposed.mjs` (superseded by the preferred pinned Python/wrapper proposal above) replaces the historical renderer, integrated at the original scripts location. Source views/viewports from the effective live contract; visit each actual static HTML file; check explicit demo/view/state identity, loaded live.js functions and real help/menu interactions. Do not inject a fake readiness marker or relax the wait to any body.
2. Use `CHROMIUM_PATH=/usr/bin/chromium` in the current environment. The original renderer already supports this variable; missing bundled browser is an environment issue, not a contract defect.
3. Update physical `ui/contracts/visual-artifact-bindings.json` with `visual-artifact-bindings.proposed.json`: preserve stable artifact IDs and screenshot names, but replace obsolete query-state source URLs with the actual current view files. The renderer explicitly maps historical screenshot scenarios to effective view IDs, so screenshots remain independently traceable.
4. Record active source hashes for every HTML/CSS/JS/logo actually requested, live-experience/control/action contracts, source document, renderer and browser/dependency versions. The proposed Node renderer still needs the coordinator to add dependency/renderer hashes if adopting it unchanged; the isolated report already records dependency and script versions.
5. Do not overwrite legacy `generation.png` with the different live-specification panel. `render_reference_package.py` owns administrative page screenshots; current live references own `workspace-specification.png`.
6. Keep a separate visual-inspection status. I inspected 4/96 screenshots (`visual-review.json`): desktop specification, mobile dashboard, desktop UNKNOWN response, English human-login wait. The remaining 92 are not claimed manually reviewed. The mobile branch glyph before the source label appears as a small square under the current fallback font; Montserrat and Segoe resolve to OpenAI Sans in this environment. A canonical font/glyph review remains distinct from no-overflow/interaction PASS.

## Exposure blockers: preserved, not relabeled

Exact active pointers are saved in `input-actions.json`:

- `dashboard.start`: `ui/contracts/ui-control-registry.json#/pages/3/actions/18` → binding → `contracts/operation-contracts.json#/records/533`, `runtime.instance.start`, AUTOMATED_MAINTENANCE.
- `dashboard.stop`: `/pages/3/actions/19` → `contracts/operation-contracts.json#/records/540`, `runtime.stop`, AUTOMATED_MAINTENANCE.
- `gen.editSpec`: `/pages/4/actions/9` → `contracts/operation-contracts.json#/records/357`, `generation.spec.propose`, INTERNAL_PROTOCOL.

The required OWNER actions are explicit in the current embedded UI registry and live dashboard surface binding. `ui/contracts/live-experience.json#/specification/edit` additionally requires form/chat edit → new DRAFT revision, old approval/execution immutable. §§43.3, 49.3–49.5 provide the canonical OWNER-intent/server-command bridge: persist authenticated OWNER input, exact stable idempotency scope and CAS, then canonical orchestrator issues server-owned bounded worker context. The browser/model does not impersonate AUTOMATED_MAINTENANCE or invoke an INTERNAL_PROTOCOL operation as OWNER.

An explicit OWNER request facade is therefore a technical realization of an existing required action, not automatically a new business feature or trust policy. Its request, durable command, worker-reference resolution, response/event and failure masks must be authored together before claiming the exposure closed. Preserve all three existing internal operations and their writer/authority classes.

Unresolved exact contracts that currently prevent a verified facade integration:

- Start/stop internal command refs remain operation schema locators rather than demonstrated exact native masks; §§50.10–50.11 require the full server-resolved immutable runtime launch snapshot, not just a selected ID. Fresh actor, component/revision/release/binding/activation/runtime/deployment/recovery snapshot, ordered locks, parent-child identity and bounded worker context must be checked against their own authority. No schema field may stand in for a missing resolver/helper.
- There is no existing OWNER start/stop facade in the current catalog. `component.state.request` is a state **query**; it cannot serve as a start/stop mutation. `component.enable/disable` change component control eligibility; aliasing runtime start/stop to them may change product semantics. The live context-menu `operations` list says enable/disable while the active dashboard.start/stop profile names a current runtime instance; resolve this source inconsistency explicitly, not by silent aliasing.
- Specification form fields (#goal/#role/#input/#output) are presentation examples; the canonical OWNER patch mask and transport to a new immutable DRAFT revision are absent. `generation.message.append` is a valid OWNER input operation, and §43.3 says OWNER input after proposal creates a new revision, but its current body/response remain generic. Rebinding the action to it alone is not a typed editor submission/receipt proof.

No genuine additional OWNER business decision was established in this scoped review. These are technical materialization/source-consistency gaps. Keep them BLOCKED until the explicit bridge is independently verified.

## Create receipt → current read → UI consumer

`gen.create` and `secret.create` now name exact request and create receipt schemas in their argument profiles. That is useful bounded DESIGN mapping, not full current-read hydration closure. The existing completion verifier checks frozen create receipt bytes and semantic relations; those bytes are not the full `generation.job.read` or Secret metadata/version read payload.

Current mandatory read boundaries are still generic schemaId/values bags:

- `generation.job.read`: `contracts/payload-contracts.json#/records/217/responseSchema`, GET `/generation/jobs/{id}`.
- `generation.job.snapshot.read`: `/records/218/responseSchema`.
- `secret.metadata.read`: `/records/387/responseSchema`, GET `/secrets/{id}`.
- `secret.version.list`: `/records/392/responseSchema`, GET `/secrets/{id}/versions`.
- `secret.value.read`: `/records/390/responseSchema`; exact selected-version transport is not proved by a generic query list.

A precise UI consumer DESIGN repair should explicitly declare:

1. Authenticate the canonical API producer/origin and bind operation/request/correlation; model proposals and echoed client IDs are never server receipts.
2. On generation SUCCEEDED, consume exact server jobId/kind/state/version/initial digest/frozenBasis; fetch by that jobId, never latest-global. Validate full typed current job/snapshot output, persisted immutable initial request linkage and real bytes, then map its own lifecycle to UI states. Current state/version may advance; a newer snapshot must not rewrite the frozen creation receipt.
3. On Secret SUCCEEDED, use secretId for metadata/versions and select **versionId**, not active-version/latest substitution. Verify same stableName/type and immutable secret/version lineage. CREATED is the creation fact, not an implicit activation/binding grant. Later legitimate activation/current metadata may differ; preserve the frozen CREATED receipt.
4. ACCEPTED and retryable attempt failure show pending/original logical operation; UNKNOWN triggers reconciliation without a second create or claimed final failure. Stable idempotency key stays unchanged on network retry. Error display uses canonical stable code/classification/directive, not localized text as recovery authority.
5. Map concrete inputs to the exact native body: gen.intent/source URL/credential and Secret stable/display/type/value metadata with omission rules and UTF8/BASE64 byte preservation. The current prose fieldMappings strings do not constitute an executable validated transform for every field/variant.
6. Add valid domain current-read and UI projection witnesses first, then mutations: wrong root/version ID, changed immutable bytes/digest/schema/kind, missing reference, latest-global substitution, model receipt, stateVersion regression, stale source, second create on UNKNOWN, Secret CREATE→ACTIVE substitution, and invalid producer/channel/context.

Missing typed read/output/byte-hydration or UI projection contracts are required DESIGN gaps (A). Absence of a running application, real browser accounts, actual event backend or real Secret Broker execution is future IMPLEMENTATION acceptance (C), not itself a reason to block a complete design. Neither fresh screenshots nor reference fixtures establish that implementation gate.
