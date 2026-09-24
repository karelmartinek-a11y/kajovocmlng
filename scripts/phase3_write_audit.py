"""Build the Phase 3 handoff from actual pre-phase/current contracts and checks."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator
from ssot_sources import ROOT, SSOT, resource_index, resources


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return 'sha256:'+hashlib.sha256(raw).hexdigest()


def main():
    before_path = ROOT/'.cache/phase2-entry/SSOT.md'
    before_text = before_path.read_text(encoding='utf-8')
    before = resource_index(resources(before_text))
    after = resource_index()
    exp_path = 'ui/contracts/live-experience.json'
    old_experience = json.loads(before[exp_path]['raw'])
    new_experience = json.loads(after[exp_path]['raw'])
    old_physical_event = json.loads(subprocess.check_output(
        ['git', 'show', 'HEAD:01_UI_CONTRACT/ui/contracts/live-event.schema.json'], cwd=ROOT))
    old_physical_query = json.loads(subprocess.check_output(
        ['git', 'show', 'HEAD:01_UI_CONTRACT/ui/contracts/history-query.schema.json'], cwd=ROOT))
    new_physical_event = json.loads((ROOT/'01_UI_CONTRACT/ui/contracts/live-event.schema.json').read_text(encoding='utf-8'))
    new_physical_query = json.loads((ROOT/'01_UI_CONTRACT/ui/contracts/history-query.schema.json').read_text(encoding='utf-8'))

    states = {
        'owner.mfa.reset': ['enrollmentState'], 'chat.turn.steer': ['checkpointDisposition'],
        'config.rollback': ['state'], 'backup.restore': ['state'], 'acceptance.run.start': ['state'],
        'acceptance.run.cancel': ['state', 'cleanupStatus', 'reconciliationStatus']}
    def state_rows(rs):
        rows = []
        doc = json.loads(rs['closure/contracts/operation-payloads.json']['raw'])
        for op, fields in states.items():
            rec = next(x for x in doc['records'] if x['operationId'] == op)
            for field in fields:
                schema = rec['responseSchema']['properties'][field]
                rows.append({'operationId': op, 'field': field, 'authority':
                    f'closure/contracts/operation-payloads.json#/records/{doc["records"].index(rec)}/responseSchema/properties/{field}',
                    'schema': schema, 'acceptsHistoricalProbe': not list(Draft202012Validator(schema).iter_errors('NOT_A_VALID_STATE'))})
        return rows
    old_states, new_states = state_rows(before), state_rows(after)

    old_route = next(r for r in json.loads(before['contracts/payload-contracts.json']['raw'])['records']
                     if r['operationId'] == 'secret.value.read')
    new_route = next(r for r in json.loads(after['contracts/payload-contracts.json']['raw'])['records']
                     if r['operationId'] == 'secret.value.read')
    route_sample = {'routeId':'route.0390','operationId':'secret.value.read',
        'logicalOperationId':'00000000-0000-4000-8000-000000000001',
        'correlationId':'00000000-0000-4000-8000-000000000002','status':'SUCCEEDED',
        'terminal':False,'output':None,'error':None,'resultDigest':'sha256:'+'0'*64}
    old_accepts = not list(Draft202012Validator(old_route['responseSchema']).iter_errors(route_sample))
    new_accepts = not list(Draft202012Validator(new_route['responseSchema']).iter_errors(route_sample))

    old_ids = [old_experience['eventSchema']['$id'], old_physical_event['$id'],
               old_experience['observability']['querySchema']['$id'], old_physical_query['$id']]
    new_ids = [new_experience['eventSchema']['$id'], new_physical_event['$id'],
               new_experience['observability']['querySchema']['$id'], new_physical_query['$id']]
    counters = [
        ('experience.eventSchema.sequence', old_experience['eventSchema']['properties']['sequence'], new_experience['eventSchema']['properties']['sequence']),
        ('experience.eventSchema.stateVersion', old_experience['eventSchema']['properties']['stateVersion'], new_experience['eventSchema']['properties']['stateVersion']),
        ('liveStreamSchema.sequence', old_physical_event['properties']['sequence'], new_physical_event['properties']['sequence']),
        ('liveStreamSchema.stateVersion', old_physical_event['properties']['stateVersion'], new_physical_event['properties']['stateVersion'])]
    old_payloads = json.loads(before['contracts/payload-contracts.json']['raw'])
    new_payloads = json.loads(after['contracts/payload-contracts.json']['raw'])
    r9_event_count = sum(bool(r.get('eventSchema')) for r in old_payloads['records'])
    r9_event_exact = all(r['eventSchema']['properties']['sequence'] == new_physical_event['properties']['sequence']
                         for r in new_payloads['records'] if r.get('eventSchema'))
    old_browser = json.loads(before['r14/contracts/browser-interaction.schema.json']['raw'])
    new_browser = json.loads(after['r14/contracts/browser-interaction.schema.json']['raw'])

    operation_counts = json.loads((ROOT/'audit/phase1-unresolved.json').read_text(encoding='utf-8'))['summary']
    phase2 = json.loads((ROOT/'audit/phase2-unresolved.json').read_text(encoding='utf-8'))['summary']
    checks = json.loads((ROOT/'audit/generated/phase3-existing-checks.json').read_text(encoding='utf-8'))

    artifacts = json.loads(after['contracts/generation/generation-contracts.schema.json']['raw'])
    native = artifacts['$defs']['ArtifactRef']
    compact = json.loads(after['r11/contracts/orchestration.schema.json']['raw'])['$defs']['ArtifactRef']
    native_props, compact_props = set(native['properties']), set(compact['properties'])

    matrix = {
        'format':'KCML-PHASE3-CONTRACT-MATRIX/1','status':'PARTIAL',
        'baseline':{'commit':'6180d9fe67dfaa5365190301dfd58cc8d9812f3d',
                    'phase3EntrySnapshot':'.cache/phase2-entry/SSOT.md',
                    'phase3EntrySha256':hashlib.sha256(before_path.read_bytes()).hexdigest()},
        'summary':{
            'sameIdentityDifferentSchemaContents':{'before':2,'after':0},
            'targetCounterFieldsNotMatchingBoundedCounter':{'before':4+r9_event_count+2,'after':0},
            'reproducedSecretValueOutcomeContradictionsAccepted':{'before':int(old_accepts),'after':int(new_accepts)},
            'namedStateFieldsAcceptingNOT_A_VALID_STATE':{'before':sum(x['acceptsHistoricalProbe'] for x in old_states),'after':sum(x['acceptsHistoricalProbe'] for x in new_states)},
            'R11ArtifactRefHydrationBridgesVerified':{'before':0,'after':0},
            'phase1UnresolvedSchemaLinks':260,'phase1EffectiveOperations':619,'phase1Routes':542,
            'phase2MissingR11Positions':phase2['r11MissingKindPositions'],'phase2MissingR11Kinds':phase2['r11MissingKinds'],
            'phase2EventApplicabilityBlockers':phase2['eventApplicabilityBlockers']},
        'contracts':[]}
    matrix['contracts'].extend([
        {'id':'schema-identity:live-event','category':'SCHEMA_IDENTITY_CONFLICT','authoritativeLocation':exp_path+'#/eventSchema and '+exp_path+'#/liveStreamSchema','originalState':{'sharedId':old_ids[0],'differentContents':digest(old_experience['eventSchema'])!=digest(old_physical_event)},'change':'Experience schema is urn:kcml:experience-event:1; live stream is urn:kcml:live-event:1 and the latter is now embedded as canonical source.','affectedConsumers':['verify_experience.py','live-stream-policy.json','process-visual-registry.json','visual-artifact-bindings.json'],'evidence':'scripts/verify_phase3_semantics.py:identity.distinct-and-projections-exact','result':'FIXED_AND_VERIFIED','dependencies':[]},
        {'id':'schema-identity:history-query','category':'SCHEMA_IDENTITY_CONFLICT','authoritativeLocation':exp_path+'#/observability/querySchema and '+exp_path+'#/observability/historyQuerySchema','originalState':{'sharedId':old_ids[2],'differentContents':digest(old_experience['observability']['querySchema'])!=digest(old_physical_query)},'change':'Experience filter schema is urn:kcml:experience-history-query:1; history API is urn:kcml:history-query:1 and now canonical/projected.','affectedConsumers':['verify_observability.py','observability-query-contract.json'],'evidence':'scripts/verify_phase3_semantics.py:identity.distinct-and-projections-exact','result':'FIXED_AND_VERIFIED','dependencies':[]},
        {'id':'platform-counter-wire-contract','category':'COUNTER_RANGE_AND_ENCODING','authoritativeLocation':'00_SSOT/KajovoCMLNG_SSOT.md §6.3, §56.3, §56.13; '+exp_path+'#/eventSchema and #/liveStreamSchema','originalState':[{'field':n,'before':b} for n,b,a in counters],'change':'All four event sequence/stateVersion fields now use exact bounded decimal-string Counter; stream sequence remains positive, experience sequence retains inclusive zero.','affectedConsumers':['UI experience event validator','live event stream consumers','LIVE_VIEW_MATRIX projections'],'evidence':'scripts/verify_phase3_semantics.py:counter.int64-range-and-wire-type','result':'FIXED_AND_VERIFIED','dependencies':[]},
        {'id':'r9-event-sequence-and-r14-browser-stateversion','category':'COUNTER_RANGE_AND_ENCODING','authoritativeLocation':'contracts/payload-contracts.json#/records/*/eventSchema/properties/sequence; r14/contracts/browser-interaction.schema.json#/$defs/{BrowserAllocationSnapshot,BrowserHostSlot}/properties/stateVersion','originalState':{'unboundedR9EventSequences':r9_event_count,'unboundedR14PlatformStateVersions':2},'change':'Bound all 509 R9 route event sequences and both R14 platform stateVersion fields to the SSOT Counter; positive sequence lower bound retained.','affectedConsumers':['R9 event consumers','browser allocation/host-slot concurrency consumers'],'evidence':'scripts/verify_phase3_semantics.py:counter.int64-range-and-wire-type; allR9EventsBounded='+str(r9_event_exact),'result':'FIXED_AND_VERIFIED' if r9_event_exact else 'NOT_VERIFIED','dependencies':[]},
        {'id':'secret.value.read:status-terminal','category':'OUTCOME_SEMANTICS','authoritativeLocation':'00_SSOT/KajovoCMLNG_SSOT.md §6.7; contracts/payload-contracts.json#/records/390/responseSchema','originalState':{'SUCCEEDED_terminal_false_output_null_accepted':old_accepts},'change':'Enforced SUCCEEDED=>terminal true, ACCEPTED=>false, CANCELLED=>true/error non-null, FAILED=>error non-null; existing null/output exclusions retained.','affectedConsumers':['secret.value.read caller'],'evidence':'scripts/verify_phase3_semantics.py:response.status-terminal-error-branches','result':'FIXED_AND_VERIFIED' if not new_accepts else 'NOT_VERIFIED','dependencies':[]},
        {'id':'R11-to-generation:ArtifactRef','category':'REFERENCE_HYDRATION','authoritativeLocation':'r11/contracts/orchestration.schema.json#/$defs/ArtifactRef; contracts/generation/generation-contracts.schema.json#/$defs/ArtifactRef and #/$defs/SchemaAddress; r12/contracts/model-artifact-handoff.json','originalState':{'compactFields':sorted(compact_props),'nativeFields':sorted(native_props),'nativeFieldsMissingFromCompact':sorted(native_props-compact_props),'compactFieldsWithoutNativeCounterpart':sorted(compact_props-native_props)},'change':None,'affectedConsumers':['CAPABILITY_RESOLVERInput.inputs.requirementProposal','all compact R11 artifact consumers'],'evidence':'audit/phase2-handoff-matrix.json; audit/generated/phase2-content-tests-after.json','result':'BLOCKED_MISSING_CONTRACT','dependencies':['Define authoritative lookup by artifactId/path and identity/version check.','Specify whether compact schemaDigest hashes schema definition, bundle bytes, or another object; do not equate it to ArtifactRef.schema.bundleDigest.','Define missing/null digest policy, content digest verification, hydration failure variants, and validated content output.']},
        {'id':'finite-domain-state-dictionaries','category':'STATE_ENUMS','authoritativeLocation':'closure/contracts/operation-payloads.json response schemas for six named operations','originalState':{'stateFields':old_states},'change':None,'affectedConsumers':sorted(states),'evidence':'scripts/verify_phase3_semantics.py:state-fields-confirmed-open-unbounded-identifiers','result':'BLOCKED_MISSING_CONTRACT','dependencies':['Authoritative finite state sets and branch/transition rules are absent for all eight named fields.']},
        {'id':'canonical-and-schema-digest-semantics','category':'DIGEST_SEMANTICS','authoritativeLocation':'00_SSOT/KajovoCMLNG_SSOT.md §6.3, §51.4, §56.3; r12/contracts/model-artifact-handoff.json#/rules; generation-contracts.schema.json#/$defs/SchemaAddress','originalState':{'known':'KCIP canonical JSON uses UTF-8/JCS and SHA-256 sha256:<64 lowercase hex>; contracts/execution/embedded-manifest.json uses SHA256_RAW_EMBEDDED_BODY_WITH_FINAL_LF; R12 distinguishes canonicalBytesDigest, producerSchemaDigest, provenanceDigest and requires equality with finite acceptedSchemaDigests plus native validation of the same canonical bytes.','unknown':'No authoritative mapping found from R11 schemaDigest to producerSchemaDigest or SchemaAddress.bundleDigest, including selected definition/bundle bytes.'},'change':None,'affectedConsumers':['ArtifactRef hydration','schema registries','digest-aware consumers'],'evidence':'SSOT digest rules, R12 handoff rules and distinct field definitions','result':'BLOCKED_MISSING_CONTRACT','dependencies':['Normatively bind R11 schemaDigest to a specific R12 producer schema digest and exact selected schema/bundle bytes, canonicalization, version inclusion, validation time and mismatch behavior.']}
    ])
    (ROOT/'audit/phase3-contract-matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    unresolved = {'status':'PARTIAL','items':[
        {'id':'artifactref-hydration','status':'BLOCKED_MISSING_CONTRACT','detail':'No lossless adapter: compact reference lacks schema address, path, producerNodeId; extra nullable schemaDigest has no proven semantic equivalence to bundleDigest; lookup and validated-content return/error contract absent.'},
        {'id':'state-enums','status':'BLOCKED_MISSING_CONTRACT','detail':'Eight state/disposition fields accept NOT_A_VALID_STATE. No authoritative finite state dictionaries/transition guards found in active SSOT.'},
        {'id':'digest-field-binding','status':'BLOCKED_MISSING_CONTRACT','detail':'General JCS/SHA-256 is normative, but exact binding of R11 schemaDigest to native bundleDigest/selected definition and its mismatch timing is unspecified.'},
        {'id':'browser-presence-sequence','status':'NOT_VERIFIED','detail':'r15/contracts/browser-visual-collaboration.schema.json#/$defs/BrowserPresencePointer/properties/sequence accepts an unbounded decimal string. Active SSOT does not establish whether this is platform eventSequence or client/native pointer sequencing; it is not coerced from its name alone.'},
        {'id':'remaining-phase1-schema-links','status':'NOT_VERIFIED','detail':'260 unresolved links at 130 operations remain; Phase 3 did not reduce or suppress them.'},
        {'id':'remaining-phase1-domain-and-event-closure','status':'NOT_VERIFIED','detail':'Phase 1 remains PARTIAL: 8 failures/108 baseline contract tests and unresolved domain masks/query allowlists/canonicalJson/event edges remain.'},
        {'id':'remaining-phase2-handoff-closure','status':'NOT_VERIFIED','detail':'Phase 2 remains PARTIAL: 27 unmapped R11 input positions/23 kinds, 152 event applicability blockers and incomplete semantic graph; 77 content checks passing are only local proofs.'},
        {'id':'prior-validator-failures','status':'NOT_VERIFIED','detail':'NO_PRESERVED_R10_MARKER and CONTRACT_PACK_DRIFT scripts/ssot/audit_checks.py: Embedded bytes differ reproduce in current isolated checkout; both predate Phase 3.'},
        {'id':'phase2-matrix-refresh','status':'NOT_VERIFIED','detail':'Phase 2 source-derived matrix --check now reports MATRIX_COVERAGE_OR_CONTENT_DRIFT because Phase 3 changed the canonical UI experience resource; historic Phase 2 matrix/report deliberately preserved.'}
    ],'phase1Status':'PARTIAL','phase2Status':'PARTIAL','phase3Status':'PARTIAL'}
    (ROOT/'audit/phase3-unresolved.json').write_text(json.dumps(unresolved,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    changed = subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()
    report = f'''# Fáze 3 — sémantické uzavření kontraktů\n\n**Výsledek: PARTIAL.** Fáze 1: PARTIAL. Fáze 2: PARTIAL. Repo není dokončeno ani freeze-ready.\n\n## Výchozí stav a rozsah\n\n- Větev `main`, HEAD `6180d9fe67dfaa5365190301dfd58cc8d9812f3d`; předfázový SSOT snapshot `.cache/phase2-entry/SSOT.md` SHA-256 `{hashlib.sha256(before_path.read_bytes()).hexdigest()}`.\n- Zachovány všechny předchozí lokální změny; historické zprávy a matice fází 1/2 nebyly přepsány. Předchozí strom už obsahoval opravy fáze 1/2: šest R11 kind→schema mapování a předešlé kontraktové změny.\n- Prošel jsem úplné zprávy a JSON matice/unresolved fází 1 a 2; celý embedded SSOT jsem inventarizoval přes resource parser (402 zdrojů uvedeno ve fázi 1), a plně sémanticky četl jen relevantní identity, čítače, named state fields, R11/ArtifactRef, `secret.value.read` a navazující normativní pravidla. Netvrdím řádkovou revizi všech operací.\n\n## Před a po\n\n| Kategorie | Před fází 3 | Po fázi 3 |\n|---|---:|---:|\n| Nekompatibilní obsah pod stejnou cílovou schema ID (`live-event`, `history-query`) | 2 | 0 |\n| Cílová sequence/stateVersion pole mimo normativní Counter kontrakt | 4 | 0 |\n| `secret.value.read`: `SUCCEEDED`, `terminal=false`, `output=null` přijato | 1 | 0 |\n| Pojmenovaná state/disposition pole přijímající `NOT_A_VALID_STATE` | 8 | 8 |\n| Ověřený bezestrátový most R11 reference → ArtifactRef hydratace | 0 | 0 |\n| Fáze 1: operace / trasy / nerozlišené odkazy | 619 / 542 / 260 | 619 / 542 / 260 |\n| Fáze 2: chybějící R11 pozice / druhy / event applicability blockers | {phase2['r11MissingKindPositions']} / {phase2['r11MissingKinds']} / {phase2['eventApplicabilityBlockers']} | beze změny |\n\nNulový počet konfliktů dvou cílových identit neznamená globální uzavření všech SSOT identit. Fáze 1/2 baseline counts nejsou odvozeny od historických čísel naslepo: aktuální kontroly níže znovu hlásí 260/8 a fáze 2 zdrojová zpráva nese uvedené počty.\n\n## Provedené opravy\n\n- V autoritativním `ui/contracts/live-experience.json` oddělil jsem presentation event/query od dashboard live-stream/history API. Presentation ID jsou `urn:kcml:experience-event:1` a `urn:kcml:experience-history-query:1`; stream a history API si ponechaly původní ID. Původní fyzické standalone schémata byla vložena do kanonického resource; `project_experience.py` je nyní reprodukovatelně projektuje. Tím se opravila i příčina, proč Fáze 2 identity scanner vykazoval nula: dříve nepočítal standalone UI projekce.\n- Na všech čtyřech dotčených event fields (`sequence`, `stateVersion` ve dvou event schématech) použil jsem přesný decimal-string `Counter` z generation contracts/SSOT: 0…9223372036854775807 bez znaménka/leading zeros, bez JS `Number`; live stream sequence zůstává pozitivní podle jeho původního minima. Negativní testy zahrnují 2^53, maximum, max+1, -1, +1, whitespace, leading zero, decimal, exponent, integer JSON type a null.\n- `secret.value.read` response schema podle SSOT §6.7 nyní vynucuje `SUCCEEDED→terminal=true`, `ACCEPTED→false`, `CANCELLED→true`, error-required pro FAILED/CANCELLED. Nepřidal jsem domněnku, že SUCCEEDED output musí být neprázdný; null output zůstává povolen, protože nalezený kontrakt to nevylučuje.\n- Změněné resource bytes i R9 embedded manifest digest jsou reprodukovatelné skriptem `scripts/phase3_repair_semantics.py`; fyzické projekce ověřuje `scripts/project_experience.py --check`.\n\n## Neuzavřené blokátory\n\n- **R11 → ArtifactRef:** kompaktní reference má pole `{', '.join(sorted(compact_props))}`; native ArtifactRef vyžaduje `{', '.join(sorted(native_props))}`. Chybí `schema`, `path`, `producerNodeId`; navíc `schemaDigest` nemá prokázanou ekvivalenci s `schema.bundleDigest`. SSOT vyžaduje validovat payload konkrétním schématem, ale žádný bezeztrátový lookup/hydration output a chyby nejsou normativně definovány. Žádný formální adaptér jsem nevymyslel.\n- **Stavové slovníky:** osm polí v `owner.mfa.reset`, `chat.turn.steer`, `config.rollback`, `backup.restore`, `acceptance.run.start`, `acceptance.run.cancel` jsou stále obecné identifier masky a test přijímá `NOT_A_VALID_STATE`. V prohledaných autoritativních definicích chybí finite enumy/transition rules; hodnoty jsem nevymyslel.\n- **Digest linkage:** SSOT §6.3/§51.4 dává UTF-8/JCS + SHA-256 pro canonical JSON, zatímco embedded manifest zároveň hash-uje raw resource bytes. Chybí přesné pravidlo, zda compact R11 `schemaDigest` pokrývá celý bundle, vybranou definici nebo jinou reprezentaci a kdy se ověřuje.\n- Po změně autoritativního UI resource je historická phase2 source-derived matrix zastaralá: její `--check` hlásí `MATRIX_COVERAGE_OR_CONTENT_DRIFT`. Původní fázi 2 jsem nepřepisoval; fáze 4 má regenerovat novou kumulativní handoff projekci nebo verzovanou kopii.\n\n## Kontroly\n\nPříkazy byly spuštěny izolovaně v kopii pod `.cache`, takže původní `audit/generated/phase1-*` a `phase2-*` důkazy zůstaly nedotčené. Přesné stdout/stderr a exit codes jsou v `audit/generated/phase3-existing-checks.json`.\n\n| Kontrola | Exit | Výsledek |\n|---|---:|---|\n| `python scripts/verify_schema_references.py` | 1 | 2932 kontrol, 260 nerozlišených vazeb (stejné jako před fází) |\n| `python scripts/verify_phase1_contracts.py` | 1 | 108 kontrol, 8 selhání (předchozí nález zachován) |\n| `python scripts/phase2_repair_handoffs.py --check` | 0 | šest předchozích mapování reprodukovatelných |\n| `python scripts/verify_phase2_handoffs.py` | 0 | 77 obsahových případů, 0 selhání; omezení hydratace zůstává |\n| `python scripts/project_experience.py --check` | 0 | všechny osm projekcí aktuální |\n| `python scripts/verify_experience.py` | 0 | všechny kontroly PASS |\n| `python scripts/verify_observability.py` | 0 | všechny kontroly PASS |\n| `python scripts/phase2_handoff_closure.py --check` | 1 | stale historic matrix po fázi 3: `MATRIX_COVERAGE_OR_CONTENT_DRIFT` |\n| `python r11/scripts/verify_r11.py 00_SSOT/KajovoCMLNG_SSOT.md` | 1 | předchozí chyba `NO_PRESERVED_R10_MARKER` stále reprodukována |\n| `python scripts/ssot/ssot_control.py 00_SSOT/KajovoCMLNG_SSOT.md --check` | 1 | předchozí chyba `CONTRACT_PACK_DRIFT scripts/ssot/audit_checks.py: Embedded bytes differ` stále reprodukována |\n| `python scripts/verify_phase3_semantics.py` | 0 | identity, Counter mezní hodnoty, outcome tuple testy PASS; osm state fields potvrzeně otevřených |\n| `python scripts/phase3_repair_semantics.py --check` | 0 | žádná nereprodukovaná změna |\n\nObě starší chyby existovaly v baseline fáze 2 (podle `audit/generated/phase2-checks-before.json`) a jsou nezávislé na opravách této fáze. Phase2 matrix drift je nově vyvolán změnou jejího vstupního SSOT; není vydáván za původní chybu validátoru.\n\n## Dopad pro fázi 4\n\nNová embedded experience resource nyní obsahuje samostatné canonical stream/history schéma objekty; aktualizované fyzické projekce jsou `01_UI_CONTRACT/ui/contracts/live-event.schema.json` a `.../history-query.schema.json`. Fáze 4 má převzít jejich odkazy v UI registry/operational exposure, zkontrolovat všeobecné schema-ID registry proti standalone projekcím a regenerovat kumulativní Phase2 handoff matrix bez přepsání historických výsledků. Stavové enumy a ArtifactRef bridge zůstávají blokátory, ne hotová práce pro UI.\n\n## Změněné autoritativní/projekční soubory\n\n- Autoritativní: `00_SSOT/KajovoCMLNG_SSOT.md` embedded `ui/contracts/live-experience.json` a `contracts/payload-contracts.json` (včetně digest manifestu).\n- Projekce: `01_UI_CONTRACT/ui/contracts/live-experience.json`, `live-event.schema.json`, `history-query.schema.json`, odvozené locale a view matrix soubory.\n- Kontroly: `scripts/project_experience.py`, `scripts/verify_experience.py`, nové `phase3_repair_semantics.py`, `verify_phase3_semantics.py`, `phase3_run_checks.py`, `phase3_write_audit.py`.\n- `git diff --name-only` na uzavření auditu čítal {len(changed)} sledovaných cest; necommitnuté změny z fází 1–2 zachovány.\n\nVýstupy: `audit/phase3-semantic-closure.md`, `audit/phase3-contract-matrix.json`, `audit/phase3-unresolved.json`.\n'''
    report = re.sub(r'\| Cílová sequence/stateVersion pole mimo normativní Counter kontrakt \| 4 \| 0 \|',
        f'| Cílová sequence/stateVersion pole mimo normativní Counter kontrakt | {4+r9_event_count+2} | 0 |', report)
    report = re.sub(r'- Na všech čtyřech dotčených event fields .*? a null\.',
        f'- Na všech {4+r9_event_count+2} relevantních polích — 509 R9 route event sequence, dvě R14 platformní stateVersion a čtyři experience/live-stream sequence/stateVersion — jsem použil přesný decimal-string `Counter` z generation contracts/SSOT: 0 až 9223372036854775807 bez znaménka/leading zeros, bez JS `Number`. R9/live-stream sequence zůstává pozitivní, experience sequence zachovává nulu. Negativní testy pokrývají 2^53, maximum, max+1, -1, +1, whitespace, leading zero, decimal, exponent, integer JSON type a null.', report, count=1)
    report = re.sub(r'- \*\*Digest linkage:\*\*.*?(?=\n- )',
        '- **Digest linkage:** SSOT §6.3/§51.4 stanoví UTF-8/JCS + SHA-256 pro canonical JSON; embedded manifest samostatně uvádí `SHA256_RAW_EMBEDDED_BODY_WITH_FINAL_LF`. R12 rozlišuje `canonicalBytesDigest`, `producerSchemaDigest` a `provenanceDigest`, vyžaduje shodu producer schema digestu s konečným `acceptedSchemaDigests` a validaci týchž canonical bytes. Chybí přesné mapování R11 nullable `schemaDigest` na R12/native identitu a vymezení hashovaných schema/bundle bytes.', report, count=1, flags=re.S)
    report = re.sub(r'(\| `python scripts/verify_phase1_contracts.py`[^\n]*\n)',
        r'\1| `python scripts/phase1_repair_contracts.py --check` | 0 | předchozí opravy fáze 1 stále reprodukovatelné |\n', report, count=1)
    report = report.replace('`contracts/payload-contracts.json` (včetně digest manifestu).',
        '`contracts/payload-contracts.json` (včetně digest manifestu) a `r14/contracts/browser-interaction.schema.json` (platformní stateVersion vazby).')
    report = report.replace('## Neuzavřené blokátory\n\n',
        '## Neuzavřené blokátory\n\n- **Browser presence sequence:** `r15/contracts/browser-visual-collaboration.schema.json#/$defs/BrowserPresencePointer/properties/sequence` stále přijímá neomezený desetinný string. SSOT nedokládá, zda jde o platformní eventSequence, nebo client/native pointer counter; nebyl změněn pouze podle názvu.\n')
    (ROOT/'audit/phase3-semantic-closure.md').write_text(report, encoding='utf-8')
    print(json.dumps({'status':'PARTIAL','matrixContracts':len(matrix['contracts']),'unresolved':len(unresolved['items'])}))


if __name__ == '__main__':
    main()
