### 50.25 Deadline, cancellation, streaming a cleanup

Deadline je serverem určený monotonic/realtime pair a pouze se zkracuje přes child calls. Handler nemůže deadline prodloužit. Runtime host nastaví timer a cancellation version; gateway a každý broker dostane zbývající budget.

Cancellation:

1. commitne cancellation intent/version v parent state machine,
2. zastaví admission nových child calls,
3. odešle `CANCEL` přes capability channel,
4. zruší pending broker/network/browser operation, pokud je bezpečně abortovatelná,
5. mutující dispatch přejde do reconciliation,
6. po grace uzavře channel a ukončí process tree,
7. terminalizuje pouze podle známých outcomes.

Streaming používá credit-based backpressure. Producer nesmí mít více unacknowledged bytes než current credit window. Disconnect, cancellation nebo terminal result okamžitě zavře stream state, file descriptors a buffers. Slow consumer nemůže blokovat cancellation, heartbeat nebo shutdown; control frames mají rezervovanou queue a prioritu.

EOF není success. Final response se emituje pouze z persistovaného canonical outcome. Descriptor, socket, HTTP body, stream buffer a temporary file se uzavírá v `finally`/RAII a současně eviduje persistentní cleanup, pokud přežil process crash.

