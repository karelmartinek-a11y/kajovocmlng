### 51.2 Databázové role, session stav a transakční profily

Každá trusted systemd služba používá deploymentem spravovanou PostgreSQL login roli s nejmenším potřebným DML/EXECUTE rozsahem; společné NOLOGIN group role oddělují domain write, broker write, read-only/acceptance a migration oprávnění. Tyto infrastrukturové role nejsou aplikační principal, OWNER role ani permission systém. Pouze deployment migrator smí měnit schema; běžné role nesmějí vytvářet extensions/roles/schema, používat superuser nebo `BYPASSRLS` ani převzít jinou roli mimo svůj explicitní grant. Generated handler databázový credential ani síťovou cestu k PostgreSQL nemá.

Connection pool po každém checkoutu i návratu resetuje session-local stav. Aplikační kód nesmí spoléhat na session-level advisory lock, dočasnou tabulku, změněný `search_path`, změněný isolation level, změněný timeout ani jiný stav z předchozího požadavku.

Kanonické online profily jsou:

| Profil | Isolation | `lock_timeout` | `statement_timeout` | `idle_in_transaction_session_timeout` | Použití |
|---|---:|---:|---:|---:|---|
| `ONLINE_MUTATION` | `READ COMMITTED` | 1500 ms | 10 s | 10 s | UI/API/chat/KCIP krátké autoritativní mutace |
| `WORKER_COMMIT` | `READ COMMITTED` | 3000 ms | 15 s | 15 s | claim, checkpoint, outcome, terminalizace, enqueue |
| `ACTIVATION_SWITCH` | `READ COMMITTED` | 5000 ms | 30 s | 30 s | barrier state, atomic switch a reverse switch |
| `CONSISTENT_READ` | `REPEATABLE READ READ ONLY` | 3000 ms | 60 s | 60 s | export, diff, vícequery diagnostický snapshot |
| `CLOSURE_SNAPSHOT` | `SERIALIZABLE READ ONLY DEFERRABLE` | 5000 ms | 120 s | 120 s | closure, restore a cross-table invariant verification |
| `SERIALIZABLE_PREDICATE` | `SERIALIZABLE` | 3000 ms | 15 s | 15 s | pouze výslovně katalogovaná bounded predicate mutace |

Timeouty jsou automatická platformní konfigurace, nikoli OWNER-editable produktové parametry. Konkrétní operace může mít přísnější limit. Vyšší limit vyžaduje operation-catalog evidence, že transakce stále neobsahuje externí I/O a nemůže být rozdělena bez porušení atomického invariantu.

`READ UNCOMMITTED` se nepoužívá. Izolace se nastaví bezprostředně po `BEGIN` a před prvním business dotazem. Aplikační transaction wrapper při dokončení ověří, že transakce není ponechána `idle in transaction`.

