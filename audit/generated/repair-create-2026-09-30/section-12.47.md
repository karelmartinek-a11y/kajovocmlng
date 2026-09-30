### 12.47 Create request admission

`generation.job.create` přijímá přes `POST /generation/jobs` přesnou masku
`urn:kcml:create-operation-design:1#/$defs/GenerationJobCreateBody`.
`intent` je povinný nenullový neprázdný OWNER záměr (§12.2, §72.11); jeho
původní UTF-8 text se nemění. Volitelné `kind` používá enum §12.3 a při
vynechání znamená `CREATE`. `targetKind` je technické pojmenování výrobců
§12.1, nikoli jiný produktový rozsah. UPDATE vyžaduje exact existující
`targetObjectId` a `targetKind`; server resolveuje jejich typ a aktuální
revision. `parentJobId` odkazuje na parent/source job podle §25.11; server
ověřuje vztah k původnímu jobu. CREATE může mířit na registered placeholder
bez předchozí release podle §49.18, nejde o klientské vytvoření identity. `requestedModel` je OWNER výběr OpenAI modelu,
ne capability snapshot vytvořený klientem.

`sources` jsou explicitní TEXT, FILE, IMAGE, URL, API_DOC, CREDENTIAL_REF
nebo OBJECT_REF podle §12.2 a §25.11. FILE/IMAGE/API_DOC obsahují pouze
`artifactId`: server načte persistovaný artefakt, ověří jeho identitu, skutečné
bytes/content digest a media type a teprve potom provede hydration/parser.
Klient nenahrává `ArtifactRef` jako trusted receipt. Volitelné `credential`
je přesná hodnota dedikovaného OWNER pole gen.credential (§72.11/§8.6);
server vyžaduje bounded ephemeral policy a serverový Secret-use context
svázaný s novým jobem před použitím. Absence ověřené policy je BLOCKED.
CREDENTIAL_REF obsahuje
stable name a vyžaduje serverový Secret-use context; přímý credential v OWNER
textu zůstává dovolen podle §8.6.1. URI zdroje podléhají server navigation
policy; reference objektů serverově resolveují actual owner/identity/revision.
Initial request a všechny vstupy se persistují před následným modelovým
zpracováním. Nový root vzniká ve stavu DISCUSSING podle §49.15; tento stav,
OWNER context, ID, authority, digest, phase a timestamps nesmí dodat klient.

Obě create operace používají UTF-8 JSON body, `Content-Type: application/json`
a povinný `Idempotency-Key` (§25.16). Nemají path parametry ani query.
Duplikované JSON klíče na jakékoliv hloubce, nevalidní UTF-8/JSON, nonfinite
numbers, neznámé query, neznámá pole a duplicitní doménové reference se
odmítají před admission. HTTP proxy/authentication headers zůstávají
transportními vstupy kanonické authentication service; nejsou business pole
ani způsob, jak klient deklaruje trusted authority. Create root nemá starou
CAS verzi; If-Match nebo klientské identity nového rootu nejsou create guard.
R9 guards zachovávají idempotency key, deadline a volitelný client digest hint;
root snapshot guards jsou null. Client digest se nikdy nepřevezme bez
serverového přepočtu. Native body je přesně dekódovaný domain body, žádný
schemaId/slot/values/canonicalJson adapter.

Idempotency scope je exact OWNER + operation + key; serverový request digest
váže canonical operationId a domain body. Tentýž key/digest replayuje původní
receipt či failure, jiný digest je konflikt. UNKNOWN outcome vyžaduje lookup
nebo reconciliation původní operace; nesmí vytvořit další root ani být
prohlášen za známý failure. Persistence/admission/queue/outbox mají hranice
§49 a §51. Request schema samo nedokazuje executable SQL nebo runtime closure.

