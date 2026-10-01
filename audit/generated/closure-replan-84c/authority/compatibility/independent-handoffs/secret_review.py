from pathlib import Path
import sys,json,copy,os,hashlib,importlib
ROOT=Path('/workspace/kajovocmlng');OWN=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT
m=importlib.import_module('verify_secret_profile_handoffs');cases=[]
def run(label):
 out=OWN/label;os.environ['KCML_AUDIT_OUTPUT']=str(out);code=m.main();q=json.loads((out/'secret-profile-native-tests.json').read_text());return code,q
code,q=run('secret-positive');assert code==0 and q['checked']==205;cases.append({'case':'secret-current205-positive','passed':True})
p=ROOT/'audit/generated/closure-replan-84c/secret/compatibility/runs/final-116e/native/tree/audit/generated/resume-34d/review/secret-current/secret-native-review.json';original=json.loads(p.read_text());old=Path.read_text
for name,alter,expected in [('secret-wrong-parser',lambda q:q['rootImplementationDigests'].__setitem__('secret_profile_parsers.py','0'*64),'independent-native/root-helper:secret_profile_parsers.py'),('secret-stale-source',lambda q:q.__setitem__('sourceDocumentSha256','0'*64),'independent-native/current-consumed-scope-or-new-execution')]:
 v=copy.deepcopy(original);alter(v)
 Path.read_text=lambda self,*a,**kw:json.dumps(v)if self==p else old(self,*a,**kw)
 try:code,q=run(name)
 finally:Path.read_text=old
 failed={c['case']for c in q['checks']if not c['passed']};assert code==1 and expected in failed;cases.append({'case':name,'passed':True,'requiredDiagnostic':expected})
# Verify source unchanged/current and actual twelve execution manifest/proof pairs.
d=json.loads((ROOT/'audit/generated/closure-replan-84c/secret/compatibility/DELIVERY.json').read_text());current=hashlib.sha256(SSOT.read_bytes()).hexdigest();assert d['sourceDocumentSha256']==current
fresh=d['actualFreshExecutionFamilies'];assert len(fresh)==12
for f in fresh:
 p=ROOT/f['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']
 q=json.loads(p.read_text());assert q.get('sourceDocumentSha256',q.get('sourceSha256',q.get('inputSsotSha256')))==current
 parent=p
 while parent.name!='tree' and parent.parent!=parent:parent=parent.parent
 manifest=json.loads((parent.parent/'execution-manifest.json').read_text());assert manifest['sourceUnchangedDuringRun']is True and manifest['sourceDocumentSha256']==current
 for item in manifest['executedPythonReads']:
  assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['originalSha256']
cases.append({'case':'all12-execution-manifests-and-exact-proof-hashes-current','passed':True})
(OWN/'secret-independent-review.json').write_text(json.dumps({'sourceSha256':current,'checked':len(cases),'failed':0,'cases':cases,'actualFreshExecutionFamilies':12,'wholeOperationClosed':False,'systemd':'BLOCKED_ENVIRONMENT','implementationAcceptance':'NOT_EVALUATED'},indent=2)+'\n');print('Secret independent4 PASS; manifests12 fresh sourcebound')
