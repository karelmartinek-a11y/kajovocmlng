### 49.23 Konfigurace, circuit breaker, monitoring a alerty

Operational setting má oddělené `desiredVersion` a per-service `effectiveVersion`. `PUT/reset/import` mění desired value pouze přes CAS a uloží config activation request. Každá desired version má právě jeden canonical apply logical operation; pozdější desired version vytváří nový apply run. Apply run používá:

```json
{
  "modelId": "model.configuration-change",
  "schemaVersion": "2.0",
  "states": [
    "APPLIED",
    "APPLYING",
    "FAILED",
    "MANUAL_REVIEW",
    "PENDING",
    "ROLLED_BACK",
    "ROLLING_BACK",
    "VALIDATING",
    "VERIFYING"
  ],
  "initialStates": [
    "PENDING"
  ],
  "terminalStates": [
    "APPLIED",
    "FAILED",
    "ROLLED_BACK"
  ],
  "edges": [
    {
      "from": "APPLYING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "APPLYING",
      "to": "MANUAL_REVIEW",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "APPLYING",
      "to": "ROLLING_BACK",
      "guardIds": [
        "PRECONDITIONS",
        "ROLLBACK"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "APPLYING",
      "to": "VERIFYING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "MANUAL_REVIEW",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "MANUAL_REVIEW",
      "to": "ROLLING_BACK",
      "guardIds": [
        "PRECONDITIONS",
        "ROLLBACK"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "MANUAL_REVIEW",
      "to": "VERIFYING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "PENDING",
      "to": "VALIDATING",
      "guardIds": [
        "PRECONDITIONS",
        "DEPENDENCIES"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "ROLLING_BACK",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "ROLLING_BACK",
      "to": "MANUAL_REVIEW",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "ROLLING_BACK",
      "to": "ROLLED_BACK",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT",
        "CLEANUP"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "VALIDATING",
      "to": "APPLYING",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "VALIDATING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "VERIFYING",
      "to": "APPLIED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "VERIFYING",
      "to": "FAILED",
      "guardIds": [
        "PRECONDITIONS",
        "KNOWN_EFFECT"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "VERIFYING",
      "to": "MANUAL_REVIEW",
      "guardIds": [
        "PRECONDITIONS"
      ],
      "authoritySection": "49.23"
    },
    {
      "from": "VERIFYING",
      "to": "ROLLING_BACK",
      "guardIds": [
        "PRECONDITIONS",
        "ROLLBACK"
      ],
      "authoritySection": "49.23"
    }
  ],
  "writerId": "writer.configuration-change",
  "authoritySection": "49.23",
  "deniedByDefault": true,
  "successRequiresKnownOutcome": true,
  "terminalClosureSeparate": true
}
```

`APPLIED`, `ROLLED_BACK` a `FAILED` jsou terminal pro danou desired version. Nová změna settingu nevzkřísí terminal run; vytvoří nový run s vyšší desired version. Manual review vyžaduje exact effective-state resolution.

Crash po změně souboru nebo restartu a před DB outcome se obnoví read-backem skutečného service config digestu, process release a readiness. `APPLIED` je přípustné pouze pokud všechny target services hlásí expected effective version. Mixed effective versions jsou explicitní `VERIFYING`/`ROLLING_BACK` stav, nikoli success. Atomic config group používá activation barrier a rollback snapshot.

Circuit breaker update používá state version a monotonic transition sequence. `CLOSED → OPEN → HALF_OPEN → CLOSED|OPEN`; právě jeden half-open probe drží fenced probe lease. Pozdní probe result nemění breaker po novém epochu nebo OWNER resetu.

Monitoring scheduler enqueue používá stable schedule occurrence ID. Opakovaný tick nevytvoří duplicate probe. Alert dedupe scope je source object + alert type + condition digest + active episode. Open/update/close používá state version; delivery je at-least-once s channel idempotency key. Stale probe může zůstat evidence, ale neotevře ani nezavře current alert episode.

Repair job vzniká unique podle source alert episode a repair policy revision. Opakované monitoring ticks vrací existující non-terminal repair job.

