### 26.9 Secrets a password manager

```json
[
  {
    "method": "GET",
    "pathSegments": [
      {
        "literal": "secrets"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "POST",
    "pathSegments": [
      {
        "literal": "secrets"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "GET",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "parameter": "id",
        "schemaDefinition": "Uuid"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "PATCH",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "parameter": "id",
        "schemaDefinition": "Uuid"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "DELETE",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "parameter": "id",
        "schemaDefinition": "Uuid"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "GET",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "parameter": "id",
        "schemaDefinition": "Uuid"
      },
      {
        "literal": "value"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "POST",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "parameter": "id",
        "schemaDefinition": "Uuid"
      },
      {
        "literal": "versions"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "GET",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "parameter": "id",
        "schemaDefinition": "Uuid"
      },
      {
        "literal": "versions"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "POST",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "parameter": "id",
        "schemaDefinition": "Uuid"
      },
      {
        "literal": "versions"
      },
      {
        "parameter": "versionId",
        "schemaDefinition": "Uuid"
      },
      {
        "literal": "activate"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "POST",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "parameter": "id",
        "schemaDefinition": "Uuid"
      },
      {
        "literal": "rotate"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "GET",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "parameter": "id",
        "schemaDefinition": "Uuid"
      },
      {
        "literal": "bindings"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "POST",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "parameter": "id",
        "schemaDefinition": "Uuid"
      },
      {
        "literal": "bindings"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "DELETE",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "parameter": "id",
        "schemaDefinition": "Uuid"
      },
      {
        "literal": "bindings"
      },
      {
        "parameter": "bindingId",
        "schemaDefinition": "Uuid"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "GET",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "parameter": "id",
        "schemaDefinition": "Uuid"
      },
      {
        "literal": "usage"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "POST",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "parameter": "id",
        "schemaDefinition": "Uuid"
      },
      {
        "literal": "test-resolve"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "POST",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "literal": "generate-password"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "POST",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "literal": "import"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  },
  {
    "method": "POST",
    "pathSegments": [
      {
        "literal": "secrets"
      },
      {
        "literal": "export"
      }
    ],
    "leadingSlash": true,
    "sourceSection": "### 26.9 Secrets a password manager",
    "base": "API_ROOT",
    "operationBinding": "EXACT_OPERATION_CATALOG",
    "transportProtocol": null
  }
]
```

