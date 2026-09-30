# SQL review at 5334d8c

The review covers all 262 operation wrappers and all 1,048 calls to the four helpers. It does not certify executable SQL or close either create operation.

`helper-review.json` supplies source/resource digests, exact helper obligations, two create transaction plans, A/B/C gate classification, and six isolated syntax/design checks. No undecidable business question was identified for these SQL gaps.

## Integration-ready bounded repair

`explicit-entities-proposed.sql` changes only the existing `idempotency_locator.logical_operation_id` declaration:

- adds `UNIQUE`, as explicitly required by §49.4/§51.12;
- makes its existing FK `DEFERRABLE INITIALLY DEFERRED`, preserving the existing `domain_command(logical_operation_id)` target and deletion rule.

This does not resolve three mismatched final locator column names, missing physical context/helper definitions, or any runtime gate. Coordinator should revalidate the exact original embedded resource digest, author the proposal into `database/explicit-entities.sql`, update affected resource manifests/projections, and rerun current syntax/design/integrity checks. Do not set helper availability PASS merely because this locator repair passes.

## Important current findings

- All four helpers lack definitions in the effective direct SQL registry.
- `kcml_operation_context_v1` also lacks a physical type definition. A caller-controlled JSON field or model assertion cannot supply trusted server authority.
- `generation.job.create` has a generic wrapper rooted at `generation_job`, ordinal90. Its 24 descriptive semantic-field/storage-fallback entries are not exact column assignments.
- `secret.create` has no wrapper in this source. Both create operations still require typed physical mutations and receipt/event/hydration joins.
- Direct SQL resources do not materialize `generation_job`, `secret_record`, `secret_version`, `domain_command`, `domain_idempotency_record`, `domain_event`, `domain_outbox`, platform/deployment heads, or `audit_head`. This search is explicitly scoped to direct `.sql` resources; prose/entity declarations are separate evidence, not executable table definitions.
- Generic helper interpreter implementation would merely conceal those unresolved bindings. No always-success or always-failing helper stubs were proposed.

## Reproduction and limits

```sh
/tmp/ssot-audit-venv/bin/python audit/generated/resume-5334/sql/verify_and_propose.py
```

The script is pinned to the recorded input SSOT snapshot and refuses a changed source. It writes only this isolated audit directory. All six checks passed: PostgreSQL17 syntax AST, actual uniqueness/deferred-FK clauses, preservation of the existing FK target, and two negatives derived from the valid proposal that independently remove the tested clause while retaining valid SQL syntax.

PostgreSQL18.6 execution, migration roles, actual locks/races/rollback/outbox recovery and production implementation are NOT_EVALUATED. The syntax parser's AST uses separate `CONSTR_ATTR_DEFERRABLE`/`CONSTR_ATTR_DEFERRED` nodes; the verifier checks those actual nodes rather than mistaking absent convenience flags for a contract defect.

## Independent exact advisory-key technical proposal

`postgres-advisory-key-proposed.sql` defines a standalone `kcml_postgres_advisory_key_v1(bytea)` projection of §51.8: validate the full32-byte digest, read the first four bytes unsigned big-endian, then preserve its bit pattern as signed int4. It explicitly gives no authority or identity; singleton namespace1000 continues using literal key0. Secret first-create namespace1020 is explicitly normative and needs no owner decision.

`verify_advisory_key.py` passes14 checks: PostgreSQL17 outer+PLpgSQL syntax, nine independently computed Python/Node boundary vectors, two invaliddigest negatives derived from a valid digest, and two concrete counterexamples to little-endian/unsigned-overflow mutants. This establishes reference vectors and syntax, not execution of the SQL function. A future real PostgreSQL18.6 test must run those same vectors against the installed function and prove role/grant/migration integration. This additional helper does not substitute for the four missing operation helpers.

## Exact generation create persistence continuation

`generation-create-transaction-contract.json` is a source-bound normative proposal for typed protected initial-request snapshot, exact conditional FOLLOW_UP basis and frozen completion rows, ordered transaction/replay/hydration conditions, and six precisely named mandatory technical dependencies. Native capsule authority was also inspected: `EntitySourceRecord#/records/73` has no fieldAuthorities; `PostgresOperationDesign#/records/222` still uses descriptive CAS and T1/T3 phase labels rather than executable per-column guards. Those projections do not supply missing root/context definitions.

`generation-create-persistence-proposed.sql` supplies three exact subordinate tables and immutable UPDATE triggers. It deliberately depends on the real `generation_job`/`domain_command` roots; it does not substitute minimal fake roots or an always-trusted context. Complete event/outbox/audit/snapshot/publication FKs and retention authority remain prerequisites. Protected canonical initialrequest includes any directcredential without automatically making a Secret record. Algorithm/key/profile identifiers are server-selected under existing Secrets policy; nonempty SQL identifiers alone never authorize them.

`generation_create_reference.py` passed17 scoped checks: real synthetic AEAD encryption/decryption, correct typed/canonical hydration, exact schema/digest/authentication negatives, no credential in public receipts/events/outbox, real isolated SQLite atomic commit/replay/conflict/rollback/unknown behavior, and PostgreSQL17 DDL/PLpgSQL parser checks. Fixture stateVersion0 is not a proposed production constant. AESGCM is only the installed fixtureprovider; its use does not choose the production canonical algorithm. Versions and exact source/SQL hashes are in `generation-create-persistence-proof.json`. PostgreSQL18.6 native SQL/helper/role/locks/runtime behavior remains NOT_EVALUATED.

No full `generation.job.create` closure is claimed. Coordinator can author the typed persistence sub-contracts, then fill the named physical/context/crypto/pending/event joins and compose actual owned-kind admission/consumer evidence before evaluating the whole operation.
