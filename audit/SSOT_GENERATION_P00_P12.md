# Postup generování P00–P12

Derived continuation procedure. Output paths are planning conventions, not new normative product requirements.

P00 requires current complete SSOT_CONTRACT_READY and separate freeze authorization. This repair task authorizes no freeze, application generation, release, deployment or production calls.

No successor RUNNING before predecessor current PASSED with identical SSOT/Contract Pack/toolchain lineage (71.7).

SSOT SHA-256: `6e7312694cd1bf97419540bcc574f3bace4ccecabad73344831ee5e8487d8605`.

Normativní deliverables a exit gates jsou převzaté z R13 a všech nalezených development-plan-delta resources. Plánované cesty jsou konkrétní umístění budoucích výstupů; aplikace nebyla generována.

## P00 — Freeze SSOT and toolchain

Závisí na: aktuální kompletní návrhové gate a samostatné oprávnění freeze.

Plánované výstupy: `frozen-contract-pack/manifest.json`, `toolchain/locks/`, `audit/design-universe-results.json`.

Deliverables:

- R13 verifier packaged in repository
- effective Contract Pack extractor
- exact runtime/package lock manifests
- CI drift detector

Exit criteria:

- R13 whole-document verifier PASS
- dependency resolution exact and reproducible
- no unclassified lock drift
- freeze R14 browser source locks, Ubuntu apt snapshot ID, Playwright browser tuple and package-set digests
- generate exact apt name=version lock from snapshot and commit its digest

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
