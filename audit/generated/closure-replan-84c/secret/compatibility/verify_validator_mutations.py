"""Positive-derived stale source/code/SQL diagnostics; isolated report copies only."""
import copy,hashlib,importlib,json,os,sys
from pathlib import Path
R=Path('/workspace/kajovocmlng');D=Path(__file__).parent;sys.path.insert(0,str(R/'scripts'));checks=[]
from ssot_sources import SSOT
mods=[importlib.import_module('verify_'+n+'_handoffs')for n in ['producer_archive','generation_chain','secret_profile']]
files=['producer-archive-chain-tests.json','generation-chain-tests.json','secret-profile-native-tests.json']
def run(m,i,label):
 out=D/'mutation-executions'/label;os.environ['KCML_AUDIT_OUTPUT']=str(out.relative_to(R));exit=m.main();return exit,json.loads((out/files[i]).read_text())
def result(label,report,expected):
 failed={c['case']for c in report['checks']if not c['passed']};checks.append({'case':label,'passed':report['status']=='BLOCKED' and expected in failed,'requiredDiagnostic':expected,'failedCases':sorted(failed)})
for i,m in enumerate(mods):
 e,q=run(m,i,['producer','generation','secret'][i]+'-positive');checks.append({'case':['producer','generation','secret'][i]+'-valid-positive','passed':e==0 and q['failed']==0})
 if i<2:
  origin=m.PROOFS['joined']if i==0 else m.PROOF;original=json.loads((R/origin).read_text())
  for label,modify,expected in [('stale-execution',lambda q:q.update(sourceDocumentSha256='0'*64),'joined/current-execution-source'if i==0 else'current-source'),('changed-canonical-sql',lambda q:q[next(k for k in ['canonicalInputs','integratedSqlDigests']if k in q)].update({'database/generation-create-foundations.sql'if i==0 else'database/generation-create-authentication.sql':'0'*64}),'joined/canonical-resource:database/generation-create-foundations.sql'if i==0 else'canonical-sql:database/generation-create-authentication.sql')]:
   q=copy.deepcopy(original);modify(q);p=D/'mutation-inputs'/str(i)/(label+'.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(q,indent=2)+'\n')
   if i==0:m.PROOFS['joined']=str(p.relative_to(R))
   else:m.PROOF=str(p.relative_to(R))
   e,report=run(m,i,str(i)+'-'+label);result(str(i)+'-'+label,report,expected)
  if i==1:
   q=copy.deepcopy(original);support_name=next(iter(q['supportSha256']));q['supportSha256'][support_name]='0'*64;p=D/'mutation-inputs'/'1'/'changed-consumed-support.json';p.write_text(json.dumps(q,indent=2)+'\n');m.PROOF=str(p.relative_to(R));e,report=run(m,i,'changed-consumed-support');result('changed-consumed-support',report,'consumed-support:'+support_name)
   q=copy.deepcopy(original);q.pop('supportSha256');p=D/'mutation-inputs'/'1'/'missing-consumed-support.json';p.write_text(json.dumps(q,indent=2)+'\n');m.PROOF=str(p.relative_to(R));e,report=run(m,i,'missing-consumed-support');result('missing-consumed-support',report,'all-named-consumed-support')
  if i==0:m.PROOFS['joined']=origin
  else:m.PROOF=origin
 else:
  p=R/'audit/generated/closure-replan-84c/secret/compatibility/runs/final-116e/native/tree/audit/generated/resume-34d/review/secret-current/secret-native-review.json';raw=p.read_bytes();original=json.loads(raw)
  try:
   for label,modify,expected in [('stale-native-execution',lambda q:q.update(sourceDocumentSha256='0'*64),'independent-native/current-consumed-scope-or-new-execution'),('changed-native-parser',lambda q:q['rootImplementationDigests'].update({'secret_profile_parsers.py':'0'*64}),'independent-native/root-helper:secret_profile_parsers.py')]:
    q=copy.deepcopy(original);modify(q);p.write_text(json.dumps(q,indent=2)+'\n');e,report=run(m,i,label);result(label,report,expected)
  finally:p.write_bytes(raw)
report={'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'wholeOperationClosed':False,'scope':'Validator rejection sensitivity only, existing full-domain negative fixture cases preserved.'};(D/'validator-mutations.json').write_text(json.dumps(report,indent=2)+'\n');raise SystemExit(report['failed']!=0)
