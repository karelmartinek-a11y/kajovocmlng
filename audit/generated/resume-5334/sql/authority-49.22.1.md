### 49.22.1 Secret version, binding a credential rotation

Secret version je immutable. `secret_record` obsahuje `stateVersion`, active version pointer a monotonic `secretActivationEpoch`. Create version pouze vloží immutable candidate; activation/rotation pod secret row lockem ověří expected state/version, přesný candidate version a všechny systémové invarianty a v jedné transakci:

1. přepne active version pointer,
2. inkrementuje secret state version a activation epoch,
3. retire označí previous version podle policy,
4. pro `KCML_OWNER_API_KEY` současně atomicky nahradí verifier hash, fingerprint a credential version,
5. vytvoří binding/session-state invalidation events, audit a outbox.

Ztracená rotation response nevytvoří druhý klíč: opakovaný idempotency key vrátí current rotation outcome a platná OWNER session může revealnout jedinou active hodnotu. Ověření API klíče a přijetí `domain_command` má explicitní linearizační bod: command přijatý a persistovaný před rotation commitem může doběhnout pod svým immutable OWNER_FULL execution contextem; autentizace starou hodnotou zahájená nebo opakovaná po rotation commitu selže. Rotace nemění OWNER autoritu ani již commitnutý command, pouze zabrání vytvoření nového contextu ze starého verifieru.

Secret Broker resolve vytvoří immutable `secret_resolution` evidence s exact secret/version, secret activation epoch, source/target revisions, binding ID/revision/digest, logical operation, purpose a expiry. Hodnota je pinovaná pro právě jednu dispatch operation. New resolve po rotaci vždy používá nový epoch. Stale binding, retired version, změněný source/target revision nebo activation set je odmítnut před předáním hodnoty.

Rotace, která vyžaduje okamžitou invalidaci dependent browser/session/auth state, vytvoří invalidation epoch a barrier pro dotčené account/resource concurrency keys. New operations jsou blokované do invalidace. Již dispatchnuté external operations se dokončí nebo reconciliují podle své pinované version evidence; rotace jejich outcome nepřepisuje.

Secret binding candidate se stane active pouze atomicky s activation setem. Direct bind/unbind/activate operation používá state-version CAS a exact impact snapshot; nesmí vytvořit okamžik, kdy active revision odkazuje na neactive nebo jinak verzovaný binding. Tato korektnost nemění OWNER_FULL viditelnost ani závazný secret trust model.

