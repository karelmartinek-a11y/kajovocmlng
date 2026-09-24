# Fáze 3 — sémantické uzavření kontraktů

**Výsledek: PARTIAL.** Fáze 1: PARTIAL. Fáze 2: PARTIAL. Repo není dokončeno ani freeze-ready.

## Výchozí stav a rozsah

- Větev `main`, HEAD `6180d9fe67dfaa5365190301dfd58cc8d9812f3d`; předfázový SSOT snapshot `.cache/phase2-entry/SSOT.md` SHA-256 `cc72d9719a936574c2c2c550fad66f2c330cd43843b19962eadf66edeea402ee`.
- Zachovány všechny předchozí lokální změny; historické zprávy a matice fází 1/2 nebyly přepsány. Předchozí strom už obsahoval opravy fáze 1/2: šest R11 kind→schema mapování a předešlé kontraktové změny.
- Prošel jsem úplné zprávy a JSON matice/unresolved fází 1 a 2; celý embedded SSOT jsem inventarizoval přes resource parser (402 zdrojů uvedeno ve fázi 1), a plně sémanticky četl jen relevantní identity, čítače, named state fields, R11/ArtifactRef, `secret.value.read` a navazující normativní pravidla. Netvrdím řádkovou revizi všech operací.

## Před a po

| Kategorie | Před fází 3 | Po fázi 3 |
|---|---:|---:|
| Nekompatibilní obsah pod stejnou cílovou schema ID (`live-event`, `history-query`) | 2 | 0 |
| Cílová sequence/stateVersion pole mimo normativní Counter kontrakt | 515 | 0 |
| `secret.value.read`: `SUCCEEDED`, `terminal=false`, `output=null` přijato | 1 | 0 |
| Pojmenovaná state/disposition pole přijímající `NOT_A_VALID_STATE` | 8 | 8 |
| Ověřený bezestrátový most R11 reference → ArtifactRef hydratace | 0 | 0 |
| Fáze 1: operace / trasy / nerozlišené odkazy | 619 / 542 / 260 | 619 / 542 / 260 |
| Fáze 2: chybějící R11 pozice / druhy / event applicability blockers | 27 / 23 / 152 | beze změny |

Nulový počet konfliktů dvou cílových identit neznamená globální uzavření všech SSOT identit. Fáze 1/2 baseline counts nejsou odvozeny od historických čísel naslepo: aktuální kontroly níže znovu hlásí 260/8 a fáze 2 zdrojová zpráva nese uvedené počty.

## Provedené opravy

- V autoritativním `ui/contracts/live-experience.json` oddělil jsem presentation event/query od dashboard live-stream/history API. Presentation ID jsou `urn:kcml:experience-event:1` a `urn:kcml:experience-history-query:1`; stream a history API si ponechaly původní ID. Původní fyzické standalone schémata byla vložena do kanonického resource; `project_experience.py` je nyní reprodukovatelně projektuje. Tím se opravila i příčina, proč Fáze 2 identity scanner vykazoval nula: dříve nepočítal standalone UI projekce.
- Na všech 515 relevantních polích — 509 R9 route event sequence, dvě R14 platformní stateVersion a čtyři experience/live-stream sequence/stateVersion — jsem použil přesný decimal-string `Counter` z generation contracts/SSOT: 0 až 9223372036854775807 bez znaménka/leading zeros, bez JS `Number`. R9/live-stream sequence zůstává pozitivní, experience sequence zachovává nulu. Negativní testy pokrývají 2^53, maximum, max+1, -1, +1, whitespace, leading zero, decimal, exponent, integer JSON type a null.
- `secret.value.read` response schema podle SSOT §6.7 nyní vynucuje `SUCCEEDED→terminal=true`, `ACCEPTED→false`, `CANCELLED→true`, error-required pro FAILED/CANCELLED. Nepřidal jsem domněnku, že SUCCEEDED output musí být neprázdný; null output zůstává povolen, protože nalezený kontrakt to nevylučuje.
- Změněné resource bytes i R9 embedded manifest digest jsou reprodukovatelné skriptem `scripts/phase3_repair_semantics.py`; fyzické projekce ověřuje `scripts/project_experience.py --check`.

## Neuzavřené blokátory

- **Browser presence sequence:** `r15/contracts/browser-visual-collaboration.schema.json#/$defs/BrowserPresencePointer/properties/sequence` stále přijímá neomezený desetinný string. SSOT nedokládá, zda jde o platformní eventSequence, nebo client/native pointer counter; nebyl změněn pouze podle názvu.
- **R11 → ArtifactRef:** kompaktní reference má pole `artifactId, contentDigest, kind, mediaType, provenanceDigest, schemaDigest, sizeBytes`; native ArtifactRef vyžaduje `artifactId, contentDigest, kind, mediaType, path, producerNodeId, provenanceDigest, schema, sizeBytes`. Chybí `schema`, `path`, `producerNodeId`; navíc `schemaDigest` nemá prokázanou ekvivalenci s `schema.bundleDigest`. SSOT vyžaduje validovat payload konkrétním schématem, ale žádný bezeztrátový lookup/hydration output a chyby nejsou normativně definovány. Žádný formální adaptér jsem nevymyslel.
- **Stavové slovníky:** osm polí v `owner.mfa.reset`, `chat.turn.steer`, `config.rollback`, `backup.restore`, `acceptance.run.start`, `acceptance.run.cancel` jsou stále obecné identifier masky a test přijímá `NOT_A_VALID_STATE`. V prohledaných autoritativních definicích chybí finite enumy/transition rules; hodnoty jsem nevymyslel.
- **Digest linkage:** SSOT §6.3/§51.4 stanoví UTF-8/JCS + SHA-256 pro canonical JSON; embedded manifest samostatně uvádí `SHA256_RAW_EMBEDDED_BODY_WITH_FINAL_LF`. R12 rozlišuje `canonicalBytesDigest`, `producerSchemaDigest` a `provenanceDigest`, vyžaduje shodu producer schema digestu s konečným `acceptedSchemaDigests` a validaci týchž canonical bytes. Chybí přesné mapování R11 nullable `schemaDigest` na R12/native identitu a vymezení hashovaných schema/bundle bytes.
- Po změně autoritativního UI resource je historická phase2 source-derived matrix zastaralá: její `--check` hlásí `MATRIX_COVERAGE_OR_CONTENT_DRIFT`. Původní fázi 2 jsem nepřepisoval; fáze 4 má regenerovat novou kumulativní handoff projekci nebo verzovanou kopii.

## Kontroly

Příkazy byly spuštěny izolovaně v kopii pod `.cache`, takže původní `audit/generated/phase1-*` a `phase2-*` důkazy zůstaly nedotčené. Přesné stdout/stderr a exit codes jsou v `audit/generated/phase3-existing-checks.json`.

| Kontrola | Exit | Výsledek |
|---|---:|---|
| `python scripts/verify_schema_references.py` | 1 | 2932 kontrol, 260 nerozlišených vazeb (stejné jako před fází) |
| `python scripts/verify_phase1_contracts.py` | 1 | 108 kontrol, 8 selhání (předchozí nález zachován) |
| `python scripts/phase1_repair_contracts.py --check` | 0 | předchozí opravy fáze 1 stále reprodukovatelné |
| `python scripts/phase2_repair_handoffs.py --check` | 0 | šest předchozích mapování reprodukovatelných |
| `python scripts/verify_phase2_handoffs.py` | 0 | 77 obsahových případů, 0 selhání; omezení hydratace zůstává |
| `python scripts/project_experience.py --check` | 0 | všechny osm projekcí aktuální |
| `python scripts/verify_experience.py` | 0 | všechny kontroly PASS |
| `python scripts/verify_observability.py` | 0 | všechny kontroly PASS |
| `python scripts/phase2_handoff_closure.py --check` | 1 | stale historic matrix po fázi 3: `MATRIX_COVERAGE_OR_CONTENT_DRIFT` |
| `python r11/scripts/verify_r11.py 00_SSOT/KajovoCMLNG_SSOT.md` | 1 | předchozí chyba `NO_PRESERVED_R10_MARKER` stále reprodukována |
| `python scripts/ssot/ssot_control.py 00_SSOT/KajovoCMLNG_SSOT.md --check` | 1 | předchozí chyba `CONTRACT_PACK_DRIFT scripts/ssot/audit_checks.py: Embedded bytes differ` stále reprodukována |
| `python scripts/verify_phase3_semantics.py` | 0 | identity, Counter mezní hodnoty, outcome tuple testy PASS; osm state fields potvrzeně otevřených |
| `python scripts/phase3_repair_semantics.py --check` | 0 | žádná nereprodukovaná změna |

Obě starší chyby existovaly v baseline fáze 2 (podle `audit/generated/phase2-checks-before.json`) a jsou nezávislé na opravách této fáze. Phase2 matrix drift je nově vyvolán změnou jejího vstupního SSOT; není vydáván za původní chybu validátoru.

## Dopad pro fázi 4

Nová embedded experience resource nyní obsahuje samostatné canonical stream/history schéma objekty; aktualizované fyzické projekce jsou `01_UI_CONTRACT/ui/contracts/live-event.schema.json` a `.../history-query.schema.json`. Fáze 4 má převzít jejich odkazy v UI registry/operational exposure, zkontrolovat všeobecné schema-ID registry proti standalone projekcím a regenerovat kumulativní Phase2 handoff matrix bez přepsání historických výsledků. Stavové enumy a ArtifactRef bridge zůstávají blokátory, ne hotová práce pro UI.

## Změněné autoritativní/projekční soubory

- Autoritativní: `00_SSOT/KajovoCMLNG_SSOT.md` embedded `ui/contracts/live-experience.json` a `contracts/payload-contracts.json` (včetně digest manifestu) a `r14/contracts/browser-interaction.schema.json` (platformní stateVersion vazby).
- Projekce: `01_UI_CONTRACT/ui/contracts/live-experience.json`, `live-event.schema.json`, `history-query.schema.json`, odvozené locale a view matrix soubory.
- Kontroly: `scripts/project_experience.py`, `scripts/verify_experience.py`, nové `phase3_repair_semantics.py`, `verify_phase3_semantics.py`, `phase3_run_checks.py`, `phase3_write_audit.py`.
- `git diff --name-only` na uzavření auditu čítal 16 sledovaných cest; necommitnuté změny z fází 1–2 zachovány.

Výstupy: `audit/phase3-semantic-closure.md`, `audit/phase3-contract-matrix.json`, `audit/phase3-unresolved.json`.
