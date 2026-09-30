"""Build bounded integration materials without changing shared/canonical files."""
import ast,hashlib,json,re,sys
from pathlib import Path
from generation_admission_reference import *
OUT=Path(__file__).resolve().parent
path=OUT/'generation_admission_reference.py'
node=ast.parse(path.read_text());codes=set();conditions={};parents={}
for n in ast.walk(node):
 for child in ast.iter_child_nodes(n):parents[child]=n
for n in ast.walk(node):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='fail' and n.args and isinstance(n.args[0],ast.Constant):
  codes.add(n.args[0].value)
  ancestor=n
  while ancestor in parents and not isinstance(ancestor,ast.If):ancestor=parents[ancestor]
  condition=ast.unparse(ancestor.test) if isinstance(ancestor,ast.If) else 'Explicit mandatory schema or format validation raises this exact typed diagnostic'
  conditions.setdefault(n.args[0].value,[]).append({'condition':condition,'implementationLine':n.lineno})
for n in ast.walk(node):
 if isinstance(n,ast.Dict):
  for key,val in zip(n.keys,n.values):
   if isinstance(key,ast.Constant) and isinstance(val,ast.Constant) and isinstance(val.value,str) and val.value.startswith('GENERATION_BASIS_'):codes.add(val.value)
codes.update(['GENERATION_BASIS_SCHEMA_INVALID','GENERATION_REQUEST_INVALID','MONITORING_OBSERVATION_INVALID'])
policy_codes={'GENERATION_APPROVED_AUTHORITY_ARTIFACT_KIND_UNRESOLVED','GENERATION_ADMISSION_CONTRACT_UNRESOLVED','GENERATION_ADMISSION_AUTHORITY_MAP_UNRESOLVED','GENERATION_SCHEMA_BUNDLE_INVALID','GENERATION_SCHEMA_BUNDLE_DIGEST_MISMATCH','GENERATION_SCHEMA_BUNDLE_ID_MISSING','GENERATION_SCHEMA_BUNDLE_ID_AMBIGUOUS','GENERATION_BASIS_SCHEMA_REFERENCE_UNRESOLVED','GENERATION_BASIS_SCHEMA_ADDRESS_INVALID','GENERATION_BASIS_SCHEMA_BUNDLE_UNAVAILABLE','GENERATION_BASIS_SCHEMA_ID_MISMATCH','GENERATION_BASIS_DEFINITION_UNRESOLVED','GENERATION_BASIS_BYTES_UNAVAILABLE','GENERATION_OWNER_APPROVAL_UNAVAILABLE','GENERATION_RETRY_TERMINAL_RESULT_UNAVAILABLE','MONITORING_OBSERVATION_SCHEMA_UNAVAILABLE','MONITORING_OBSERVATION_SCHEMA_INVALID','MONITORING_OBSERVATION_SCHEMA_POINTER_UNRESOLVED'}
input_codes={'GENERATION_REQUEST_INVALID','GENERATION_KIND_OWN_BASIS_NOT_APPLICABLE'}
decoder_origin={
 'GENERATION_BASIS_UTF8_INVALID':'create_operation_contracts.strict_json raw.decode(utf8) raised UnicodeDecodeError; source_json wraps exact INVALID_UTF8 and retains RFC6901 pointer',
 'GENERATION_BASIS_UNICODE_INVALID':'strict_json unicode_check failed UTF8 encoding of an unpaired surrogate in a decoded key/value; source_json wraps exact INVALID_UNICODE',
 'GENERATION_BASIS_JSON_INVALID':'strict_json json.loads/convert raised syntax ValueError, TypeError or RecursionError; source_json wraps exact INVALID_JSON; not duplicate/nonfinite/UTF8 errors',
 'GENERATION_BASIS_NONFINITE_JSON_NUMBER':'strict_json convert encountered float for which math.isfinite is false, including JSON numeric overflow; wraps exact NONFINITE_JSON_NUMBER at original absolute pointer',
 'GENERATION_BASIS_DUPLICATE_JSON_KEY':'strict_json ObjectPairs conversion encountered a key already present in that exact object; wraps exact DUPLICATE_JSON_KEY at original escaped RFC6901 key pointer',
 'GENERATION_BASIS_SCHEMA_INVALID':'Repository.hydrate decodes actual persisted bytes and validates exact frozen SchemaAddress.schemaId/definition from recomputed bundleDigest; iter_errors returns at least one real native violation and preserves its absolute RFC6901 field path',
 'GENERATION_REQUEST_INVALID':'select_generation_basis validates actual HTTP/native body against closed GenerationJobCreateBody plus discriminated generationBasis requiredness before record reads; actual schema iter_errors is nonempty at preserved field path',
 'MONITORING_OBSERVATION_INVALID':'Repository.observation loads exact SchemaArtifact.bundle bytes, validates full meta-schema/schemaId/rootPointer/nativeSchemaDigest, then selected compiled schema rejects actual EvidenceRecord.observations at /observations plus error.absolute_path',
 'GENERATION_ADMISSION_CONTRACT_UNRESOLVED':'Repository.from_current_ssot load_resource raises ValueError for missing/ambiguous mandatory native generation/admission/artifact-map/domain-map canonical resource; no proposal fallback',
 'GENERATION_SCHEMA_BUNDLE_INVALID':'checked_bundle decoded actual registered schema bytes and Draft202012Validator.check_schema raised SchemaError under official installed 2020-12 meta-schema',
 'MONITORING_OBSERVATION_SCHEMA_INVALID':'Repository.observation Draft202012Validator.check_schema raised SchemaError for actual observation schema bundle or selected definition; not an unrelated parser exception'}
for code,text in decoder_origin.items():
 if code in codes:
  conditions[code]=[{'condition':text,'implementationFunction':'source_json/validate/checked_bundle/Repository.from_current_ssot/Repository.observation','implementationFile':str(path.relative_to(path.parents[4]))}]
rows=[]
for code in sorted(codes):
 stable='CREATE_POLICY_UNRESOLVED' if code in policy_codes else 'CREATE_INPUT_INVALID' if code in input_codes else 'CREATE_REFERENCE_INVALID'
 rows.append({'diagnostic':code,'stableCode':stable,'httpStatus':503 if code in policy_codes else 400 if code in input_codes else 422,
 'predicate':conditions[code],
 'pointerRule':'JSON/RFC6901 source field path when available; empty pointer denotes repository cross-record invariant, never sensitive field value',
 'sources':['SSOT §12.41','SSOT §12.49','SSOT §25.11','SSOT §49.4','SSOT §49.15','PROPOSED SSOT §12.51']})
(OUT/'diagnostics-proposed.json').write_text(json.dumps({'format':'KCML-GENERATION-ADMISSION-DIAGNOSTICS/1','diagnostics':rows,'unknownDiagnostic':'HTTP_FAILURE_PROJECTION_UNRESOLVED; BLOCKED; no prefix fallback'},indent=2)+'\n')
fields={
 'basisKind':('Explicit own-kind selector discriminator; never format/kind sniffing','SSOT §12.41; technical spelling §12.18'),
 'snapshotId':('Immutable server-owned target identity snapshot PK','SSOT §25.11 generation_execution_authority target identities snapshot; §49.4'),
 'expectedDigest':('Caller precondition over selected actual immutable bytes; server recomputes SHA-256','SSOT §25.11 immutable source/spec/result digests; §49.4; §12.49'),
 'phaseRunId':('Select exact terminal FAILED technical phase attempt, not whole-job state','SSOT §25.11 generation_phase_run; §49.15'),
 'planId':('Select immutable source plan; failed node subset must belong to this exact plan and phase','contracts/generation/generation-contracts.schema.json#/$defs/GenerationPlan/properties/planId; SSOT §25.11 generation_plan'),
 'expectedPlanDigest':('Caller digest precondition; server checks plan/run/spec cross-binding','SSOT §25.11 generation_plan canonical DAG JSON and digest; §49.15'),
 'approvedRevisionId':('Exact source immutable approved specification PK','SSOT §25.11 generation_spec_revision; §12.21-12.22'),
 'expectedSpecificationDigest':('Exact approved functional specification bytes SHA-256; no current moving reference','SSOT §25.11 generation_execution_authority source revision/digest; §12.22'),
 'authorityId':('Existing approved authority identity only; caller cannot create authority','SSOT §25.11 generation_execution_authority; §12.22'),
 'expectedAuthorityDigest':('Frozen source authority snapshot bytes precondition; verify actual native GenerationAuthority and OWNER approval receipt','SSOT §12.22; §25.11 generation_execution_authority lineage digest/frozenAt'),
 'monitoringArtifactId':('Exact committed MONITORING_EVIDENCE artifact identity','contracts/generation/artifact-schema-map.json#/MONITORING_EVIDENCE; SSOT §12.41'),
 'expectedTargetDigest':('Digest of selected immutable current target identity/last-approved-lineage snapshot','SSOT §12.41 preserved identities; §12.22 target IDs snapshot; §51.12 atomic repository heads')}
field_rows=[]
for variant in selector_schema()['oneOf']:
 for key,value in variant['properties'].items():
  semantic,source=fields[key];field_rows.append({'variant':variant['properties']['basisKind']['const'],'field':key,'meaning':semantic,'schema':value,'required':True,'nullable':False,'origin':'CLIENT_SELECTOR_HINT_VALIDATED_AGAINST_SERVER_PERSISTENCE','authoritativeSource':source,'newTechnicalSpelling':True})
contract={'format':'KCML-GENERATION-ADMISSION-BASIS/1','inputCommit':'d362487999bd795d4723c2a930e93fc7aa8aa295',
 'ssotSha256':'22256baa17729b7577ca4e2498b74b7dfc2b3e6bab57f3b88c338a059557a0ee','status':'TECHNICAL_PROPOSAL_PENDING_COORDINATOR_INTEGRATION_AND_REVIEW',
 'normativeSectionReservation':'12.51','selectorSchema':selector_schema(),'requestSchema':request_schema(),'fields':field_rows,
 'sourceDefinitions':LOCAL_DEFINITIONS,
 'admissionByKind':{
 'UPDATE':{'phase':'DISCUSSING','admission':['Owned immutable existing target snapshot actual bytes/schema/id/digest; preserve component/runtime identities'],'execution':['Exact current approved OWNER specification','Compatibility and migration plan'],'activation':['Current dependency/fence snapshot and complete own validation gates'],'forbidden':['Changing component or runtime identity through update','Treating successful discussion admission as execution approval']},
 'RETRY':{'phase':'DISCUSSING','admission':['Exact owned approved specification and authority source bytes','Native authorityModel referenced record bytes equal frozen authority payload','Exact committed OWNER approval receipt','Exact FAILED technical phase-run and known terminal result bytes','Failed node set belongs to exact source plan and matching phase; no pending UNKNOWN side effects'],'execution':['Inherited technical authority commit','New attempt records under own phase sequence','Current dependency/fence/reconciliation guards'],'forbidden':['Retry successful/cancelled/nontechnical part','Changing approved functional authority','Inferring a source-job terminal requirement from phase terminality']},
 'REPAIR':{'phase':'DISCUSSING','admission':['Current target head selects exact immutable last-approved-lineage snapshot','Source approved spec/authority and actual referenced native authority bytes','Exact committed MONITORING_EVIDENCE artifact/publication/observation-schema bytes','Evidence subject binds target snapshot','Actual observations validate against explicitly frozen observation schema','Preserve existing component/runtime identities'],'execution':['Inherited technical authority commit','Technical-only repair plan against unchanged approved functional lineage','Current context/dependency/fence guards'],'activation':['Complete regression validation'],'forbidden':['Using arbitrary old approved lineage','Replacing full regression with monitoring schema validity','Changing requirements/external semantics/exact bindings/OWNER decisions']},
 'FOLLOW_UP':{'admission':['Existing approved rule unchanged','Actual initial request/specification revision/native artifact bytes validated under pinned complete schema bundle','Required final output has committed publication receipt'],'sourceJobTerminalityRequired':False,'authorityBeforeExecution':'New OWNER approval for functional branch'}},
 'freeze':{'fields':['Every consulted record identity/contentDigest/exact SchemaAddress','Every consumed schema bundle digest','Immutable lineage digest over complete consulted dependency closure'],
 'mutableInputsExcluded':['Source current job state','Source current specification pointer','Model validity/consistent/sufficient booleans'],
 'requiredAtomicContext':'Coordinator integrates actual authenticated OWNER repository transaction and locking per §49.4/§51.12; this fixture does not establish SQL authority'},
 'remaining':[{'id':'GEN-ADMISSION-NATIVE-GRAPH','kind':'PRE_GENERATION_TECHNICAL','source':'SSOT §12.20','admissionStage':'Not a prerequisite for UPDATE/FOLLOW_UP discussion admission. Source RETRY/REPAIR must already carry authentic immutable OWNER approval; execution must fully hydrate unchanged approved graph before planning/dispatch.',
 'scope':'Hydrate all ContractRecordRef graphs, requirement/acceptance coverage, conformance predicate implementations and their consumed bytes; schema validity of the frozen approved document alone does not prove these predicates'},
 {'id':'GEN-REPAIR-CONSUMER-PREDICATE','kind':'PRE_GENERATION_TECHNICAL','source':'SSOT §12.41; EvidenceRecord observationSchema; consumer monitoring profile','admissionStage':'Monitoring-source content shape and publication proven for discussion candidate; automatic eligible technical repair dispatch remains BLOCKED until its exact monitoring consumer predicate is hydrated/executed.',
 'scope':'Concrete target monitoring profile→observation schema→repair-policy implementation must establish repair eligibility, not merely syntax. Synthetic health-check schema is a fixture, not universal predicate'},
 {'id':'GEN-CREDENTIAL-SOURCE-POLICIES','kind':'PRE_GENERATION_TECHNICAL','source':'SSOT §8.4; §12.2; §12.47; §72.21','scope':'Optional ephemeral credential policy, Secret source exact use context, URL navigation and object target own state/load contracts are not fully closed by kind-selector work'},
 {'id':'GEN-ADMISSION-PG-CONTEXT','kind':'PRE_GENERATION_FIXTURE','source':'SSOT §49.4; §49.15; §51.12; §73.7','scope':'Roles/authenticated trusted context, exact root FK, locking/recovery heads, immutable constraints and SQL commit/replay under PostgreSQL required separately'},
 {'id':'GEN-ADMISSION-APP','kind':'IMPLEMENTATION_ACCEPTANCE','source':'Generated application acceptance scope','scope':'Future deployed runtime admission/consumer execution; not evaluated here'}],
 'proof':'audit/generated/resume-d362/admission/generation-admission-tests.json'}
(OUT/'generation-admission-contract-proposed.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'diagnostics':len(rows),'selectorFieldRows':len(field_rows)}))
