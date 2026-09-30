### 12.5 Stavové přechody a guards

Každý job/phase command ověřuje current platform incarnation, job `stateVersion`, phase state/version, current coordinator/phase fencing token, cancellation version, approved specification digest, execution authority lineage, plan a dependency snapshot, workspace/candidate/activation pointers a latest checkpoint.

Phase success, phase terminal evidence, job transition, next phase pointer, next phase run, queue/outbox, generation event a audit se commitují v jedné transakci. Pozdní worker nebo stale attempt nemůže dokončit phase, změnit job, založit další phase ani posunout checkpoint.

Povolené hrany a crash semantics jsou v 49.15 a 49.25. Přechod neuvedený v mapě je odmítnut jako `CONFLICT`.

