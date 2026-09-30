### 49.4 Idempotency scope a exactly-once observable outcome

Freeze scope přijaté operation je kanonická n-tice:

```json
{
  "contractKind": "NORMATIVE_CONSTRAINT_DECLARATION",
  "declarationId": "SSOT-DECL-151",
  "sourceSection": "### 49.4 Idempotency scope a exactly-once observable outcome",
  "clauses": [
    "operationContractId + operationContractRevision",
    "callerAuthorityKind",
    "stableCallerObjectId + stableCallerRevisionId",
    "businessTargetId nebo concurrencyResourceKey",
    "clientIdempotencyKey"
  ],
  "allClausesMandatory": true,
  "recordDefinition": "RegistryRequirement",
  "materializationRequiredBefore": "ARCHITECTURE_READINESS",
  "unknownBindingPolicy": "BLOCKED"
}
```

Pro OWNER session a `KCML_OWNER_API_KEY` je `callerAuthorityKind = OWNER_FULL` a scope se neliší podle session ID, zařízení, IP ani fingerprintu klíče. Pro interní runtime je source component/agent/automation revision součástí zmrazeného execution scope; stable caller object v locatoru se při jejím upgrade nemění. Worker ID, execution attempt, lease token, HTTP request ID, JSON-RPC request ID, provider call ID a process restart nejsou součástí business idempotency scope.

Kanonický idempotency record používá stavy:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "urn:kcml:generation-contracts:2#/$defs/SourceEnum152"
}
```

Přechody:

- neexistující record → `RESERVED` pouze unique insertem,
- `RESERVED` → `EXECUTING` při fenced claimu,
- `EXECUTING` -> `WAITING_FOR_INPUT` nebo `WAITING_FOR_RECONCILIATION`,
- `WAITING_FOR_INPUT` -> `EXECUTING` po atomic consume požadovaného inputu a fresh guards,
- `WAITING_FOR_RECONCILIATION` -> `EXECUTING` pouze po potvrzeném bezpečném retry s nezměněnou business identitou,
- `EXECUTING|WAITING_FOR_INPUT|WAITING_FOR_RECONCILIATION` -> `SUCCEEDED|FAILED_FINAL` pouze při známém odpovídajícím business outcome a splněném terminal/child/side-effect closure kontraktu,
- `RESERVED|EXECUTING|WAITING_FOR_INPUT|WAITING_FOR_RECONCILIATION` -> `CANCELLED_FINAL` pouze po cancellation linearizačním bodu, known effect outcomes a povinném cleanupu; neznámý effect tuto hranu zakazuje,
- non-terminal stav → `MANUAL_REVIEW` při neznámém outcome,
- `MANUAL_REVIEW → EXECUTING|WAITING_FOR_RECONCILIATION|SUCCEEDED|FAILED_FINAL|CANCELLED_FINAL` pouze exact OWNER resolution commandem s current evidence digestem,
- `SUCCEEDED`, `FAILED_FINAL` a `CANCELLED_FINAL` jsou immutable terminal stavy.

Stejný scope, key a request digest vrací current nebo terminal record. Stejný scope a key s jiným request digestem vždy vrací `IDEMPOTENCY_CONFLICT`. Retryable selhání jednoho attemptu neterminalizuje business idempotency record; vytvoří nový attempt pod stejným logical operation ID. Terminal failure se ukládá pouze tehdy, když kontrakt určuje, že stejný požadavek nemá být automaticky znovu proveden.

Exactly-once observable outcome znamená:

- právě jeden kanonický result/error digest,
- právě jeden terminal domain event,
- právě jeden active pointer outcome,
- opakovaný request vrací stejný outcome,
- pozdní nebo duplicitní worker nemůže výsledek změnit.

Exactly-once external execution se netvrdí, pokud jej neposkytuje target idempotency key nebo jednoznačná read-back postcondition. V takovém případě je bezpečným výsledkem `UNKNOWN` a `MANUAL_REVIEW`.

Idempotency record se nesmí odstranit ani expirovat, dokud může klient, queue, provider callback, task, MRTR exchange, browser run nebo recovery proces legitimně zopakovat danou logical operation. Po expiračním cleanupu se původní key nesmí přiřadit jiné business operaci v témže stabilním scope.

Stable lookup před vytvářením operation používá samostatný `idempotency_locator` s unique `(operation_family_id, caller_authority_kind, stable_caller_object_id, stable_business_target_key, client_key_digest)`. `operation_family_id` je trvalý serverový identifikátor, zachovaný i při rename nebo upgrade operation contractu. Locator odkazuje na právě jednu logical operation a její výše uvedený frozen revision scope. Session ID, credential fingerprint, aktuální contract/caller revision, worker, lease, aktuální epoch ani nově vytvořený context nejsou součástí locatoru.

`clientRequestDigest` se počítá pouze z kanonických caller-controlled business argumentů, původně požadovaného cíle a explicitně zaslaných CAS/revision guards podle pinned input schema. `executionDescriptorDigest` přidává zmrazené serverové revisions, bindings a authority/context metadata. Retry porovná první digest a druhý převezme z původního recordu; nepřepočítá jej z current registru. Změna serverové revision sama stejný požadavek nerozdělí na novou operation. Skutečně nový business příkaz musí použít nový client key.

Tombstone locatoru zůstává po odstranění detailu výsledku. Nemá-li už systém retention právo vrátit detail, vrátí deterministický výsledek podle retained terminal metadata, případně existující `IDEMPOTENCY_CONFLICT` s machine reason `RESULT_RETAINED_AS_TOMBSTONE`; nikdy nepoužije starý key k novému effectu. API vrací current operation odkaz i při nonterminal wait/recovery, nikoli nový create.

