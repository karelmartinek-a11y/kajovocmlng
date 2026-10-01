# Repair explicit SSOT boundaries and finite completion dependencies

The SSOT still contains generic masks, unresolved references and incomplete
producer–consumer handoffs. This branch preserves prior repairs, publishes exact
create/import and lifecycle boundaries, and separates normative definitions,
authority-backed pre-generation fixtures and future implementation acceptance.

The latest integration enforces the five final gate families required by §73.7,
defines exact retained-result/tombstone errors, corrects dedicated OWNER key
reveal API/session scope, and publishes OWNER session list/revoke and Audit
list/read masks. Audit reading includes required pre-root retained outcomes.
Four MCP native references are resolved without making optional native metadata
mandatory. Four SQL helpers are defined for two scoped OWNER query wrappers;
260 typed wrapper implementations remain unresolved and none is runtime-enabled.

Verification uses the audit requirements environment, positive-derived negative
cases and actual canonical PostgreSQL 18.6 fixtures. Historical execution hashes
remain unchanged; current reuse requires matching consumed sources. Current
runner results and integrity are recorded in audit/SSOT_REPAIR_CHECKPOINT.json.

Both create operations remain open. SSOT_CONTRACT_READY remains BLOCKED and
IMPLEMENTATION_PRODUCTION_ACCEPTANCE remains NOT_EVALUATED. Actual systemd
credential fixture is blocked by unavailable manager/bus capabilities. No
application generation, merge, release or deployment is performed.

Compare: https://github.com/karelmartinek-a11y/kajovocmlng/compare/main...ssot-repair-2026-09-30
