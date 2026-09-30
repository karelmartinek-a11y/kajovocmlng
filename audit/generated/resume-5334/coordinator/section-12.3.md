### 12.3 Generation job

Generation job je stabilní výrobní objekt s kind:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$ref": "urn:kcml:generation-contracts:2#/$defs/SourceEnum033"
}
```

Job obsahuje:

- immutable initial request,
- OWNER identity a execution context,
- target kind a volitelný target object,
- message history a discussion turns,
- source inventory a verified facts,
- capability snapshot,
- specification revisions,
- approved specification a digest,
- execution authority,
- generation plan,
- phase runs a checkpoints,
- OpenAI model calls a tool dispatches,
- implementation workspace a patch history,
- contract candidates a generated artifacts,
- validation, evaluation a conformance evidence,
- activation set,
- previous a candidate releases,
- blockers, cancellation a recovery state,
- events, logs, traces a audit.

Job má jeden autoritativní lifecycle a nejvýše jeden aktivní phase run. Souběžné read-only analýzy mohou běžet pod jedním phase runem, ale pouze phase coordinator mění lifecycle.

