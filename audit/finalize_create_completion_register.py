"""Join bounded create DESIGN proof to inventory; never close whole operations.

Run with the pinned audit interpreter after completion_register.py and the
resumable runner. All source, helper, environment and log bindings are checked.
This audit-only overlay is outside the runner's supporting-source universe.
"""
import hashlib,importlib.metadata,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_ssot_repair_design_checks import evidence_inputs_hash
from ssot_sources import resource_index

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 source=sha(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md')
 resources=resource_index()
 payload=json.loads(resources['contracts/payload-contracts.json']['raw'])
 pointers={r['operationId']:'contracts/payload-contracts.json#/records/'+str(i) for i,r in enumerate(payload['records'])}
 runner_path=ROOT/'audit/generated/repair-2026-09-30/design-current/commands.json'
 runner=json.loads(runner_path.read_text())
 assert runner['sourceSha256']==source and runner['allCommandsFinished']
 support=hashlib.sha256()
 for base in ['scripts','01_UI_CONTRACT','03_UI_REFERENCE']:
  for path in sorted((ROOT/base).rglob('*')):
   if path.is_file() and '__pycache__' not in path.parts:
    support.update(path.relative_to(ROOT).as_posix().encode()+b'\0'+path.read_bytes()+b'\0')
 assert support.hexdigest()==runner['supportInputsSha256']
 packages={line.split('==')[0]:importlib.metadata.version(line.split('==')[0]) for line in (ROOT/'requirements-audit.txt').read_text().splitlines() if '==' in line}
 env=hashlib.sha256(json.dumps({'python':sys.version,'packages':packages},sort_keys=True).encode()).hexdigest()
 assert env==runner['environmentSha256'] and sha(ROOT/'requirements-audit.txt')==runner['requirementsSha256']
 entries={Path(c['script']).name:c for c in runner['commands']}
 for c in entries.values():
  assert c['sourceSha256']==source and c['scriptSha256']==sha(ROOT/c['script'])
  assert c['evidenceLogSha256']==sha(ROOT/c['evidence'])
  assert c['evidenceInputsSha256']==evidence_inputs_hash(Path(c['script']).name)
 path=ROOT/'audit/SSOT_COMPLETION_REGISTER.json';register=json.loads(path.read_text());assert register['sourceDocumentSha256']==source
 register['obligations']=[o for o in register['obligations'] if not o['id'].startswith(('create-design:','follow-up-design:','secret-format:'))]
 def proof(script,filename):
  command=entries[script];assert command['exitCode']==0 and command['diagnostic']=='PASS'
  p=ROOT/'audit/generated/repair-2026-09-30/design-current'/script.removesuffix('.py')/filename
  r=json.loads(p.read_text());assert r['sourceDocumentSha256']==source and r['failed']==0
  assert len(r['checks'])==r['checked'] and all(case.get('passed') is True for case in r['checks'])
  return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'runnerPath':runner_path.relative_to(ROOT).as_posix(),'runnerSha256':sha(runner_path),'runnerLogSha256':command['evidenceLogSha256'],'sourceSha256':source,'supportInputsSha256':support.hexdigest(),'environmentSha256':env,'scope':'DESIGN_REFERENCE_MODEL_NOT_RUNTIME'}
 request=proof('verify_create_operation_requests.py','create-request-tests.json')
 completion=proof('verify_create_completion.py','completion-tests.json')
 http=proof('verify_create_http_errors.py','create-http-errors.json')
 follow=proof('verify_follow_up_contracts.py','follow-up-tests.json')
 def add(identity,area,scope,state,authority,proofs=(),dependencies=(),blocker=None):
  register['obligations'].append({'id':identity,'area':area,'scope':scope,'state':state,'verificationLevel':'SEMANTIC_DESIGN_REFERENCE','authoritativeSources':[{'pointer':a,'ssotSha256':source} for a in authority],'dependencies':list(dependencies),'blocker':blocker,'repair':'00_SSOT/KajovoCMLNG_SSOT.md#12.48-12.49','evidence':list(proofs),'sourceBinding':{'ssotSha256':source},'implementationAcceptance':'NOT_EVALUATED'})
 for oid in ['generation.job.create','secret.create']:
  for role,evidence,scope in [('request',request,'Exact route/domain shape, HTTP decoding, scoped frozen replay; unresolved type/kind policies excluded'),('response',completion,'Exact server receipt/status/error tuples and frozen receipt relations; full operation/persistence implementation excluded'),('event',completion,'Typed aggregate create receipt, commit/persisted event equality and digest/sequence relations in reference model; actual outbox/inbox excluded'),('http-error',http,'Exact known-diagnostic HTTP projection; unknown diagnostics blocked; actual webserver excluded')]:
   add('create-design:'+oid+':'+role,oid,{'operationId':oid,'boundary':role,'coverage':scope},'VERIFIED',[pointers[oid]+'/'+('requestSchema' if role=='request' else 'responseSchema' if role=='response' else 'eventSchema' if role=='event' else 'responseSchema/properties/error'),'00_SSOT/KajovoCMLNG_SSOT.md#section.12.48'],[evidence])
 add('follow-up-design:frozen-admission','generation',{'coverage':'Approved55matrixcells; three explicit selectors×11source states; frozen byte hydration and no source mutation in reference model'},'VERIFIED',['00_SSOT/KajovoCMLNG_SSOT.md#section.12.49','contracts/follow-up-admission.json#/matrix'],[follow],['create-design:generation.job.create:request'])
 add('follow-up-design:actual-sufficiency','generation',{'coverage':'Real validator for consistency/sufficiency per basis; actual SQL locks/commit/publication/inbox and consumer'},'BLOCKED',['00_SSOT/KajovoCMLNG_SSOT.md#section.12.49'],dependencies=['follow-up-design:frozen-admission'],blocker={'kind':'TECHNICAL','reason':'Trusted reference flags are not concrete basis validators or runtime transaction evidence'})
 proposal_path=ROOT/'audit/generated/create-review-authority/secret-variant-proposals.json';proposal=json.loads(proposal_path.read_text())
 for c in proposal['contracts']:
  add('secret-format:'+c['secretType'],'Secrets',{'secretType':c['secretType'],'coverage':'Approve concrete discriminator/field/encoding/semantic/import/storage/consumer format; proposal is not effective'},'BLOCKED',['00_SSOT/KajovoCMLNG_SSOT.md#section.8.2','00_SSOT/KajovoCMLNG_SSOT.md#section.8.4','00_SSOT/KajovoCMLNG_SSOT.md#section.72.21'],[{'path':proposal_path.relative_to(ROOT).as_posix(),'sha256':sha(proposal_path),'scope':'PROPOSAL_ONLY_PENDING_OWNER_FORMAT_REVIEW'}],blocker={'kind':'OWNER_DECISION','reason':'Explicit variant principle approved; concrete format/fields/bounds awaiting review'})
 assert len({o['id'] for o in register['obligations']})==len(register['obligations'])
 register['boundedCreateProofJoin']={'overlayPath':Path(__file__).relative_to(ROOT).as_posix(),'overlaySha256':sha(Path(__file__)),'runnerSha256':sha(runner_path),'sourceSha256':source,'supportInputsSha256':support.hexdigest(),'environmentSha256':env,'wholeOperationsClosed':0,'reviewedDesignObligations':9,'explicitlyExcluded':'Actual backend/SQL/runtime; full create policies/consumer handoffs; concrete Secret format approvals'}
 register['coverage']['states']=dict(Counter(o['state'] for o in register['obligations']))
 register['coverage']['levels']=dict(Counter(o['verificationLevel'] for o in register['obligations']))
 register['coverage']['totalRegisteredObligations']=len(register['obligations'])
 register['coverage']['verifiedBoundedCreateDesignObligations']=9
 path.write_text(json.dumps(register,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'sourceSha256':source,'registered':len(register['obligations']),'boundedDesignVerified':9,'wholeOperationsVerified':'0/619'}))
if __name__=='__main__':main()
