### 12.41 Follow-up, update a repair

Funkční OWNER follow-up vytváří novou discussion větev a novou specification revision. Po approval vznikne nové authority lineage.

UPDATE zachovává component a runtime identity a vytváří candidate revisions/releases. Compatibility a migration plan jsou povinné.

RETRY zachovává stejný approved functional authority a opakuje pouze neúspěšnou technickou část s novými attempt records.

REPAIR vzniká z monitoring evidence, zachovává identity a poslední approved functional lineage a smí měnit pouze technickou implementaci. Aktivuje se jen po úplné regresní validaci.

