"""Positive-derived native-mask/HTTP decoder checks; GET has no JSON body parser."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
from jsonschema import Draft202012Validator,FormatChecker
from secret_metadata_status_read import decode_metadata_read
from secret_value_read_transport import decode_http_value_read
rows=json.loads(resource_index()['contracts/payload-contracts.json']['raw'])['records'];checks=[]
def record(name,ok,**extra):checks.append({'id':name,'status':'PASS'if ok else'BLOCKED',**extra})
id_='aaaaaaaa-1111-4111-8111-111111111111'
for op in ['secret.metadata.read','secret.value.read']:
 r=next(x for x in rows if x['operationId']==op);v=Draft202012Validator(r['requestSchema'],format_checker=FormatChecker())
 positive={'routeId':r['routeId'],'operationId':op,'pathParameters':{'id':id_},'query':{},'body':None,'guards':{}}
 record(op+'/positive',not list(v.iter_errors(positive)))
 for field,value,keyword in [('body',{},'type'),('guards',{'authorized':True},'additionalProperties'),('query',{'unknown':'x'},'additionalProperties'),('pathParameters',{'id':id_,'unknown':'x'},'additionalProperties'),('pathParameters',{'id':id_.upper()},'pattern'),('pathParameters',{'id':id_+'\n'},'pattern')]:
  case=copy.deepcopy(positive);case[field]=value;errors=list(v.iter_errors(case));record(op+'/reject/'+field+'/'+keyword,any(e.validator==keyword and field in e.path for e in errors),actualKeywords=[e.validator for e in errors])
 if op=='secret.value.read':
  case=copy.deepcopy(positive);case['query']={'versionId':id_};record(op+'/history-positive',not list(v.iter_errors(case)))
  case['query']['versionId']=id_.upper();record(op+'/history-uppercase',any(e.validator=='pattern'for e in v.iter_errors(case)))
 decode=(lambda path,query:decode_metadata_read('GET',path,query,None))if op=='secret.metadata.read'else(lambda path,query:decode_http_value_read('GET',path,query,None))
 record(op+'/http-positive',decode({'id':id_},b'')['secretId']==id_)
 for label,path,query,code in [('uppercase',{'id':id_.upper()},b'', 'SECRET_METADATA_READ_PATH_INVALID'if op=='secret.metadata.read'else'SECRET_VALUE_READ_PATH_INVALID'),('query',{'id':id_},b'unknown=x','SECRET_METADATA_READ_QUERY_NOT_ALLOWED'if op=='secret.metadata.read'else'SECRET_VALUE_READ_QUERY_UNKNOWN')]:
  try:decode(path,query);actual='ACCEPTED'
  except ValueError as exc:actual=str(exc)
  record(op+'/http-reject/'+label,actual==code,actualDiagnostic=actual)
q={'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'status':'PASS'if all(c['status']=='PASS'for c in checks)else'BLOCKED','checked':len(checks),'failed':sum(c['status']!='PASS'for c in checks),'checks':checks,'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Only current native request masks and actual GET decoding; whole read producers/event/errors/implementation not closed'}
Path(__file__).with_name('read-route-projection-tests.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:q[k]for k in ['status','checked','failed']}));raise SystemExit(q['failed']!=0)
