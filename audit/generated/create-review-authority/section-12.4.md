### 12.4 Generation lifecycle

Lifecycle používá:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "urn:kcml:generation-contracts:2#/$defs/SourceEnum034"
}
```

Happy path je lineární:

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

Z každého non-terminal happy-path stavu lze přejít do `BLOCKED`, `FAILED` nebo po bezpečném cancellation/cleanup do `CANCELLED`. `BLOCKED` ukládá exact resume state/phase, checkpoint a context digest. Resume znovu ověří current specification, authority, dependencies, bindings, credentials, workspace, candidate a activation snapshot. `COMPLETED`, `FAILED` a `CANCELLED` jsou immutable terminal.

Každá fáze vytváří `generation_phase_run`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "urn:kcml:generation-contracts:2#/$defs/SourceEnum036"
}
```

Phase attempt terminalita, retry a exact transition map jsou v 49.15. Každá fáze má terminal evidence; `FULL_REUSE` používá explicitní `NO_NEW_CODE_REQUIRED`, nikoli silent skip.

