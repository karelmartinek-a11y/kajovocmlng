"""Bounded encrypted snapshot/transaction DESIGN model; not PostgreSQL runtime."""
import copy,hashlib,json,sqlite3,uuid
from pathlib import Path
import cryptography
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
import pglast
from jsonschema import Draft202012Validator,FormatChecker
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'scripts'))
from ssot_sources import SSOT,resource_index,resources
OUT=Path(__file__).resolve().parent
raw=SSOT.read_bytes();source_hash=hashlib.sha256(raw).hexdigest();rs=resource_index(resources(raw.decode()))
row=next(r for r in json.loads(rs['contracts/payload-contracts.json']['raw'])['records'] if r['operationId']=='generation.job.create')
v=Draft202012Validator(row['requestSchema']['properties']['body'],format_checker=FormatChecker())
uid=lambda n:str(uuid.UUID(int=n));digest=lambda b:'sha256:'+hashlib.sha256(b).hexdigest()
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
class Rejection(Exception):pass
KEY=bytes(range(32));NONCE=bytes(range(12))
# AES-GCM is only the installed isolated referenceprovider, not a newly chosen
# canonical production algorithm. Normative profile selection remains BLOCKED.
BODY={'intent':'Create synthetic reference fixture','kind':'CREATE','credential':'SYNTHETIC_PRIVATE_CREDENTIAL_DO_NOT_PUBLISH'}
assert v.is_valid(BODY)
AAD=canonical({'jobId':uid(1),'snapshotId':uid(2),'schemaId':'urn:kcml:r9:semantic:route.0215:body'})
plain=canonical(BODY)
SNAPSHOT={'jobId':uid(1),'snapshotId':uid(2),'schemaId':'urn:kcml:r9:semantic:route.0215:body',
 'schemaDigest':digest(canonical(row['requestSchema']['properties']['body'])),'contentDigest':digest(plain),
 'ciphertext':AESGCM(KEY).encrypt(NONCE,plain,AAD),'nonce':NONCE,'aad':AAD}
def hydrate(snapshot):
 if snapshot['aad']!=canonical({key:snapshot[key] for key in ['jobId','snapshotId','schemaId']}):raise Rejection('INITIAL_REQUEST_IDENTITY_BINDING_MISMATCH')
 if snapshot['schemaDigest']!=SNAPSHOT['schemaDigest']:raise Rejection('INITIAL_REQUEST_SCHEMA_DIGEST_MISMATCH')
 try:data=AESGCM(KEY).decrypt(snapshot['nonce'],snapshot['ciphertext'],snapshot['aad'])
 except InvalidTag:raise Rejection('INITIAL_REQUEST_AUTHENTICATION_FAILED')
 if digest(data)!=snapshot['contentDigest']:raise Rejection('INITIAL_REQUEST_CONTENT_DIGEST_MISMATCH')
 value=json.loads(data)
 if list(v.iter_errors(value)):raise Rejection('INITIAL_REQUEST_TYPED_SCHEMA_INVALID')
 if canonical(value)!=data:raise Rejection('INITIAL_REQUEST_NONCANONICAL_BYTES')
 return value
checks=[]
def check(identity,condition):checks.append({'id':identity,'status':'PASS' if condition else 'FAIL'})
def reject(identity,value,reason):
 try:hydrate(value);actual=None
 except Rejection as exc:actual=str(exc)
 checks.append({'id':identity,'expectedDiagnostic':reason,'actualDiagnostic':actual,'positiveWitnessValid':hydrate(SNAPSHOT)==BODY,'status':'PASS' if actual==reason else 'FAIL'})
check('positive.typed-encrypted-hydration',hydrate(SNAPSHOT)==BODY)
check('positive.no-plaintext-in-ciphertext',BODY['credential'].encode() not in SNAPSHOT['ciphertext'])
for identity,key,value,reason in [
 ('wrong-schema','schemaDigest','sha256:'+'0'*64,'INITIAL_REQUEST_SCHEMA_DIGEST_MISMATCH'),
 ('wrong-content-digest','contentDigest','sha256:'+'0'*64,'INITIAL_REQUEST_CONTENT_DIGEST_MISMATCH'),
 ('wrong-ciphertext','ciphertext',SNAPSHOT['ciphertext'][:-1]+bytes([SNAPSHOT['ciphertext'][-1]^1]),'INITIAL_REQUEST_AUTHENTICATION_FAILED'),
 ('wrong-bound-job','aad',canonical({'jobId':uid(99),'snapshotId':uid(2),'schemaId':SNAPSHOT['schemaId']}),'INITIAL_REQUEST_IDENTITY_BINDING_MISMATCH')]:
 s=copy.deepcopy(SNAPSHOT);s[key]=value;reject('negative.'+identity,s,reason)
for key in ['jobId','snapshotId','schemaId']:
 s=copy.deepcopy(SNAPSHOT);s[key]=uid(99) if key!='schemaId' else 'urn:synthetic:wrong-schema'
 reject('negative.changed-stored-'+key,s,'INITIAL_REQUEST_IDENTITY_BINDING_MISMATCH')
# Construct authvalid ciphertexts with exactly one typed/encoding violation.
for identity,bad in [('extra-field',{**BODY,'clientAuthority':True}),('missing-intent',{'kind':'CREATE'}),('null-intent',{**BODY,'intent':None})]:
 s=copy.deepcopy(SNAPSHOT);data=canonical(bad);s['nonce']=hashlib.sha256(data).digest()[:12];s['ciphertext']=AESGCM(KEY).encrypt(s['nonce'],data,AAD);s['contentDigest']=digest(data)
 reject('negative.'+identity,s,'INITIAL_REQUEST_TYPED_SCHEMA_INVALID')
s=copy.deepcopy(SNAPSHOT);data=json.dumps(BODY,sort_keys=True).encode();s['nonce']=hashlib.sha256(data).digest()[:12];s['ciphertext']=AESGCM(KEY).encrypt(s['nonce'],data,AAD);s['contentDigest']=digest(data)
reject('negative.noncanonical-authenticated-bytes',s,'INITIAL_REQUEST_NONCANONICAL_BYTES')
# Real SQLite in-memory transaction model, explicitly not PostgreSQL execution.
def database():
 c=sqlite3.connect(':memory:');c.executescript('''
 CREATE TABLE locator(scope TEXT,key TEXT,request_digest TEXT,logical_id TEXT UNIQUE,outcome BLOB,PRIMARY KEY(scope,key));
 CREATE TABLE job(id TEXT PRIMARY KEY,state TEXT CHECK(state='DISCUSSING'),initial_digest TEXT);
 CREATE TABLE snapshot(job_id TEXT PRIMARY KEY,ciphertext BLOB NOT NULL,content_digest TEXT);
 CREATE TABLE event(id TEXT PRIMARY KEY,job_id TEXT UNIQUE,payload BLOB NOT NULL);
 CREATE TABLE outbox(event_id TEXT UNIQUE,payload BLOB NOT NULL);
 CREATE TABLE audit(logical_id TEXT UNIQUE,result_digest TEXT);
 ''');return c
RECEIPT={'jobId':uid(1),'state':'DISCUSSING','stateVersion':'0','initialRequestDigest':SNAPSHOT['contentDigest'],'createdAt':'2026-09-30T00:00:00Z'}
# StateVersion0 is an isolated fixture, not a proposed fixed create counter.
PUBLIC=canonical(RECEIPT)
def transaction(c,request_digest=SNAPSHOT['contentDigest'],failure_at=None):
 prior=c.execute('SELECT request_digest,outcome FROM locator WHERE scope=? AND key=?',('OWNER_FULL:generation.job.create','fixture-key')).fetchone()
 if prior:
  if prior[0]!=request_digest:raise Rejection('IDEMPOTENCY_CONFLICT')
  if prior[1] is None:raise Rejection('UNKNOWN_OUTCOME_REQUIRES_RECONCILIATION')
  return prior[1]
 try:
  c.execute('BEGIN')
  c.execute('INSERT INTO locator VALUES(?,?,?,?,?)',('OWNER_FULL:generation.job.create','fixture-key',request_digest,uid(3),None))
  c.execute('INSERT INTO job VALUES(?,?,?)',(uid(1),'DISCUSSING',SNAPSHOT['contentDigest']))
  c.execute('INSERT INTO snapshot VALUES(?,?,?)',(uid(1),SNAPSHOT['ciphertext'],SNAPSHOT['contentDigest']))
  if failure_at=='after-root':raise Rejection('FORCED_TRANSACTION_ROLLBACK')
  c.execute('INSERT INTO event VALUES(?,?,?)',(uid(4),uid(1),PUBLIC))
  c.execute('INSERT INTO outbox VALUES(?,?)',(uid(4),PUBLIC))
  c.execute('INSERT INTO audit VALUES(?,?)',(uid(3),digest(PUBLIC)))
  c.execute('UPDATE locator SET outcome=? WHERE scope=? AND key=?',(PUBLIC,'OWNER_FULL:generation.job.create','fixture-key'))
  c.commit();return PUBLIC
 except Exception:
  c.rollback();raise
c=database();check('positive.atomic-root-snapshot-receipt-event-outbox-audit',transaction(c)==PUBLIC and all(c.execute('SELECT count(*) FROM '+t).fetchone()[0]==1 for t in ['locator','job','snapshot','event','outbox','audit']))
check('positive.replay-original-receipt-no-new-event',transaction(c)==PUBLIC and c.execute('SELECT count(*) FROM event').fetchone()[0]==1)
check('positive.public-event-outbox-no-credential',all(BODY['credential'].encode() not in c.execute('SELECT payload FROM '+t).fetchone()[0] for t in ['event','outbox']))
try:transaction(c,'sha256:'+'0'*64);conflict=False
except Rejection as exc:conflict=str(exc)=='IDEMPOTENCY_CONFLICT'
check('negative.replay-conflict-no-second-root',conflict and c.execute('SELECT count(*) FROM job').fetchone()[0]==1)
c=database()
try:transaction(c,failure_at='after-root');rollback=False
except Rejection as exc:rollback=str(exc)=='FORCED_TRANSACTION_ROLLBACK'
check('negative.rollback-no-partial-pipeline',rollback and all(c.execute('SELECT count(*) FROM '+t).fetchone()[0]==0 for t in ['locator','job','snapshot','event','outbox','audit']))
c=database();c.execute('INSERT INTO locator VALUES(?,?,?,?,?)',('OWNER_FULL:generation.job.create','fixture-key',SNAPSHOT['contentDigest'],uid(3),None));c.commit()
try:transaction(c);unknown=False
except Rejection as exc:unknown=str(exc)=='UNKNOWN_OUTCOME_REQUIRES_RECONCILIATION'
check('negative.unknown-not-second-create',unknown and c.execute('SELECT count(*) FROM job').fetchone()[0]==0)
sql=(OUT/'generation-create-persistence-proposed.sql').read_text();pglast.parse_sql(sql);pglast.parse_plpgsql(sql);check('positive.postgresql17-ddl-and-trigger-syntax',True)
if SSOT.read_bytes()!=raw:raise RuntimeError('SOURCE_CHANGED')
report={'sourceDocumentSha256':source_hash,'referenceScriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'requirementsAuditSha256':hashlib.sha256((Path(__file__).resolve().parents[4]/'requirements-audit.txt').read_bytes()).hexdigest(),'nativePayloadResourceSha256':rs['contracts/payload-contracts.json']['sha256'],'proposedSQLSha256':hashlib.sha256(sql.encode()).hexdigest(),'checked':len(checks),'failed':sum(c['status']!='PASS' for c in checks),'checks':checks,'runtimeVersions':{'cryptography':cryptography.__version__,'sqlite':sqlite3.sqlite_version,'postgresqlParser':pglast.__version__},'proofScope':'Typed protected-snapshot/storage boundary only, not proof that unresolved directcredential admission is allowed. Actual AEAD fixture and SQLite isolated reference transactions, plus PostgreSQL17 syntax AST. None is production PostgreSQL18.6/nativehelper/runtime acceptance. Exact production crypto-profile binding remains BLOCKED; referenceAESGCM is not a policy decision.','wholeGenerationJobCreateDesignClosure':'BLOCKED','implementationProductionAcceptance':'NOT_EVALUATED'}
(OUT/'generation-create-persistence-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['checked','failed','wholeGenerationJobCreateDesignClosure','proofScope']}))
