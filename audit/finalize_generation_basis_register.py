"""Join named generation design proofs; PostgreSQL producer/consumer gates remain open."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=sha(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md');p=ROOT/'audit/SSOT_COMPLETION_REGISTER.json';r=json.loads(p.read_text());assert r['sourceDocumentSha256']==source
 proof=ROOT/'audit/generated/repair-2026-09-30/design-current/verify_generation_admission_basis/generation-admission-current-tests.json';q=json.loads(proof.read_text());assert q['sourceDocumentSha256']==source and q['failed']==0
 for name,h in q['supportSha256'].items():assert sha(ROOT/name)==h,name
 import sys
 sys.path.insert(0,str(ROOT/'scripts'))
 from run_ssot_repair_design_checks import evidence_inputs_hash
 from ssot_sources import resource_index
 runner=json.loads((ROOT/'audit/generated/repair-2026-09-30/design-current/commands.json').read_text());check=next(x for x in runner['commands']if x['script']=='scripts/verify_generation_admission_basis.py')
 assert check['exitCode']==0 and check['evidenceInputsSha256']==evidence_inputs_hash('verify_generation_admission_basis.py')
 r['obligations']=[o for o in r['obligations']if not o['id'].startswith(('generation-basis-design:','admission-predicate:'))]
 diagnostics=json.loads(resource_index()['contracts/generation/admission-diagnostics.json']['raw'])['diagnostics']
 for index,row in enumerate(diagnostics):
  r['obligations'].append({'id':'admission-predicate:'+row['diagnostic'],'area':'generation','scope':{'operationId':'generation.job.create','diagnostic':row['diagnostic'],'coverage':'Exact predicate execution from actual valid witness; finite HTTP projection is already tested but does not prove predicate'},'authoritativeSources':[{'pointer':'contracts/generation/admission-diagnostics.json#/diagnostics/'+str(index),'ssotSha256':source}],'dependencies':['operation:generation.job.create:request'],'state':'OPEN','verificationLevel':'SEMANTIC_PREDICATE','blocker':None,'repair':'scripts/generation_admission_contracts.py or scripts/generation_retry_inventory.py','evidence':[{'path':proof.relative_to(ROOT).as_posix(),'sha256':sha(proof),'limitation':'Mapping-only for complete finite catalog; named native/ledger executed cases recorded separately'}],'sourceBinding':{'ssotSha256':source},'implementationAcceptance':'NOT_EVALUATED'})
 scopes={'UPDATE':'Exact immutable target identity/revision bytes for discussion; migration/compatibility/execution/activation remain mandatory','RETRY':'Exact failed technical run/plan/approval lineage for discussion. Separate actual native ledger reference tests; PostgreSQL complete locked scan and real classifiers remain mandatory','REPAIR':'Exact target head/approved lineage and actual native monitoring observation bytes for discussion; consumer repair predicate remains mandatory','FOLLOW_UP':'Actual initial request/specification/final output native bytes, declared source result role, publication and output schema; physical producer/locked consumer joins remain mandatory','retry-current-projection':'Nonempty synthetic operation/attempt/evidence actual bytes, pinned CAS read-back and current identity/version; not an actual PostgreSQL phase table-scan or universal classifier'}
 for identity,scope in scopes.items():
  r['obligations'].append({'id':'generation-basis-design:'+identity,'area':'generation','scope':scope,'authoritativeSources':[{'pointer':'00_SSOT/KajovoCMLNG_SSOT.md#section.12.51','ssotSha256':source}],'dependencies':['follow-up-design:actual-sufficiency'] if identity=='FOLLOW_UP' else [],'state':'VERIFIED','verificationLevel':'SEMANTIC_DESIGN_REFERENCE','blocker':None,'repair':'scripts/close_generation_admission_basis.py','evidence':[{'path':proof.relative_to(ROOT).as_posix(),'sha256':sha(proof),'sourceSha256':source,'limitation':scope}],'sourceBinding':{'ssotSha256':source},'implementationAcceptance':'NOT_EVALUATED'})
 from collections import Counter
 r['coverage'].update(states=dict(Counter(o['state']for o in r['obligations'])),levels=dict(Counter(o['verificationLevel']for o in r['obligations'])),totalRegisteredObligations=len(r['obligations']),verifiedGenerationBasisDesignObligations=5,finiteGenerationAdmissionPredicatesRegistered=len(diagnostics),wholeOperationsSemanticallyVerified=0)
 p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r['coverage']))
if __name__=='__main__':main()
