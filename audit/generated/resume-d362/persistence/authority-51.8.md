### 51.8 Advisory-lock namespaces a key derivation

Povoleny jsou pouze transaction-scoped funkce `pg_advisory_xact_lock(int,int)`, `pg_try_advisory_xact_lock(int,int)`, `pg_advisory_xact_lock_shared(int,int)` a `pg_try_advisory_xact_lock_shared(int,int)`. Shared varianty se používají pouze u namespace s explicitním shared/exclusive kontraktem. Session-level `pg_advisory_lock`, `pg_advisory_unlock` a držení advisory locku přes commit jsou zakázané.

Kanonické namespace IDs jsou:

| Namespace ID | Symbol | Účel |
|---:|---|---|
| 1000 | `PLATFORM_RECOVERY_BARRIER` | singleton recovery guard, druhý key `0`; sdílený pro admission, výlučný pro recovery transition; získává se před všemi dalšími advisory locks |
| 1001 | `BOOTSTRAP_SINGLETON` | bootstrap právě jednoho OWNER/platform head row |
| 1010 | `COMPONENT_CODE` | first-create KCML number/code/hostname |
| 1020 | `SECRET_STABLE_NAME` | first-create stable secret name |
| 1030 | `IDEMPOTENCY_SCOPE` | first-create idempotency row při vysokém contention |
| 1040 | `CONCURRENCY_CLAIM` | first-create persistent concurrency claim row |
| 1050 | `ACTIVATION_DOMAIN` | first-create activation domain head |
| 1060 | `BROWSER_CONTROL` | first-create browser control lease row |
| 1070 | `CLEANUP_REMEDIATION` | first remediation/cleanup candidate pro owner scope |
| 1080 | `SCHEDULE_OCCURRENCE` | unique materializace schedule occurrence |
| 1090 | `INBOUND_EVENT` | first-create inbox row při provider duplicate burstu |
| 1100 | `SCHEMA_MIGRATION` | jediný migrator/deployment schema step |

Pro singleton PLATFORM_RECOVERY_BARRIER je druhý int key výhradně 0 a nehashuje se. U ostatních zde uvedených namespaces vznikne druhý `int` key přesně z prvních čtyř bytes SHA-256 canonical key bytes v network byte order: bytes se interpretují jako unsigned big-endian `uint32` a stejný bit pattern se převede two's-complement na PostgreSQL signed `int4`. Aplikační knihovna `PostgresAdvisoryKey` je jediná implementace převodu a má cross-language test vectors včetně hodnot nad `0x7fffffff`. Plný 32-byte digest je vždy uložen v row a chráněn unique constraintem; advisory key není identita.

Více advisory locků se získává seřazeně podle `(namespace_id, signed_key)`. Try-lock failure nemění business stav. Žádný advisory lock se nedrží při HTTP, OpenAI, browser, filesystem, systemd, DNS, TLS ani jiné externí operaci.

