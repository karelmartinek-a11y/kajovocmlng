from pathlib import Path
import sys,json,hashlib,re,copy
ROOT=Path('/workspace/kajovocmlng');HERE=Path(__file__).parent;AUTHOR=ROOT/'audit/generated/resume-8cc/secrets/rotation'
program=(AUTHOR/'verify_rotation_pg.py').read_text().split('report={',1)[0]
program=program.replace('OUT=Path(__file__).parent',"OUT=Path("+repr(str(AUTHOR))+")").replace('owner_rotate_projection_8cc','peer_owner_rotate_archive_8cc')
ns={'__file__':str(AUTHOR/'verify_rotation_pg.py')};exec(compile(program,'independent-reproduction-rotation-projection','exec'),ns)
assert all(c['status']=='PASS'for c in ns['checks']),ns['checks']
import generation_auth_crypto
assert Path(generation_auth_crypto.__file__).resolve()==ROOT/'scripts/generation_auth_crypto.py'
db=ns['db'];b=ns['b'];sha=ns['sha'];canonical=ns['canonical'];checks=[];defects=[]
class Mutator:
 def __init__(self,db,kind):self.db=db;self.kind=kind
 def query(self,sql):
  if self.kind=='zero-semantic-digest':sql=sql.replace(b(self.result),b(bytes(32)))if hasattr(self,'result')else sql
  if sql.startswith('INSERT INTO domain_event VALUES('):
   if self.kind=='event-type':sql=sql.replace("'OPERATION_TERMINAL'","'WRONG_ROTATION_EVENT'")
   if self.kind=='event-aggregate-kind':sql=sql.replace("'SECRET_RECORD'","'OTHER_AGGREGATE'")
   if self.kind=='event-schema-id':sql=sql.replace("'urn:kcml:proposed:owner-rotation-projection:event'","'urn:kcml:foreign:rotation:event'")
   if self.kind=='event-schema-digest':
    m=list(re.finditer(r"decode\('[0-9a-f]+','hex'\)",sql))[0];sql=sql[:m.start()]+b(bytes(32))+sql[m.end():]
  if sql.startswith('INSERT INTO kcml_secret_v1.rotation_projection_completion'):
   matches=list(re.finditer(r"decode\('([0-9a-f]+)','hex'\)",sql));assert len(matches)==3
   if self.kind=='zero-result-digest':m=matches[2];sql=sql[:m.start()]+b(bytes(32))+sql[m.end():]
   if self.kind=='semantic-mismatch':
    raw=bytes.fromhex(matches[1].group(1));v=json.loads(raw);v['operationId']='secret.create';bad=canonical(v)
    sql=sql[:matches[2].start()]+b(sha(bad))+sql[matches[2].end():];sql=sql[:matches[1].start()]+b(bad)+sql[matches[1].end():]
  if self.kind=='audit-after-digest'and sql.startswith('INSERT INTO audit_event VALUES('):
   m=re.search(r"decode\('([0-9a-f]+)','hex'\)",sql[sql.index('kcml_audit_hash_v1'):]);assert m
   # Last repeated canonical audit bytes appear in hash function and row.
   candidates=re.findall(r"decode\('([0-9a-f]+)','hex'\)",sql)
   raw=next(bytes.fromhex(x)for x in candidates if bytes.fromhex(x).startswith(b'{'))
   value=json.loads(raw);value['afterDigest']='sha256:'+'0'*64;bad=canonical(value);sql=sql.replace(b(raw),b(bad))
  return self.db.query(sql)
 def transaction_status(self):return self.db.transaction_status()
for kind,expected in [('zero-result-digest','rotation_projection_completion_check'),('semantic-mismatch','OWNER_ROTATION_SEMANTIC_RESULT_MISMATCH'),('event-type','OWNER_ROTATION_PROJECTION_ATOMIC_CLOSURE_INVALID'),('event-aggregate-kind','OWNER_ROTATION_PROJECTION_ATOMIC_CLOSURE_INVALID'),('event-schema-id','OWNER_ROTATION_PROJECTION_ATOMIC_CLOSURE_INVALID'),('event-schema-digest','OWNER_ROTATION_PROJECTION_ATOMIC_CLOSURE_INVALID'),('audit-after-digest','OWNER_ROTATION_PROJECTION_ATOMIC_CLOSURE_INVALID')]:
 before=ns['states']();db.query('BEGIN');accepted=False;diag=None
 try:
  result=ns['rotate'](Mutator(db,kind),ns['latest_token'],ns['request'](),'peer-'+kind);db.query('SET CONSTRAINTS ALL IMMEDIATE');accepted=True
 except Exception as e:diag=str(e).splitlines()[0]
 finally:db.query('ROLLBACK')
 passed=not accepted and expected in (diag or '')
 checks.append({'id':kind,'passed':passed,'expectedDiagnostic':expected,'actualDiagnostic':diag,'acceptedUnderAllDeferredConstraints':accepted,'baseline':'independently reproduced actual author positive42','rollbackPreservedHeads':ns['states']()==before})
 if not passed:defects.append({'id':kind,'accepted':accepted,'diagnostic':diag})
# Actual public adapter has no empty-inventory shortcut, even with a proposed empty argument.
try:ns['rotate_owner_api_key'](effectiveInvalidationInventory=[]);diag='ACCEPTED'
except ValueError as e:diag=str(e)
checks.append({'id':'empty-invalidation-does-not-open-public-guard','passed':diag=='OWNER_ROTATION_EFFECTIVE_INVALIDATION_INVENTORY_UNRESOLVED','actualDiagnostic':diag})
report={'sourceSha256':sha(ns['source']).hex(),'candidateSqlSha256':sha((AUTHOR/'rotation-projection.sql').read_bytes()).hex(),'candidateHelperSha256':sha((AUTHOR/'owner_rotation_projection.py').read_bytes()).hex(),'authorAssertionsReproduced':len(ns['checks']),'checks':checks,'defects':defects,'pass':sum(c['passed']for c in checks),'fail':sum(not c['passed']for c in checks),'postgresVersion':db.query('SHOW server_version')[0][0],'canonicalCryptoHelperPath':str(Path(generation_auth_crypto.__file__).resolve()),'wholeRotationClosed':False,'effectiveInvalidationInventory':'OPEN_NOT_ASSUMED_EMPTY','provider':'NOT_EVALUATED_SYNTHETIC_FIXTURE_KEY_ONLY','scope':'Actual isolated full author commit/CAS/concurrency/AEAD/replay plus independent deferred-closure mutations; no full invalidation/source/runtime rotation claim.'}
(HERE/'rotation-peer-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'authorReproduced':report['authorAssertionsReproduced'],'peerPASS':report['pass'],'peerFAIL':report['fail'],'defects':defects}))
