### 51.12 Idempotency, request digest a logical operation creation

`domain_idempotency_record` obsahuje:

- `scope_digest bytea` s délkou 32,
- `key_digest bytea` s délkou 32,
- canonical key pouze pro OWNER debug,
- `request_digest bytea` s délkou 32,
- `logical_operation_id uuid`,
- lifecycle, state version a canonical outcome digests.

Povinné constraints:

```json
{
  "contractKind": "NORMATIVE_CONSTRAINT_DECLARATION",
  "declarationId": "SSOT-DECL-203",
  "sourceSection": "### 51.12 Idempotency, request digest a logical operation creation",
  "clauses": [
    "UNIQUE (scope_digest, key_digest)",
    "UNIQUE (logical_operation_id)",
    "CHECK (octet_length(scope_digest) = 32)",
    "CHECK (octet_length(key_digest) = 32)",
    "CHECK (octet_length(request_digest) = 32)"
  ],
  "allClausesMandatory": true,
  "recordDefinition": "RegistryPostgres",
  "materializationRequiredBefore": "ARCHITECTURE_READINESS",
  "unknownBindingPolicy": "BLOCKED"
}
```

Claim algoritmus je přesně:

1. již autentizovaný internal/session path může před singleton heads volitelně získat xact advisory lock `IDEMPOTENCY_SCOPE`; API-key acceptance caller-derived advisory lock před credential verification nepoužívá,
2. provede `INSERT ... ON CONFLICT DO NOTHING` s novým `logical_operation_id`,
3. provede `SELECT ... FOR UPDATE` podle `(scope_digest,key_digest)`,
4. porovná `request_digest` constant-time v aplikační vrstvě a byte equality v DB,
5. při shodě replayuje nebo pokračuje pod existujícím logical operation ID,
6. při neshodě vrátí `IDEMPOTENCY_CONFLICT` před root mutací a před side-effect intentem.

`ON CONFLICT DO UPDATE` se pro idempotency claim nepoužívá. Request digest, logical operation ID ani terminal outcome existujícího recordu se nikdy nepřepíší payloadem retry requestu.

Vytvoření `domain_command`, idempotency recordu a přijetí async operation je jedna transakce. Po class C idempotency a class D activation-domain admission zamkne všechny existující target aggregate rooty class E, znovu ověří expected state/revision/binding/activation snapshot a teprve potom vloží `domain_command` child ordinal `35` a queue/outbox ordinal `900|910`. CREATE bez existujícího target rootu zamkne jeho stable parent/namespace guard a first-create advisory podle operation contractu. Worker execution všechny guards znovu ověří; acceptance lock není náhradou execution CAS. HTTP `202` lze vrátit pouze po commitu commandu a queue/outbox row. Ztracená HTTP odpověď se řeší replayem stejného idempotency key.

Před class C claimem revision-pinned domain recordu se provede stable locator lookup podle 49.4. `idempotency_locator` je součást class C se subordinalem `0`; `domain_idempotency_record` má subordinal `1`. Oba se řadí podle canonical key digestu uvnitř své subtřídy. `UNIQUE(operation_family_id, caller_authority_kind, stable_caller_object_id, stable_business_target_key, client_key_digest)` a `UNIQUE(logical_operation_id)` spolu s deferred FK na doménový record fyzicky vynutí jednu operation. Hodnoty jsou non-null; pro CREATE použije target key stabilní namespace/create request identitu, ne právě generované UUID.

Terminal replay neprovádí fresh command admission a žádný target lease či activation lock nepoužívá k rozhodnutí o novém effectu. Autentizace a přístup k výsledku zůstávají povinné. Nový command vloží locator a doménový record atomicky s command/queue; concurrent konflikt znamená read-and-compare, ne zvýšení revision scope a druhý insert.

