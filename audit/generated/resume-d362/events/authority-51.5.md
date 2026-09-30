### 51.5 Kanonická transakční obálka a linearizační bod

Každá autoritativní mutace používá tuto obálku:

1. `BEGIN` a nastavení přesného transaction profilu,
2. normalizace inputu mimo transakci; žádné provider/browser/network I/O,
3. získání potřebných transaction-scoped advisory locků v pořadí 51.8,
4. zamknutí platform/deployment heads a podle access/operation typu singleton security nebo activation headu,
5. claim nebo lock idempotency recordu,
6. zamknutí activation domain heads,
7. zamknutí aggregate rootů a dalších rows v pořadí 51.6,
8. získání `db_now`, načtení current hodnot z právě zamknutých rows a opětovné vyhodnocení všech guards,
9. provedení právě jednoho povoleného přechodu nebo deklarovaného atomic setu,
10. guarded update se `state_version = state_version + 1`, případně alokace sequences,
11. vložení immutable event/checkpoint/evidence rows,
12. vložení queue/outbox/invalidation/reconcile rows,
13. zamknutí a update `audit_head` jako posledního sdíleného hot row,
14. `COMMIT` jako jediný linearizační bod,
15. response/SSE/NOTIFY se vytvoří pouze z commitnutého stavu.

Každý read použitý k mutačnímu rozhodnutí musí být buď:

- načten z řádku již zamknutého odpovídajícím row lockem,
- znovu ověřen CAS predikátem v `UPDATE`/`DELETE`,
- nebo chráněn unique/check/foreign-key constraintem, jehož violation je explicitně zpracována.

Validace provedená před získáním locku je preflight, nikoli autoritativní guard. Všechny current state, eligibility, deadline, cancellation, revision, binding, epoch, fence a terminality podmínky se znovu vyhodnotí po získání locků.

External side effect nikdy není uvnitř této transakce. Transakce před external side effectem končí commitnutým `side_effect_operation` intentem a dispatch outboxem. Následující outcome/reconciliation používá novou transakci.

