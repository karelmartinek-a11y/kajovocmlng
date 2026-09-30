### 12.49 FOLLOW_UP immutable admission

Schválené produktové pravidlo OWNER (2026-09-30, podmínky 1–7) dovoluje
nezávislou FOLLOW_UP větev před terminalitou source jobu. §12.41 nadále
vyžaduje vlastní discussion/specification a následnou execution authority;
§25.11 terminal immutability zdrojového jobu není zákaz nové větve. Frozen
podklad sám nepovoluje execution ani nenahrazuje požadovaný finální výsledek.
Nezavádí se plošný terminal-state guard ani lifecycle převzatý od jiného kindu.

FOLLOW_UP vyžaduje parentJobId a followUpBasis s jednoznačným basisKind:
INITIAL_REQUEST (expectedDigest), SPECIFICATION_REVISION (revisionId,
expectedDigest), PUBLISHED_FINAL_OUTPUT (artifactId, expectedDigest).
To jsou pouze klientské selektory/preconditions, nikdy trusted receipts.
Každá uzavřená varianta má vlastní přesnou masku bez extra/null polí.
INITIAL_REQUEST znamená původní immutable request konkrétního parent jobu,
nikoli current obsah. Revision/artifact UUID musí vybírat přesně identifikovaný
persistovaný neměnný podklad. Chybějící/nepublikovaný potřebný finální output
se odmítá konkrétním FOLLOW_UP_BASIS_UNAVAILABLE nebo
FOLLOW_UP_FINAL_OUTPUT_UNPUBLISHED; chybějící závazný COMMITTED publication
receipt je FOLLOW_UP_PUBLICATION_RECEIPT_UNVERIFIED.

Matice kind × source state × dostupnost je contracts/follow-up-admission.json.
FOLLOW_UP ve všech jedenácti vlastních stavech generation_job dovoluje pouze
AVAILABLE_IMMUTABLE podklad: owned, konzistentní, dostatečný pro vybraný druh,
se skutečně načtenými bytes a přepočteným digestem. Pro finální output musí
odpovídat závazný publication receipt. MISSING, INCONSISTENT, INSUFFICIENT,
UNPUBLISHED jsou odmítnutí; jiné kinds mají vlastní §12.41 dependencies a
nepřebírají toto povolení. Jejich neuzavřené policies zůstávají OPEN.

Admission atomicky autentizuje OWNER, ověří parent ownership, přesný
snapshot/revision/artifact, bytes a obsahovou způsobilost pod příslušnými
locks. Neověřená atomicita je BLOCKED. Server persistuje frozenBasis:
sourceJobId, snapshotId, basisKind, contentDigest, lineageDigest a podle
varianty revisionId nebo artifactId/publicationReceiptId. Descriptor nikdy
neobsahuje plaintext podkladu, current pointer ani důvěryhodnost dodanou
modelem. Lineage digest pokrývá přesný descriptor bez samotného lineageDigest.
GenerationCreated a generation.job.created obsahují stejný kind/frozenBasis;
pro ostatní kinds je frozenBasis=null. Descriptor, nový child root, initial
request, canonical outcome, audit a outbox se commitnou společně (§49.5).
Source inputs/plan/state/artifacts/control se nemění. Jeho pozdější update,
failure nebo cancel nemění zmrazené vstupy child jobu. Hydration z uloženého
snapshotId ověřuje actual bytes, content/lineage digest a případný publication
receipt, nikdy current state source jobu. Consumer používá tento frozen podklad.

Idempotency lookup §49.4 předchází nové způsobilostní kontrole: stejný stable
locator/request digest vrací původní frozen receipt, změněný selector/digest
se stejným klíčem je IDEMPOTENCY_CONFLICT, UNKNOWN vyžaduje reconciliation
původního commitu. Souběžná změna relevantních locked zdrojů vede k novému
ověření před jedním commitem, nikoli k přijetí pohyblivého podkladu. Nový key
má vlastní child identity/běh. Sdílené prostředky a side effects nadále
podléhají existující isolation/coordination; FOLLOW_UP není jejich výjimka.

Referenční model netvrdí skutečné SQL locks ani runtime sufficiency.
Serverové consistent/sufficient výsledky musí pocházet z konkrétního
validatoru daného podkladu; boolean dodaný klientem/modelovým proposalem
nestačí. Tyto implementační a ostatní kind policies jsou samostatné povinnosti.

