import json,hashlib,sys,subprocess,os,copy,base64
from pathlib import Path
ROOT=Path('/workspace/kajovocmlng');BASE=ROOT/'audit/generated/closure-replan-84c';OUT=Path(__file__).parent;PIN='116e2e50b80b29b957be97a7d89b0b6df959a13fc68e87d6260198e612768bb0'
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resources,resource_index
from jsonschema import Draft202012Validator,FormatChecker
from referencing import Registry,Resource
from referencing.jsonschema import DRAFT202012
from native_byte_format import install_native_byte_checker
sha=lambda raw:hashlib.sha256(raw).hexdigest();read=lambda p:json.loads(p.read_text());checks=[];files={};consumed={}
def file(path):
 p=ROOT/path;files[path]=sha(p.read_bytes());return read(p)
def check(name,value,details=None):
 checks.append({'id':name,'status':'PASS' if value else 'FAIL','details':details})
def mutation(obj,path,value=None,remove=False):
 out=copy.deepcopy(obj);node=out
 for key in path[:-1]:node=node[key]
 if remove:del node[path[-1]]
 else:node[path[-1]]=value
 return out
source=SSOT.read_bytes();check('current-source-pin',sha(source)==PIN,sha(source));rs=resource_index(list(resources(source.decode())));consumed['00_SSOT/KajovoCMLNG_SSOT.md']=sha(source)
def resource(path):
 consumed[path]=rs[path]['sha256'];return json.loads(rs[path]['raw'])
cat=resource('contracts/operation-contracts.json');payload=resource('contracts/payload-contracts.json');rows={r['operationId']:r for r in payload['records']}
checker=install_native_byte_checker();files['scripts/native_byte_format.py']=sha((ROOT/'scripts/native_byte_format.py').read_bytes())
for val,expect in [('',True),('AAE=',True),('YWJj',True),('%%%',False),('a',False),('AA E=',False),('é',False)]:check('actual-byte-checker.'+repr(val),checker.conforms(val,'byte')==expect)
native=cat['$defs']['mcp.native.2026-07-28'];registry=Registry().with_resource('urn:kcml:mcp-native:2026-07-28',Resource.from_contents(native,default_specification=DRAFT202012));aliases={k:s for k,s in cat['$defs'].items()if k in ['mcp.prompts.get:command','mcp.prompts.get:response','mcp.resources.read:command','mcp.resources.read:response']}
for key,s in aliases.items():registry=registry.with_resource(s['$id'],Resource.from_contents(s))
check('canonical-exact-four-native-aliases',len(aliases)==4)
meta={'io.modelcontextprotocol/protocolVersion':'2026-07-28','io.modelcontextprotocol/clientCapabilities':{}}
for op,method,key,target,result in [('mcp.prompts.get','prompts/get','name','synthetic-prompt',{'resultType':'complete','messages':[{'role':'user','content':{'type':'text','text':'synthetic'}}]}),('mcp.resources.read','resources/read','uri','fixture://resource',{'resultType':'complete','contents':[{'uri':'fixture://resource','blob':'AAE=','mimeType':'application/octet-stream'}],'ttlMs':0,'cacheScope':'private'})]:
 rv=Draft202012Validator(aliases[op+':command'],registry=registry,format_checker=checker);sv=Draft202012Validator(aliases[op+':response'],registry=registry,format_checker=checker)
 req={'jsonrpc':'2.0','id':23,'method':method,'params':{'_meta':meta,key:target}};response={'jsonrpc':'2.0','id':23,'result':result};mrtr={'jsonrpc':'2.0','id':23,'result':{'resultType':'input_required','requestState':'synthetic-opaque-state'}}
 for label,v,o in [('request',rv,req),('complete-no-meta',sv,response),('mrtr-no-meta',sv,mrtr)]:check(op+'.positive.'+label,v.is_valid(o))
 for label,v,obj,path,value,remove in [('missing-target',rv,req,['params',key],None,True),('missing-request-meta',rv,req,['params','_meta'],None,True),('unknown-param',rv,req,['params','x'],True,False),('invalid-present-complete-meta',sv,response,['result','_meta'],None,False),('invalid-present-mrtr-meta',sv,mrtr,['result','_meta'],7,False),('task-forbidden',sv,response,['result','resultType'],'task',False),('mrtr-no-state',sv,mrtr,['result','requestState'],None,True)]:check(op+'.negative.'+label,not v.is_valid(mutation(obj,path,value,remove)))
 if op=='mcp.resources.read':
  for value in ['%%%','AA E=','a']:check('resource.actual-blob-reject.'+repr(value),not sv.is_valid(mutation(response,['result','contents',0,'blob'],value)))
# Compare canonical selected masks to independently reviewed owned source, no assumptions about whole operation completion.
owner=resource('contracts/owner-session-family.json');review=file('audit/generated/closure-replan-84c/secret/session-review/final-integrated/DELIVERY.json');check('owner-exact-reviewed-profile',rs['contracts/owner-session-family.json']['sha256']==review['exactCanonicalProfileSha256'])
for op in owner['operations']:
 for boundary in ['requestSchema','responseSchema','eventSchema']:check('owner.canonical.'+op['operationId']+'.'+boundary,rows[op['operationId']][boundary]==op[boundary])
audit=file('audit/generated/closure-replan-84c/family-read/core-audit/authorable-core-delta.json');audit_schema=file('audit/generated/closure-replan-84c/family-read/core-audit/core-audit-read.schema.json');check('audit-exact-owned-native-schema',resource('contracts/audit/core-read.schema.json')==audit_schema)
for p in audit['patches']:
 for k,value in p['replace'].items():
  if k in ['requestSchema','responseSchema']:check('audit.canonical.'+p['operationId']+'.'+k,rows[p['operationId']][k]==value)
# Genuine PostgreSQL proofs remain historical executions. Verify their exact SQL/ACL/driver consumption, do not rerun or rehash their execution source as current.
sql=file('audit/generated/closure-replan-84c/sql/DELIVERY.json');proof=file('audit/generated/closure-replan-84c/sql/owner-query-postgres-proof.json');peer=file('audit/generated/closure-replan-84c/authority/sql-review/final/owner-query-independent-proof.json');family=file('audit/generated/closure-replan-84c/sql/owner-query-family.json');calls=file('audit/generated/closure-replan-84c/sql/operation-helper-callsite-registry.json')
check('actual-PG-proof10',proof['status']=='PASS' and proof['passed']==10 and str(proof['postgresqlVersion']).startswith('18.6'))
check('independent-PG-proof9',peer['failed']==0 and peer['passed']==9 and str(peer['postgresVersion']).startswith('18.6'))
for path,local in sql['canonicalResourceProposal'].items():
 owned=BASE/'sql'/local;consumed[path]=rs[path]['sha256'];files[str(owned.relative_to(ROOT))]=sha(owned.read_bytes());check('SQL-ACL-canonical-exact.'+path,rs[path]['raw']==owned.read_bytes());check('SQL-ACL-reviewed-digest.'+local,sha(owned.read_bytes())==peer['inputs'][local])
for name,h in peer['inputs'].items():
 p=BASE/'sql'/name;files[str(p.relative_to(ROOT))]=sha(p.read_bytes());check('PG-consumed-unchanged.'+name,sha(p.read_bytes())==h)
original=rs['database/operation-functions.sql'];consumed['database/operation-functions.sql']=original['sha256'];check('original-entire-wrapper-resource-unchanged-vs-84-source',original['sha256']==family['sourceResourceSha256'] and original['sha256']==calls['sourceResourceSha256'])
for op in family['family']:check('actual-original-wrapper-substring.'+op['operationId'],op['sourceSql'] in original['raw'].decode())
check('actual-tested-helperSQL-byte-binding',proof['helperSqlSha256']==sha((BASE/'sql/owner-query-helpers.sql').read_bytes()))
check('actual-tested-original-wrapper-byte-binding',proof['actualOriginalWrapperSha256']==sha((BASE/'sql/owner-query-original-wrappers.sql').read_bytes()))
# Real publication tools in read-only check mode twice; exact input hashes before/after prove no authoring.
commands=[['scripts/close_owner_session_family.py','--check'],['scripts/close_audit_read_family.py','--check'],['scripts/close_scoped_sql_helpers.py','--check'],['audit/generated/closure-replan-84c/references/author_native_read_refs.py','--check']]
watch=[SSOT]+list((ROOT/'01_UI_CONTRACT/contracts').rglob('*.json'))
before={str(p.relative_to(ROOT)):sha(p.read_bytes())for p in watch};runs=[];env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
for cmd in commands:
 files[cmd[0]]=sha((ROOT/cmd[0]).read_bytes());pair=[]
 for attempt in range(2):
  run=subprocess.run([sys.executable,*cmd],cwd=ROOT,env=env,capture_output=True,text=True,timeout=120);pair.append({'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
 check('publisher.readonly.'+cmd[0],all(r['returncode']==0 for r in pair),pair)
 check('publisher.idempotent-check.'+cmd[0],pair[0]==pair[1]);runs.append({'command':cmd,'attempts':pair})
after={str(p.relative_to(ROOT)):sha(p.read_bytes())for p in watch};check('read-only-source-projections-unchanged',before==after);check('source-still-pin',sha(SSOT.read_bytes())==PIN)
report={'status':'PASS_BOUNDED_INDEPENDENT_SCOPE'if all(c['status']=='PASS'for c in checks)else'FAIL_BOUNDED_INDEPENDENT_SCOPE','sourceSha256':PIN,'sourceStable':sha(SSOT.read_bytes())==PIN,'checks':checks,'passed':sum(c['status']=='PASS'for c in checks),'failed':sum(c['status']=='FAIL'for c in checks),'actualConsumedCanonicalResourceHashes':consumed,'consumedFileHashes':files,'publisherRuns':runs,'wholeOperationsClosed':0,'evidenceClass':'FRESH_CANONICAL_SCHEMA_REPRODUCTION_AND_PRIOR_ACTUAL_PG_BYTE_SCOPE_REVALIDATION','limitations':['No new PostgreSQL execution; historical10+9 proofs retain their original execution hashes','No trusted access registry publisher, atomic root/event pipeline, backend application or systemd invocation proof','Source equality supports reuse only in exact selected scopes; it is not semantic closure or readiness','Native raw wire metadata stays optional; platform completion producer remains a separate requirement'],'implementationAcceptance':'NOT_EVALUATED'}
(OUT/'independent-scope-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','passed','failed','sourceStable']}))
