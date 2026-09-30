"""Isolated SQL source/design proof. Never executes PostgreSQL or mutates SSOT."""
import hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'scripts'))
import pglast
from ssot_sources import ROOT,SSOT,resources,resource_index
from verify_operation_sql_literals import literal_arguments,expressions
OUT=Path(__file__).resolve().parent
raw=SSOT.read_bytes();rs=resource_index(resources(raw.decode()));source_hash=hashlib.sha256(raw).hexdigest()
snapshot=json.loads((OUT/'source-snapshot.json').read_text())
if source_hash!=snapshot['sourceDocumentSha256']:raise RuntimeError('HISTORICAL_SOURCE_CHANGED: coordinator must revalidate findings against current resources before reuse')
HELPERS=['kcml_apply_exact_domain_plan_v1','kcml_assert_operation_descriptor_v1','kcml_assert_recovery_and_incarnation_v1','kcml_lock_exact_root_plan_v1']
wrappers=rs['database/operation-functions.sql']['raw'];calls=[literal_arguments(e) for e in expressions(wrappers)]
create_ops=['generation.job.create','secret.create']
by_helper={h:[] for h in HELPERS}
for name,args in calls:by_helper[name].append(args)
covered={args[0] for name,args in calls if name=='kcml_assert_operation_descriptor_v1'}
plans=[json.loads(args[0]) for name,args in calls if name=='kcml_apply_exact_domain_plan_v1']
all_sql={p:r for p,r in rs.items() if p.endswith('.sql')}
definitions={m[1] for p,r in all_sql.items() for m in re.finditer(r'(?i)CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(\w+)',r['raw'].decode())}
context_defs=[p for p,r in all_sql.items() if re.search(r'(?i)CREATE\s+TYPE\s+kcml_operation_context_v1\b',r['raw'].decode())]
root_ordinals=json.loads(rs['database/design/root-ordinals.json']['raw']);ordinal={r['rootTable']:r['ordinal'] for r in root_ordinals}
# These two physical constraints are explicitly required by51.12 and retain the
# already-authoritative logical-operation FK target. No table/type/runtime claims.
old=rs['database/explicit-entities.sql']['raw'].decode()
proposal=old.replace('logical_operation_id uuid NOT NULL REFERENCES domain_command(logical_operation_id) ON DELETE RESTRICT,',
 'logical_operation_id uuid NOT NULL UNIQUE REFERENCES domain_command(logical_operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,')
if proposal==old:raise ValueError('LOCATOR_DECLARATION_CHANGED')
(OUT/'explicit-entities-proposed.sql').write_text(proposal)
# Constraint proof inspects actual PostgreSQL AST, not string labels.
tree=json.loads(pglast.parser.parse_sql_json(proposal));oldtree=json.loads(pglast.parser.parse_sql_json(old))
create=[s['stmt']['CreateStmt'] for s in tree['stmts'] if 'CreateStmt' in s['stmt']]
loc=next(t for t in create if t['relation']['relname']=='idempotency_locator')
col=next(e['ColumnDef'] for e in loc['tableElts'] if 'ColumnDef' in e and e['ColumnDef']['colname']=='logical_operation_id')
constraints=[c['Constraint'] for c in col['constraints']]
unique=any(c['contype']=='CONSTR_UNIQUE' for c in constraints)
def deferred_fk(cs):
 fk_index=next((i for i,c in enumerate(cs) if c['contype']=='CONSTR_FOREIGN'),None)
 if fk_index is None:return False
 fk_constraint=cs[fk_index]
 attributes={c['contype'] for c in cs[fk_index+1:]}
 return bool(fk_constraint.get('deferrable') or 'CONSTR_ATTR_DEFERRABLE' in attributes) and bool(fk_constraint.get('initdeferred') or 'CONSTR_ATTR_DEFERRED' in attributes)
fk=next(c for c in constraints if c['contype']=='CONSTR_FOREIGN')
checks=[{'id':'proposal.postgresql17-parser-positive','status':'PASS'},
 {'id':'locator.logical-operation-unique','status':'PASS' if unique else 'FAIL'},
 {'id':'locator.logical-operation-deferred-fk','status':'PASS' if deferred_fk(constraints) else 'FAIL'},
 {'id':'locator.existing-fk-target-preserved','status':'PASS' if fk['pktable']['relname']=='domain_command' else 'FAIL'}]
# Each negative starts from parsed valid proposal and removes exactly the tested
# clause. PostgreSQL syntax remains valid; design AST must reject the omission.
for identity,mutated,predicate in [
 ('negative.missing-logical-operation-uniqueness',proposal.replace('logical_operation_id uuid NOT NULL UNIQUE REFERENCES','logical_operation_id uuid NOT NULL REFERENCES'),lambda cs:any(c['contype']=='CONSTR_UNIQUE' for c in cs)),
 ('negative.nondeferrable-logical-operation-fk',proposal.replace(' DEFERRABLE INITIALLY DEFERRED',''),deferred_fk)]:
 t=json.loads(pglast.parser.parse_sql_json(mutated));l=next(s['stmt']['CreateStmt'] for s in t['stmts'] if s['stmt'].get('CreateStmt',{}).get('relation',{}).get('relname')=='idempotency_locator')
 c=next(e['ColumnDef'] for e in l['tableElts'] if e.get('ColumnDef',{}).get('colname')=='logical_operation_id')
 checks.append({'id':identity,'positiveWitnessValid':True,'syntaxStillValid':True,'specificClauseRejected':not predicate([v['Constraint'] for v in c['constraints']]),'status':'PASS' if not predicate([v['Constraint'] for v in c['constraints']]) else 'FAIL'})
# Current locator scope must be compared to explicitly named final rules.
legacy_columns=[e['ColumnDef']['colname'] for e in loc['tableElts'] if 'ColumnDef' in e]
expected=['operation_family_id','caller_authority_kind','stable_caller_object_id','stable_business_target_key','client_key_digest','logical_operation_id']
missing_columns=[n for n in expected if n not in legacy_columns]
helper_contracts=[]
algorithms={
 'kcml_assert_operation_descriptor_v1':{'sources':['49.4','49.5','51.12'], 'requiredAlgorithm':['Authenticated server context only; caller cannot supply trusted authority or descriptor digest','Stable locator lookup before fresh admission','Replay selects the retained frozen operation/caller revision and execution descriptor, never recomputes it from the current registry','Fresh admission resolves effective operationId/revision/native descriptor digest and exact typed masks','Unknown/missing/conflicting descriptor means BLOCKED before domain mutation'], 'unbound':['kcml_operation_context_v1 exact physical type and trusted construction boundary','retained effective/frozen descriptor registry storage and access','wrapper-current descriptor digest versus retained replay descriptor reconciliation']},
 'kcml_assert_recovery_and_incarnation_v1':{'sources':['49.33','51.5','51.6','51.9'], 'requiredAlgorithm':['Lock platform/deployment/security heads in canonical order','Read current recovery/incarnation/deployment/fence from locked server rows','Fresh mutation requires READY and exact current incarnation/fence; re-evaluate after lock acquisition','Recheck every authoritative write using expected CAS/fence; nonmatching guards are conflict, not PASS','Terminal replay does not become fresh admission; authenticate result access and retained identity'], 'unbound':['exact platform/deployment/security-head physical tables and current field bindings','trusted context creation and lease/fence applicability per operation']},
 'kcml_lock_exact_root_plan_v1':{'sources':['51.5','51.6','51.12'], 'requiredAlgorithm':['Derive all actual parents from persisted relationships, never caller root declarations','Acquire class A advisory, B singleton, C locator/idempotency, D activation, E parent roots/children and audit head last','Order roots by native ordinal then uuid_send(id); multi-parent roots acquire all actual parents','CREATE absent new root uses stable parent/namespace guard plus first-create advisory, never just new random root UUID','Do not perform mutation inside a lock-only helper; eventual write keeps CAS and fence predicates'], 'unbound':['precise trusted physical root-resolution relation path for each262 wrapper operations','new-create namespace/first-create advisory key derivation','exact composite context and per-class lock object columns']},
 'kcml_apply_exact_domain_plan_v1':{'sources':['25.6','25.11','49.4','49.22.1','51.5','51.9','51.12','51.30','12.48','12.49'], 'requiredAlgorithm':['Select an explicit operation-specific persisted typed mutation plan, not a generic semantic-field JSON interpreter','Claim locator and idempotency record without replacing an existing request/outcome','After all locks, recompute guards from current rows and execute exactly the permitted atomic transition','Persist root/immutable request-or-secret-version/frozen basis/typed receipt/event/audit/outbox/canonical outcome together','Commit is sole linearization; publish response/SSE/outbox only from committed state','Rollback/failure/unknown and replay reconcile the same locator without second root/event','No network/provider/browser I/O inside SQL transaction'], 'unbound':['every semantic field to exact physical typed column mapping; currentfieldUpdatePlan is descriptive storage fallback','generation_job/secret_record/secret_version and domain command/event/outbox schemas','secret authenticated-encryption provider/type-specific validated payload handoff','typed response/event hydration joins and immutable lineage constraints']}}
for name in HELPERS:
 helper_contracts.append({'helper':name,'status':'BLOCKED','blockerKind':'TECHNICAL','callSites':len(by_helper[name]),'definitionPresent':name in definitions,**algorithms[name]})
completion=json.loads(rs['contracts/create-completion.json']['raw'])
create_plans=[]
for oid in create_ops:
 root='generation_job' if oid.startswith('generation') else 'secret_record'
 create_plans.append({'operationId':oid,'currentWrapperPresent':oid in covered,'root':root,'rootOrdinal':ordinal.get(root),
 'authoritativeSources':['contracts/create-completion.json#/operations/'+oid,'contracts/create-completion.json#/transactions','contracts/create-completion.json#/postconditions','25.11' if root=='generation_job' else '25.6','49.4','51.5','51.12'],
 'exactTransactionArtifacts':(['generation_job:DISCUSSING','immutable initial request+digest','generation_source references and actual-byte digests','FOLLOW_UP immutable frozen basis when explicitly selected'] if root=='generation_job' else ['secret_record unique stableName including soft-delete','secret_version CREATED with immutable ciphertext,nonce,algorithm,keyID,fingerprint,valueDigest','versionNumber allocated uniquely persecret','activeVersionId null; no implicit activation'])+['one server-created logical operation identity','stable locator and domain idempotency outcome','typed frozen completion receipt','one typed aggregate event and aggregate-localsequence','audit-chain append and publish-after-commit outbox'],
 'persistencePostconditions':completion['postconditions'],'status':'BLOCKED','reason':('Existing wrapper applies generic physical plan' if oid in covered else 'No operation-specific wrapper') + '; no explicit root/child physical materialization in effective direct SQL resources; exact format/own admission policies remain independent obligations'})
report={'format':'KCML-SQL-HELPER-REVIEW/1','sourceDocumentSha256':source_hash,'sourceCommit':'5334d8caa1b284cb1b4857f51aef2d431b571427',
 'sourceBindings':{p:rs[p]['sha256'] for p in ['database/operation-functions.sql','database/explicit-entities.sql','database/design/root-ordinals.json','contracts/create-completion.json']},
 'coverage':{'wrappers':len(covered),'helperCallSites':len(calls),'helperDefinitionsMissing':[h for h in HELPERS if h not in definitions],'contextDefinitions':context_defs,'createWrappersMissing':[o for o in create_ops if o not in covered],'genericPhysicalPlans':sum(any(f.get('storage')=='EXPLICIT_COLUMN_WHERE_SOURCE_OR_CONSTRAINT_NAMES_COLUMN_ELSE_ENTITY_CONTRACT_PAYLOAD_JSONB' for f in p.get('fieldUpdatePlan',[])) for p in plans)},
 'helpers':helper_contracts,'createTransactionPlans':create_plans,
 'locatorProposal':{'file':'explicit-entities-proposed.sql','repairScope':'UNIQUE logical_operation_id and deferred existing logical-operation FK; no claim to complete locator physical contract','authorities':['49.4','51.12'],'stillMissingFinalNamedColumns':missing_columns,'allOtherSourceBytesPreserved':proposal.replace('logical_operation_id uuid NOT NULL UNIQUE REFERENCES domain_command(logical_operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,','logical_operation_id uuid NOT NULL REFERENCES domain_command(logical_operation_id) ON DELETE RESTRICT,')==old},
 'gateClassification':{'A_MANDATORY_BEFORE_GENERATION':['Exact helper/context/physical relation contracts; typed per-operation plans, guards, lock order, complete persistence+event+hydration design','Materialize all explicitly mandatory constraints per51.12 beforeARCHITECTURE_READINESS'],'B_DESIGN_REFERENCE_PROOF':['PostgreSQL syntax AST checks over explicit proposals','Exact source/native-resource coverage, positive and specific negative clause checks; no DB/runtime inference'],'C_FUTURE_IMPLEMENTATION_ACCEPTANCE':['PostgreSQL18.6 executable migration and helper functions with actualroles/authconstruction, locks/deadlocks/races/rollback/outbox recovery tests','RealSecret encryption/storage/hydration/consumer runtime and idempotency replay underfaultinjection']},
 'ownerDecisions':[],'ownerDecisionLimitation':'The unavailable SQL/context/column bindings are technically specified design gaps, not demonstrated undecidable business questions. Independent Secret-format policy review remains outside this SQL scope.',
 'checks':checks,'failed':sum(r['status']!='PASS' for r in checks),'implementationProductionAcceptance':'NOT_EVALUATED','wholeCreateOperationsClosed':[]}
(OUT/'helper-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if SSOT.read_bytes()!=raw:raise RuntimeError('SOURCE_CHANGED_DURING_REVIEW')
print(json.dumps({'coverage':report['coverage'],'checks':len(checks),'failed':report['failed'],'locatorStillMissingFinalNamedColumns':missing_columns,'wholeCreateOperationsClosed':[]}))
