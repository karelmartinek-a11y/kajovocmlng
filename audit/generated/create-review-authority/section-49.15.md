### 49.15 Generation job, phase run, source a discussion turn

Generation job povoluje:

```json
{
  "modelId": "model.generation-job",
  "schemaVersion": "2.0",
  "states": [
    "ACTIVATING",
    "ANALYZING",
    "BLOCKED",
    "CANCELLED",
    "CML_CONFORMANCE",
    "COMPLETED",
    "DISCUSSING",
    "FAILED",
    "IMPLEMENTING",
    "INTEGRATING",
    "VALIDATING"
  ],
  "initialStates": [
    "DISCUSSING"
  ],
  "terminalStates": [
    "CANCELLED",
    "COMPLETED",
    "FAILED"
  ],
  "edges": [
    {
      "from": "ACTIVATING",
      "to": "COMPLETED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "CLEANUP"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "ANALYZING",
      "to": "IMPLEMENTING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "CML_CONFORMANCE",
      "to": "ACTIVATING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "DISCUSSING",
      "to": "ANALYZING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "IMPLEMENTING",
      "to": "INTEGRATING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "INTEGRATING",
      "to": "VALIDATING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "VALIDATING",
      "to": "CML_CONFORMANCE",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "DISCUSSING",
      "to": "BLOCKED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "DISCUSSING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "DISCUSSING",
      "to": "CANCELLED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "CLEANUP",
        "CANCEL"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "BLOCKED",
      "to": "DISCUSSING",
      "guardIds": [
        "PRECONDITIONS",
        "RESUME"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "ANALYZING",
      "to": "BLOCKED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "ANALYZING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "ANALYZING",
      "to": "CANCELLED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "CLEANUP",
        "CANCEL"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "BLOCKED",
      "to": "ANALYZING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES",
        "RESUME"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "IMPLEMENTING",
      "to": "BLOCKED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "IMPLEMENTING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "IMPLEMENTING",
      "to": "CANCELLED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "CLEANUP",
        "CANCEL"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "BLOCKED",
      "to": "IMPLEMENTING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES",
        "RESUME"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "INTEGRATING",
      "to": "BLOCKED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "INTEGRATING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "INTEGRATING",
      "to": "CANCELLED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "CLEANUP",
        "CANCEL"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "BLOCKED",
      "to": "INTEGRATING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES",
        "RESUME"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "VALIDATING",
      "to": "BLOCKED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "VALIDATING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "VALIDATING",
      "to": "CANCELLED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "CLEANUP",
        "CANCEL"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "BLOCKED",
      "to": "VALIDATING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES",
        "RESUME"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "CML_CONFORMANCE",
      "to": "BLOCKED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "CML_CONFORMANCE",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "CML_CONFORMANCE",
      "to": "CANCELLED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "CLEANUP",
        "CANCEL"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "BLOCKED",
      "to": "CML_CONFORMANCE",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES",
        "RESUME"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "ACTIVATING",
      "to": "BLOCKED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "ACTIVATING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "ACTIVATING",
      "to": "CANCELLED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "CLEANUP",
        "CANCEL"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "BLOCKED",
      "to": "ACTIVATING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES",
        "RESUME"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "BLOCKED",
      "to": "DISCUSSING",
      "guardIds": [
        "PRECONDITIONS",
        "FUNCTIONAL_CHANGE"
      ],
      "authoritySection": "49.15"
    }
  ],
  "writerId": "writer.generation-job",
  "authoritySection": "49.15",
  "deniedByDefault": true,
  "successRequiresKnownOutcome": true,
  "terminalClosureSeparate": true
}
```

Z kteréhokoli non-terminal happy-path stavu lze přejít do `BLOCKED`, `FAILED` nebo po dokončení cancellation/cleanup do `CANCELLED`. `BLOCKED` obsahuje exact `resumeState`, `resumePhase`, checkpoint ID, context digest a blocker. `BLOCKED → resumeState` je povoleno pouze po atomickém uzavření blockeru a revalidaci specification, authority, dependency, credential, binding, workspace, candidate a activation snapshotů. Změněný funkční kontrakt se neobnovuje; vrací job do `DISCUSSING` s novou specification revision.

`COMPLETED`, `FAILED` a `CANCELLED` jsou terminal. `MANUAL_REVIEW` generation toku se reprezentuje job state `BLOCKED` s classification `MANUAL_REVIEW`; job nepokračuje, dokud exact side-effect outcome není uzavřen.

Phase run povoluje:

```json
{
  "modelId": "model.generation-phase",
  "schemaVersion": "2.0",
  "states": [
    "CANCELLED",
    "CANCEL_REQUESTED",
    "FAILED",
    "QUEUED",
    "REPAIRING",
    "RUNNING",
    "SUCCEEDED",
    "WAITING_FOR_DEPENDENCY",
    "WAITING_FOR_OWNER"
  ],
  "initialStates": [
    "QUEUED"
  ],
  "terminalStates": [
    "CANCELLED",
    "FAILED",
    "SUCCEEDED"
  ],
  "edges": [
    {
      "from": "CANCEL_REQUESTED",
      "to": "CANCELLED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "CLEANUP",
        "CANCEL"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "CANCEL_REQUESTED",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "QUEUED",
      "to": "CANCEL_REQUESTED",
      "guardIds": [
        "PRECONDITIONS",
        "CANCEL"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "QUEUED",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "NO_NEW_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "QUEUED",
      "to": "RUNNING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "REPAIRING",
      "to": "CANCEL_REQUESTED",
      "guardIds": [
        "PRECONDITIONS",
        "CANCEL"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "REPAIRING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "REPAIRING",
      "to": "RUNNING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "REPAIRING",
      "to": "SUCCEEDED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "RUNNING",
      "to": "CANCEL_REQUESTED",
      "guardIds": [
        "PRECONDITIONS",
        "CANCEL"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "RUNNING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "RUNNING",
      "to": "REPAIRING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "RUNNING",
      "to": "SUCCEEDED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "RUNNING",
      "to": "WAITING_FOR_DEPENDENCY",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "RUNNING",
      "to": "WAITING_FOR_OWNER",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "WAITING_FOR_DEPENDENCY",
      "to": "CANCEL_REQUESTED",
      "guardIds": [
        "PRECONDITIONS",
        "CANCEL"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "WAITING_FOR_DEPENDENCY",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "WAITING_FOR_DEPENDENCY",
      "to": "RUNNING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "WAITING_FOR_OWNER",
      "to": "CANCEL_REQUESTED",
      "guardIds": [
        "PRECONDITIONS",
        "CANCEL"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "WAITING_FOR_OWNER",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "WAITING_FOR_OWNER",
      "to": "RUNNING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES"
      ],
      "authoritySection": "49.15"
    }
  ],
  "writerId": "writer.generation-phase",
  "authoritySection": "49.15",
  "deniedByDefault": true,
  "successRequiresKnownOutcome": true,
  "terminalClosureSeparate": true
}
```

`SUCCEEDED`, `FAILED` a `CANCELLED` jsou terminal pro konkrétní attempt. Nový attempt má vyšší attempt sequence a vznikne až po terminalizaci předchozího. Partial unique constraint blokuje více active phase runs a více active coordinator leases na job.

Phase success transakce současně:

1. ověří phase fence, current job state/phase, cancellation version, authority, spec/plan/dependency digests a complete output checkpoint,
2. terminalizuje phase run jako `SUCCEEDED`,
3. uloží phase result digest a terminal evidence,
4. změní job na právě následující povolený state,
5. nastaví new current phase pointer,
6. vytvoří next phase run a queue/outbox item,
7. uloží job event a audit.

Crash před commitem nezmění nic; crash po commitu ponechá next queue item v outboxu. Neexistuje stav „phase succeeded, ale další phase nebyla naplánována“.

Source state map:

```json
{
  "modelId": "model.generation-source",
  "schemaVersion": "2.0",
  "states": [
    "PARSED",
    "PARSING",
    "RECEIVED",
    "REJECTED",
    "SUPERSEDED",
    "VERIFIED"
  ],
  "initialStates": [
    "RECEIVED"
  ],
  "terminalStates": [
    "REJECTED",
    "SUPERSEDED"
  ],
  "edges": [
    {
      "from": "PARSED",
      "to": "REJECTED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "PARSED",
      "to": "SUPERSEDED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "PARSED",
      "to": "VERIFIED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "PARSING",
      "to": "PARSED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "PARSING",
      "to": "REJECTED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "PARSING",
      "to": "SUPERSEDED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "RECEIVED",
      "to": "PARSING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "RECEIVED",
      "to": "REJECTED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "RECEIVED",
      "to": "SUPERSEDED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "VERIFIED",
      "to": "SUPERSEDED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    }
  ],
  "writerId": "writer.generation-source",
  "authoritySection": "49.15",
  "deniedByDefault": true,
  "successRequiresKnownOutcome": true,
  "terminalClosureSeparate": true
}
```

`REJECTED` a `SUPERSEDED` jsou terminal. Parser write vyžaduje source fence/state version. Normalized content a digest jsou immutable. Pozdní parser nesmí přepsat verified nebo superseded source.

Discussion turn map:

```json
{
  "modelId": "model.generation-discussion",
  "schemaVersion": "2.0",
  "states": [
    "COMPLETED",
    "FAILED",
    "INTERRUPTED",
    "INTERRUPT_REQUESTED",
    "QUEUED",
    "RUNNING"
  ],
  "initialStates": [
    "QUEUED"
  ],
  "terminalStates": [
    "COMPLETED",
    "FAILED",
    "INTERRUPTED"
  ],
  "edges": [
    {
      "from": "INTERRUPT_REQUESTED",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "INTERRUPT_REQUESTED",
      "to": "INTERRUPTED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "QUEUED",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "NO_NEW_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "QUEUED",
      "to": "INTERRUPT_REQUESTED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "QUEUED",
      "to": "RUNNING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "RUNNING",
      "to": "COMPLETED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "CLEANUP"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "RUNNING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.15"
    },
    {
      "from": "RUNNING",
      "to": "INTERRUPT_REQUESTED",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.15"
    }
  ],
  "writerId": "writer.generation-discussion",
  "authoritySection": "49.15",
  "deniedByDefault": true,
  "successRequiresKnownOutcome": true,
  "terminalClosureSeparate": true
}
```

Provider completion versus steer race zamkne turn a job. Pokud completion commitne první, turn přejde přímo `RUNNING → COMPLETED` a nová OWNER message vytvoří běžného unique successora. Pokud interrupt commitne první, turn přejde `RUNNING → INTERRUPT_REQUESTED`; pozdní provider completion je pouze evidence a nesmí turn dokončit. Po zrušení streamu a reconciliation read-only nebo mutujících calls přejde turn do `INTERRUPTED`, případně `FAILED` při technicky neuzavíratelné interruption chybě. V téže transakci vznikne nejvýše jeden successor relation a nejvýše jeden queue item pro successor. Partial assistant content je immutable interrupted evidence.

