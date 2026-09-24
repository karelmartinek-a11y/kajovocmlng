# Fáze 2 — PARTIAL

Fáze 1 zůstává **PARTIAL**, celý SSOT není uzavřený ani freeze-ready. Bylo opraveno šest chybějících mapování a ověřena jejich skutečná účast při validaci obsahu. Úplný graf a kompatibilita všech předávek nejsou prokázány. Žádná úplná předávka proto nebyla jen na základě opravy mapování označena VERIFIED.

## Výchozí a výsledný checkout

Větev `main`, výchozí i výsledný HEAD `6180d9fe67dfaa5365190301dfd58cc8d9812f3d`. Výchozím bodem fáze 2 je **necommitnutý výsledek fáze 1**, nikoli samotný HEAD. Nebyl proveden commit, push, merge, release, reset ani clean. AGENTS.md nebyl nalezen v repozitáři ani v nadřazených adresářích pracovního kořene.

`audit/generated/phase2-entry.json` zaznamenává počáteční status, hashe všech tehdejších změněných/nezařazených souborů, hash celého binárního diffu a dekódovaný rozdíl vložených zdrojů proti HEAD. Úplný diff a přesná vstupní kopie jsou v `.cache/phase2-entry/`. `audit/generated/phase2-provenance.json` obsahuje výsledný status a kontrolu zachování předchozích souborů. Všechny předchozí dirty soubory kromě záměrně dále upraveného SSOT zůstaly bajtově stejné; historická zpráva ani JSON výsledky fáze 1 nebyly přepsány.

Výsledný SHA-256 SSOT: `dc70b68c27dfae40e5836ce7913d819c336a8d22df48c585c147e877cdea011d`.

Autorita: README, SSOT 55.2–55.3 a `r13/contracts/effective-precedence-index.json#/interpretationRules`. Pořadí revizí samo nepovoluje override. Kanonické vložené zdroje a jejich shodné vložené kopie se mění společně; historické manifesty nejsou přepisovány na novou historii.

## Proč 16 browserových odkazů nezměnilo počet 260

Fáze 1 změnila proti HEAD přesně tři vložené zdroje: `contracts/payload-contracts.json`, jeho R9 `manifest.json` a `r16/contracts/r15-visual-operation-closure.json`. Poslední obsahuje osm browserových operací, každou se dvěma nově explicitními odkazy. Před změnou už měly `requestDefinition`/`responseDefinition` a příslušné `*SchemaAuthority`; definice tedy existovaly a alternativním mechanismem se rozlišovaly. Doplnění `*SchemaRef` zpřístupnilo vazby také projekcím UI.

Naproti tomu například `contracts/operation-contracts.json#/records/3` (`agent.approval.request`) odkazuje na chybějící `urn:kcml:r9:operation:agent.approval.request:command` a `:response`. Těchto 260 referencí patří 130 jiným operacím. Průnik s osmi browserovými operacemi je prázdný. Nejde o snížení zakryté chybným čítačem ani o neúčinnou browserovou změnu. Konkrétní původní a nové browserové atributy i všech 260 chybějících referencí jsou v `phase2-provenance.json`.

## Počty před a po

| Vlastnost | Před | Po |
|---|---:|---:|
| Efektivní operace / trasy | 619 / 542 | 619 / 542 |
| Vstupní pozice specialistů R11 | 66 | 66 |
| Pozice R11 bez kind → schema nebo raw kontraktu | 46 | 27 |
| Odlišné nemapované kinds v těchto pozicích | 29 | 23 |
| Generační druhy uzlů / integrační kroky | 19 / 14 | 19 / 14 |
| Druhy artefaktů v modelovaných slotech | 81 | 81 |
| Nevyjasněné událostní hranice fáze 1 | 152 | 152 |
| Konfliktní schema identity v automatickém inventáři | 0 | 0 |
| Nerozlišené odkazy fáze 1 | 260 | 260 |
| Obecné trasy fáze 1 | 509 | 509 |
| Selhání obsahových testů fáze 1 | 8 / 108 | 8 / 108 |
| Selhání nových testů obsahu artefaktů | 6 / 77 | 0 / 77 |
| Řádky BLOCKED_MISSING_CONTRACT | 458 | 439 |
| Řádky NOT_VERIFIED | 2 746 | 2 765 |
| Úplné předávky VERIFIED / FIXED_AND_VERIFIED | 0 / 0 | 0 / 0 |

Matice obsahuje 3 204 řádků povinností a hranic: 66 specialistních vstupů, 122 generačních vstupních/výstupních slotů, 25 řídicích hran R11, 13 explicitních integračních závislostí, 1 588 výskytů hranic v route kontraktech, 1 238 vstupních/výstupních hranic operací a 152 událostních blokátorů. **To není počet prokázaných runtime předávek.** Route a operation záznamy jsou různé lokace téhož možného toku; nejsou vydávány za unikátní runtime hrany.

Dalších 1 008 zdrojových výskytů potenciálních vazeb je zachováno v `discoveredCandidates`, včetně kapsle, runtime a UI zdrojů. Vyžadují posouzení aktivní autority a významu. Úplný počet skutečných producentů, konzumentů a relevantních předávek proto není uzavřený; `namedProducers` a `namedConsumers` jsou pouze počty různých pojmenovaných konců v modelovaných řádcích, včetně označení volajícího. Matice tuto nejistotu nezaměňuje za nulu chyb.

Tyto počty pojmenovaných konců jsou před i po 667 / 666. Přesun 19 pozic z BLOCKED_MISSING_CONTRACT do NOT_VERIFIED znamená opravené mapování, nikoli ověřenou celou předávku. Prokázán je jeden opakovaně používaný strukturální nesoulad tvarů referencí; počet dalších skutečných nekompatibilit zůstává neurčený.

## Provedené opravy a důkazy

Autoritativní změny:

- `contracts/generation/artifact-schema-map.json`: šest položek níže, současně v obou shodných vložených výskytech KCML-EMBEDDED a KCML-R5-RESOURCE.
- `contracts/execution/embedded-manifest.json`: jen velikost a raw digest změněné mapy, rovněž obě vložené kopie.

| Kind | Konkrétní definice | Doložený producent návrhu | Opravené pozice R11 |
|---|---|---|---:|
| REQUIREMENT_PROPOSAL | RequirementProposal | REQUIREMENTS_ANALYST | 5 |
| SOURCE_ANALYSIS | SourceAnalysis | SOURCE_RESEARCHER | 3 |
| CAPABILITY_DECISION | CapabilityDecision | CAPABILITY_RESOLVER | 4 |
| CONTRACT_ARCHITECTURE | ContractArchitecture | CONTRACT_ARCHITECT | 4 |
| GENERATION_PLAN | GenerationPlan | IMPLEMENTATION_PLANNER | 2 |
| INTEGRATION_PLAN | IntegrationPlan | INTEGRATION_ARCHITECT | 1 |

Definice jsou v `contracts/generation/generation-contracts.schema.json#/$defs/<Definition>`, bundle ID `urn:kcml:generation-contracts:2`. Vazby producenta jsou doloženy `contracts/generation/specialist-output-map.json`, `r11/contracts/specialist-call-sites.json`, příslušnými instrukcemi a výstupními obálkami `<ROLE>Proposal/properties/proposal/anyOf/0`. Cílové kinds jsou konkrétní konstanty vstupních polí `r11/contracts/orchestration.schema.json#/$defs/<ROLE>Input/properties/inputs/properties/<slot>`; návaznosti dokládá řídicí graf R11. Nejde pouze o převod podobných názvů.

Například `CAPABILITY_RESOLVERInput.inputs.requirementProposal` vyžaduje referenci druhu REQUIREMENT_PROPOSAL. Nenulová větev producenta REQUIREMENTS_ANALYST přímo odkazuje na RequirementProposal, jehož povinná pole jsou `objective`, `requirements`, `ownerDecisionRefs`, `openQuestions`, objekt je uzavřený a `requirements` má nejméně jeden prvek. Oprava vybírá **tutéž definici**, ne její zjednodušenou kopii. Pro obsahový podkontrakt tedy není třeba odhadovat obecnou inkluzi dvou různých schémat. Zachovány jsou rovněž původní nullable větve obálky pro dotaz/blokátor.

Skutečná validační cesta je existující vložený `scripts/ssot/ssot_control.py`: `ArtifactResolver.get` ověří trusted inventory, velikost/digest bajtů, provede strict JSON parse, vybere mapu kind, vyžaduje přesnou definici a předá obsah `Document.validate_address`. Ta kontroluje ID a bundle digest a provede nativní JSON Schema validaci s FormatChecker. Selhání se propaguje jako ContractFailure, nikoli PASS. GEN-G02 a R12 `model-artifact-handoff.json` tuto validaci normativně vyžadují.

Testy před opravou odmítají šest validních obsahů na `Unknown artifact kind`; po opravě je tatáž cesta přijímá a odmítá chybějící pole, špatný typ, null, neznámé pole, chybnou JSON serializaci, duplicitní JSON klíče, nesprávnou definici a digest. RequirementProposal má navíc negativní testy prázdných requirements, nepovolené varianty a duplicitních identit. Testovaná JSON_SCHEMA_BUNDLE výjimka používá existující metaschéma 2020-12 a kontrolu lokálních referencí; chybný typ a chybějící reference jsou odmítnuty.

Omezení testů: fyzické čtení bajtů je nahrazeno paměťovým čtením; parser, trusted inventory, adresy, digests a validátor jsou původní vložený referenční kontrakt. Testy necertifikují zabezpečení filesystemu, dostupnost tranzitivních registry artefaktů, sémantickou platnost celého generačního plánu ani produkční runtime. Platné příklady jsou schema fixtures, nikoli důkaz všech runtime preconditions.

Reprodukce: `scripts/phase2_repair_handoffs.py` odvozuje a ověřuje změny ze zdrojových vazeb, zachovává obě vložené kopie. `--reproduce` porovnává celý výsledný SSOT s opravou aplikovanou na přesný dirty vstup fáze 2. UI projekce nejsou změnou mapy dotčené; všech šest existujících projekcí zůstává shodných. Kapsle a historické manifesty nejsou přepsány. Globální integritní manifesty nebyly v této fázi prohlášeny za aktuální.

## Otevřené blokátory a neověřené oblasti

1. **Kompaktní reference R11 není ArtifactRef.** Vstup `CAPABILITY_RESOLVERInput.inputs.requirementProposal` obsahuje nullable `schemaDigest`, nemá `schema` adresu, `path` ani `producerNodeId`; nativní ArtifactRef tyto položky vyžaduje a je uzavřený. Protipříklady v testech dokazují odmítnutí oběma směry. Chybí doložené úplné materializační/hydratační propojení: lookup v autoritativním inventáři, přesný význam schemaDigest a finite accepted schema digests podle R12, odmítnutí stale/null, zachování provenance a korelace. Nelze ho nahradit object-spread nebo domyšlenou cestou. Obsahové mapování opravuje dílčí chybu, nikoli tento transportní podkontrakt.
2. **Zbývajících 23 kinds / 27 pozic:** ACCEPTANCE_CRITERIA, AGENTIC_SECURITY_CONTEXT, BROWSER_DIRECTIVE_SET, CANONICAL_CHAT_HISTORY, CHAT_TURN, CLOSURE_SNAPSHOT, COMPONENT_REGISTRY_SNAPSHOT, CONTRACT_REGISTRY_SNAPSHOT, CONTRACT_SET, EXTERNAL_DEPENDENCY_SET, FAILED_ARTIFACT_SET, GENERATION_SPECIFICATION, MCP_CONTRACT_SET, OWNER_INTENT, REPAIR_HISTORY, RESEARCH_ARTIFACT_SET, RUNTIME_EVIDENCE, RUNTIME_PROFILE, SECRET_REFERENCE_SET, SOURCE_BUNDLE, VALIDATOR_PROFILE, VALIDATOR_REPORT, WORKSPACE_SNAPSHOT. Přesné konzumenty a pointery obsahuje matice. Pro množinové/snapshot kinds není prokázán člen, obálka, kardinalita, verze ani producent; nelze je mechanicky přesměrovat na jeden existující záznam. U GENERATION_SPECIFICATION existuje kandidát GenerationSpecification i přísnější ApprovedGenerationSpecification; samotný název nedokládá přijatelný stav předchozí specifikace a producer binding. Chybí důkaz výběru, nikoli nutně definice v celém SSOT.
3. **152 událostních hranic:** každá má vlastní `event-applicability:<operationId>`, autoritativní lokaci a související event/terminal/successor atributy. Aktuálně odvozená množina přesně odpovídá fázi 1. Všechny jsou BLOCKED_MISSING_CONTRACT, žádná nebyla prohlášena za N/A. Je třeba doložit konkrétní emisi, payload a konzumenta, nebo normativní nepoužitelnost. Automatické dohledání atributů není úplná ruční event review.
4. **Větvení a obnova:** R11 graf zachovává všech 25 predikátů a repair-loop pravidla; matice z řídicí hrany nedělá automaticky datový tok. Nenulový návrh není totéž co dotaz nebo blokátor. Je třeba dokázat vymahatelnou podmínku předání do povinného slotu, včetně větví `ALWAYS`. Generační inputBindings vybírají root nebo konkrétního předchůdce; katalogové pořadí neurčuje tok. Ukončení, fan-out, retry a resume nemají plošný důkaz kompatibility.
5. **Šíře grafu:** 1 008 kandidátních výskytů zůstává k sémantické klasifikaci. Úplný graf nebyl dokončen. Terminální ani volitelně nepoužitý výstup není automaticky označen jako osiřelá chyba. Část zbytku je neprovedená revize, nikoli prokázané chybějící rozhodnutí vlastníka; nelze tvrdit, že všechny zbývající opravy vyžadují nové doménové pravidlo.
6. **Závislosti fáze 1:** 260 referencí/130 operací, 509 obecných tras, 1 527 obecných hraničních schémat, 74 strukturálně rozlišených definic bez úplné sémantické revize a osm známých negativních selhání zůstávají. Neznámé query, canonicalJson, neznámé a duplicitní doménové sloty u secret.create/generation.job.create nejsou touto fází opraveny. Jejich původní selhání nebyla schválena jako nový očekávaný PASS.
7. **Starší samostatné validační blokátory:** R11 verifier končí `NO_PRESERVED_R10_MARKER`; generation checker končí `CONTRACT_PACK_DRIFT scripts/ssot/audit_checks.py: Embedded bytes differ`. Oba stavy byly přítomny již na dirty vstupu fáze 2 a po opravě se nezměnily. Je nutné rozlišit historický receipt a aktivní manifest; nebyly naslepo přehashovány historické podklady.

## Kontroly a návratové kódy

| Příkaz | Před | Po | Skutečný výsledek |
|---|---:|---:|---|
| `python scripts/phase2_run_checks.py --entry` / bez přepínače | 1 | 1 | Izolované spouštění níže; nezmění evidenci fáze 1 |
| `python scripts/verify_schema_references.py` | 1 | 1 | 2 932 kontrol, 260 selhání |
| `python scripts/verify_phase1_contracts.py` | 1 | 1 | 108 případů, 8 selhání |
| `python scripts/run_baseline_gates.py` | 0 | 0 | Pět stávajících bran PASS; nikoli doménové uzavření |
| `python r11/scripts/verify_r11.py 00_SSOT/KajovoCMLNG_SSOT.md` | 1 | 1 | Chybí preserved R10 marker |
| `python scripts/ssot/ssot_control.py 00_SSOT/KajovoCMLNG_SSOT.md --check` | 1 | 1 | Již existující drift audit_checks.py |
| `python scripts/verify_phase2_handoffs.py --entry` / bez přepínače | 1 | 0 | 77 případů, 6 → 0 selhání; transportní protipříklady nadále otevřené |
| `python scripts/phase2_handoff_closure.py --entry` / bez přepínače | 1 | 1 | Reprodukovatelný inventář; úplné uzavření FAIL |
| `python scripts/phase2_handoff_closure.py --check` | — | 1 | Matice se přesně reprodukuje; kód 1 ponechává viditelné neuzavřené předávky |
| `python scripts/phase2_repair_handoffs.py --check` | — | 0 | Žádné čekající změny, idempotence |
| `python scripts/phase2_repair_handoffs.py --reproduce` | — | 0 | Přesná reprodukce celého SSOT z dirty vstupu |
| `python scripts/phase2_evidence.py` | — | 0 | Zachování předchozí práce, stejná množina 152 událostí, tři testy odmítnutí vynechaného záznamu |
| `python scripts/project_experience.py --check` | — | 0 | Shodných šest projekcí |
| `git diff --check` a `python -m compileall -q scripts` | — | 0 | Whitespace / syntaktická kontrola, nikoli sémantický PASS |

Podrobné stdout/stderr a kódy existujících kontrol: `audit/generated/phase2-checks-before.json`, `phase2-checks-after.json`. Obsahové případy i fixtures: `phase2-content-tests-before.json`, `phase2-content-tests-after.json`. Anti-omission testy odstraňují hranu, kandidátní výskyt nebo celý zdroj z kopie matice a vyžadují odmítnutí. Kontrola není obecný rozhodovač inkluze JSON Schema; bez důkazu ponechá NOT_VERIFIED a vrací nenulový kód. Import validační závislosti není volitelný.

## Skutečný rozsah čtení

Přečteny pracovní instrukce, README, QUALITY_ASSURANCE, zpráva fáze 1; oba JSON výstupy fáze 1 byly celé strojově načteny, s kontrolou souhrnů, browserových a chybějících referencí. Celý aktuální diff byl zachycen; ručně byl kontrolován význam dekódovaných změn a změny validačních instrukcí/skriptu, nikoli každá řádka rekomprimovaného base64 diffu nebo generovaných reportů.

Pro opravy byly přečteny mapy artifact-schema, raw kinds, specialist-output, R11 specialist-input a instrukce, generační step-catalog, orchestration-graph, R12 model-artifact-handoff, všechny šestice opravovaných kořenových definic a obálka RequirementProposal včetně Objective, Requirement, OwnerDecision, Question, SourceRef a ArtifactRef. Dále cíleně CAPABILITY_RESOLVERInput, SchemaArtifact, GenerationSpecification/ApprovedGenerationSpecification, PlanNode, ScopeLock, RequirementCoverage, CapabilityCoverage a integrační katalog. U rozsáhlých call-sites a semantic-validation-rules byly celé dokumenty načteny a cíleně posouzeny relevantní vazby; není tvrzena ruční revize všech polí. Referenční validátor byl cíleně přečten v oblastech Document, ArtifactResolver, validate_plan a částí result/patch validace; test spouští skutečný vložený kód.

Automatický inventář načetl 402 JSON dokumentů ze všech rozpoznaných rodin, samostatných JSON bloků a 21 souborů kapsle. Seznam s původem je v `matrix.sources`. Kandidátní výskyty zahrnují mj. GenerationFlowLink z kapsle a domain-orchestration-binding. To není úplná řádková sémantická revize těchto zdrojů ani důkaz aktivní relevance každého kandidáta. Žádný historický podklad nebyl bez dalšího povýšen na autoritu.

## Předání fázi 3

Převzít neuzavřené mapování a adapter/hydration hranice výše, nikoli předpoklad hotové fáze 2. Prověřit význam bundle/definition/content digestů, nullable schemaDigest R11 a konečné seznamy přijatých schémat R12; nezaměnit s nulovým počtem konfliktů `$id`. Čítače 597/520 v R11 a 619/542 v aktuální efektivní vrstvě mají různé revizní rozsahy, proto nejsou automaticky konflikt stejného počítadla. Prověřit jejich explicitní scope. U stavů a úspěšných odpovědí odlišit nenulový proposal, otázku, blocker, serverový commit, ACK, dokončení a post-activation důkaz; zvláště sladit řídicí predikáty s povinnými vstupními sloty. Otevřené negativní příklady fáze 1 i samostatná selhání starších kontrol musí zůstat viditelné.

Povinné výstupy: `audit/phase2-handoff-closure.md`, `audit/phase2-handoff-matrix.json`, `audit/phase2-unresolved.json`. Pomocná před-opravová matice: `audit/phase2-handoff-matrix-before.json`.
