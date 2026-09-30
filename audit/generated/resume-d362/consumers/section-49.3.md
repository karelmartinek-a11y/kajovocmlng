### 49.3 Kanonický command contract a souběžné OWNER příkazy

Každá mutující UI, API, chatová, KCIP, MCP, workerová nebo schedulerová operace vytváří serverový `domain_command` s:

- `commandId`,
- `logicalOperationId`,
- caller channel a serverovým execution contextem,
- operation key a contract revision,
- target aggregate kind a ID,
- canonical arguments a `requestDigest`,
- `idempotencyKey`,
- expected `stateVersion`, pokud operace není explicitně komutativní,
- expected revision/digest, binding-set revision a activation epoch podle kontraktu,
- deadline,
- correlation a causation,
- created, accepted a terminal timestamps.

Všechny současné webové relace, zařízení a API klienti jsou tentýž OWNER, ale jejich mutace nejsou implicitně last-write-wins. Pravidla souběhu jsou:

1. nekomutativní změna vyžaduje expected `stateVersion` nebo přesný ekvivalentní compare-and-swap guard,
2. append operace, například nová zpráva s unikátním `clientMessageId`, alokuje sequence pod root row lockem a nepotřebuje předchozí `stateVersion`,
3. idempotentní cancel, close, acknowledge nebo reconcile přijímá opakování stejného command digestu a vrací původní outcome,
4. dvě approval, activation, rotation, pointer nebo metadata operace nad stejnou expected version nemohou obě uspět,
5. vítězem je transakce, která první commitne; druhá vrátí current snapshot a `STATE_VERSION_CONFLICT`, nikoli tichý přepis,
6. bulk operace zamyká cíle v kanonickém pořadí a buď commitne celý deklarovaný atomic set, nebo žádný jeho člen,
7. operace nad nezávislými agregáty mohou běžet souběžně, pokud nesdílejí concurrency key nebo activation domain.

UI generuje stabilní idempotency key před prvním odesláním a při síťovém retry jej zachová. API klient mutující operaci bez požadovaného idempotency key nedostane k doménovému handleru. Response obsahuje `logicalOperationId`, `stateVersion`, `eventSequence`, `activationEpoch`, `resultDigest` a příznak `idempotencyReplay`.

