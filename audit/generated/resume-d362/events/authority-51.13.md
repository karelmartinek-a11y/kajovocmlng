### 51.13 Monotonic a contiguous sequence allocation

Sekvence se dělí na dvě třídy:

1. **Identity sequence s povolenými gaps** — interní surrogate IDs a neautoritativní ordering; může použít PostgreSQL sequence.
2. **Business contiguous nebo fenced sequence** — aggregate event, command, checkpoint, session item, stream, audit chain, activation epoch, control epoch, attempt number; používá zamknutý head/root row.

`MAX(sequence)+1` je vždy zakázané. Contiguous allocator provede pod parent/root `FOR UPDATE` atomické `last_sequence = last_sequence + 1 RETURNING last_sequence`. Insert child row a update head jsou ve stejné transakci.

Attempt sequence smí mít gap pouze tehdy, když reservation sama představuje immutable attempt evidence. Číslo rezervované v rollbacknuté transakci neexistuje a není gapem v commitnutém streamu.

Activation epoch alokuje pouze `activation_head FOR UPDATE`. Browser control epoch alokuje browser session root. Lease fencing token alokuje persistentní fenced resource row; row se po release neodstraňuje, aby nedošlo k ABA.

