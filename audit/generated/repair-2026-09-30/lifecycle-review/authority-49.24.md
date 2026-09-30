### 49.24 Application deployment a disaster recovery

Deployment run používá fenced state machine:

```json
{
  "modelId": "model.application-deployment",
  "schemaVersion": "2.0",
  "states": [
    "ACTIVE",
    "BACKED_UP",
    "FAILED",
    "MANUAL_REVIEW",
    "MIGRATING",
    "PREPARING",
    "QUEUED",
    "RESTARTING",
    "ROLLED_BACK",
    "ROLLING_BACK",
    "STAGING",
    "SWITCHING",
    "VERIFYING"
  ],
  "initialStates": [
    "QUEUED"
  ],
  "terminalStates": [
    "ACTIVE",
    "FAILED",
    "ROLLED_BACK"
  ],
  "edges": [
    {
      "from": "BACKED_UP",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "BACKED_UP",
      "to": "MIGRATING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "BACKED_UP",
      "to": "ROLLING_BACK",
      "guardIds": [
        "PRECONDITIONS",
        "ROLLBACK"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "MANUAL_REVIEW",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "MANUAL_REVIEW",
      "to": "ROLLING_BACK",
      "guardIds": [
        "PRECONDITIONS",
        "ROLLBACK"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "MANUAL_REVIEW",
      "to": "VERIFYING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "MIGRATING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "MIGRATING",
      "to": "MANUAL_REVIEW",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "MIGRATING",
      "to": "ROLLING_BACK",
      "guardIds": [
        "PRECONDITIONS",
        "ROLLBACK"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "MIGRATING",
      "to": "STAGING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "PREPARING",
      "to": "BACKED_UP",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "PREPARING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "QUEUED",
      "to": "PREPARING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "RESTARTING",
      "to": "MANUAL_REVIEW",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "RESTARTING",
      "to": "ROLLING_BACK",
      "guardIds": [
        "PRECONDITIONS",
        "ROLLBACK"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "RESTARTING",
      "to": "VERIFYING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "ROLLING_BACK",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "ROLLING_BACK",
      "to": "MANUAL_REVIEW",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "ROLLING_BACK",
      "to": "ROLLED_BACK",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "CLEANUP"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "STAGING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "STAGING",
      "to": "ROLLING_BACK",
      "guardIds": [
        "PRECONDITIONS",
        "ROLLBACK"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "STAGING",
      "to": "SWITCHING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "SWITCHING",
      "to": "MANUAL_REVIEW",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "SWITCHING",
      "to": "RESTARTING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "SWITCHING",
      "to": "ROLLING_BACK",
      "guardIds": [
        "PRECONDITIONS",
        "ROLLBACK"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "VERIFYING",
      "to": "ACTIVE",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "VERIFYING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "VERIFYING",
      "to": "MANUAL_REVIEW",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.24"
    },
    {
      "from": "VERIFYING",
      "to": "ROLLING_BACK",
      "guardIds": [
        "PRECONDITIONS",
        "ROLLBACK"
      ],
      "authoritySection": "49.24"
    }
  ],
  "writerId": "writer.application-deployment",
  "authoritySection": "49.24",
  "deniedByDefault": true,
  "successRequiresKnownOutcome": true,
  "terminalClosureSeparate": true
}
```

`ACTIVE`, `ROLLED_BACK` a `FAILED` jsou terminal pro konkrétní deployment run. Pozdější OWNER rollback již aktivního application release je nový deployment run se samostatným logical operation ID, previous/candidate snapshotem a vyšším application deployment epoch; terminal `ACTIVE` run se znovu neotevírá. Manual review vyžaduje exact filesystem/DB/process evidence resolution.

Každý step má intent, expected before/after digest, outcome a checkpoint. Migrations jsou forward-only a musí být kompatibilní s previous i candidate application release po celé rollback window. Externí call ani systemd restart neprobíhá uvnitř DB transakce.

Application release switch používá atomic filesystem rename pro `current` a databázový `applicationDeploymentEpoch`. Protože tyto dva zdroje nelze commitnout jednou transakcí, deployment recovery vždy čte oba, release manifest digest a skutečné process heartbeats. Stav se rozhodne deterministicky:

- oba ukazují previous → switch nebyl applied,
- oba ukazují candidate a required processes potvrzují epoch → applied,
- symlink a DB epoch se liší → recovery dokončí nebo vrátí switch podle persisted deployment intentu; readiness zůstává false,
- process release/epoch mix → gateway blokuje mutující provoz a restart/reconcile pokračuje,
- outcome, který nelze ověřit, vede do `MANUAL_REVIEW`.

Při změně singleton `application_deployment_head.current_epoch` přestanou staré process leases, execution contexts a queue claims přijímat autoritativní writes, protože každý guarded write ověřuje current application deployment epoch. Jejich pending side effects zůstávají v DB a nové procesy je reconciliují.

Disaster restore vytvoří nový platform incarnation před spuštěním workerů. Restore poté ověří audit head, active activation epochs, queue/outbox, leases, pending side effects, browser host/session stav, current application release a backups. Všechny leases z předchozí incarnation jsou neplatné bez čekání na jejich původní expiry. Externí pending outcomes se reconciliují; nepovažují se automaticky za not applied.

