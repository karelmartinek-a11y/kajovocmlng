"""Root-owned integration proposals: pure transforms, no shared target writes.
Mutable checkpoint progress is preserved. CLI writes only owned review previews.
"""
from pathlib import Path
import json,copy,hashlib
ROOT=Path('/workspace/kajovocmlng');OWN=Path(__file__).parent

def patch_checklist(current,proposal):
 doc=copy.deepcopy(current)
 for op in proposal['operations']:
  cur=doc;parts=op['path'].lstrip('/').split('/')
  for key in parts[:-1]:cur=cur[int(key)]if isinstance(cur,list)else cur[key]
  key=int(parts[-1])if isinstance(cur,list)else parts[-1]
  if op['op']=='test':
   if cur[key]!=op['value']:raise ValueError('PATCH_CHECKLIST_PRECONDITION_CHANGED_ROOT_REVIEW_REQUIRED')
  elif op['op']in('replace','add'):cur[key]=copy.deepcopy(op['value'])
  else:raise ValueError('PATCH_OPERATION_UNSUPPORTED')
 return doc

def merge_checkpoint(current,proposal,expected_source):
 if current.get('sourceDocumentSha256')!=expected_source:raise ValueError('PATCH_SOURCE_CHANGED_ROOT_REVIEW_REQUIRED')
 doc=copy.deepcopy(current)
 for op in proposal['operations']:
  if op['op']=='test':continue
  if op['path']=='/environmentBlockers/byId:SHARED.CRYPTO.SYSTEMD_SOURCE/layerScope':
   rows=[x for x in doc.get('environmentBlockers',[])if x.get('id')=='SHARED.CRYPTO.SYSTEMD_SOURCE']
   if len(rows)!=1:raise ValueError('PATCH_ENV_ID_NOT_UNIQUE_ROOT_REVIEW_REQUIRED')
   rows[0]['layerScope']=copy.deepcopy(op['value'])
  elif op['path']=='/closureDependencyReview':doc['closureDependencyReview']=copy.deepcopy(op['value'])
  else:raise ValueError('PATCH_CHECKPOINT_PATH_UNSUPPORTED')
 return doc

def validate_preserved(before,after,kind):
 assert before['SSOT_CONTRACT_READY']==after['SSOT_CONTRACT_READY']=='BLOCKED'
 assert before['IMPLEMENTATION_PRODUCTION_ACCEPTANCE']==after['IMPLEMENTATION_PRODUCTION_ACCEPTANCE']=='NOT_EVALUATED'
 if kind=='checklist':
  assert len(after['obligations'])==36
  for field in ['id','state','proofRequirements']:
   assert [x[field]for x in before['obligations']]==[x[field]for x in after['obligations']]
 else:
  for key in before:
   if key not in('environmentBlockers','closureDependencyReview'):assert before[key]==after[key],key
  for a,b in zip(before['environmentBlockers'],after['environmentBlockers']):
   assert {k:v for k,v in a.items()if k!='layerScope'}=={k:v for k,v in b.items()if k!='layerScope'}

if __name__=='__main__':
 proposals=json.loads((OWN/'integration-patch-proposals.json').read_text());proof=[]
 for p in proposals['patches']:
  raw=(ROOT/p['target']).read_bytes();before=json.loads(raw)
  if p['target'].endswith('CHECKLIST.json'):
   assert hashlib.sha256(raw).hexdigest()==p['requiresInputSha256'],'PATCH_PRECONDITION_ONLY_CHECKLIST_REVIEW_REQUIRED'
   after=patch_checklist(before,p);kind='checklist'
  else:after=merge_checkpoint(before,p,proposals['sourceSha256']);kind='checkpoint'
  validate_preserved(before,after,kind)
  (OWN/('preview-'+Path(p['target']).name)).write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
  proof.append({'target':p['target'],'capturedCurrentInputSha256':hashlib.sha256(raw).hexdigest(),'transformValidatedInMemory':True,'currentProgressAndGatesPreserved':True,'sharedTargetWritten':False})
 (OWN/'merge-validation.json').write_text(json.dumps({'status':'PASS_SCOPED_PURE_TRANSFORMS','sourceSha256':proposals['sourceSha256'],'targets':proof,'byteHashDriftIsOnlyPatchPrecondition':True},indent=2)+'\n');print('Pure audit transforms validated; no shared files written')
