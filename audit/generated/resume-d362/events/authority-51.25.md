### 51.25 Audit sequence a hash chain

`audit_head` je singleton s `last_sequence bigint`, `last_hash bytea`, `chain_format_version`, `CHECK (last_sequence >= 0)` a `CHECK (octet_length(last_hash) = 32)` a state version. Bootstrap hodnota je přesně `last_sequence = 0`, `last_hash = decode(repeat('00',32),'hex')`, `chain_format_version = 1`; první event používá tento zero hash jako previous hash. Každá auditovaná domain transaction zamkne `audit_head FOR UPDATE` až po všech ostatních rows.

Append provede:

1. `next_sequence = last_sequence + 1`,
2. sestaví immutable canonical audit bytes obsahující next sequence, previous hash, event/actor/object, before/after digests, correlation/causation/trace a DB timestamp,
3. vypočte `event_hash = kcml_audit_hash(chain_format_version,previous_hash,next_sequence,canonical_bytes)`,
4. vloží `audit_event` s `UNIQUE (chain_sequence)` a `CHECK (octet_length(event_hash) = 32)`,
5. aktualizuje head na next sequence/hash,
6. vloží archive outbox právě tehdy, když active audit-retention policy revision požaduje external archive pro danou `chain_sequence`; jinak uloží explicitní `archive_required = false` v audit delivery projection,
7. commitne společně s domain mutation.

`kcml_audit_hash` je versioned immutable DB function s test vectors; změna hash formátu vytváří explicitní chain-format revision, nikoli tichou změnu.

Audit row je immutable. `audit_event` je buď nepartitionovaná, nebo range-partitionovaná podle `chain_sequence`, aby PostgreSQL mohl fyzicky vynutit globálně unikátní sequence; time-only partitioning bez sequence partition key se pro canonical chain nepoužívá. Unpartitioned `audit_head` zůstává jediným allocator headem.

Po získání class I `audit_head` už transakce nesmí zamknout ani měnit žádný dříve existující A–H row. Povoleny jsou pouze append-only inserty nového `audit_event` a jeho nového `audit_archive_outbox` row s právě alokovanou sequence/event ID; jejich keys nemohou kolidovat s jinou transakcí. Pozdější archive delivery claim zachází s existujícím archive-outbox row jako s class H ordinalem `910`. Archive delivery může být at-least-once, ale canonical chain v DB se nemění podle úspěchu archivu.

