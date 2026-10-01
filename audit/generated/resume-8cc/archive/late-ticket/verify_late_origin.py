from pathlib import Path
import sys,json,hashlib
HERE=Path(__file__).parent;ROOT=Path('/workspace/kajovocmlng');AUTHOR=HERE.parent
sys.path.insert(0,str(AUTHOR))
program=(AUTHOR/'verify_publisher.py').read_text().split('# Closed masks',1)[0]
program=program.replace('from generation_policy_package import *','from generation_policy_package import build_package,digest,load_package,dispatch_own_kind,PACKAGE_ID')
program=program.replace("HERE=Path(__file__).parent;ROOT=Path('/workspace/kajovocmlng')","HERE=Path("+repr(str(HERE))+");ROOT=Path('/workspace/kajovocmlng')").replace('archive_publisher_8cc','archive_late_origin_8cc')
ns={'__file__':str(HERE/'verify_late_origin.py')};exec(compile(program,'isolated-late-origin-schema-setup','exec'),ns)
db=ns['db'];checks=[]
def rec(id,ok,diag=None):checks.append({'id':id,'passed':bool(ok),'diagnostic':diag});assert ok,(id,diag)
db.query('BEGIN');parts,meta,plain=ns['ns']['build']();ctx=meta['trustedContextId'];cmd=meta['logicalOperationId'];db.query(ns['ticket'](meta))
rec('actual-canonical-verifier-insert-emits-same-tx-origin',db.query('SELECT count(*)FROM generation_policy_authentication_origin_v1 WHERE acceptance_txid=pg_current_xact_id()')[0][0]=='1')
rec('actual-context-ticket-binds-same-tx',db.query('SELECT count(*)FROM generation_policy_acceptance_ticket_v1 WHERE acceptance_txid=pg_current_xact_id()')[0][0]=='1')
def denied(id,sql,code):
 db.query('SAVEPOINT negative')
 try:db.query(sql);rec(id,False)
 except Exception as e:rec(id,code in str(e),code)
 finally:db.query('ROLLBACK TO SAVEPOINT negative')
denied('domain-cannot-fabricate-origin','SET LOCAL ROLE kcml_domain_writer;INSERT INTO generation_policy_authentication_origin_v1 SELECT * FROM generation_policy_authentication_origin_v1;','permission denied')
denied('origin-trigger-not-callable-authority','SELECT kcml_policy_authentication_origin_v1();','trigger functions can only be called as triggers')
denied('immutable-origin-update','UPDATE generation_policy_authentication_origin_v1 SET acceptance_txid=pg_current_xact_id();','FROZEN_ARCHIVE_IMMUTABLE')
db.query('COMMIT');db.query('BEGIN')
# Different command avoids unique constraint; failure must be the old receipt origin.
old={**meta,'logicalOperationId':'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'}
denied('retained-context-cannot-mint-new-transaction-ticket',ns['ticket'](old),'GENERATION_ARCHIVE_CURRENT_AUTHENTICATION_ORIGIN_REQUIRED');db.query('ROLLBACK')
fn=db.query("SELECT pg_get_functiondef('kcml_pin_policy_acceptance_v1(uuid,uuid)'::regprocedure)")[0][0]
rec('late-ticket-no-lower-lock-statements','FOR SHARE'not in fn.upper() and all(x not in fn for x in ['owner_api_credential','owner_session','owner_identity','generation_policy_release_v1']))
report={'sourceDocumentSha256':hashlib.sha256(ns['source']).hexdigest(),'candidateSha256':hashlib.sha256((HERE/'generation-trusted-policy-publisher.sql').read_bytes()).hexdigest(),'checks':checks,'pass':sum(c['passed']for c in checks),'fail':sum(not c['passed']for c in checks),'postgresqlVersion':db.query('SHOW server_version')[0][0],'scope':'Actual trigger/ticket SQL against actual bearer-verifier receipt/context only; legacy setup persists H context before C, so this intentionally does not certify global ordered admission. Ordered native producer joined proof remains required.'}
(HERE/'late-origin-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'PASS':report['pass'],'FAIL':report['fail']}))
