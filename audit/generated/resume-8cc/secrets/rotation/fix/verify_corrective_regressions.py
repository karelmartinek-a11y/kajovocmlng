from pathlib import Path
import sys,json,re,hashlib
HERE=Path(__file__).parent;program_bytes=(HERE/'verify_rotation_pg.py').read_bytes();helper_bytes=(HERE/'owner_rotation_projection.py').read_bytes();sql_bytes=(HERE/'rotation-projection.sql').read_bytes()
program=program_bytes.decode().split('report={',1)[0].replace('owner_rotate_fix_8cc','owner_rotate_fix_regression_8cc')
ns={'__file__':str(HERE/'verify_rotation_pg.py')};exec(compile(program,'corrective-actual-positive-reproduction','exec'),ns);assert all(x['status']=='PASS'for x in ns['checks'])
db=ns['db'];b=ns['b'];sha=ns['sha'];canonical=ns['canonical'];checks=[]
previous_receipt=canonical(ns['first']['output']);previous_digest='sha256:'+sha(previous_receipt).hex()
class Mutator:
 def __init__(self,actual,kind):self.actual=actual;self.kind=kind
 def query(self,sql):
  if sql.startswith('INSERT INTO domain_event VALUES('):
   if self.kind=='event-type':sql=sql.replace("'OPERATION_TERMINAL'","'WRONG_ROTATION_EVENT'")
   if self.kind=='aggregate-kind':sql=sql.replace("'SECRET_RECORD'","'OTHER_AGGREGATE'")
   if self.kind=='schema-id':sql=sql.replace("'urn:kcml:r9:route:route.0024:event'","'urn:kcml:foreign:rotation:event'")
   matches=list(re.finditer(r"decode\('([0-9a-f]+)','hex'\)",sql))
   if self.kind in ['schema-digest-zero','schema-digest-other-valid-schema']:
    wrong=bytes(32)if self.kind=='schema-digest-zero'else sha((HERE/'rotation-request-proposal.schema.json').read_bytes());sql=sql[:matches[0].start()]+b(wrong)+sql[matches[0].end():]
   if self.kind=='payload-previous-valid-receipt-and-SHA':
    sql=sql[:matches[2].start()]+b(sha(previous_receipt))+sql[matches[2].end():];sql=sql[:matches[1].start()]+b(previous_receipt)+sql[matches[1].end():]
  if sql.startswith('INSERT INTO kcml_secret_v1.rotation_projection_completion'):
   matches=list(re.finditer(r"decode\('([0-9a-f]+)','hex'\)",sql))
   if self.kind=='zero-result-digest':m=matches[2];sql=sql[:m.start()]+b(bytes(32))+sql[m.end():]
   if self.kind=='semantic-wrong-operation-valid-SHA':
    obj=json.loads(bytes.fromhex(matches[1][1]));obj['operationId']='secret.create';raw=canonical(obj);sql=sql[:matches[2].start()]+b(sha(raw))+sql[matches[2].end():];sql=sql[:matches[1].start()]+b(raw)+sql[matches[1].end():]
  if self.kind in ['audit-after-zero','audit-after-previous-valid-receipt']and sql.startswith('INSERT INTO audit_event VALUES('):
   encoded=re.findall(r"decode\('([0-9a-f]+)','hex'\)",sql);raw=next(bytes.fromhex(x)for x in encoded if bytes.fromhex(x).startswith(b'{'));obj=json.loads(raw);obj['afterDigest']='sha256:'+'0'*64 if self.kind=='audit-after-zero'else previous_digest;sql=sql.replace(b(raw),b(canonical(obj)))
  return self.actual.query(sql)
 def transaction_status(self):return self.actual.transaction_status()
for kind,expected in [('event-type','OWNER_ROTATION_EVENT_PROJECTION_MISMATCH'),('aggregate-kind','OWNER_ROTATION_EVENT_PROJECTION_MISMATCH'),('schema-id','OWNER_ROTATION_EVENT_PROJECTION_MISMATCH'),('schema-digest-zero','OWNER_ROTATION_EVENT_PROJECTION_MISMATCH'),('schema-digest-other-valid-schema','OWNER_ROTATION_EVENT_PROJECTION_MISMATCH'),('payload-previous-valid-receipt-and-SHA','OWNER_ROTATION_EVENT_PAYLOAD_MISMATCH'),('audit-after-zero','OWNER_ROTATION_AUDIT_SEMANTIC_MISMATCH'),('audit-after-previous-valid-receipt','OWNER_ROTATION_AUDIT_SEMANTIC_MISMATCH'),('zero-result-digest','rotation_projection_completion_check'),('semantic-wrong-operation-valid-SHA','OWNER_ROTATION_SEMANTIC_RESULT_MISMATCH')]:
 before=ns['states']();db.query('BEGIN');accepted=False;error=None
 try:ns['rotate'](Mutator(db,kind),ns['latest_token'],ns['request'](),'fixed-regression-'+kind);db.query('SET CONSTRAINTS ALL IMMEDIATE');accepted=True
 except (ValueError,RuntimeError)as e:error=str(e).splitlines()[0]
 finally:
  if db.transaction_status()!=0:db.query('ROLLBACK')
 checks.append({'id':kind,'status':'PASS'if not accepted and expected in(error or'')and ns['states']()==before else'FAIL','expectedDiagnostic':expected,'actualDiagnostic':error,'acceptedUnderAllDeferredConstraints':accepted,'rollbackPreservedHeads':ns['states']()==before,'baseline':'49 actual positive author cases freshly reproduced; mutation starts with current valid token/CAS/body'})
# Validate the actual event row's native -> wire mapping with the source-derived envelope.
row=db.query("SELECT d.operation_id,d.logical_operation_id,e.correlation_id,e.aggregate_sequence,e.event_type,convert_from(e.payload_bytes,'UTF8'),encode(e.payload_digest,'hex')FROM domain_event e JOIN domain_command d ON d.logical_operation_id=e.logical_operation_id WHERE d.logical_operation_id="+ns['lit'](ns['first']['logicalOperationId']))[0]
wire={'routeId':'route.0024','operationId':row[0],'logicalOperationId':row[1],'correlationId':row[2],'sequence':row[3],'eventType':'TERMINAL'if row[4]=='OPERATION_TERMINAL'else row[4],'payload':json.loads(row[5]),'payloadDigest':'sha256:'+row[6]}
from jsonschema import Draft202012Validator,FormatChecker
schema=json.loads((HERE/'rotation-event-projection-proposal.schema.json').read_bytes());Draft202012Validator(schema,format_checker=FormatChecker()).validate(wire)
checks.append({'id':'actual-native-event-to-authoritative-envelope-identity-and-exact-proposed-payload','status':'PASS'})
report={'status':'PASS'if all(x['status']=='PASS'for x in checks)else'BLOCKED','checked':len(checks),'failed':sum(x['status']!='PASS'for x in checks),'checks':checks,'authorBaselineChecksReproduced':len(ns['checks']),'sourceSha256':sha(ns['source']).hex(),'sourceUnchanged':ns['source']==ns['SSOT'].read_bytes(),'fixedSqlSha256':sha(sql_bytes).hex(),'fixedHelperSha256':sha(helper_bytes).hex(),'fixedSQLUnchanged':sql_bytes==(HERE/'rotation-projection.sql').read_bytes(),'fixedHelperUnchanged':helper_bytes==(HERE/'owner_rotation_projection.py').read_bytes(),'projectionBindingSha256':sha((HERE/'source-projection-bindings.json').read_bytes()).hex(),'previousValidReceiptDigest':previous_digest,'postgresVersion':db.query('SHOW server_version')[0][0],'wholeRotationClosed':False,'effectiveInvalidationInventory':'OPEN_NOT_ASSUMED_EMPTY','systemdCredentialSource':'NOT_EVALUATED_SYNTHETIC_FIXTURE_KEY_ONLY','implementationAcceptance':'NOT_EVALUATED'}
(HERE/'corrective-regressions.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}));db.close();ns['observer'].close()
