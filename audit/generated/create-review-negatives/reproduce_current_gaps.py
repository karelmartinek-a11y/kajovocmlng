"""Independent review probes; accepted invalid candidates are GAP evidence, not PASS."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
from create_operation_contracts import admit,decode_http,ContractFailure
from jsonschema import Draft202012Validator,FormatChecker
UID='00000000-0000-4000-8000-000000000001';TARGET='00000000-0000-4000-8000-000000000002';PARENT='00000000-0000-4000-8000-000000000003'
server={'owner':UID,'actor':'OWNER','authenticated':True,'recovery':'READY','stableNames':[],
 'valuePolicyTypes':['PASSWORD','CERTIFICATE'],'targets':{TARGET:{'objectId':TARGET,'kind':'PLATFORM_COMPONENT','owner':UID,'state':'ACTIVE'}},
 'jobs':{PARENT:{'jobId':PARENT,'owner':UID,'state':'COMPLETED'}},'artifacts':{TARGET:{'artifactId':TARGET,'owner':UID,'immutable':True,'bytes':b'fixture','contentSha256':hashlib.sha256(b'fixture').hexdigest(),'mediaType':'text/plain'}}}
headers=[('Content-Type','application/json'),('Idempotency-Key','fixture-key')]
gen={'intent':'Create fixture component','kind':'UPDATE','targetKind':'PLATFORM_COMPONENT','targetObjectId':TARGET,'parentJobId':PARENT}
sec={'stableName':'FIXTURE_SECRET','displayName':'Fixture','type':'PASSWORD','value':{'encoding':'UTF8','text':'synthetic fixture'}}
def request(op,body):return decode_http(op,'POST','/generation/jobs' if op=='generation.job.create' else '/secrets',[],headers,json.dumps(body).encode())
probes=[]
def probe(name,fn,scope):
 try:result=fn();probes.append({'case':name,'observed':'ACCEPTED','result':result,'scope':scope,'verdict':'POSITIVE_CONTROL_ONLY' if name=='password-positive' else 'GAP_REQUIRES_REVIEW'})
 except ContractFailure as exc:probes.append({'case':name,'observed':'STRUCTURED_REJECTION','code':exc.code,'pointer':exc.pointer,'scope':scope})
 except Exception as exc:probes.append({'case':name,'observed':'UNRELATED_EXCEPTION','type':type(exc).__name__,'scope':scope,'verdict':'NOT_A_VALID_NEGATIVE_PASS'})
for name,body in [('invalid-certificate-type-whitelist',{**sec,'type':'CERTIFICATE','value':{'encoding':'UTF8','text':'not a certificate'}}),('password-positive',sec)]:
 probe(name,lambda body=body:admit(request('secret.create',body),server),'type policy')
for name,updates in [('target-owner-mismatch',{'targets':{TARGET:{**server['targets'][TARGET],'owner':PARENT}}}),('parent-owner-mismatch',{'jobs':{PARENT:{**server['jobs'][PARENT],'owner':PARENT}}}),('parent-state-unverified',{'jobs':{PARENT:{'jobId':PARENT}}}),('target-state-unverified',{'targets':{TARGET:{'objectId':TARGET,'kind':'PLATFORM_COMPONENT'}}})]:
 probe(name,lambda updates=updates:admit(request('generation.job.create',gen),{**server,**updates}),'server resolved snapshot scope/state')
file={**gen,'sources':[{'kind':'FILE','artifactId':TARGET}]}
bad=copy.deepcopy(server);del bad['artifacts'][TARGET]['contentSha256']
probe('missing-artifact-content-digest',lambda:admit(request('generation.job.create',file),bad),'structured diagnostics')
rs=resource_index(); rows={r['operationId']:r for r in json.loads(rs['contracts/payload-contracts.json']['raw'])['records']}
for oid in ['generation.job.create','secret.create']:
 row=rows[oid];base={'routeId':row['routeId'],'operationId':oid,'logicalOperationId':UID,'correlationId':UID,'status':'SUCCEEDED','terminal':True,'output':None,'error':None,'resultDigest':'sha256:'+'0'*64}
 validator=Draft202012Validator(row['responseSchema'],format_checker=FormatChecker())
 for name,mutation in [('success-null-output',{}),('success-nonterminal',{'terminal':False}),('failure-no-error',{'status':'FAILED'}),('accepted-terminal',{'status':'ACCEPTED'})]:
  probe(oid+'/'+name,lambda mutation=mutation,base=base,validator=validator: {'schemaAccepted':validator.is_valid({**base,**mutation})},'response coupling: schema only, no full semantic closure')
report={'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'scriptSha256':hashlib.sha256(Path(ROOT/'scripts/create_operation_contracts.py').read_bytes()).hexdigest(),'evidenceKind':'INDEPENDENT_DESIGN_GAP_REPRODUCTIONS_NOT_RUNTIME','probes':probes}
Path(__file__).with_name('observed-gaps.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'probes':len(probes),'sourceDocumentSha256':report['sourceDocumentSha256']}))
