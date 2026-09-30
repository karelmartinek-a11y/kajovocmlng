### 8.8 Secret resolution

Trusted runtime posílá kanonickému Secret Brokeru serverový execution context, stable name, target context, correlation ID a operation scope. Broker ověří exact active secret binding, source/target revisions a binding digest, vrátí hodnotu pouze procesu provádějícímu danou operaci a zapíše debug log i audit.

Po úspěšné validaci exact Secret bindingu obdrží generated handler skutečnou plaintext hodnotu business secretu jako runtime data konkrétní operace. Broker eviduje secret version, consumer step, target, purpose, operation context a correlation. Handler může hodnotu v rámci active contractu přímo číst, transformovat, použít v payloadu, logu, generovaném kódu nebo dalším deklarovaném business zpracování. Každé serverové resolve a typed dispatch použití zůstává svázané s current operation contextem a auditní evidencí.

