# Whole-operation design closure at resume 5334

Both operations remain **BLOCKED**; whole design-closed operations: **0 / 619**. Select `generation.job.create` next: its product rule for FOLLOW_UP is approved, while `secret.create` additionally depends on nine pending concrete Secret type formats. Selection is about dependencies, not the number of fixtures.

A = mandatory design contract before generation; B = can be checked with a design/reference proof; C = acceptance requiring a future implementation. A and B overlap: a reference proof may verify a mandatory design requirement. C does not replace A. Effective §73.7 still requires the final R10/R16/UI/CLOSURE/R17 family with zero mandatory blockers; no gate was weakened or moved.

| Obligation / own authority | generation.job.create | secret.create | Stage and remaining evidence |
|---|---|---|---|
| Exact request/HTTP decoding (§12.47, §8.11) | Exact mask/strict JSON/query/header decoder, positive witnesses | Exact mask/strict JSON/query/header decoder, positive witnesses | A/B bounded VERIFIED; actual HTTP server C |
| Admission (§12.41, §12.49, §25.11 / §8.2–8.11, §25.6) | Own UPDATE/RETRY/REPAIR selectors, actual basis sufficiency and referenced-object admissibility unresolved | Nine complex type formats, reserved-value and target/purpose policies unresolved | A/B BLOCKED; no boolean policy flag or mere object existence closes it |
| Response/error/event (§12.48–12.49, §49.4–5) | Exact frozen create output and generation.job.created receipt | Exact CREATED output and OPERATION_TERMINAL receipt | A/B bounded proofs; individual domain error predicates and full operation handoffs still A; real publishing C |
| Persistence/transaction/concurrency (§25.11/25.6, §49.4–5, §51.12) | Protected initial request, immutable basis/completion proposal; unresolved complete root/context/event-outbox-audit FK joins | Stable name/version/root, bindings and full joins not closed | A exact executable design/transaction contract; B synthetic atomicity/parser proofs; C real concurrent deployment execution. PostgreSQL design fixtures required by R17 remain pre-generation where normative, not automatically C |
| Read/hydrate/consumer (§12.49, §13.15, §8.4–8.8) | Frozen byte reference works; actual request/spec/artifact schema and sufficient basis validators remain | Pending import-to-stored conversion, exact-byte version hydration and consumer profiles | A/B BLOCKED; real adapters/permissions/crypto behavior C |
| UI (§43.3, §49.3–5, effective UI registry) | generic job read/snapshot boundaries remain | generic metadata/version/reveal boundaries remain | A/B full typed UI handoffs remain; current reference renderer checks layout/interactions only; actual app UI C |

## Own generation kind rules; no borrowed lifecycle

- UPDATE preserves component/runtime identity and requires compatibility/migration planning for candidate revision/release (§12.41). A migration plan is an execution/activation prerequisite; it must not be invented as a terminal-source-job rule for starting discussion.
- RETRY preserves the same approved functional authority, addresses the failed technical part only and creates separate attempt records (§12.41). Exact failed-part identity and retained approved bytes must be authored, not inferred from the parent job's name/state.
- REPAIR uses monitoring evidence and last approved functional lineage, preserves identity and changes technical realization only; activation needs complete regression (§12.41). Do not force a parent job where the own monitoring lineage can bind the target directly.
- FOLLOW_UP follows the approved immutable snapshot/revision rule (§12.49): nonterminal source is allowed if the selected actual basis is available, consistent and sufficient; required unpublished final output rejects. No second owner approval is requested.

The current reference admission now returns the already defined `PARENT_TARGET_ADMISSION_POLICY_UNVERIFIED` (HTTP `CREATE_POLICY_UNRESOLVED`) for fresh UPDATE/RETRY/REPAIR while their exact persisted policies remain missing. Valid request shapes and synthetic authority flags cannot bypass it. Frozen replay is evaluated first and retains its existing semantics. This closes an unsafe reference acceptance gap, **not** the own kind policy obligation.

SQL helper review: four call-site helpers and `kcml_operation_context_v1` lack resolved executable definitions; generation has an existing generic wrapper, Secret does not have its own resolved wrapper. Complete physical root/field authorities and transaction joins are mandatory A. Locator uniqueness/deferred FK and the pure signed advisory-key projection are bounded technical repairs, not helper closure.

Next coherent block: materialize the own generation persisted selectors and byte validators, then full trusted context/root/atomic completion joins, read hydration and UI input/result postconditions. Re-run own-kind positive/negative witnesses before claiming a whole operation. Lifecycle and UI helper findings are source-bound review inputs, not current PASS for the canonical contract; six open state fields and three exposure blockers are retained.
