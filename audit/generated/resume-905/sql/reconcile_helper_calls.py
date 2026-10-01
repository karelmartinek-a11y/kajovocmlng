"""Current direct-SQL helper call inventory, not domain semantic acceptance."""
import sys,json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
from repair_operation_sql_literals import CALLS
from verify_operation_sql_literals import audit,literal_arguments,expressions
rs=resource_index();raw=rs['database/operation-functions.sql']['raw'];a=audit(raw)
assert a['status']=='PASS',a
calls=[dict(index=i,helper=n,arguments=args)for i,(n,args)in enumerate(a['calls'])]
wrappers=[]
assert len(calls)%4==0
for offset in range(0,len(calls),4):
 group=calls[offset:offset+4]
 descriptor=next(c for c in group if c['helper']=='kcml_assert_operation_descriptor_v1')
 plan=json.loads(next(c['arguments'][0]for c in group if c['helper']=='kcml_apply_exact_domain_plan_v1'))
 assert descriptor['arguments'][0]==plan['operationId']
 wrappers.append(dict(operationId=plan['operationId'],descriptorDigest=descriptor['arguments'][1],helperCalls=[c['helper']for c in group],genericPlan=plan))
defs={};types={}
for p,x in rs.items():
 if p.endswith('.sql'):
  for n in re.findall(r'(?i)CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(\w+)',x['raw'].decode()):defs.setdefault(n,[]).append(p)
  for n in re.findall(r'(?i)CREATE\s+TYPE\s+(\w+)',x['raw'].decode()):types.setdefault(n,[]).append(p)
text=SSOT.read_text()
authorities={}
for section in ['49.4','49.5','51.5','51.6','51.8','51.12']:
 m=re.search(r'^### '+re.escape(section)+r'\b.*?\n(?=### |## |<!-- KCML-|\Z)',text,re.M|re.S)
 if not m:raise ValueError('SOURCE_UNRESOLVED:'+section)
 authorities[section]=dict(heading=m[0].splitlines()[0],line=text[:m.start()].count('\n')+1,sha256=hashlib.sha256(m[0].encode()).hexdigest())
report=dict(sourceDocumentSha256=hashlib.sha256(SSOT.read_bytes()).hexdigest(),entryCommit='905555e47f3547516439a699e262df62cbbec229',resourceBindings={p:rs[p]['sha256']for p in ['database/operation-functions.sql','database/generation-create-foundations.sql','database/generation-create-authentication.sql','database/generation-create-preroot.sql','database/secret-profile-roots.sql']},coverage=dict(wrappers=len(wrappers),calls=len(calls),perHelper={h:sum(c['helper']==h for c in calls)for h in sorted(CALLS)},unresolvedDefinitions=sorted(CALLS-defs.keys()),genericContextTypePresent='kcml_operation_context_v1'in types,scopedGenerationContextPhysicallyPresent='CREATE TABLE generation_create_trusted_context'in rs['database/generation-create-foundations.sql']['raw'].decode(),secretCreateWrapperPresent=any(w['operationId']=='secret.create'for w in wrappers)),authorities=authorities,createWrappers=[w for w in wrappers if w['operationId']in ['generation.job.create','secret.create']],calls=calls,status='BLOCKED',specificRemaining=[dict(id='SQL-GENERATION-EXACT-DISPATCH',source=['49.4','49.5','51.12'],missing='Replace generation generic wrapper composite p_ctx with canonical scoped context constructor and explicit accepted request/basis/root writer. Existing CREATE-root descriptor does not itself encode or authenticate protected parent/target bytes.',verification='Canonical SQL dispatcher calls trusted acceptance, exact byte-hydrated admission, C0/C1 locator then source/target E roots, complete guarded create persistence under same transaction; stale/mismatched request rejects before root.'),dict(id='SQL-GENERATION-RETAINED-LOCATOR-HANDOFF',source=['49.4','51.6','51.12'],candidate='generation-locator-lock-proposed.sql',proof='locator-lock-postgres-proof.json',scope='Bounded candidate trusted-context -> retained C0 locator -> C1 original scope only; no fresh claim/source-root or whole helper closure.'),dict(id='SQL-SECRET-EXACT-DISPATCH',source=['51.5','51.8','51.12'],missing='No generic secret.create wrapper exists; exact trusted Secret context/command/event producer must link canonical bounded kcml_secret_v1 roots, request candidate bytes, owner activation/broker and atomically persisted receipt.',verification='Canonical native Secret request -> verified locked registry/context -> explicit typed create transaction -> event/outbox/audit/locator -> exact byte load/use; duplicate stable-name and replay same operation.'),dict(id='SQL-GENERIC-262-CALLSITE-DOMAIN-PLANS',source=['51.5','51.6'],missing='Each descriptive fieldUpdatePlan storage fallback is not an executable typed column mutation. 261 sibling operations remain separate; do not supply generic JSON or unconditional-success interpreter.',verification='Owned per-family explicit physical handlers, trusted root resolution and current-row guards, unique/durable replay and failure/unknown joins for each affected operation.')],implementationProductionAcceptance='NOT_EVALUATED')
(HERE/'helper-call-sites-current.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['coverage']))
