import sys,json,copy,hashlib,base64,subprocess,re
from pathlib import Path
from urllib.parse import urlencode
ROOT=Path('/workspace/kajovocmlng');sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
from core_audit_reference import *
from generation_auth_crypto import canonical
R=resource_index();cases=[]
def good(n,fn):fn();cases.append({'id':n,'status':'PASS'})
def bad(n,fn,code):
 try:fn()
 except AuditError as e:
  assert str(e)==code,(n,str(e),code)
 else:raise AssertionError(n+' accepted')
 cases.append({'id':n,'status':'PASS','specificDiagnostic':code,'positiveDerived':True})
u=lambda n:'00000000-0000-4000-8000-'+str(n).zfill(12)
query={'recordKinds':'EVENT','from':'2026-10-01T00:00:00Z','to':'2026-10-02T00:00:00Z','direction':'ANY','result':'ANY','sort':'TIME_ASC','limit':'200'}
wire=urlencode(query).encode();native=decode('audit.event.list','/audit/events',wire)
good('core200-positive-all-native-required-fields',lambda:valid('CoreQuery',native,'FAIL'))
good('single-read-exact-ID-positive',lambda:decode('audit.event.read','/audit/events/'+u(1),b''))
for n,q,code in [('unknown-query',wire+b'&authorized=true','AUDIT_QUERY_UNKNOWN_PARAMETER'),('duplicate-limit',wire+b'&limit=200','AUDIT_QUERY_DUPLICATE_PARAMETER'),('duplicate-kind',wire+b'&recordKinds=EVENT','AUDIT_QUERY_DUPLICATE_RECORD_KIND'),('bad-percent',wire+b'&cursor=%GG','AUDIT_QUERY_ENCODING_INVALID'),('bad-UTF8',wire+b'&cursor=%ff','AUDIT_QUERY_ENCODING_INVALID')]:bad(n,lambda q=q:decode('audit.event.list','/audit/events',q),code)
for n,change,code in [('limit201',{'limit':'201'},'AUDIT_QUERY_INVALID'),('limit0',{'limit':'0'},'AUDIT_QUERY_INVALID'),('wrong-kind',{'recordKinds':'READY'},'AUDIT_QUERY_INVALID'),('invalid-sort',{'sort':'NEWEST'},'AUDIT_QUERY_INVALID'),('backward-interval',{'from':query['to']},'AUDIT_QUERY_INTERVAL_INVALID')]:bad(n,lambda change=change:decode('audit.event.list','/audit/events',urlencode({**query,**change}).encode()),code)
bad('read-no-query',lambda:decode('audit.event.read','/audit/events/'+u(1),b'versionId=x'),'AUDIT_QUERY_UNKNOWN_PARAMETER')
bad('GET-no-JSON-body',lambda:decode('audit.event.list','/audit/events',wire,b'{}'),'AUDIT_TRANSPORT_INVALID')
bad('missing-required-sort',lambda:decode('audit.event.list','/audit/events',urlencode({k:v for k,v in query.items() if k!='sort'}).encode()),'AUDIT_QUERY_REQUIRED_PARAMETER')
audit={'logicalOperationId':u(2),'eventId':u(3),'objectId':u(4),'actorId':u(5),'beforeDigest':None,'afterDigest':'sha256:'+'11'*32,'correlationId':u(6),'causationId':None,'traceId':u(6),'occurredAt':'2026-10-01T01:00:00.000001Z','chainSequence':'1','previousHash':'sha256:'+'00'*32}
# Exact existing secret_command_chain canonical JSON encoding, no live credential.
ab=canonical(audit);pb=b'{"secretId":"'+u(4).encode()+b'","status":"INACTIVE"}'
row={'recordKind':'DOMAIN_EVENT_AUDIT','auditId':u(1),'chainSequence':'1','previousHash':audit['previousHash'],'eventHash':'sha256:'+framed_hash(1,b'\0'*32,1,ab).hex(),'chainFormatVersion':1,'canonicalAuditBytesBase64':base64.b64encode(ab).decode(),'logicalOperationId':u(2),'actorId':u(5),'domainEventId':u(3),'aggregateId':u(4),'aggregateKind':'SECRET','eventType':'SECRET_CREATED','eventSchemaId':'urn:synthetic:secret-created:1','eventSchemaDigest':'sha256:'+'22'*32,'eventPayloadBytesBase64':base64.b64encode(pb).decode(),'eventPayloadDigest':'sha256:'+hashlib.sha256(pb).hexdigest(),'correlationId':u(6),'causationId':None,'occurredAt':'2026-10-01T01:00:00.000001Z','archiveRequired':False}
good('typed-physical-byte-inspection-positive',lambda:inspect(row,u(1)))
good('named-existing-producer-audit-JSON-binding-positive',lambda:exact_secret_audit_projection(row))
assert inspect(row)['verifiedCanonicalAuditBytes']==ab and inspect(row)['verifiedEventPayloadBytes']==pb
assert inspect(row)['businessPayloadHydrated'] is False
def mutation(name,field,value,code):
 changed=copy.deepcopy(row);changed[field]=value;bad(name,lambda:inspect(changed,u(1)),code)
mutation('wrong-requested-identity','auditId',u(7),'AUDIT_RECORD_IDENTITY_MISMATCH')
mutation('chain-sequence-change','chainSequence','2','AUDIT_CHAIN_HASH_MISMATCH')
mutation('chain-prev-change','previousHash','sha256:'+'01'*32,'AUDIT_CHAIN_HASH_MISMATCH')
mutation('audit-byte-corruption','canonicalAuditBytesBase64',base64.b64encode(ab+b' ').decode(),'AUDIT_CHAIN_HASH_MISMATCH')
mutation('payload-byte-corruption','eventPayloadBytesBase64',base64.b64encode(pb+b' ').decode(),'AUDIT_EVENT_PAYLOAD_DIGEST_MISMATCH')
mutation('invalid-base64','eventPayloadBytesBase64','%','AUDIT_BYTE_ENCODING_INVALID')
mutation('null-audit-id','auditId',None,'AUDIT_RECORD_MASK_INVALID')
mutation('wrong-sequence-type','chainSequence',1,'AUDIT_RECORD_MASK_INVALID')
mutation('positive-chain-sequence-cannot-be-zero','chainSequence','0','AUDIT_RECORD_MASK_INVALID')
mutation('int64-overflow','chainSequence','9223372036854775808','AUDIT_RECORD_MASK_INVALID')
extra={**row,'authorized':True};bad('no-caller-authority-slot',lambda:inspect(extra),'AUDIT_RECORD_MASK_INVALID')
missing={k:v for k,v in row.items() if k!='eventHash'};bad('missing-required-event-hash',lambda:inspect(missing),'AUDIT_RECORD_MASK_INVALID')
def rehash(data):return {**row,'canonicalAuditBytesBase64':base64.b64encode(data).decode(),'eventHash':'sha256:'+framed_hash(1,b'\0'*32,1,data).hex()}
# These are the actual current native JSON parser boundary, not forbidden GET body.
bad('valid-chain-duplicate-canonical-key',lambda:exact_secret_audit_projection(rehash(ab[:-1]+b',"eventId":"'+u(3).encode()+b'"}')),'AUDIT_CANONICAL_DUPLICATE_KEY')
bad('valid-chain-invalid-JSON-UTF8',lambda:exact_secret_audit_projection(rehash(b'\xff')),'AUDIT_CANONICAL_JSON_INVALID')
bad('valid-chain-invalid-JSON-syntax',lambda:exact_secret_audit_projection(rehash(ab[:-1])),'AUDIT_CANONICAL_JSON_INVALID')
wrong={**audit,'eventId':u(8)};bad('valid-chain-wrong-inner-event-identity',lambda:exact_secret_audit_projection(rehash(json.dumps(wrong).encode())),'AUDIT_CANONICAL_ROW_BINDING_MISMATCH')
# Actual canonical PG18.6 hash function bytes, isolated own fixture database.
PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-U','agent','-v','ON_ERROR_STOP=1','-At']
def sql(query,db='core_audit_read_84c',check=True):
 p=subprocess.run(PSQL+['-d',db],input=query,text=True,capture_output=True)
 if check and p.returncode:raise RuntimeError(p.stderr)
 return p
sql('DROP DATABASE IF EXISTS core_audit_read_84c;','postgres');sql('CREATE DATABASE core_audit_read_84c;','postgres')
src=R['database/generation-create-foundations.sql']['raw'].decode();fn=re.search(r'CREATE FUNCTION kcml_audit_hash_v1\(.*?END; \$\$;',src,re.S).group()
(O/'canonical-audit-hash.sql').write_text(fn+'\n');sql(fn)
version=sql('SHOW server_version;').stdout.strip();assert version=='18.6',version
pg=sql("SELECT encode(kcml_audit_hash_v1(1,decode('"+'00'*32+"','hex'),1,decode('"+ab.hex()+"','hex')),'hex');").stdout.strip()
assert pg==row['eventHash'][7:];cases.append({'id':'actual-PG18.6-canonical-framed-hash-native-equivalence','status':'PASS'})
for label,fragment in [('invalid-version',"2,decode('"+'00'*32+"','hex'),1,decode('"+ab.hex()+"','hex')"),('invalid-prev',"1,decode('00','hex'),1,decode('"+ab.hex()+"','hex')"),('invalid-sequence',"1,decode('"+'00'*32+"','hex'),0,decode('"+ab.hex()+"','hex')")]:
 p=sql('SELECT kcml_audit_hash_v1('+fragment+');',check=False);assert p.returncode and 'AUDIT_HASH_INPUT_INVALID' in p.stderr
 cases.append({'id':'actual-PG-'+label,'status':'PASS','specificDiagnostic':'AUDIT_HASH_INPUT_INVALID','positiveDerived':True})
complete={'resolvedInterval':{'from':native['from'],'to':native['to']},'items':[row],'nextCursor':None,'snapshotWatermark':'synthetic-watermark-mask-fixture','coverageFrom':native['from'],'coverageTo':native['to'],'completeness':'COMPLETE','missingSources':[],'provenanceRefs':['synthetic-native-fixture:not-producer-proof']}
good('exact-core-result-mask-positive-not-coverage-proof',lambda:validate_core_result(native,complete))
bad('complete-cannot-declare-missing-sources',lambda:validate_core_result(native,{**complete,'missingSources':['synthetic-gap']}),'AUDIT_RESULT_MASK_INVALID')
bad('result-interval-wrong-query-binding',lambda:validate_core_result(native,{**complete,'resolvedInterval':{'from':native['from'],'to':'2026-10-03T00:00:00Z'}}),'AUDIT_RESULT_INTERVAL_BINDING_MISMATCH')
bad('duplicate-result-domain-item',lambda:validate_core_result(native,{**complete,'items':[row,row]}),'AUDIT_RESULT_DUPLICATE_AUDIT_ID')
bad('result-exceeds-actual-request-page-limit',lambda:validate_core_result({**native,'limit':1},{**complete,'items':[row,row]}),'AUDIT_RESULT_PAGE_LIMIT_MISMATCH')
from author_core_audit import updates
first=updates(R);virtual=dict(R);virtual['contracts/payload-contracts.json']={**R['contracts/payload-contracts.json'],'raw':first['contracts/payload-contracts.json']}
assert updates(virtual)==first;cases.append({'id':'reusable-authoring-hook-idempotent-current-source','status':'PASS'})
report={'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'consumedInputs':{k:R[k]['sha256'] for k in ['database/generation-create-foundations.sql','ui/contracts/live-experience.json','contracts/payload-contracts.json']},'consumedScriptDigests':{k:hashlib.sha256((ROOT/k).read_bytes()).hexdigest() for k in ['scripts/secret_command_chain.py','scripts/generation_auth_crypto.py']},'checked':len(cases),'failed':0,'cases':cases,'postgresVersion':version,'canonicalFunctionSha256':hashlib.sha256(fn.encode()).hexdigest(),'scope':'CORE200 HTTP decoder and exact immutable physical audit-byte inspection; native JSON profile only current Secret producer. Actual PostgreSQL canonical hash, not full authenticated read producer or access-audit commit.','wholeOperationsClosed':0,'implementationAcceptance':'NOT_EVALUATED'}
(O/'core-audit-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'PASS; PostgreSQL',version,'actual canonical hash; full producer not claimed')
