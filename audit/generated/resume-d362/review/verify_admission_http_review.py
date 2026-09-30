from pathlib import Path
import sys,json,hashlib
HERE=Path(__file__).parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
from create_operation_contracts import ContractFailure
from create_completion_contracts import http_failure
rows=json.loads(resource_index()['contracts/generation/admission-diagnostics.json']['raw'])['diagnostics'];source=SSOT.read_bytes();cases=[]
UID='99999999-9999-4999-8999-999999999999'
for row in rows:
 result=http_failure('generation.job.create',ContractFailure(row['diagnostic'],'/generationBasis/expectedDigest'),request_id=UID,correlation_id=UID)
 cases.append({'id':row['diagnostic']+'-finite-projection','passed':result['statusCode']==row['httpStatus']and result['error']['stableCode']==row['stableCode']})
for name,operation,diagnostic,expected in [('unknown-same-prefix','generation.job.create','GENERATION_BASIS_FUTURE_NOT_DECLARED','HTTP_FAILURE_PROJECTION_UNRESOLVED'),('wrong-operation','secret.create',rows[0]['diagnostic'],'HTTP_FAILURE_OPERATION_MISMATCH')]:
 try:http_failure(operation,ContractFailure(diagnostic,''),request_id=UID,correlation_id=UID);actual='ACCEPTED'
 except ContractFailure as exc:actual=exc.code
 cases.append({'id':name,'expected':expected,'actual':actual,'passed':actual==expected})
report={'scope':'Exact finite HTTP projection only. These synthetic diagnostics do NOT prove their error predicates; concrete domain mutations are separate proofs.','sourceSha256':hashlib.sha256(source).hexdigest(),'catalogSha256':resource_index()['contracts/generation/admission-diagnostics.json']['sha256'],'cases':cases,'checked':len(cases),'failed':sum(not c['passed']for c in cases),'wholeOperationClosed':False}
(HERE/'admission-http-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(cases),'failed':report['failed']}))
