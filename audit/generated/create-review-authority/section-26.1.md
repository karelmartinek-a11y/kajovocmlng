### 26.1 Obecná pravidla

API root je `https://kaja.hcasc.cz/api/v1`. Response používají JSON, ISO 8601, UUID, stabilní enumy, cursor pagination a deterministic sort.

Každý OWNER endpoint přijímá OWNER session nebo jediný `KCML_OWNER_API_KEY` a po autentizaci používá konstantní `OWNER_FULL`; neexistuje role/scope autorizace. UI, chat a API key volají stejnou doménovou operaci.

Každá mutace deklaruje:

- povinný `Idempotency-Key` a jeho scope,
- `If-Match` nebo body `expectedStateVersion` pro nekomutativní změnu,
- expected revision/digest, binding-set revision, activation/control epoch a checkpoint digest podle operace,
- authority-lineage, OWNER-intent a operation-context digests u agentní/modelové/browserové nebo content-derived operace,
- side-effect, retry a concurrency class,
- synchronous linearization point nebo durable async operation reference.

Authority-lineage, OWNER-intent a operation-context fields jsou authoritative server-derived metadata; OWNER/API klient, model ani business payload je nesmí zvolit nebo přepsat. Root OWNER command posílá pouze business požadavek a běžné CAS/idempotency guards; gateway semantic context sestaví a persistuje před modelovým nebo mutujícím dispatch.

UI idempotency key vytvoří před prvním sendem a při retry jej zachová. Chybějící povinný key nebo CAS guard je validation error před doménovým handlerem. Timeout klienta serverový command neruší.

Operation catalog:

```json
[
  {
    "method": "GET",
    "pathSegments": [
      {
        "literal": "operations"
      },
      {
        "literal": "catalog"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.1 Obecná pravidla",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "POST",
    "pathSegments": [
      {
        "literal": "operations"
      },
      {
        "parameter": "operationKey",
        "schemaDefinition": "Id"
      },
      {
        "literal": "invoke"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.1 Obecná pravidla",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  }
]
```

Success `meta` obsahuje `correlationId`, `logicalOperationId`, `commandId`, current `stateVersion`, `eventSequence`, `activationEpoch`, `resultDigest`, `idempotencyReplay` a `serverTime`. Async `202` znamená commitnutý command+queue/outbox, nikoli dokončený side effect.

Conflict response vrací stable code, current snapshot/version/digests a canonical next action. Standardní error envelope zachovává classification, details a correlation. Přesný concurrency/recovery contract je v 49.27.

