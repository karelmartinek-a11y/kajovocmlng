import sys,json,copy,hashlib
from pathlib import Path
O=Path(__file__).parent;ROOT=Path('/workspace/kajovocmlng');sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(O))
# Actual canonical PG/auth/crypto/root witness produced in own20-case chain.
import verify_owner_value_read as witness
sys.path.insert(0,str(O))
from secret_metadata_status_read import decode_metadata_read,hydrate_owner_metadata,hydrate_status_ui
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
from ssot_sources import SSOT,resource_index
s=json.loads((O/'secret-metadata-read.schema.json').read_bytes());cases=[]
def ok(label):cases.append({'id':label,'status':'PASS'})
def check(which,value):Draft202012Validator({'$schema':s['$schema'],**s[which]},format_checker=FormatChecker()).validate(value)
native=decode_metadata_read('GET',{'id':witness.target},b'',b'');check('request',native);check('response',witness.md);ok('actual-root-detail-all-existing-physical-fields-exact-schema')
check('response',witness.md_inactive);check('response',witness.md_deleted);ok('actual-INACTIVE-ACTIVE-DELETED-preserved-root-metadata-vocab')
for label,args,code in [('unknown-query',('GET',{'id':witness.target},b'status=ACTIVE',b''),'SECRET_METADATA_READ_QUERY_NOT_ALLOWED'),('status-body',('GET',{'id':witness.target},b'',b'{"status":"ACTIVE"}'),'SECRET_METADATA_READ_BODY_NOT_ALLOWED'),('caller-owner',('GET',{'id':witness.target,'ownerId':witness.owner},b'',b''),'SECRET_METADATA_READ_PATH_INVALID')]:
 try:decode_metadata_read(*args);raise AssertionError(label+' accepted')
 except ValueError as e:assert str(e)==code;ok(label);cases[-1]['diagnostic']=code
for label,snapshot,headers,code in [('status-ACTIVE-does-not-authorize-wrong-bearer',witness.snapshot,[('Authorization',b'Bearer WRONG')],'OWNER_API_AUTHENTICATION_FAILED'),('root-status-projection-mismatch',{**witness.snapshot,'recordMetadata':{**witness.snapshot['recordMetadata'],'status':'DELETED'}},witness.headers,'SECRET_METADATA_STATUS_BINDING_MISMATCH'),('integrity-diagnostic-not-INACTIVE',{**witness.snapshot,'diagnostic':'SECRET_STATUS_POINTER_NOT_ACTIVE'},witness.headers,'SECRET_STATUS_POINTER_NOT_ACTIVE')]:
 try:hydrate_owner_metadata(snapshot,headers,1024);raise AssertionError(label+' accepted')
 except ValueError as e:assert str(e)==code;ok(label);cases[-1]['diagnostic']=code
for label,metadata,value,code in [('different-root', {**witness.md,'id':witness.sid},witness.response,'SECRET_UI_STATUS_SNAPSHOT_MISMATCH'),('stale-root-state',{**witness.md,'state_version':'999'},witness.response,'SECRET_UI_STATUS_SNAPSHOT_MISMATCH'),('wrong-derived-status',{**witness.md,'status':'INACTIVE'},witness.response,'SECRET_UI_STATUS_SNAPSHOT_MISMATCH'),('DELETED-value',{**witness.md,'status':'DELETED'},witness.response,'SECRET_UI_DELETED_VALUE_FORBIDDEN')]:
 try:hydrate_status_ui(metadata,value);raise AssertionError(label+' accepted')
 except ValueError as e:assert str(e)==code;ok(label);cases[-1]['diagnostic']=code
bad={**witness.md,'status':'CREATED'}
try:check('response',bad);raise AssertionError('version-lifecycle substituted for root status')
except ValidationError:ok('metadata-mask-refuses-version-lifecycle-CREATED')
for label,field,value in [('overflow-state','state_version','9223372036854775808'),('noncanonical-state','state_version','00'),('negative-epoch','secret_activation_epoch','-1')]:
 bad={**witness.md,field:value}
 try:check('response',bad);raise AssertionError(label+' accepted')
 except ValidationError:ok(label)
r=resource_index();report={'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'consumedInputDigests':{p:r[p]['sha256']for p in ['database/secret-profile-roots.sql','database/secret-record-status.sql','database/secret-owner-api-value-read.sql','contracts/secrets/root-status.schema.json']},'checked':len(cases),'failed':0,'cases':cases,'actualParentChainChecks':20,'syntheticValuesOnly':True,'plaintextInReport':False,'wholeUIClosed':False,'globalAudit':'OPEN','implementationAcceptance':'NOT_EVALUATED'}
(O/'metadata-status-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'metadata/UI status PASS')
