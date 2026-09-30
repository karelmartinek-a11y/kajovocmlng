### 49.25 Crash-point rozhodovací matice

Pro každou autoritativní operaci platí následující rozhodnutí při smrti procesu přesně mezi kroky:

| Poslední potvrzený bod | Stav po restartu | Povinná akce |
|---|---|---|
| před vytvořením command/idempotency recordu | operace neexistuje | klient může request znovu odeslat se stejným key |
| po `RESERVED`, před queue/outbox commitem | command a enqueue jsou v jedné transakci, takže buď existují oba, nebo žádný | claim existing item nebo replay create |
| po queue claimu, před prvním work checkpointem | lease může expirovat; žádný side effect nemá intent | takeover novým fence a deterministic restart kroku |
| po pre-checkpointu a `INTENT_RECORDED`, před `DISPATCHING` | request nebyl předán dispatch workeru | dispatch existing intent právě jednou |
| po `DISPATCHING`, před network sendem | lokálně nerozlišitelné od smrti po sendu | reconciliation; nikdy automaticky `NOT_APPLIED` jen podle absence response |
| po external sendu, před response | outcome neznámý | target idempotency lookup/read-back; `UNKNOWN` → manual review |
| po response v process memory, před outcome commitem | response není autoritativní | retrieve/read-back/reconcile podle targetu |
| po confirmed outcome commitu, před post-checkpointem | zakázaná konstrukce; outcome a checkpoint pointer se commitují spolu | žádný mezistav nesmí existovat |
| po post-checkpointu, před enqueue pokračování | zakázaná konstrukce; checkpoint a outbox se commitují spolu | outbox publisher pokračování doručí |
| po phase terminal resultu, před změnou jobu/next phase | zakázaná konstrukce; jedna transakce | recovery vidí buď starý phase state, nebo complete transition |
| OpenAI 1 — před submit | descriptor/call může být `QUEUED`; `DISPATCH_STARTED` neexistuje | claimnout stejný call a provést právě jeden submit, nebo cancel bez effectu |
| OpenAI 2 — během submit | `DISPATCH_STARTED`; response ID může chybět | bez jednoznačného `NOT_SUBMITTED` nastavit `MODEL_SUBMIT_OUTCOME_UNKNOWN`; s handlem retrieve; nikdy blind create |
| OpenAI 3 — po submitu před persistencí response ID | provider mohl response vytvořit, local handle chybí | provider request ID uložit jen diagnosticky; bez `response.id` manual review; s durable raw handlem dokončit persistence |
| OpenAI 4 — po persistenci response ID | exact `response.id` a request digest | retrieve/poll/resume tentýž response a deduplikovat events/output |
| OpenAI 5 — během streamu | response ID, last contiguous provider sequence a partial events | background resume od cursoru, jinak retrieve stored response; delta ani EOF nejsou terminal success |
| OpenAI 6 — po model outputu před tool execution | terminal provider snapshot a ordered output items | znovu vyhodnotit items a vytvořit unique tool reservations; model znovu nevolat |
| OpenAI 7 — během tool execution | tool intent/attempt a pre-checkpoint | read-only podle contractu retry; mutující effect read-back/reconcile; stale fence nesmí write |
| OpenAI 8 — po tool side effectu před provider continuation | potvrzený tool outcome nebo reconciliation evidence | atomicky vytvořit output se stejným `call_id`, checkpoint a jedinou successor reservation; tool neopakovat |
| OpenAI 9 — před terminal persistence | final candidate/output existuje, parent terminal commit chybí | pod current fence znovu validovat a atomicky commitnout terminal run, session, memory, event, audit a outbox; model znovu nevolat |
| po workspace blob write, před workspace revision commitem | unreferenced blob | garbage cleanup; current workspace beze změny |
| po workspace revision commitu, před materialization | DB revision je current | znovu materializovat exact revision |
| po integration resource vytvoření, před step outcome | resource může existovat | read-back exact digest a candidate ownership; reconcile |
| po activation barrieru, před pointer switch | previous set zůstává current, admission je dočasně blokovaná | release barrier nebo zopakovat preflight |
| uprostřed pointer-switch transakce | PostgreSQL atomicita | celý previous nebo celý candidate snapshot, nikdy část |
| po pointer switchi, před runtime effective ack | set je `VERIFYING` | reconcile candidate epoch; při fail reverse switch |
| po reverse-switch transakci, před candidate shutdown | previous/absent snapshot je current | candidate je fenced; dokončit cleanup |
| po terminal state commitu, před SSE/HTTP response | terminal result existuje | replay přes idempotency/event stream |
| během cleanup kroku | cleanup checkpoint ukazuje poslední complete step | idempotentně pokračovat; nový business run neaktivovat před required safe pointem |
| po backup restore, před worker restartem | nová platform incarnation invaliduje staré writes | obnovit queues/outbox a reconcile pending side effects |
| po MCP HTTP/JSON parse rejection | nevznikl call ani handler side effect | klient opraví request; nový transport ID |
| po active JSON-RPC ID rezervaci, před call create | request event existuje, business call ještě ne | recovery rezervaci uzavře failure nebo dokončí create; duplicate ID se mezitím odmítá |
| po `input_required`/requestState commitu, před response | exchange je durable a parent čeká | retry stejné operation načte stejný exchange; nevytvoří nový side effect |
| po MRTR accepted input commitu, před resume delivery | consume a successor outbox jsou atomické | publisher doručí právě jeden resume |
| po task commitu, před CreateTaskResult delivery | task je durable a resolvable | caller načte task přes idempotentní retry/outcome; nevytvoří druhý task |
| po `tasks/update` consume commitu, před ACK | accepted keys a successor jsou durable | retry je idempotentní; `tasks/get` ukáže current state |
| po `tasks/cancel` intent commitu, před ACK | cancel intent je durable, task může ještě terminalizovat jinak | retry vrátí ACK/current state; first terminal commit wins |
| po subscription ACK commitu, před first frame | subscription nesmí emitovat jinou notification | recovery buď emituje ACK jako first message, nebo stream uzavře a client refreshne |
| po MCP terminal response commitu, před JSON/SSE delivery | canonical call/task outcome existuje | retry/poll načte outcome; transport loss jej nemění |
| po SSE disconnect před dispatch claimem | cancellation intent blokuje nový dispatch | terminalizovat bez effectu nebo načíst current outcome |
| po SSE disconnect po possible dispatchi | outcome není odvozen z disconnectu | reconcile; `UNKNOWN` → manual review |

Implementace nesmí obsahovat jiný recovery význam pro tentýž poslední potvrzený bod v MCP, agentním, generation, browserovém, deploymentovém nebo component-control runtime.

