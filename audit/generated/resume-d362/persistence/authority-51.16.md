### 51.16 Terminal write, successor reservation a enqueue

Každý workflow edge, jehož predecessor terminalizace vyžaduje successor, používá jednu PostgreSQL transakci. V ní se současně:

1. zamkne parent/predecessor root a ověří current fence/state version,
2. uloží terminal result/error digest a immutable terminal evidence,
3. inkrementuje parent state/event sequence,
4. vytvoří nebo aktivuje právě jednu successor reservation,
5. vloží právě jeden unique queue item/outbox event pro successor,
6. uloží domain event, audit a checkpoint pointer,
7. commitne.

Povinný unique constraint je nejméně `(parent_logical_operation_id, successor_kind, successor_ordinal)` nebo doménově ekvivalentní stabilní klíč. Redelivery predecessor completion pouze replayuje existující successor.

Tento kontrakt platí pro phase success + next phase, approval/input fulfilment + resume, task input + resume, model output + tool dispatch, tool completion + next model turn, discussion completion + successor turn, cleanup step + next cleanup step a configuration apply step + next target.

