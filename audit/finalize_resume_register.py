"""Bind current bounded storage/reference evidence; never close whole operations."""
import hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 source=sha(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md')
 path=ROOT/'audit/SSOT_COMPLETION_REGISTER.json';register=json.loads(path.read_text())
 assert register['sourceDocumentSha256']==source
 storage_path=ROOT/'audit/generated/resume-5334/coordinator/storage-invariant-tests.json'
 # The verifier's stable destination is explicit, not inferred from old logs.
 if not storage_path.exists():storage_path=ROOT/'audit/generated/resume-5334/coordinator/create-storage-invariants.json'
 storage=json.loads(storage_path.read_text());assert storage['sourceDocumentSha256']==source and storage['failed']==0
 assert storage['scriptSha256']==sha(ROOT/'scripts/verify_create_storage_invariants.py')
 assert storage['requirementsSha256']==sha(ROOT/'requirements-audit.txt')
 visual_path=ROOT/'audit/visual-validation.json';visual=json.loads(visual_path.read_text())
 assert visual['sourceDocumentSha256']==source and visual['status']=='PASS' and visual['failed']==0
 assert visual['scriptSha256']==sha(ROOT/'scripts/render_reference.py')
 for item in visual['results']:
  assert sha(ROOT/item['screenshot'])==item['screenshotSha256']
 for name,digest in visual['sourceHashes'].items():assert sha(ROOT/name)==digest
 semantic_path=ROOT/'audit/generated/resume-5334/coordinator/secret-semantic-tests.json'
 semantic=json.loads(semantic_path.read_text());assert semantic['sourceDocumentSha256']==source and semantic['failed']==0
 register['obligations']=[o for o in register['obligations'] if not o['id'].startswith('resume-design:')]
 def add(identity,area,scope,authority,evidence,checks):
  register['obligations'].append({'id':'resume-design:'+identity,'area':area,'scope':scope,'authoritativeSources':[{'pointer':'00_SSOT/KajovoCMLNG_SSOT.md#section.'+a,'ssotSha256':source} for a in authority],'dependencies':[],
   'state':'VERIFIED','verificationLevel':'SEMANTIC_DESIGN_REFERENCE','blocker':None,'repair':'scripts/verify_create_storage_invariants.py' if area=='SQL' else 'scripts/render_reference.py',
   'evidence':[{'path':evidence.relative_to(ROOT).as_posix(),'sha256':sha(evidence),'sourceSha256':source,'scope':checks}],
   'sourceBinding':{'ssotSha256':source},'acceptanceStage':'B_DESIGN_REFERENCE','implementationAcceptance':'NOT_EVALUATED'})
 add('locator-unique-deferred','SQL','Existing stable business locator has unique logical operation and deferred FK; full root/context/helpers/transaction excluded',['49.4','51.12'],storage_path,'Parsed SQL constraints and precise removal mutations; no PostgreSQL18 execution')
 add('advisory-key-signed','SQL','Exact SHA256 first-four-big-endian signed int4 projection only; no trust/context/helper authority',['51.8'],storage_path,'SQL/PLpgsql parse and independent Python/Node projection vectors; no PostgreSQL18 execution')
 add('current-reference-renderer','UI','12 effective illustrative views ×4 viewports ×2 locales; automated layout/interactions only; exposure, semantic action closure and manual visual acceptance excluded',['45.10'],visual_path,'96 current renders, source and screenshot hashes; no backend execution')
 for o in register['obligations']:
  if o['id'].startswith('secret-format:'):
   o['evidence'].append({'path':semantic_path.relative_to(ROOT).as_posix(),'sha256':sha(semantic_path),'sourceSha256':source,'scope':'42 isolated synthetic candidate checks; proposal remains pending owner review, not effective format'})
   o['ownerDecisionReview']='audit/SSOT_SECRET_OWNER_DECISIONS.md'
 register['stageSeparation']={'authority':'00_SSOT/KajovoCMLNG_SSOT.md#section.73.7','mandatoryBeforeGeneration':'Effective required contracts, field provenance/admission/physical joins and mandatory final-family design/fixture gates; runtime fixtures explicitly required by R17 are not waived',
  'designReferenceEvidence':'B may verify a bounded A requirement; successful schema/reference checks do not close remaining operation requirements',
  'futureImplementationAcceptance':'C: real generated-app HTTP/database/browser/provider behavior, deployment execution and production acceptance NOT_EVALUATED',
  'operationScopeTable':'audit/SSOT_CREATE_OPERATION_OBLIGATIONS.md','gateMeaningChanged':False}
 register['coverage']['states']=dict(Counter(o['state'] for o in register['obligations']))
 register['coverage']['levels']=dict(Counter(o['verificationLevel'] for o in register['obligations']))
 register['coverage']['totalRegisteredObligations']=len(register['obligations'])
 register['coverage']['verifiedAdditionalBoundedDesignObligations']=3
 register['coverage']['wholeOperationsSemanticallyVerified']=0
 assert len({o['id'] for o in register['obligations']})==len(register['obligations'])
 path.write_text(json.dumps(register,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(register['coverage']))
if __name__=='__main__':main()
