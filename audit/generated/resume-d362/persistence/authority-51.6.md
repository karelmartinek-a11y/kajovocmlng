### 51.6 Jediné kanonické pořadí row locků

Všechny transakce v systému získávají row locky v tomto úplném pořadí; přeskočené třídy se ignorují, pořadí zbylých se nemění:

```json
{
  "contractKind": "NORMATIVE_CONSTRAINT_DECLARATION",
  "declarationId": "SSOT-DECL-198",
  "sourceSection": "### 51.6 Jediné kanonické pořadí row locků",
  "clauses": [
    "A. transaction-scoped advisory locks: (namespace_id ASC, signed_key ASC)",
    "B. singleton authority heads:",
    "   B1 platform_incarnation singleton FOR SHARE",
    "   B2 application_deployment_head singleton FOR SHARE",
    "   B3 owner_api_credential FOR SHARE při API-key acceptance nebo FOR UPDATE při rotaci",
    "   B4 activation_head singleton FOR UPDATE pouze při alokaci epoch",
    "C. idempotency_locator subordinal 0, domain_idempotency_record subordinal 1: canonical key digest order uvnitř subtřídy",
    "D. activation_domain_head: domain_key byte order",
    "E. aggregate roots: (aggregate_kind_ordinal, aggregate_uuid raw bytes)",
    "F. concurrency_claim: (namespace_id, key_digest)",
    "G. dedicated sequence allocator rows: (sequence_namespace, parent_uuid, sequence_kind)",
    "H. mutable child/head/claimable-work rows: (child_kind_ordinal, primary_parent_uuid, child stable ID/sequence)",
    "I. audit_head singleton FOR UPDATE"
  ],
  "allClausesMandatory": true,
  "recordDefinition": "RegistryPostgres",
  "materializationRequiredBefore": "ARCHITECTURE_READINESS",
  "unknownBindingPolicy": "BLOCKED"
}
```

Kanonické `aggregate_kind_ordinal` je stabilní serverový enum. Greenfield baseline obsahuje úplné mapování všech samostatně zamykaných rootů; čísla se nikdy nepřidělují podle názvu tabulky ani pořadí migrace:

| Ordinal | Aggregate kind | Kanonický root row |
|---:|---|---|
| 10 | `OWNER_IDENTITY` | `owner_identity`; session/MFA/recovery/throttle jsou children |
| 20 | `SECRET_RECORD` | `secret_record` |
| 30 | `COMPONENT` | `component`; revisions/contracts/releases/readiness/E2E jsou children nebo immutable rows |
| 45 | `EXTERNAL_TARGET` | `external_target`; mutable circuit fields jsou součástí tohoto root row |
| 60 | `AGENT_DEFINITION` | `agent_definition`; eval suite/cases/runs jsou children |
| 70 | `BROWSER_SESSION` | `browser_session`; page/frame/lease/input/action/challenge/teaching jsou children |
| 75 | `BROWSER_ACCOUNT_BINDING` | `browser_account_binding`; state-bundle revisions jsou immutable children |
| 80 | `BROWSER_AUTOMATION_DEFINITION` | `browser_automation_definition` |
| 85 | `BINDING_SET` | `binding_set`; revisions a members jsou immutable children |
| 90 | `GENERATION_JOB` | `generation_job`; turn/phase/plan/workspace/validation/checkpoint jsou children |
| 100 | `AGENT_RUN` | `agent_run`; model/tool/handoff/approval/checkpoint jsou children |
| 105 | `AGENT_SESSION` | `agent_session` |
| 106 | `SYSTEM_CHAT_CONVERSATION` | `system_chat_conversation` |
| 107 | `AGENT_MEMORY_NAMESPACE` | `agent_memory_namespace` |
| 110 | `MCP_CALL_RUN` | `mcp_call_run`; progress/input-exchange/subscription jsou children |
| 115 | `MCP_TASK` | `mcp_task` |
| 116 | `MCP_STATE_HANDLE` | `mcp_state_handle` |
| 120 | `GENERATION_ACTIVATION_SET` | `generation_activation_set` |
| 125 | `BROWSER_AUTOMATION_RUN` | `browser_automation_run`; run steps jsou children |
| 127 | `RUNTIME_INSTANCE` | `runtime_instance`; process/IPC identity rows jsou children |
| 130 | `DEPLOYMENT_RUN` | `deployment_run`; deployment steps jsou children |
| 140 | `OPERATIONAL_SETTING` | `operational_setting` |
| 145 | `CONFIGURATION_APPLY_RUN` | `configuration_apply_run` |
| 150 | `CLEANUP_OPERATION` | `cleanup_operation`; cleanup resources jsou children |
| 155 | `OPERATIONAL_ALERT` | `operational_alert`; deliveries jsou children/outbox work |
| 165 | `SELF_TEST_RUN` | `self_test_run`; case results jsou children |
| 166 | `PRODUCTION_ACCEPTANCE_RUN` | `production_acceptance_run` |
| 170 | `SCHEMA_MIGRATION` | `schema_migration` persistentní migration step/root |

MCP server/tool/resource/prompt identity a revision rows jsou vždy children kanonického `COMPONENT = 30`; nemají alternativní root kind. `application_release`, immutable revisions/evidence a immutable provider/output rows se nezamykají jako mutable root. Pokud jedna mutable child row odkazuje na více parent rootů, operation před child lockem zamkne všechny tyto rooty podle tabulky.

`owner_api_credential`, `platform_incarnation`, `application_deployment_head` a `activation_head` zůstávají ve singleton class B; `activation_domain_head` ve class D; `concurrency_claim` ve class F; `audit_head` ve class I. Každý root row má UUID `id`; stable text key je samostatný unique business key a nikdy se nepoužívá místo UUID v row-lock sortu.

Nový aggregate kind dostane nový nikdy nerecyklovaný ordinal. Ordinal již zveřejněný v migraci se nesmí změnit. Bulk operation před `BEGIN` kanonicky seřadí celý známý target set; během transakce nesmí objevit další dříve řazený root. Pokud je nový root zjištěn až po locku, transakce rollbackne a začne znovu s úplným setem.

`INSERT`, `UPSERT`, first-create unique-index wait a získání row locku nad mutable rootem se pro lock-order pravidla považují za získání jeho class E slotu. Root insert se proto provede až na jeho seřazené pozici po všech nižších rootech.

Class G obsahuje pouze dedicated sequence allocator, pokud čítač není přímo v již zamknutém rootu. Class H používá tento stabilní baseline `child_kind_ordinal`:

| Child ordinal | Mutable child/work kind |
|---:|---|
| 10 | OWNER session/MFA/recovery/throttle state |
| 20 | Secret version lifecycle, binding a invalidation child |
| 30 | Component pointer/runtime/control/readiness child |
| 35 | `domain_command` mutable lifecycle row |
| 40 | Activation admission, barrier a switched-member projection |
| 50 | Generation turn/phase/checkpoint/workspace mutable head |
| 60 | Agent model/tool/handoff/approval child |
| 65 | Agentic authority intent/context/action-plan/provenance mutable child |
| 70 | MCP progress/input exchange/subscription child |
| 80 | Browser control lease/input/action/challenge child |
| 90 | Browser automation run-step child |
| 100 | Runtime process/IPC/credential-generation child |
| 110 | Deployment step child |
| 120 | Cleanup resource child |
| 130 | Configuration effective, monitoring projection a alert-delivery child |
| 140 | `side_effect_operation` mutable state |
| 150 | Mutable attempt/delivery projection nad immutable attempt evidence |
| 900 | `queue_item` claim/enqueue row |
| 910 | `transactional_outbox` a delivery-claim projection; audit archive row má zvláštní insert pravidlo 51.25 |
| 920 | `transactional_inbox` row |

Immutable child insert má stejný ordinal svého druhu, i když nevyžaduje následný row lock. `primary_parent_uuid` je explicitní non-null lock-parent column; u multi-parent child určuje pouze H sort, nikoli ownership, a všechny skutečné parent rooty musí být již zamknuté. Ordinal 900–999 je rezervovaný pro claimable work/delivery rows, takže successor queue/outbox/inbox insert proběhne po všech doménových child rows a před audit headem. Nový child kind dostane explicitní nikdy nerecyklovaný ordinal v migration manifestu; runtime nesmí odvozovat pořadí z názvu tabulky nebo OID.

`audit_head` se vždy zamyká poslední. Doménový diff, event payload a všechny outcome digests musí být před jeho lockem definitivní. Tím se globální chain serializace nestane příčinou lock-order inversion.

Každý insert/update/delete mutable child row, který patří do aggregate invariantu, nejprve zamkne jeho parent aggregate root. Jedinou výjimkou je worker delivery claim nebo delivery-marker update class H ordinalů `900|910` podle 51.14; ten nesmí měnit parent business state a před dispatch má samostatnou fresh parent-root transakci. Proto je ostatní child-set predicate vyhodnocený pod parent lockem stabilní vůči korektním writerům; unique/FK constraints zůstávají konečným guardem proti nekorektnímu nebo budoucímu writeru.

Lock plan každé operation je testovatelná metadata. Runtime v test/debug režimu zaznamenává pořadí získaných lock classes a odmítne operation, která se pokusí získat nižší class po vyšší.

