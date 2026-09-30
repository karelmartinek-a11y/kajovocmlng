from pathlib import Path
import sys,copy,json,hashlib
HERE=Path(__file__).parent
sys.path.insert(0,str(HERE.parent/'admission'))
import generation_admission_fixtures as f
from generation_admission_reference import select_generation_basis,ContractFailure,canonical,digest
checks=[]
def expect(name,code,body,records):
 try:select_generation_basis(body,f.repo(records));actual='ACCEPTED'
 except ContractFailure as exc:actual=exc.code
 except Exception as exc:actual=type(exc).__name__+':'+str(exc)
 checks.append({'id':name,'expected':code,'actual':actual,'passed':code==actual})
def edit(records,key,fn):
 value=json.loads(records[key]['bytes']);fn(value);raw=canonical(value);records[key].update(bytes=raw,contentDigest=digest(raw));return digest(raw)
for kind in f.bodies:
 result=select_generation_basis(f.bodies[kind],f.repo())
 checks.append({'id':kind+'-independent-positive','passed':result['decision']=='ADMIT_DISCUSSION'})
rs=copy.deepcopy(f.records);body=copy.deepcopy(f.bodies['REPAIR']);body['generationBasis']['expectedSpecificationDigest']=edit(rs,f.REV,lambda v:v.update(jobId=f.ids(99)))
expect('repair-foreign-document-job','GENERATION_BASIS_DOCUMENT_JOB_MISMATCH',body,rs)
rs=copy.deepcopy(f.records);body=copy.deepcopy(f.bodies['REPAIR']);body['generationBasis']['expectedAuthorityDigest']=edit(rs,f.AUTH,lambda v:v['authority'].update(rootIntentId=f.ids(98)))
expect('repair-replaced-native-authority','GENERATION_APPROVED_AUTHORITY_CONTENT_MISMATCH',body,rs)
rs=copy.deepcopy(f.records);rs[f.SCHEMA]['schema']['bundleDigest']='sha256:'+'a'*64
expect('repair-unresolvable-observation-bundle','GENERATION_BASIS_SCHEMA_BUNDLE_UNAVAILABLE',copy.deepcopy(f.bodies['REPAIR']),rs)
rs=copy.deepcopy(f.records);rs.pop(f.APP)
expect('repair-missing-owner-approval','GENERATION_OWNER_APPROVAL_UNAVAILABLE',copy.deepcopy(f.bodies['REPAIR']),rs)
for kind in ['RETRY','REPAIR']:
 result=select_generation_basis(f.bodies[kind],f.repo());keys={x['recordId'] for x in result['frozenInputs']}
 required={f.APP,f.NATIVE_AUTHORITY}|({f.resultdig} if kind=='RETRY' else {f.SCHEMA,f.SREC,f.MREC})
 checks.append({'id':kind+'-consulted-dependency-lineage-retention','requiredRetainedIds':sorted(required),'missing':sorted(required-keys),'passed':required<=keys})
report={'scope':'Independent positive-derived admission mutations; design reference only. §12.20 graph-wide semantic eligibility remains separate.','checks':checks,'failed':sum(not x['passed'] for x in checks),'inputFilesSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE.parent/'admission/generation_admission_reference.py',HERE.parent/'admission/generation_admission_fixtures.py']}}
(HERE/'admission-review-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'failed':report['failed']}))
