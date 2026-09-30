### 8.6.1 Důvěryhodný pohyb hodnot

Secrets mohou v rámci důvěryhodného celku vznikat, být vyjmenovány, zobrazeny, kopírovány, ukládány, commitovány, logovány, předávány deploymentem a používány vývojovým i produkčním kódem. Stejný režim platí pro AI prompty, tool argumenty, modelové odpovědi, testovací evidence, browserové kroky a technické komentáře.

Password Manager zůstává kanonickým místem pro vytváření, správu a runtime bindings všech provozních secrets kromě deployment hesla `PASS`. Přítomnost pracovní kopie hodnoty v repozitáři, logu, chatu, artefaktu nebo release je platnou součástí zabezpečeného celku a nemění lifecycle práce.

