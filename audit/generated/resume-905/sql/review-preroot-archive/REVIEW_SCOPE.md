# Independent pre-root frozen archive review

Pinned HEAD32a63a9e3447bd4ed9a7dc4638cadc113071a8b7, canonical SHA256a2bdb08ec729881087e59d7a3fd31053c1e0989bb5b3c640a65cf698a75af4b5. Reviewer did not author the proposed extension; only this directory is owned for this task.

Existing effective `database/generation-create-preroot.sql` preserves accepted pending/failure snapshots without a generation job. The same command/context/prospective job identity transfers to the successful snapshot; `kcml_generation_command_context_consistency_v1` already rejects changed snapshot/schema/content/ciphertext/nonce/algorithm/key/profile bytes. Existing successful archive binding references the successful snapshot physically, so cannot certify an accepted pre-root archive simply by inserting its digest into that success table. Exact original schema/domain-policy/authority/implementation bytes and declared dependencies must exist before retained acceptance and survive later success.

Independent checks will retain these distinctions:

- accepted pending with archived bytes creates no generation root/event/outbox;
- missing pre-root archive rolls back the accepted command, protected snapshot and retained pending outcome atomically;
- later success preserves original protected bytes **and** original schema/policy/dependency archive selection;
- same schemaID with different genuine available digest or a different genuine policy digest must not silently replace frozen selection;
- rollback leaves earlier accepted pending, audit and archive history intact;
- successful direct create continues using the existing success archive contract;
- retained prior outcomes and archive references cannot be rewritten/deleted after success;
- canonical SQL execution and fixture synthetic auth/opaque crypto remain separate evidence categories.

No pre-root archive proof is claimed until candidate execution and independent counterexamples are recorded here. Full admission/kind policy and trusted archive producer authority remain separate obligations.
