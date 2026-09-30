### 51.20 Secret version, binding a atomická rotace `KCML_OWNER_API_KEY`

`secret_version` je immutable. Fyzické constraints zahrnují:

```json
{
  "contractKind": "NORMATIVE_CONSTRAINT_DECLARATION",
  "declarationId": "SSOT-DECL-212",
  "sourceSection": "### 51.20 Secret version, binding a atomická rotace `KCML_OWNER_API_KEY`",
  "clauses": [
    "UNIQUE (secret_id, version_number)",
    "UNIQUE (secret_id, id)",
    "CHECK (octet_length(canonical_value_digest) = 32)",
    "partial UNIQUE (secret_id) WHERE lifecycle = 'ACTIVE'"
  ],
  "allClausesMandatory": true,
  "recordDefinition": "RegistryPostgres",
  "materializationRequiredBefore": "ARCHITECTURE_READINESS",
  "unknownBindingPolicy": "BLOCKED"
}
```

Ciphertext, nonce, algorithm, key ID, fingerprint a canonical value digest se po insertu nemění. Active pointer a `secret_activation_epoch` jsou pouze v `secret_record` rootu. Lifecycle projection version row smí v activation transakci přejít `CREATED|RETIRED → ACTIVE` a previous version `ACTIVE → RETIRED`; tím zůstává možné znovu aktivovat OWNERem vybranou historickou verzi bez kopírování hodnoty. Každý takový přechod vytvoří immutable domain event/audit s novým secret activation epoch; projection timestamps na version row historii nenahrazují. Trigger zakáže změnu cryptographic fields.

Obecná secret activation/rotation:

1. claimne idempotency record,
2. před mutací odvodí celý finite set dotčených aggregate rootů a zamkne je v jediném pořadí 51.6; případný `OWNER_IDENTITY = 10` předchází `SECRET_RECORD = 20`, zatímco component/browser/agent/runtime roots následují podle svých ordinalů,
3. nad zamknutým `secret_record` načte candidate i current version a ověří parent, lifecycle, digest a expected secret state version,
4. zamkne dependent mutable invalidation child/head rows až po všech jejich parent roots a v class H pořadí,
5. pokud candidate není current, nejprve změní previous `ACTIVE → RETIRED` s `retired_at = db_now` a potom candidate `CREATED|RETIRED → ACTIVE` s `activated_at = db_now`, `retired_at = NULL`, aby immediate partial unique index nebyl ani na okamžik porušen,
6. přepne active pointer, zvýší secret state version a activation epoch,
7. vytvoří invalidation epoch, exact binding/session/browser invalidation outbox, immutable activation event a audit,
8. commitne. Pokud candidate již je current active version, operation uloží nebo replayuje canonical `ALREADY_ACTIVE` no-op outcome, neinkrementuje secret epoch ani state version a nevytváří invalidation event.

`KCML_OWNER_API_KEY` používá navíc singleton `owner_api_credential`. Credential je singleton authority head třídy B3 a zamyká se před idempotency row; `SECRET_RECORD` je následný aggregate root ordinal 20. Credential row má composite FK `(secret_id,secret_version_id)` na version téhož secretu a DB trigger/check ověřuje stable name `KCML_OWNER_API_KEY`.

Rotace OWNER API klíče je jedna transakce, která současně a v tomto fyzickém pořadí:

- ověří rotation idempotency a expected credential/secret state versions,
- vloží novou immutable secret version ve stavu `CREATED`,
- změní previous version `ACTIVE → RETIRED` a potom novou version `CREATED → ACTIVE`,
- přepne `secret_record.active_version_id` a zvýší secret epoch,
- přepne `owner_api_credential.secret_version_id`, verifier hash, fingerprint a `credential_version`,
- zvýší credential `state_version` a credential activation epoch,
- uloží canonical rotation outcome, invalidation events, audit a outbox.

Neexistuje commit, v němž active Secret version a verifier ukazují na různé hodnoty. Deferred constraint trigger `kcml_secret_active_pointer_consistency` po každé změně ověří, že `secret_record.active_version_id` je právě jediná `ACTIVE` version téhož secretu; pro reserved OWNER key navíc ověří shodu `owner_api_credential.secret_version_id`, credential version/epoch a verifier fingerprintu.

Authentication OWNER API klíčem a durable acceptance `domain_command` mají společný krátký linearizační kontrakt:

1. transaction po platform/deployment heads zamkne `owner_api_credential FOR SHARE`,
2. načte current verifier/version/epoch a provede bounded constant-time verifier check bez externího I/O,
3. při úspěchu následně claimne idempotency row a ve stejné transakci vytvoří immutable `OWNER_FULL` execution context snapshot, append-only usage/audit evidence, command acceptance a queue/outbox,
4. commitne; teprve tento commit znamená přijetí requestu. `last_used_at` a souhrnná usage metadata jsou odvozená projection z append-only evidence a nezpůsobují upgrade shared credential locku při každém callu.

Rotation transaction potřebuje `owner_api_credential FOR UPDATE`, a proto nastane právě jedno pořadí: command acceptance commitne před rotací a může doběhnout pod pinovaným contextem, nebo rotace commitne první a starý verifier již nový command nepřijme. Stav „starý klíč ověřen, ale command ještě není persistovaný a rotace mezitím commitla“ není přípustný.

Reveal klíče pod OWNER session je read operation nad current locked snapshotem a audit eventem. Ztracená rotation response se neopakuje s novou hodnotou; stejný idempotency key vrátí původní outcome a OWNER session může revealnout jedinou active version.

