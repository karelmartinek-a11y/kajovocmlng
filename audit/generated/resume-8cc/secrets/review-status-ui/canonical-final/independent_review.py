from pathlib import Path
import sys,json,hashlib,subprocess,uuid,copy
OUT=Path(__file__).parent;ROOT=Path('/workspace/kajovocmlng');sys.path[:0]=[str(OUT),str(ROOT/'scripts')]
import verify_metadata_status as author
w=author.witness
from secret_metadata_status_read import hydrate_owner_metadata,hydrate_status_ui
from secret_value_read_transport import reveal_response
from secret_owner_value_read import open_owner_value
from ssot_sources import SSOT,resource_index
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
source=SSOT.read_bytes();resources=resource_index();checks=[]
def record(label,passed,diagnostic=None):checks.append({'id':label,'status':'PASS'if passed else'FAIL','diagnostic':diagnostic})
validator=Draft202012Validator(json.loads((OUT/'secret-metadata-read.schema.json').read_bytes())['response'],format_checker=FormatChecker())
conn=subprocess.Popen(w.P+['-d',w.DB],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
def tx(sql):
 conn.stdin.write(sql.rstrip().rstrip(';')+';\n\\echo REVIEW_END\n');conn.stdin.flush();lines=[]
 while True:
  line=conn.stdout.readline()
  if not line:raise RuntimeError('Independent transaction terminated: '+conn.stderr.read())
  if line.strip()=='REVIEW_END':return lines
  lines.append(line.strip())
def snapshot(target,version=None):
 lines=tx('BEGIN;SELECT kcml_secret_v1.owner_api_value_read_begin_v1('+w.lit(target)+','+('NULL'if version is None else w.lit(version))+');')
 return json.loads(next(x for x in lines if x.startswith('{')))
headers=[('Authorization',b'Bearer '+w.token2)]
# Independent actual metadata roots include both formerly omitted simple types.
for kind in ['BEARER_TOKEN','WEBHOOK_SECRET']:
 root=str(uuid.uuid4());q=w.run("INSERT INTO kcml_secret_v1.secret_record(id,stable_name,display_name,secret_type,state_version,secret_activation_epoch,created_at,updated_at)VALUES("+w.lit(root)+','+w.lit('PEER_'+kind)+",'Synthetic peer',"+w.lit(kind)+',0,0,now(),now());');assert q.returncode==0,q.stderr
 s=snapshot(root);md=hydrate_owner_metadata(s,headers,1024);validator.validate(md)
 record('actual-canonical-INACTIVE-'+kind+'-root-and-mask',md['secret_type']==kind and md['status']=='INACTIVE');tx('ROLLBACK')
# The actual bigint maximum survives PG -> JSON integer -> native decimal -> UI.
q=w.run('UPDATE kcml_secret_v1.secret_record SET state_version=9223372036854775807,secret_activation_epoch=9223372036854775807 WHERE id='+w.lit(w.target));assert q.returncode==0,q.stderr
s=snapshot(w.target);md=hydrate_owner_metadata(s,headers,1024);validator.validate(md);raw=open_owner_value(s,headers,1024,w.base.key,w.base.KEYID);value=reveal_response(s,raw)
record('actual-PG-int64-max-to-native-metadata-and-value',md['state_version']=='9223372036854775807'and md['secret_activation_epoch']=='9223372036854775807'and value['recordStateVersion']==md['state_version'])
ui=hydrate_status_ui(md,value);record('actual-same-root-same-int64-state-UI-feed',ui['recordStateVersion']==md['state_version']);tx('ROLLBACK')
try:hydrate_status_ui(w.md,value);record('real-stale-metadata-same-root-new-value-rejected',False)
except ValueError as e:record('real-stale-metadata-same-root-new-value-rejected',str(e)=='SECRET_UI_STATUS_SNAPSHOT_MISMATCH',str(e))
q=w.run('UPDATE kcml_secret_v1.secret_record SET state_version=9223372036854775808 WHERE id='+w.lit(w.target));record('actual-PG-int64-overflow-rejected',q.returncode!=0 and 'bigint out of range'in q.stderr,'bigint out of range'if 'bigint out of range'in q.stderr else q.stderr[:160])
for value_bad in [True,-1,9223372036854775808,'1']:
 bad=copy.deepcopy(s);bad['recordMetadata']['state_version']=value_bad
 try:hydrate_owner_metadata(bad,headers,1024);record('native-counter-type-range-'+repr(value_bad),False)
 except ValueError as e:record('native-counter-type-range-'+repr(value_bad),str(e)=='SECRET_METADATA_COUNTER_INVALID',str(e))
# Authentic ACTIVE metadata is not request authority; token verification is first.
try:hydrate_owner_metadata(s,[('Authorization',b'Bearer WRONG')],1024);record('actual-positive-snapshot-wrong-token-is-auth-failure',False)
except ValueError as e:record('actual-positive-snapshot-wrong-token-is-auth-failure',str(e)=='OWNER_API_AUTHENTICATION_FAILED',str(e))
# Reproduce live DELETED denial without publishing a new allowed deletion API.
deleted_lines=tx('BEGIN;UPDATE kcml_secret_v1.secret_record SET deleted_at=now()WHERE id='+w.lit(w.target)+';SELECT kcml_secret_v1.owner_api_value_read_begin_v1('+w.lit(w.target)+','+w.lit(w.base.ids['version'])+');');fresh_deleted=json.loads(next(x for x in deleted_lines if x.startswith('{')))
# Use exact author's valid deleted snapshot, from the same actual source contract.
try:open_owner_value(fresh_deleted,headers,1024,w.base.key,w.base.KEYID);record('actual-DELETED-historical-value-denied',False)
except ValueError as e:record('actual-DELETED-historical-value-denied',str(e)=='SECRET_OWNER_VALUE_REFERENCE_UNAVAILABLE',str(e))
md_deleted=hydrate_owner_metadata(fresh_deleted,headers,1024);record('DELETED-metadata-available-without-value',hydrate_status_ui(md_deleted)['valueRevealed']is False);tx('ROLLBACK')
record('actual-INACTIVE-history-no-activation',w.inactive['recordStatus']=='INACTIVE'if 'recordStatus'in w.inactive else w.inactive['recordMetadata']['status']=='INACTIVE')
# Existing registry shape and page identity support readonly append, not create input.
ui_registry=json.loads(resources['ui/contracts/ui-control-registry.json']['raw']);proposal=json.loads((OUT/'ui-status-proposal.json').read_bytes());f=proposal['value']
record('UI-page13-is-secrets-and-status-not-editable',ui_registry['pages'][13]['id']=='secrets'and all(x.get('type')=='readonly'and x.get('source')=='SERVER_PROJECTION'and x.get('required')is False for x in ui_registry['pages'][13]['fields']if x['id']=='secret.status'))
record('UI-field-readonly-server-projection-not-required-create',f['type']=='readonly'and f['editableWhen']=='NEVER'and f['source']=='SERVER_PROJECTION'and f['required']is False)
record('UI-readonly-shape-has-existing-canonical-example',any(x.get('type')=='readonly'and x.get('inputProfile')==f['inputProfile']and x.get('source')==f['source']and x.get('required')is False for p in ui_registry['pages']for x in p['fields']))
text=SSOT.read_text();a=text.index('### 72.21');z=text.find('\n### ',a+1);record('UI-existing-value-version-binding-usage-panels-preserved',all(x in text[a:z]for x in ['Value/reveal area','Versions timeline','Bindings matrix','Usage graph']))
# Exact boundary review; do NOT invent a historical complete replay pipeline.
current=(ROOT/'scripts/secret_command_chain.py').read_text();start=current.index('if claimed!=op:');end=current.index("q(db,'INSERT INTO domain_idempotency_record",start);replay=current[start:end]
record('current-create-replay-does-not-inject-new-recordStatus-field',"json.loads(rows[0][0])"in replay and 'recordStatus'not in replay)
record('metadata-UI-helper-does-not-touch-create-receipts',all('create_completion'not in (OUT/p).read_text()and 'output_receipt_bytes'not in (OUT/p).read_text()for p in ['secret_metadata_status_read.py','secret_value_read_transport.py']))
conn.stdin.close();assert conn.wait(timeout=5)==0
canonical_equal={}
for filename,resource in [('secret-owner-api-value-read.sql','database/secret-owner-api-value-read.sql'),('secret-value-read.schema.json','contracts/secrets/owner-value-read.schema.json'),('secret-metadata-read.schema.json','contracts/secrets/metadata-read.schema.json')]:
 canonical_equal[resource]=(OUT/filename).read_bytes()==resources[resource]['raw']
 record('canonical-resource-byte-equality-'+filename,canonical_equal[resource])
for filename in ['secret_metadata_status_read.py','secret_value_read_transport.py']:
 canonical_equal['scripts/'+filename]=(OUT/filename).read_bytes()==(ROOT/'scripts'/filename).read_bytes()
 record('canonical-helper-byte-equality-'+filename,canonical_equal['scripts/'+filename])
bindings=json.loads((OUT/'copied-source-bindings.json').read_text())
unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest for p,digest in bindings['authorSources'].items())
report={'status':'PASS'if all(x['status']=='PASS'for x in checks)else'BLOCKED','checked':len(checks),'failed':sum(x['status']!='PASS'for x in checks),'checks':checks,'sourceSha256':hashlib.sha256(source).hexdigest(),'sourceUnchanged':source==SSOT.read_bytes(),'authorSourcesUnchangedDuringReview':unchanged,'canonicalByteEquality':canonical_equal,'authorReproductions':{'broker':29,'ownerRead':20,'metadataUI':16},'copiedBindingsSha256':hashlib.sha256((OUT/'copied-source-bindings.json').read_bytes()).hexdigest(),'postgresVersion':w.run('SHOW server_version').stdout.strip(),'oldReceiptCoverage':'Structural current replay and readonly-consumer boundary only. Historical frozen-schema/archive/replay pipeline NOT_EVALUATED; no invented fixture pipeline.','wholeOperationClosed':False,'implementationAcceptance':'NOT_EVALUATED'}
(OUT/'independent-status-ui-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}))
