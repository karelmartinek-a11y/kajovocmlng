from pathlib import Path
import sys,json,hashlib,copy
HERE=Path(__file__).parent;PARENT=HERE.parent;ROOT=Path('/workspace/kajovocmlng');sys.path[:0]=[str(PARENT),str(ROOT/'scripts')]
import verify_metadata_status as author
w=author.witness
from jsonschema import Draft202012Validator,FormatChecker
from secret_metadata_status_read import decode_metadata_read
from ssot_sources import SSOT,resource_index
source=SSOT.read_bytes();original=json.loads((PARENT/'secret-metadata-read.schema.json').read_bytes());fixed=json.loads((HERE/'secret-metadata-read.schema.json').read_bytes());checks=[]
def errors(schema,kind,value):return list(Draft202012Validator(schema[kind],format_checker=FormatChecker()).iter_errors(value))
def rec(label,passed,diagnostic=None):checks.append({'id':label,'status':'PASS'if passed else'FAIL','diagnostic':diagnostic})
lower='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';upper=lower.upper();valid=decode_metadata_read('GET',{'id':lower},b'',b'');rec('canonical-lowercase-positive-both-masks-native',not errors(original,'request',valid)and not errors(fixed,'request',valid))
invalid={**valid,'secretId':upper};rec('original-mask-reproducibly-accepts-noncanonical-uppercase',not errors(original,'request',invalid))
try:decode_metadata_read('GET',{'id':upper},b'',b'');rec('native-rejects-same-original-mask-witness',False)
except ValueError as e:rec('native-rejects-same-original-mask-witness',str(e)=='SECRET_METADATA_READ_PATH_INVALID',str(e))
rec('patched-mask-rejects-exact-uppercase-violation',bool(errors(fixed,'request',invalid)))
for name,metadata in [('ACTIVE',w.md),('INACTIVE',w.md_inactive),('DELETED',w.md_deleted)]:rec('actual-authenticated-PG-'+name+'-metadata-preserved-by-mask',not errors(fixed,'response',metadata))
for field,s in fixed['response']['properties'].items():
 if s.get('format')!='uuid'and not any(x.get('format')=='uuid'for x in s.get('anyOf',[])):continue
 good={**w.md,field:lower};bad={**good,field:upper};rec('canonical-response-UUID-'+field,not errors(fixed,'response',good));rec('reject-noncanonical-response-UUID-'+field,bool(errors(fixed,'response',bad)))
 if (isinstance(s.get('type'),list)and'null'in s['type'])or any(x.get('type')=='null'for x in s.get('anyOf',[])):rec('preserve-nullability-'+field,not errors(fixed,'response',{**w.md,field:None}))
report={'status':'PASS'if all(x['status']=='PASS'for x in checks)else'BLOCKED','checked':len(checks),'failed':sum(x['status']!='PASS'for x in checks),'checks':checks,'sourceSha256':hashlib.sha256(source).hexdigest(),'sourceUnchanged':source==SSOT.read_bytes(),'originalSchemaSha256':hashlib.sha256((PARENT/'secret-metadata-read.schema.json').read_bytes()).hexdigest(),'fixedSchemaSha256':hashlib.sha256((HERE/'secret-metadata-read.schema.json').read_bytes()).hexdigest(),'nativeHelperSha256':hashlib.sha256((PARENT/'secret_metadata_status_read.py').read_bytes()).hexdigest(),'authorActualOwnerPGChecks':20,'postgresVersion':w.run('SHOW server_version').stdout.strip(),'wholeOperationClosed':False,'implementationAcceptance':'NOT_EVALUATED'}
(HERE/'metadata-mask-fix-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}))
