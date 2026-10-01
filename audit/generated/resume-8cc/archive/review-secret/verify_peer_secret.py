from pathlib import Path
import sys,json,hashlib,re
ROOT=Path('/workspace/kajovocmlng');HERE=Path(__file__).parent;AUTHOR=ROOT/'audit/generated/resume-8cc/secrets'
program=(AUTHOR/'verify_secret_chain_pg.py').read_text().split("for component in ['completion'",1)[0]
program=program.replace("OUT=Path(__file__).parent","OUT=Path("+repr(str(AUTHOR))+")").replace("name='secret_chain_8cc'","name='secret_peer_archive_8cc'")
ns={'__file__':str(AUTHOR/'verify_secret_chain_pg.py')};exec(compile(program,'independently-reproduced-secret-author-positive','exec'),ns)
assert all(c['status']=='PASS'for c in ns['checks']),ns['checks']
db=ns['db'];lit=ns['lit'];b=ns['b'];canonical=ns['canonical'];sha=ns['sha'];checks=[]
def rec(id,ok,diagnostic=None):
 checks.append({'id':id,'passed':bool(ok),'actualDiagnostic':diagnostic});assert ok,(id,diagnostic)
rec('actual-author-positive-and-replay-reproduced',True)
foreign=db.query('SELECT trusted_context_id FROM kcml_secret_v1.create_completion WHERE logical_operation_id='+lit(ns['result']['logicalOperationId']))[0][0]
import secret_command_chain as module
original_q=module.q
# Only mutate one execution-context identity in an otherwise actual token/import/AEAD chain.
def context_swap(db_,sql):
 if sql.startswith('INSERT INTO domain_command('):
  fields=sql.split(') VALUES(',1)[0].split('(',1)[1].split(',')
  # Context appears immediately before the fixed SECRET_RECORD discriminator.
  sql=re.sub(r"'[0-9a-f-]{36}','SECRET_RECORD'",lit(foreign)+",'SECRET_RECORD'",sql,count=1)
 return original_q(db_,sql)
module.q=context_swap;db.query('BEGIN')
try:
 ns['create']({**ns['body'],'stableName':'SYNTHETIC_FOREIGN_CONTEXT'},'peer-foreign-context');db.query('SET CONSTRAINTS ALL IMMEDIATE');rec('valid-foreign-context-substitution',False)
except Exception as e:rec('valid-foreign-context-substitution','SECRET_CONTEXT_SINGLE_COMMAND_REQUIRED'in str(e),'SECRET_CONTEXT_SINGLE_COMMAND_REQUIRED')
finally:db.query('ROLLBACK');module.q=original_q
rec('foreign-context-substitution-no-command-event-leak',db.query('SELECT(SELECT count(*)FROM domain_command),(SELECT count(*)FROM domain_event)')[0]==['1','1'])
# Swap with a valid committed other Secret receipt; preserve structural SQL digests.
foreign_receipt=canonical(ns['result']['output'])
def receipt_swap(db_,sql):
 if sql.startswith('INSERT INTO domain_event VALUES('):
  matches=list(re.finditer(r"decode\('([0-9a-f]+)','hex'\)",sql));assert len(matches)==3
  for match,new in reversed([(matches[1],b(foreign_receipt)),(matches[2],b(sha(foreign_receipt)))]):sql=sql[:match.start()]+new+sql[match.end():]
 return original_q(db_,sql)
module.q=receipt_swap;db.query('BEGIN')
try:
 ns['create']({**ns['body'],'stableName':'SYNTHETIC_SWAPPED_RECEIPT'},'peer-receipt');db.query('SET CONSTRAINTS ALL IMMEDIATE');rec('valid-other-receipt-event-substitution',False)
except Exception as e:rec('valid-other-receipt-event-substitution','SECRET_CREATE_ATOMIC_CLOSURE_INCOMPLETE'in str(e),'SECRET_CREATE_ATOMIC_CLOSURE_INCOMPLETE')
finally:db.query('ROLLBACK');module.q=original_q
rec('receipt-substitution-no-partial-chain',db.query('SELECT(SELECT count(*)FROM domain_command),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM audit_event)')[0]==['1']*3)
# Exact candidate public/domain authority isolation, not superuser simulation of token.
db.query('BEGIN')
try:
 db.query('SET LOCAL ROLE kcml_secret_domain_writer;INSERT INTO kcml_secret_v1.owner_api_context SELECT * FROM kcml_secret_v1.owner_api_context;');rec('domain-role-cannot-forge-auth-context',False)
except Exception as e:rec('domain-role-cannot-forge-auth-context','permission denied'in str(e),'permission denied')
finally:db.query('ROLLBACK')
report={'canonicalSourceDigest':'sha256:'+hashlib.sha256(ns['source']).hexdigest(),'candidateSqlDigest':'sha256:'+hashlib.sha256((AUTHOR/'secret-command-chain.sql').read_bytes()).hexdigest(),'candidateHelperDigest':'sha256:'+hashlib.sha256((AUTHOR/'secret_command_chain.py').read_bytes()).hexdigest(),'postgresVersion':db.query('SHOW server_version')[0][0],'checks':checks,'pass':sum(c['passed']for c in checks),'fail':sum(not c['passed']for c in checks),'limitations':['Candidate SQL bytes reviewed, coordinator must reproduce activated canonical resource bytes.','Fixture root status/retention remain explicit server-policy gaps; public create adapter correctly BLOCKED.','Actual protected Secret/global key authority and full broker/use chain remain outside this bounded command proof.']}
(HERE/'secret-peer-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'PASS':report['pass'],'FAIL':report['fail'],'source':report['canonicalSourceDigest']}))
