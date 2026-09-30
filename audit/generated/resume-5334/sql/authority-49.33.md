### 49.33 Persistentní platform recovery state machine

`platform_recovery_head` je singleton mutable aggregate s immutable recovery attempts. Používá pouze stavy:

```json
{
  "modelId": "model.platform-recovery",
  "schemaVersion": "2.0",
  "states": [
    "BLOCKED",
    "MANUAL_REVIEW",
    "READY",
    "RECONCILING",
    "STARTING"
  ],
  "initialStates": [
    "STARTING"
  ],
  "terminalStates": [],
  "edges": [
    {
      "from": "BLOCKED",
      "to": "MANUAL_REVIEW",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.33"
    },
    {
      "from": "BLOCKED",
      "to": "RECONCILING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.33"
    },
    {
      "from": "MANUAL_REVIEW",
      "to": "RECONCILING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.33"
    },
    {
      "from": "READY",
      "to": "STARTING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.33"
    },
    {
      "from": "RECONCILING",
      "to": "BLOCKED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.33"
    },
    {
      "from": "RECONCILING",
      "to": "MANUAL_REVIEW",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.33"
    },
    {
      "from": "RECONCILING",
      "to": "READY",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES"
      ],
      "authoritySection": "49.33"
    },
    {
      "from": "STARTING",
      "to": "RECONCILING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.33"
    }
  ],
  "writerId": "writer.platform-recovery",
  "authoritySection": "49.33",
  "deniedByDefault": true,
  "successRequiresKnownOutcome": true,
  "terminalClosureSeparate": true
}
```

Každý attempt obsahuje current database start identity, platform incarnation, application deployment epoch, recovery epoch, state version, lease owner/fence/expiry, started/finished time, inventory watermark, schema/constraint digest, classification counts, unresolved object IDs a evidence digest. `READY` je platné pouze pro exact n-tici, která byla reconciliována; změna kteréhokoli členu ji okamžitě zneplatní.

Mutující admission transakce pod shared recovery guardem ověří, že:

1. existuje právě jeden current head,
2. head je `READY`,
3. current database start identity odpovídá persistovanému `readyDatabaseStartIdentity`,
4. platform incarnation a application deployment epoch odpovídají request/worker snapshotu,
5. recovery epoch a state version jsou current,
6. požadovaný domain scope nemá blocking unresolved recovery item.

Nesoulad vzniká před side-effect intentem a vrací `PLATFORM_RECOVERY_IN_PROGRESS` nebo `PLATFORM_RECOVERY_BLOCKED`. Read-only diagnostika může pokračovat, nesmí však získat žádnou write nebo dispatch authority.

Recovery inventory zahrnuje všechny nonterminal roots, queue/outbox/inbox items, leases, concurrency claims, side-effect operations/attempts, model calls, MCP calls/tasks/input exchanges, agent runs, browser sessions/actions/downloads/uploads, runtime instances/processes/sockets, generation phases, activation/deployment/rollback/cleanup operations a filesystem pointers/artifacts. Každá položka získá právě jednu persistovanou klasifikaci:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "urn:kcml:generation-contracts:2#/$defs/SourceEnum182"
}
```

Klasifikace a successor enqueue se commitují atomicky. Recovery worker lze zabít před/po každém itemu; takeover pokračuje pod vyšším fence bez opakovaného external dispatchu. `READY` se commitne pouze po stabilním druhém inventárním průchodu, nulovém unclassified item countu, platných constraints/pointer digestech a uzavření všech mandatory startup blockers.

