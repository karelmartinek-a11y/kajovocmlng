# Bounded trusted generation policy publisher and historical own-kind dispatcher

Pinned input: 8cc19fbc69fb839ea88597b736da03d8b3eaecd4; canonical SSOT SHA-256 4ac6fe00df084e910a90093485b12172866be73db94f66b6815200556c35be06.

## Exact proposed effective clause (add after §12.55)

For each supported deployment epoch, the deployment installer registers one immutable generation policy package against the existing `(application_deployment_epoch, operation_contract_digest)` pin. The installer is the internal NOLOGIN/NOINHERIT `kcml_generation_policy_installer` role, distinct from the command writer and archive builder. It consumes exact normative schema, domain-policy, authority and available policy-implementation bytes. No OWNER request, model output, consumer parameter or public API can register or substitute those bytes. Unsafe preexisting role profiles fail startup without silently altering role attributes.

Initial admission invokes `kcml_pin_policy_acceptance_v1(context, prospective_command)` after the canonical actual credential verifier/context producer and before acquiring write locks for command/root/event/outbox/audit. It verifies the actual immutable acceptance receipt against current credential/session authority under class-B locks and retains a server-only ticket bound to context, prospective command and the current transaction ID. Invocation after those higher write locks fails `GENERATION_ARCHIVE_ACCEPTANCE_LOCK_ORDER`. Publication after protected snapshot/root insertion does not reacquire class-B locks or lock immutable deployment release rows: `kcml_publish_accepted_policy_package_v1(context, command, snapshot)` requires the same-transaction ticket and exact actual command/context/snapshot identities.

The publisher accepts no caller-supplied schema, policy, implementation bytes or authorization boolean. It archives only exact installer release members, verifies the closed package mask, all member bytes/digests and request-schema/policy identity, creates the unchanged request binding and an immutable accepted package binding, and participates in the existing atomic command/root/event/outbox/audit transaction. If a release is installed for the context epoch, a request-only archive is insufficient: deferred guards require the accepted package binding. Missing members or inconsistent request bindings abort the transaction. Within the same transaction publication is idempotent; a retained ticket does not authorize publication in a later transaction. Historical read/replay uses the retained package and prior outcome, rather than rerunning initial admission or treating this internal publisher as an idempotency gateway. Existing §49.4 lookup/reconciliation order is unchanged.

The package is an exact closed document, with explicit version, member `(kind,id,digest)` identities, request schema/policy addresses and an explicit statically supported entrypoint. The bounded `GENERATION_OWN_KIND_DISCUSSION_V1` entrypoint reproduces the existing UPDATE/RETRY/REPAIR admission rules over actual immutable source records and their frozen native schema bytes. It first applies the archived request schema and the two preexisting request rules, then actual own-kind lineage/authority/target/failure/evidence checks. Its output is discussion admission and does not grant execution/activation. All its available implementation dependencies are retained as actual source bytes. Executable dispatch is statically loaded trusted code with exact implementation/dependency digest comparison; archived Python is never evaluated. Unknown revision, unavailable source/schema/policy or conflicting selected `$id` aliases fails closed. A current global schema/policy or current source digest cannot substitute for an unavailable historical revision. Same schema ID across distinct selected historical packages is permitted; each selected closure has its own exact digest registry.

This bounded family does not certify all kind policies, the CAS effect classifier, native child consumer integration, deployment installer runtime provenance, or actual systemd credential delivery. Those remain separate explicit obligations. It does not close generation.job.create.

## Existing authority

- §12.51: independent UPDATE/RETRY/REPAIR selectors and actual-byte own-kind basis, discussion admission distinct from execution/activation.
- §12.52: physical root/context and atomic command/root/event/outbox/audit identity.
- §12.54: actual authentication/context/key chain and frozen schema/domain-policy/implementation requirements.
- §12.55: immutable available archives, exact pre-root transfer and remaining producer authority obligation.
- §49.4: stable retained outcomes, replay before new eligibility and exact request conflict.
- §51.7: global lock order and no lower-lock acquisition after higher classes.
- §51.10: immutable historical revisions and available historical content; no current-pointer substitution.
- §51.20: actual OWNER credential activation epoch binding.

## Integration files

- Embed `generation-trusted-policy-publisher.sql` unchanged as `database/generation-trusted-policy-publisher.sql` after canonical frozen/preroot archive modules.
- Copy `generation_own_kind_policy_v1.py` to scripts unchanged.
- Copy `generation_policy_package.py` to scripts unchanged; it resolves repository from SSOT and uses the adjacent versioned own-kind implementation.
- Keep fixture and outputs in this audit directory; coordinator must rerun against activated canonical SQL/helper bytes, not relabel the candidate proof.

Reproduction: `PGOPTIONS='-c client_min_messages=warning' /tmp/ssot-audit-venv/bin/python audit/generated/resume-8cc/archive/verify_publisher.py`.

The isolated role fixture bootstraps release installation with the local PostgreSQL administrator; it proves SQL role separation and authentic archive byte selection, not deployment-service installer attestation. Synthetic historical schema revisions are stored in actual PostgreSQL and exercise real static own-kind policy dispatch; they are explicitly synthetic history, not claims about an actual historical production admission. The two existing generic request rules are separately exercised and do not stand in for full kind policies.
