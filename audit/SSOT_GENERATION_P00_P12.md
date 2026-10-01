# Postup generování P00–P12

Derived continuation procedure. Output paths are planning conventions, not new normative product requirements.

P00 requires current complete SSOT_CONTRACT_READY and separate freeze authorization. This repair task authorizes no freeze, application generation, release, deployment or production calls.

No successor RUNNING before predecessor current PASSED with identical SSOT/Contract Pack/toolchain lineage (71.7).

SSOT SHA-256: `2577dacf6024e4666ba98b11eb9c7ffa6e7f225e60630697db740129615cc536`.

Aktuální integrační checkpoint je PARTIAL: generation.job.create i secret.create zůstávají OPEN. Bounded RETRY/Secret fixtures nepředstavují kompletní P00 gate; přesné definice trusted producer/read/UI/browser předávek zůstávají povinné. Skutečné systemd fixtures jsou předgenerační podle §12.56; runtime vygenerovaných backendů se ověřuje v příslušných P00–P12 etapách, nikoli jako podmínka napsání definic.

Deliverables a delta gates jsou převzaté z R13/R14/R15; finální P00 gate používá účinnou precedence §73.7 místo historického R13 whole-document gate. Plánované cesty jsou konkrétní umístění budoucích výstupů; aplikace nebyla generována.

## P00 — Freeze SSOT and toolchain

Závisí na: aktuální kompletní návrhové gate a samostatné oprávnění freeze.

Plánované výstupy: `frozen-contract-pack/manifest.json`, `toolchain/locks/`, `audit/design-universe-results.json`.

Deliverables:

- R13 verifier packaged in repository
- effective Contract Pack extractor
- exact runtime/package lock manifests
- CI drift detector

Exit criteria:

- dependency resolution exact and reproducible
- no unclassified lock drift
- freeze R14 browser source locks, Ubuntu apt snapshot ID, Playwright browser tuple and package-set digests
- generate exact apt name=version lock from snapshot and commit its digest
- SSOT 73.7: verify_package.py executes R10, R16, UI, CLOSURE and R17 successfully
- SSOT 73.7: current hash manifest matches and R17 has zero unresolved/blocking findings
- R13/R14/R15 standalone verifiers are historical revision provenance; do not execute them as final composite whole-document gates

## P01 — Repository and contract compiler kernel

Závisí na: P00.

Plánované výstupy: `packages/contract-compiler/`, `generated/schema-registry.json`, `tests/contracts/`.

Deliverables:

- monorepo/package graph
- contract-pack loader/compiler
- schema registry
- canonical JSON/digest library
- static architecture import rules

Exit criteria:

- all embedded/current contracts materialize deterministically
- same input produces byte-identical generated registries
- forbidden import paths fail CI

## P02 — PostgreSQL 18.6 authority kernel

Závisí na: P01.

Plánované výstupy: `database/migrations/`, `database/helpers/`, `evidence/postgresql-18.6/`.

Deliverables:

- greenfield migrations
- constraints/indexes/FKs
- idempotency/outbox/inbox/queue/lease/fence tables
- migration ledger
- repository layer

Exit criteria:

- real PostgreSQL 18.6 migration PASS
- pgcrypto/citext PASS
- concurrency/lock-order/CAS/idempotency tests PASS
- restore/recovery barrier fixtures PASS

## P03 — Domain state machines, KCIP and trusted runtime boundary

Závisí na: P02.

Plánované výstupy: `packages/domain/`, `generated/kcip/`, `evidence/domain-lifecycle/`.

Deliverables:

- operation registry
- state-machine writers
- KCIP codecs/gateway
- runtime capability IPC
- secret/external brokers
- side-effect/reconciliation kernel

Exit criteria:

- reference model parity PASS
- no alternate writer/permission plane
- crash-before/after-side-effect tests PASS

## P04 — OpenAI runtime and strict mask compiler

Závisí na: P03.

Plánované výstupy: `packages/openai-runtime/`, `generated/openai-schemas/`, `evidence/openai-projection/`.

Deliverables:

- OpenAIClientService
- OpenAPI locked operation compiler
- KcmlOpenAIResponsesModel
- structured-output compiler
- provider event normalization
- Responses continuation/background/recovery

Exit criteria:

- openai 7.20.0 type/compile probe PASS
- locked OpenAPI verifier PASS
- request/response mask vectors PASS
- ScriptedModel tests PASS
- real provider contract smoke PASS

## P05 — MCP 2026-07-28 runtime

Závisí na: P03.

Plánované výstupy: `packages/mcp-runtime/`, `generated/mcp-contracts/`, `evidence/mcp-wire/`.

Deliverables:

- MCP v2 server/client gateway
- server/discover
- tools/resources/prompts
- MRTR/tasks/subscriptions/extensions
- OpenAI tool projection/inverse projection

Exit criteria:

- official schema/conformance PASS
- wire negative matrix PASS
- no legacy fallback for generated modern server
- real HTTPS MCP smoke PASS

## P06 — AI agent runtime

Závisí na: P04, P05.

Plánované výstupy: `packages/agent-runtime/`, `generated/agent-handoffs/`, `evidence/agent-resume/`.

Deliverables:

- Agent revision compiler
- Agents SDK adapter
- tools/handoffs/agent-as-tool
- guardrails/approvals/sessions/RunState
- memory/checkpoints/recovery

Exit criteria:

- @openai/agents 0.18.0 compile PASS
- tool collision/approval/concurrency semantics PASS
- ScriptedModel workflow suite PASS
- actual agent-to-MCP call PASS
- resume without duplicate side effect PASS

## P07 — Browser Interaction Plane and multi-instance interactive browser runtime

Závisí na: P03.

Plánované výstupy: `packages/browser-runtime/`, `generated/kbpp/`, `evidence/browser-runtime/`.

Deliverables:

- BrowserSessionService
- Playwright host/worker
- preview/control protocol
- target observation/extraction
- teaching/replay
- Device Bridge contracts
- BrowserSessionService consumer/allocation registries
- headed Xvfb Chromium host pool
- KBPP live preview exact adapters
- human login/handoff flow
- global browser session inventory
- hibernate/restore and host drain state machines
- all-run BrowserCapabilityContract integration
- KBPP collaboration overlay with OWNER/AI ink and pointer presence
- BrowserVisualAnnotation/BrowserFocusRequest persistence and resolution service
- strict AI annotation proposal compiler
- annotation crop/snapshot artifact generation

Exit criteria:

- Playwright 1.63.0/browser build manifest PASS
- raw CDP/Playwright exposure zero
- real Chromium lifecycle/recovery PASS
- typed extraction/postcondition tests PASS
- R14 acceptance gates PASS
- multi-instance chaos leaves zero orphan contexts/displays
- generated agent and MCP browser-step specimens use no parallel browser stack
- R15 browser visual-collaboration acceptance PASS
- markup mode proves zero external page input

## P08 — Generation factory

Závisí na: P04, P05, P06, P07.

Plánované výstupy: `packages/generation-factory/`, `evidence/generation-conformance/`.

Deliverables:

- generation orchestrator
- 12 specialist templates
- 19 typed nodes
- workspace patch/apply/readback
- implementation/repair loop
- integration saga
- activation-set builder

Exit criteria:

- every specialist input/output schema digest closed
- every node handoff exact or lossless-adapter
- no placeholder/mock/demo production artifact
- real reference conformance slice chat→spec→MCP→agent→activation→rollback PASS
- reference conformance slice includes at least one generated browser-capability operation with OWNER handoff and resume
- generated browser-capable agent specimen can annotate exact target and receive OWNER focus annotation through strict BrowserFocusContext

## P09 — Central chat, OWNER API and UI parity

Závisí na: P03, P08.

Plánované výstupy: `apps/owner-ui/`, `packages/owner-api/`, `generated/ui-action-parity.json`, `evidence/ui-api-chat/`.

Deliverables:

- central chat
- object action registry
- OWNER API
- dashboard/topology
- all management/detail surfaces
- generation/browser live progress
- browser markup toolbar and chat annotation chip
- OWNER/AI focus request and acknowledgement UI

Exit criteria:

- UI/API/chat parity matrix PASS
- accessibility/viewport E2E PASS
- every visible action reaches canonical operation
- no bypass route
- UI/API/chat parity for R15 operations

## P10 — Observability, audit, self-test and chaos

Závisí na: P02, P03, P04, P05, P06, P07, P08, P09.

Plánované výstupy: `packages/monitoring-repair/`, `evidence/chaos/`, `evidence/audit-lineage/`.

Deliverables:

- monitoring/probes/alerts
- audit chain/log explorer
- self-test runtime
- property/state-model tests
- fault injection/nemesis/recovery oracles

Exit criteria:

- audit integrity PASS
- all blocking self-tests PASS
- linearizability/recovery/orphan-free closure PASS
- unknown external effect always reconciles or MANUAL_REVIEW
- stale/reconnect/crash/multi-viewer visual collaboration chaos PASS

## P11 — Deployment and CI/CD

Závisí na: P00, P01, P02, P03, P04, P05, P06, P07, P08, P09, P10.

Plánované výstupy: `deployment/systemd/`, `deployment/release-manifest.json`, `evidence/ci-deploy-preproduction/`.

Deliverables:

- Ubuntu/systemd/nginx/TLS/DNS/install/deploy/rollback
- GitHub Actions gates
- backup/restore
- artifact attestation and release manifest

Exit criteria:

- disposable privileged Ubuntu 24.04 harness PASS
- fresh install PASS
- upgrade/rollback/restore PASS
- all exact lock digests recorded

## P12 — Production-shaped acceptance and activation

Závisí na: P00, P01, P02, P03, P04, P05, P06, P07, P08, P09, P10, P11.

Plánované výstupy: `evidence/production-shaped-acceptance/`, `evidence/activation-recovery/`.

Deliverables:

- full release candidate
- complete evidence bundle
- post-activation monitoring
- rollback candidate
- recertification baseline

Exit criteria:

- all architecture/build/runtime/provider/MCP/agent/browser/security/chaos gates PASS
- real post-activation agent-to-MCP smoke PASS
- terminal closure PASS
- no blocking finding or fabricated evidence
- production-shaped OWNER↔AI mutual visual orientation smoke PASS

R17 / 73.2–73.7: P00 musí doložit exact native/PGDG package versions a integrity; P02 skutečný PostgreSQL 18.6 a extension smoke; P07 browser launch a pinned runtime tuple. Syntetické testy nenahrazují tyto runtime důkazy.

R16 orchestration and R17 native toolchain/PGDG/browser requirements must be incorporated in implementation evidence; this projection does not certify their semantic closure.

Aktuální pokračování přidává canonical §12.51 native basis a §12.52 physical roots/atomic create handoff. P00 exit není počet zelených skriptů: explicitní dostupná sada má46kontrol a přetrvávající blokace. P02 má nyní skutečný boundedSQL fixture z embedded `database/generation-create-foundations.sql` naPostgreSQL18.6; source-built fixture nedokládá všechny native/PGDG package/R17 podmínky. Constant-time OWNER API verifier, canonical systemd/master-key/crypto, úplný locked RETRYscan, failure-before-root outcomes a native graph/read/UI/Secret consumers zůstávají předgeneračními exit criteria příslušných etap. Aktuální přesné výsledky a závislosti jsou v checkpointu a registru; žádná aplikace nevznikla.

## Integrated generation chain at continuation 34d

P00 keeps effective §73.7 precedence and all mandatory design/fixture gates. The historical R13 whole-document report alone does not grant readiness. Current authenticated generation modules are `contracts/generation/create-chain-handoffs.json` and the named canonical SQL dependencies, with actual PostgreSQL18.6 and independent native producer→consumer fixtures. Mandatory encrypted-systemd per-invocation proof remains BLOCKED in this managerless environment.

P01–P03 must emit trusted acceptance/current auth, immutable protected input and own native source selectors with exact physical producer joins. Exit requires actual key/nonce authority, full locked RETRY membership through child COMMIT and every own eligibility predicate; a validity flag, opaque fixture ciphertext or phase projection alone fails.

P04–P06 must consume retained protected bytes under exact archived schema/policy, native graph and immutable lineage; output discussion does not imply execution/activation authority. Pending/failure/unknown/cancel retention and pending→same-root transfer use the canonical pre-root module. Exit includes all recovery decision producers, complete event/outbox/audit/archive and retained reader joins.

P07–P12 preserve existing business outputs/exit criteria. Exact public/native UI projections, three exposure producer-result joins, Secret broker profiles/legacy RAW, complete §13.15 browser members, MCP/agent/OpenAI/monitoring handoffs and production fixture gates remain required. Runtime application acceptance is separate and NOT_EVALUATED. No application was generated.

Current Secret continuation: P02 consumes `contracts/secrets/import.schema.json` and `profile-handoffs.schema.json`; P03 must join the bounded `database/secret-profile-roots.sql` roots to actual trusted context/domain command/event/outbox/audit. P04 must authenticate immutable version metadata and hydrate exact bytes for the declared consumer; PROFILE schema/type/digests and legacy RAW null bindings are required. P05/§13.15 retains full browser bundle/bridge/CAS/account fixtures even after14 actual Chromium cookie-member checks. P00 exit continues effective §73.7;48-check universe alone is insufficient. No application runtime acceptance is inferred.

## Účinné vrstvy dokončení po nezávislém přezkumu

Registr a create checklist oddělují A (přesné definice), B (konkrétní fixtures), C (akceptaci aplikace) a D (prostředí). §51.36 vyžaduje doklady před aktivací; sám nestanoví existenci vygenerovaného backendu před generováním. SECRET.UI.REVEAL má normativní UI zdroj §72.21 a backend akceptaci P09/P12. Tato klasifikace neodkládá výslovné fixtures §12.56–12.57. Finální gate families jsou přesně R10, R16, UI, CLOSURE, R17 podle §73.7; R9 není šestá finální family. Historické odstavce výše jsou průběžná provenance, aktuální universe a důkazy určuje checkpoint, nikoli jejich starší počty.

### Current finite integration from input 84c41ba

This execution separates the original 36 create-chain parent duties into 144
**overlapping A/B/C/D conditions in the existing checklist/register**. These are
not new independent requirements or a project completion denominator. A is the
normative definition; B requires its own explicit pre-generation authority;
C is future generated-app acceptance; D identifies the unavailable environment.
In particular SECRET.UI.REVEAL generated backend runtime belongs to P09/P12,
§51.36 fixture activation and §73.4 P02 database checks must retain their stages,
and §12.56 actual systemd credential rotation/materialization remains an explicit
pre-generation fixture. No implementation acceptance or summary gate is waived.

Integrated boundary packages: OWNER session list/revoke six masks; Audit
list/read four masks including pre-root retained outcomes; four native MCP read
references; four SQL helper definitions limited to two OWNER query wrappers.
The Audit PostgreSQL witness reproduces the old omission of one of two retained
streams and verifies both rows after repair. SQL covers eight of 1,048 call sites
by reference only: 260 of 262 typed wrapper implementations and **all runtime
dispatch acceptance** remain open. No full operation is closed by these packages.

Current source and structural metrics are in the checkpoint and the register's
`structuralInventoryBinding`. Relative to input 84c41ba: unresolved references
242→238 (operations121→119), generic boundaries1496→1486
(request498→494,response498→494,event500→498), generic routes500→498.
Reference resolution and syntactic concretization alone do not establish
semantic closure. Global258 error predicates,176 provenance detector hits,
152 unspecified event applicability and three UI exposure blockers remain
unclosed; the six former state dictionaries remain structurally closed.

The finite next work packages are the register's existing `workPackages`:
OWNER_SESSION shared trusted context/reauth/snapshot/atomic/read-replay/digest;
Audit authenticated snapshot, cursor and retained-stream producers;
SQL trusted query issuer/capability/audit/protected hydration and typed handlers;
MCP native revision/access and platform producer bindings. For create, follow
`layeredConditions/parents` for trusted publisher/context, ledger→authenticated
native child and archived kind policy definitions before claiming the joined
chain. Run a real systemd fixture only in an environment with the documented
manager/bus/invocation credential capabilities. Do not repeat the same unavailable
fixture or replace it with a key-provider PASS.

Final command results and packaging integrity are recorded by the checkpoint;
historical input hashes, execution reports and superseded integration failures
retain their original identities. The final manifest/receipt is produced after
all current evidence, without embedding the resulting commit hash into itself.
