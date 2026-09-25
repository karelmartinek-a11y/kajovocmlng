# Pokračování z 664d617 — doménové read hranice a MCP list kontrakty

Stav celého balíku: **BLOCKED**. PR #2 zůstává draft, bez merge a bez freeze.
Tento výsledek není dokončením celého sémantického auditu.

## Identita a zachování vstupu

Větev `work/ssot-completion-2026-09-25`, vstupní čistý HEAD
`664d617f4d2590a4c8f2a45b63b6532698bf051c`.
Vstupní SHA-256 `00_SSOT/KajovoCMLNG_SSOT.md`:
`98dfcebd89aee508982a87847fd347ec89307fe54d2662d7b8c8b64c251f548f`.
Výsledný SSOT SHA-256:
`8d5d6706b3ffb366b6de782af66dadb8ebb4a85f4e7db1c63110e98adabc3982`.
Autoritou zůstává účinný SSOT a jím připnutý kontrakt; nové auditní soubory
nejsou produktovým zadáním. Historické důkazy nebyly přepisovány.

`report_read_boundary_evidence.py` porovnává dekódované operation-contracts
proti 664d617: všechny operation records a deset dřívějších schema definic jsou
beze změny. Přidáno je osm konkrétních masek a jedna přesná projekce upstream
schématu. Velký textový diff SSOT vzniká zejména překódováním gzip resources;
čitelný obsah osmi nových masek je v `read-boundary-evidence.json`.

## Generation: samostatné posouzení všech tří hranic

| Operace | Request | Response a předávka | Event / zbývající blokace |
|---|---|---|---|
| `generation.spec.approve` / route.0234 | Zachováno šest přesných business polí a nenullové approval guards podle §12.21. Query/transport mapping není celý uzavřen. | §12.21 stanoví šest atomických zápisů, nikoli přesnou veřejnou projekci receiptu. Není nahrazena dokumentem ApprovedGenerationSpecification ani interním StepOutput. | §12.21 výslovně „uloží OWNER approval event a audit“; SourceEnum044 v §12.44 obsahuje `generation.spec.approved`. Není doložen převod lifecycle variant R9 na tento agregátový event a přesný doménový payload. |
| `generation.spec.revision.read` / route.0232 | Exact job/revision path zůstává. Generic body/query ještě nemá prokázaný exact/no-input mapping. | Stejný `GenerationSpecification` jako konzument; nově povinně porovnáno s trusted persisted job ID, revision ID a skutečným canonical digestem obsahu. | Samotné GET není důkaz NONE. §12.44 definuje job stream; jeho enum obsahuje proposed/approved, ne read event. R9 přesto připojuje lifecycle eventSchema bez určení vlastní vs. agregátové události. |
| `generation.plan.read` / route.0237 | Exact job/plan path zůstává; body/query otevřené jako u revision read. | Stejný `GenerationPlan`; navíc trusted persisted job/plan ID a canonical digest obsahu. | §12.44 uvádí `generation.plan.created`, nikoli read event. Nedoložené přiřazení R9 eventSchema k readu nebo agregátu zůstává otevřené. |

Všechny tři eventSchema stále nabízejí `ACCEPTED`, `PROGRESS`,
`WAITING_FOR_INPUT`, `RECONCILING`, `TERMINAL` s obecným payloadem.
§26.15 stanoví pro replayable domain SSE `SseEnvelope`, ale jeho `payload`
je `JsonValue`: pouhé nahrazení `$ref` by žádnou business masku neuzavřelo.
§49.5 požaduje persistenci/outbox, immutable event ID, deduplikaci a očekávanou
sequence; gap vede k replay/snapshot, nikoli k tichému přeskočení.

U obou read operation records navíc stojí `READ_ONLY`,
`possibleEffectTrigger=NONE`, `outboxPurposes=[]`, ale současně obecné
`auditEventTypes=OPERATION_ADMITTED/OPERATION_STATE_CHANGED/OPERATION_TERMINAL`.
Tato pole ani absence read jména v enumu sama neprokazují význam veřejného
eventSchema. Přesné record values a celé příslušné pasáže jsou v aktuálním
`read-boundary-evidence.json`, nikoli pouze citované číslem kapitoly.

Prověřena byla i pozdější `ui/contracts/live-experience.json`: `#/stream`
odkazuje na existující authenticated event endpoints a canonical sources;
`#/specification/scope` výslovně stanoví review projection, nikoli náhradu
generation-job lifecycle. `#/eventSchema` nese `payloadRef`, ne approval
payload. Ani tato vrstva tedy nedodává chybějící převod těchto tří event hranic.

### Konkrétní otázky předložené OWNERovi

1. Approval: veřejná event hranice má být agregátový `generation.spec.approved`,
   nebo samostatný lifecycle operace s definovaným převodem na agregátový event?
   První varianta potřebuje přesný approval payload a replay vazbu; druhá navíc
   masky lifecycle variant a jejich vazbu na stejný commit. Ovlivněny jsou
   route.0234, generation stream, UI approval projection a outbox/recovery.
2. Oba reads: mají pouze request/response a změny sledují samostatným aggregate
   streamem, nebo emitují vlastní persistovaný read event? První varianta
   vyžaduje explicitní nepoužitelnost vlastního eventSchema; druhá také obsah,
   sequence, persistenci a replay read eventu. Ovlivněny jsou route.0232/0237,
   detail revision/planu, UI reducer a event publisher.

Tyto otázky nepřevádějí zbývající technické request/response práce na OWNERa.
Dosud není přijata žádná z alternativ. Žádná z těchto tří tras se neodečítá
z 505 obecných tras.

### Opravená vazba na persisted outcome

Normativní `scripts/ssot/ssot_control.py:validate_generation_read_handoff`
již nemůže přijmout úspěšný read jen podle jobId/planId. Server musí předat
samostatné trusted persisted ID/digest; chybějící snapshot, jiná revision,
jiný job či schema-validní změněný obsah se starým digestem jsou odmítnuty.
To jsou serverová validační data, nikoli nová pole veřejného commandu.

Producent: immutable repository document + jeho důvěryhodná identita/digest.
Konzument: response.output → stejný nativní document validator → precheck/plan
validation. FAILED/CANCELLED/ACCEPTED se nepředají jako dokument. Recovery
musí dodat nový potvrzený read odpovídající trusted snapshotu. Predicate
neprokazuje samotnou DB transakci, původ snapshotu ani celé DAG/hydratační gates.

## Nezávislá skupina: čtyři MCP list operace

SSOT již připínal `contracts/mcp-native-schema-artifact.json`:

- repository `modelcontextprotocol/modelcontextprotocol`,
- Git blob `213c58f6d9a1c2ce6ad055afe90bbdb095a29ee8`,
- `schema/2026-07-28/schema.json`, 181474 bajtů,
- SHA-256 `ef70b61f99b6d2e5e3b46863822eab08dff6a45bedc7a08914e0e5b133f40203`.

Byly získány přesně tyto bytes a ověřeny oba hashe i délka. Nebylo použito
latest schéma ani podobnost názvů. Bytes jsou nyní přímo vloženy v SSOT jako
`contracts/mcp/native-2026-07-28.schema.json`; projekce pod
`urn:kcml:mcp-native:2026-07-28` zachovává všechny nativní definice beze změny.

| Operace | Native request | Native complete response | Doménové pole výsledku |
|---|---|---|---|
| `mcp.prompts.list` | `ListPromptsRequest` | `ListPromptsResultResponse` | `prompts` |
| `mcp.tools.list` | `ListToolsRequest` | `ListToolsResultResponse` | `tools` |
| `mcp.resources.list` | `ListResourcesRequest` | `ListResourcesResultResponse` | `resources` |
| `mcp.resources.templates.list` | `ListResourceTemplatesRequest` | `ListResourceTemplatesResultResponse` | `resourceTemplates` |

Masky zachovávají původně chybějící identity
`urn:kcml:r9:operation:<operationId>:command` a `:response` v autoritativním
`contracts/operation-contracts.json#/$defs`. Každý request má přesnou native
method, params a current-request metadata. Response je complete native list
nebo `JSONRPCErrorResponse`, nikdy obojí. Obsah jednotlivých položek se validuje
celou nativní definicí, ne obecnými `values` nebo popisem summary.

Výchozí registry tyto čtyři identity označují `PUBLIC_PROTOCOL`, `READ_ONLY`
a `mcp_discovery_snapshot`; preserved `OperationSemanticRecord` je obsahuje
na indexech 43 (tools), 50 (resources), 51 (templates), 53 (prompts).
`r8/registries/operation-namespace.json` zachovává jejich sourceOperationRef.
§10.7 vyjmenovává konkrétní protokolové list metody a authoring kontroluje
jejich přesné native `method.const`. Proto jde o wire masky těchto metod,
nikoli o serverový persistence receipt nebo payload podobně pojmenovaného API testu.

Normativní specializace: §10.3/10.10 zakazuje request/response směs a současný
result/error; §10.7 vyžaduje TTL/cacheScope; §10.11 zakazuje MRTR u listů;
§10.16.1 omezuje task augmentation na tools/call. Nové aliasy proto nepřijmou
`input_required`, `task`, neznámý resultType ani nedefinovaný rezervovaný error
code -32099 až -32023. Nezaměňují JSON-RPC response se serverovým DB receiptem.

Předávka: server list response → klientská validace → admission immutable
discovery snapshotu. Vložený `validate_mcp_list_handoff` ověřuje exact ID
type/value, nepředá protocol error jako snapshot, kontroluje TTL a stejný
cacheScope mezi stránkami. Rozlišuje absent nextCursor od validního prázdného
stringu. `MCP_CURSOR_INVALID` vyžaduje zahození traversal a nový request bez
cursoru (§10.7); read-only disconnect dovoluje abort a nový request podle
§10.3.1/10.12. Žádný unknown effect se nepřeznačuje na success.

Tyto čtyři operace nemají vlastní HTTP route record. Neodečítají se z 505 tras.
Transport headers/auth, request-scoped SSE notifications, skutečná persistence
snapshotů, cache context/freshness a bounded refetch zůstávají samostatné
integrační povinnosti. Osm rozlišených odkazů není osm sémantických PASS.
Zejména přenos tool descriptoru s polem inputSchema/outputSchema sám
neprokazuje uzavření referencí a validitu tohoto přenášeného schématu:
§10.8 compilation, revision binding a downstream tool argument/result
validation zůstávají povinné. List wire maska není náhradou těchto kontrol.

Individuálně prošetřené další `mcp.prompts.get` a `mcp.resources.read` zůstávají
INVESTIGATION_OPEN: první potřebuje propojit exact prompt revision s argument
kontraktem a MRTR; druhý exact URI/template s MIME/output kontraktem a MRTR/cache
pravidly. Native string map arguments ani text/blob content nejsou důkaz
doménové kompatibility. Nejde o prokázané OWNER rozhodnutí.

## Počty a jednotky

| Jednotka | Vstup | Aktuální strukturální výsledek | Rozdíl |
|---|---:|---:|---:|
| Nerozlišený operation request/response schema odkaz | 250 | 242 | -8 |
| Operace s alespoň jedním takovým odkazem | 125 | 121 | -4 |
| Route record s alespoň jednou obecnou hranicí | 505 | 505 | 0 |
| Obecná request/response/event definice hranice | 1512 | 1512 | 0 |
| Efektivní operace v katalogu | 619 | 619 | 0 |
| Efektivní route records | 542 | 542 | 0 |

Nově přesné definice stále vyžadují sémantický review: tento čítač vzrostl
99 → 107. Nespecifikovaná event applicability zůstává 152. Historických 3204
inventárních řádků se nevydává za runtime předávky; tento běh dokládá konkrétní
hranice ve scoped handoff matici, nikoli celý procesní graf.

## Kontroly a reprodukce

První `read-integration/commands.json` zachovává skutečné selhání generation
regrese: tvrdě očekávala pouze deset generation definic v celém registru.
Opravena je přesná množina na generation + čtyři doložené MCP páry + jejich
native projekci. Nové negativní kontroly stále odmítají přidanou i vynechanou
definici; množinová kontrola nebyla odstraněna.

Tentýž první přepočet našel 18 výskytů `UNAVAILABLE_FORMAT_CHECKER:uri`.
Doplněna je `rfc3986-validator==0.1.1` v `requirements-audit.txt` a skutečně
spuštěno `python -m pip install rfc3986-validator==0.1.1` (exit 0). URI se
neignoruje: cílené testy nově odmítají neplatné URI přes transitive native refs
v requestu i response. `uri-check/read-current.json`: 192 kontrol, exit 0.
Následující průchod zachytil zbývající `uri-template`; doplněno a skutečně
spuštěno `python -m pip install uri-template==1.3.0` (exit 0). `domain-items`
obsahuje 208 kontrol včetně neprázdných domain descriptorů, jejich required
polí, nesprávných typů a neplatné URI template (exit 0). Žádný format nebyl
odstraněn ze schématu, aby validátor prošel.

Poslední návazný průchod `review-final/commands.json` skončil exit 0 nad výše
uvedeným výsledným SSOT hashem. Všech 17 příkazů má očekávaný návratový kód;
tři baseline reproduktory správně skončily 1, current kontroly 0. Matice má
0 nested reference failures, 0 schema identity konfliktů a 0 neparsovaných
resources. To není sémantické uzavření zbývajících masek.

| Current kontrola | Zaznamenané check/asserční záznamy | Exit |
|---|---:|---:|
| Read boundary / MCP payload + handoff | 208 | 0 |
| Dosavadní generation domain / approval handoff | 110 | 0 |
| Generation operation variants | 671 | 0 |
| ProviderOutcome | 22 | 0 |
| Saga artifact handoffs | 13 | 0 |
| Native manifest | 7 | 0 |
| Portable manifest negatives | 13 | 0 |

Celkem jde o 1044 jednotlivých kontrolních záznamů, ne o 1044 runtime E2E
scénářů nebo uzavřených požadavků. Reproduktory: 664d617 read baseline
34 kontrol / 22 selhání; 897da64 ProviderOutcome 22 / 6; 897da64 domain 84 / 15.

Po tomto průchodu byly zpřesněny pouze testovací recovery fixtures: nový
immutable dokument má nové revision/plan ID (nikoli změněné bytes pod starým
ID) a cursor failure dostává skutečný request s expirovaným cursorem.
`recovery-fixtures/read-current.json` znovu prokazuje 208 kontrol, exit 0;
`read-baseline.json` 34 / 22, exit 1. Oba reporty obsahují skutečný příkaz,
exit code, hash své verze skriptu, dependencies a resource versions.
SSOT ani opravené kontrakty se tím nezměnily.

Meziběhy `read-integration`, `read-final`, `read-verified` a `read-review`
zůstávají historické. `read-review` navíc správně odmítl uzavřít běh po změně
dossier skriptu během jeho provádění; jeho dílčí úspěchy nebyly vydány za
finální výsledek. Následující `review-final` již proběhl bez zásahu do skriptů.

Následuje skutečně použitý příkazový postup; při novém běhu zvolit nový
`KCML_AUDIT_OUTPUT`, aby se tyto důkazy nepřepsaly.

```powershell
$env:PYTHONUTF8='1'
$env:KCML_AUDIT_OUTPUT='audit/generated/continuation-664d617/review-final'
python scripts/run_domain_continuation_checks.py --focused --provider --read
python scripts/update_manifests.py
python scripts/package_integrity.py
```

Runner zaznamenává skutečný vstupní hash každého baseline i current příkazu,
hash skriptu a resource versions; nepřipisuje baseline testu current SSOT hash.
Zaznamenává také Python, validační balíčky a hash requirements i samotného
runneru. Nenulové nested reference failures, schema identity konflikty nebo
neparsované resources nově způsobí nenulový návratový kód; pouhý úspěch
inventarizačního subprocessu není úspěchem této brány.
Guard payloady nebyly změněny, proto se široká guard sada neopakuje. Native
manifest, saga, generation, ProviderOutcome a domain regrese se opakují.

Vnější manifesty byly regenerovány pro aktuální větev, SSOT hash a 713
inventarizovaných souborů. `python scripts/update_manifests.py`,
`python scripts/package_integrity.py` a `git diff --check` skončily 0.
Výsledek integrity je `INTEGRITY_MATCH` při zachovaném `packageStatus=BLOCKED`,
nikoli potvrzení celého SSOT. Po poslední aktualizaci tohoto reportu se
manifesty znovu generují a kontrolují; žádný historický PASS se nepřebírá.

## Změněné soubory a přesné pokračování

Autoritativní změny: SSOT embedded operation-contracts, pinned native MCP bytes,
R9 manifest, native ssot_control a native embedded-manifest. UI projekce
nebyly významově změněny a ověřují se příkazem `project_experience.py --check`.

Autorské/testovací skripty: `close_mcp_list_operation_masks.py`,
`close_read_handoff_provenance.py`, `verify_read_boundary_completion.py`,
`report_read_boundary_evidence.py`; návazně upraveny
`verify_generation_domain_payloads.py`, `verify_generation_operation_masks.py`,
`investigate_missing_operation_masks.py`, `run_domain_continuation_checks.py`.
Dále requirements-audit, tento report, nové scoped důkazy a tři vnější manifesty.

Pokračovat z aktuálního dossieru `review-final/missing-operation-investigation.json`
a `review-final/read-boundary-evidence.json`, nikoli ze starých PASS.
Zbývá 121 operation pairs, 505 tras / 1512 obecných hranic, úplný procesní graf,
ověření všech dynamických resolverů a skutečných failure/cancellation/recovery
hran. U tří prioritních generation tras zůstávají konkrétní request/response/event
mezery výše; nová persisted-read kontrola je neprohlašuje za hotové.

**Závěr: BLOCKED.** Žádný merge, freeze ani úplný sémantický PASS.
