from pathlib import Path
import sys,json,copy,hashlib
from jsonschema import Draft202012Validator,FormatChecker
from family_reference import decode,Violation,OPS,uid
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
rows=json.loads(resource_index()['contracts/payload-contracts.json']['raw'])['records'];proof=[]
for oid in OPS:
 old=next(x for x in rows if x['operationId']==oid);mut=oid.endswith('revoke');path='/owner/sessions/'+uid()if mut else'/owner/sessions';native=decode(oid,'DELETE'if mut else'GET',path,[],[('If-Match','"0"'),('Idempotency-Key','synthetic')]if mut else[]);positive=copy.deepcopy(native);positive['query']=[]
 Draft202012Validator(old['requestSchema'],format_checker=FormatChecker()).validate(positive)
 violation=copy.deepcopy(positive);violation['query']=[{'name':'unapprovedQuery','value':'1'}];Draft202012Validator(old['requestSchema'],format_checker=FormatChecker()).validate(violation)
 try:decode(oid,'DELETE'if mut else'GET',path,[('unapprovedQuery','1')],[('If-Match','"0"'),('Idempotency-Key','synthetic')]if mut else[]);raise AssertionError('EXPECTED_REJECTION_MISSING')
 except Violation as ex:
  assert str(ex)=='HTTP_QUERY_UNKNOWN'
 proof.append({'operationId':oid,'classification':'REPRODUCED_DEFECT','scope':'existing request mask permits unknown query; actual runtime admission was not evaluated','positiveLegacyNativeWitnessValid':True,'legacyAcceptedUnknownQuery':True,'newActualHTTPDecoderDiagnostic':'HTTP_QUERY_UNKNOWN','schemaSourcePointer':'contracts/payload-contracts.json#/records/'+str(rows.index(old))+'/requestSchema','schemaSha256':hashlib.sha256(json.dumps(old['requestSchema'],sort_keys=True,separators=(',',':')).encode()).hexdigest()})
(OUT/'legacy-mask-defect-proof.json').write_text(json.dumps({'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'proof':proof},indent=2)+'\n');print(json.dumps({'reproduced':len(proof),'actualRuntimeEvaluated':False}))
