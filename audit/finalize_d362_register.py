"""Current-source bounded evidence overlay; never certifies whole operations."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from visual_evidence import verify_reference
from ssot_sources import resource_index

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=sha(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md');p=ROOT/'audit/SSOT_COMPLETION_REGISTER.json';r=json.loads(p.read_text());assert r['sourceDocumentSha256']==source
 rs=resource_index();state_path=ROOT/'audit/generated/repair-2026-09-30/design-current/verify_operation_state_receipts/operation-state-tests.json';state=json.loads(state_path.read_text());assert state['sourceDocumentSha256']==source and state['failed']==0 and all(x['passed'] for x in state['checks'])
 for name,h in state['sourceResourceSha256'].items():assert rs[name]['sha256']==h
 for f in json.loads(rs['closure/contracts/operation-state-receipts.json']['raw'])['fields']:
  identity='state:'+f['operationId']+':'+f['field'];o=next(x for x in r['obligations'] if x['id']==identity)
  o.update(state='VERIFIED',verificationLevel='SEMANTIC_DESIGN_DICTIONARY',blocker=None,repair='scripts/close_operation_state_receipts.py',scope={'operationId':f['operationId'],'field':f['field'],'coverage':'Own required non-null response dictionary and CANCELLED tuple only; full worker provenance/SQL/operation joins remain OPEN'},authoritativeSources=[{'pointer':f['schemaPointer'],'ssotSha256':source},{'pointer':'00_SSOT/KajovoCMLNG_SSOT.md#section.12.50','ssotSha256':source}],evidence=[{'path':state_path.relative_to(ROOT).as_posix(),'sha256':sha(state_path),'sourceSha256':source,'scope':state['scope']}])
 visual_path=ROOT/'audit/visual-validation.json';v=json.loads(visual_path.read_text());assert not verify_reference(v)
 storage_path=ROOT/'audit/generated/repair-2026-09-30/design-current/verify_create_storage_invariants/create-storage-invariants.json';s=json.loads(storage_path.read_text());assert s['sourceDocumentSha256']==source and s['failed']==0
 r['obligations']=[o for o in r['obligations'] if not o['id'].startswith('resume-design:')]
 for identity,area,scope,proof,level in [('locator-unique-deferred','SQL','Existing locator unique/deferred FK only; no full root/context/helpers',storage_path,'SEMANTIC_DESIGN_REFERENCE'),('advisory-key-signed','SQL','Exact51.8 signed int4 SHA256 projection only; no helper authority',storage_path,'SEMANTIC_DESIGN_REFERENCE'),('current-reference-renderer','UI','96 existing renders reused after consumed-source/screenshot verification; manual visual and backend/action semantics excluded',visual_path,'AUTOMATED_VISUAL_REFERENCE')]:
  r['obligations'].append({'id':'resume-design:'+identity,'area':area,'scope':scope,'authoritativeSources':[{'pointer':'00_SSOT/KajovoCMLNG_SSOT.md#section.'+('45.10' if area=='UI' else '51.12'),'ssotSha256':source}],'dependencies':[],'state':'VERIFIED','verificationLevel':level,'blocker':None,'repair':'scripts/visual_evidence.py' if area=='UI' else 'scripts/verify_create_storage_invariants.py','evidence':[{'path':proof.relative_to(ROOT).as_posix(),'sha256':sha(proof),'executionSourceSha256':v['sourceDocumentSha256'] if area=='UI' else source,'bindingRule':'Exact unchanged consumed UI resources/files/screenshot bytes' if area=='UI' else 'Current source'}],'sourceBinding':{'ssotSha256':source},'implementationAcceptance':'NOT_EVALUATED'})
 r['stageSeparation']={'authority':'00_SSOT/KajovoCMLNG_SSOT.md#section.73.7','A':'Mandatory effective design and explicit pre-generation fixtures remain required','B':'Bounded reference/actual PostgreSQL fixture proves only named obligation','C':'Generated-app production acceptance NOT_EVALUATED','gateMeaningChanged':False}
 r['coverage'].update(states=dict(Counter(o['state'] for o in r['obligations'])),levels=dict(Counter(o['verificationLevel'] for o in r['obligations'])),totalRegisteredObligations=len(r['obligations']),verifiedAdditionalBoundedDesignObligations=9,wholeOperationsSemanticallyVerified=0)
 p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r['coverage']))
if __name__=='__main__':main()
