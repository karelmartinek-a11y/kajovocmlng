# Independent integrated retained-reason review

Current source `ad98ebff9e2056c2596b04a0ea31870b3c89520c6f9ab2bd6e26e13ce0a54706`. Re-executed actual root `verify_create_completion.py`:449 checks, zero failures. Independently tested canonical masks:51 PASS/0, covering both create operations and both HttpCreateFailure projections, exact tombstone positives; wrong reason/code/classification/retry/status; nonterminal terminal-outcome rejection; required legacy error fields; forbidden extra/sensitive-output fields. machineReason remains optional: valid legacy errors still validate and no existing required field is weakened.

Actual authoring --check paths close_create_completion, close_create_operation_requests and close_secret_retention_contract all pass. This binds the three current canonical resources and four source helper/authoring hashes recorded in the report. Derived masks are reproducible rather than hand-patched.

No new domain.command.outcome.updated stream entered either completion or payload resource. No retention cleanup/PG sentinel producer was activated. The source8.17 clarification remains bounded and does not close these obligations.

These are definition and reference-completion relations, not generated application/real systemd acceptance. Sensitive named value fields/receipt echoes are rejected; arbitrary diagnostic message confidentiality still requires the explicit safe producer contract and cannot be proved solely by a string schema. Whole create operations remain open; implementation acceptance NOT_EVALUATED.

Reproduce the independent cases with verify_integrated_retained_masks.py; completion-tests.json is a separate actual449 root invocation with KCML_AUDIT_OUTPUT pointing to this owned directory.
