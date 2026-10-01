# Independent execution review

Reviewer `sql_helpers` did not design consumer, archive or RETRY candidates. SQL-helper proposals in the parent directory are deliberately not self-certified by this independent review.

## Consumer counterexamples

Three existing self-consistent wrong-runtime/job result receipts were independently executed through the old native outcome validator, which accepted them. All three candidate adapter paths reject the exact `OWNER_UI_WORKER_TARGET_MISMATCH` after valid result/event digests.

Four additional actual acceptances were found: for dashboard.start and dashboard.stop, a schema-valid retained worker request could select a different runtime UUID or generation while its result matched the original intent's target. The adapter checked result→intent but omitted worker request→intent. `actual-pre-fix-defects.json` preserves those executions. Author added both exact runtime identity/generation checks. The independent verifier then replayed all four original counterexamples and now gets exactly `OWNER_UI_WORKER_ARGUMENT_BINDING_MISMATCH`.

Current `independent-consumer-review.json`: **12 PASS**, including three valid bounded witnesses, three old wrong-target rejections, four corrected worker request mismatches, NEW_DRAFT/base revision rejection and a schema-valid SAME_CANONICAL_REVISION historical producer block. An initial reviewer SAME_CANONICAL fixture mistakenly retained the NEW_DRAFT-only state field and hit the schema validator; it was corrected and its invocation record retained separately. That invocation failure is not called a product/contract defect.

These are pure reference repository execution checks. The adapter still returns BLOCKED_PENDING_EFFECT_HYDRATION, and trusted repository/context, actual domain receipt bytes and full UI workers remain OPEN.

## Actual PostgreSQL reproductions

- `retry/`: **33 PASS**, separate DB `retry_independent_sql_905`; exact canonical foundation + locked scan bytes, candidate membership/child extension, real phase scans and classification, SQL child commit, concurrent mutation/retry, stale fence, rollback and replay. The original fixture program is copied/adapted into this owned directory only, preserving exact proposal bytes. No peer directory or shared DB is changed.
- `archive/`: **32 PASS**, separate DB `archive_independent_sql_905`; exact canonical foundation + read bytes, candidate archive extension, actual archive publication/content/binding with one root/event commit, historical schema/policy bytes, wrong bindings and duplicate publication contention. The synthetic authentication receipt and opener still do not prove OWNER API credentials or canonical systemd key.

Both extension proofs are explicitly candidate proofs until their embedded canonical resource equality and effective root helper use are reproduced after integration. They do not certify whole generation.job.create, full §49.8 producer completeness or request selector/kind policy archive dispatch.

## Integrated reproduction at 4f9d6573

The final independent executions assert candidate equality and execute actual embedded `database/generation-frozen-archive.sql`, `database/generation-retry-producer-child.sql` and `database/generation-locator-lock.sql`. Archive tests now use the effective root archive/read/consumer/policy modules with explicit module path assertions, not copied candidate modules. Integrated archive **37 PASS** includes five legitimate baseline-derived malformed-binding and unavailable-repository cases with exactly `FROZEN_POLICY_BINDING_INVALID` / `FROZEN_POLICY_REPOSITORY_UNAVAILABLE`; no KeyError or unrelated schema failure counts. Integrated RETRY remains **33 PASS**, canonical retained locator **7 PASS**, effective root consumer **12 PASS**. `installed-canonical-objects.json` independently queries actual `pg_class`, `pg_proc` and `pg_roles` for **98 named objects**, all present after exact resource execution. Object presence does not certify full runtime service-role authority. Actual API verifier/systemd key and full §49.8 dispatch/raw-evidence production remain explicitly outside these fixture scopes.
