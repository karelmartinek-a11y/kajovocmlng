### 49.18 První CREATE, UPDATE a REPAIR rollback

První CREATE má tři odlišné případy:

1. **Selhání před switch commitem:** active pointer nikdy nevznikl. Cleanup zastaví provisional runtime, deaktivuje candidate-only route, retired candidate bindings, odstraní neautoritativní `current` filesystem link, označí release failed/rolled back podle evidence a zachová provisional identity pro audit nebo ji po dependency checku deregistruje.
2. **Selhání po switch commitu před `ACTIVE`:** rollback transakce přepne celý activation domain na `ABSENT` s vyšším epoch. Teprve potom se runtime zastaví a cleanupne.
3. **Selhání po `ACTIVE`:** běžný rollback opět použije previous `ABSENT`; OWNER-visible schopnost se atomicky stane neaktivní, nikoli částečně přístupná.

V žádném případě se release neoznačí `ROLLED_BACK` před potvrzením, že není current v žádném active pointeru, route, binding setu ani runtime effective epoch. Nový remediation candidate nevznikne, dokud předchozí cleanup nemá `COMPLETE`. `MANUAL_REVIEW` zůstává blockerem; není alternativou k dokončenému cleanupu.

UPDATE a REPAIR rollback vždy odkazuje na frozen previous snapshot. Atomic reverse switch obnoví previous revisions, releases, binding-set revision, routes, runtime target, component lifecycle/activation projection a agent/automation pointers, ale alokuje nový activation epoch vyšší než všechny dosud přidělené epochy; historický epoch se neobnovuje. Restart previous runtime není samostatný zdroj pravdy; jeho effective ack a readiness se ověřují proti novému rollback epoch. Pokud previous snapshot již není compatible nebo dostupný, activation se před původním switchem zablokuje. Po switchi nejednoznačný rollback effective stav vede do `MANUAL_REVIEW` a fail-closed gateway.

