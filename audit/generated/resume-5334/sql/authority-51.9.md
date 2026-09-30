### 51.9 `state_version`, `lock_version` a guarded writes

`state_version bigint NOT NULL DEFAULT 0 CHECK (state_version >= 0)` patří na každý aggregate root a každý samostatně lifecycle-řízený run/task/action/lease. Každá autoritativní business mutace daného row zvýší `state_version` právě o jedna.

`lock_version` se používá pouze na samostatných mutable leaf rows, které nejsou aggregate rootem, například dashboard layout nebo čistě prezentační metadata. Jeden row nesmí používat `state_version` a `lock_version` jako dvě alternativní autority. Pokud row ovlivňuje lifecycle, active pointer, credential, binding, side effect, queue, lease, checkpoint nebo terminal outcome, používá `state_version`.

Kanonický CAS update má tvar:

```sql
UPDATE component
SET lifecycle = $1,
    state_version = state_version + 1,
    aggregate_event_sequence = aggregate_event_sequence + 1,
    updated_at = $2
WHERE id = $3
  AND state_version = $4
  AND platform_incarnation_id = $5
  AND lifecycle = $6
  AND current_activation_epoch = $7
  AND active_binding_set_revision_id IS NOT DISTINCT FROM $8
RETURNING state_version, aggregate_event_sequence;
```

Přesný guard se může rozšířit, nesmí se zúžit proti operation contractu. Nulový počet rows je conflict/stale authority, nikoli success. Aplikace po nulovém výsledku načte current snapshot; nesmí provést blind retry s novou version bez nového business commandu.

Předchozí `SELECT FOR UPDATE` nezbavuje povinnosti zahrnout expected CAS a fence v závěrečném `UPDATE`. Tím se brání budoucímu refaktoru, který by lock omylem odstranil.

