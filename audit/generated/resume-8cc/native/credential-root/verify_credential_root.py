from pathlib import Path
import sys,json,hashlib,threading
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).resolve().parent;sys.path[:0]=[str(OUT),str(OUT.parent),str(ROOT/'scripts')]
from ordered_generation_credential_factory import CredentialRootFactory
from credential_root_fixture import install_current_credential_secret
from native_auth_factory import *
f=CredentialRootFactory('native_credential_root_8cc');sid,vid=install_current_credential_secret(f);db=f.db;checks=[]
def rec(n,ok,code=None):assert ok,(n,code);checks.append({'case':n,'passed':True,'actualDiagnostic':code})
body={'kind':'CREATE','targetKind':'PLATFORM_COMPONENT','intent':'Synthetic credential root acceptance','sources':[{'kind':'TEXT','text':'Synthetic source'}]}
db.query('BEGIN');value=f.build(body,uid(800),uid(1800),uid(2800),key='eligible-current-root');f.insert(value);f.finish(value);db.query('SET CONSTRAINTS ALL IMMEDIATE;COMMIT')
rec('current-reserved-active-root-version-genuine-token-commits',db.query("SELECT status,lifecycle FROM kcml_secret_v1.secret_record r JOIN kcml_secret_v1.secret_version v ON v.id=r.active_version_id WHERE r.id="+lit(sid))[0]==['ACTIVE','ACTIVE'])
db.query('BEGIN');replay=f.build(body,uid(800),uid(1801),uid(2801),2,value['auditHash'],key='eligible-current-root');db.query('COMMIT');rec('eligible-replay-returns-original-command',replay['replay']and replay['logicalOperationId']==uid(1800))
# Actual E20 lock prevents root deletion between validation and use.
db.query('BEGIN');pending=f.build(body,uid(802),uid(1803),uid(2803),2,value['auditHash'],key='held-credential-root')
other=DB(f.database)
try:
 other.query('BEGIN;SET LOCAL lock_timeout=\'150ms\';')
 try:other.query('UPDATE kcml_secret_v1.secret_record SET deleted_at=clock_timestamp(),state_version=state_version+1 WHERE id='+lit(sid));raise AssertionError('CREDENTIAL_ROOT_CHANGE_NOT_SERIALIZED')
 except RuntimeError as e:rec('concurrent-root-delete-blocked-by-actual-E20-lock','lock timeout'in str(e),str(e).splitlines()[0])
finally:other.query('ROLLBACK');other.close();db.query('ROLLBACK')
rec('root-lock-contention-rollback-no-partial-new-root',db.query('SELECT count(*)FROM public.generation_job')[0][0]=='1')
# Existing old ACTIVE immutable version/fingerprint cannot authorize DELETED root.
db.query('UPDATE kcml_secret_v1.secret_record SET deleted_at=clock_timestamp(),state_version=state_version+1 WHERE id='+lit(sid))
rec('deleted-root-retains-old-active-version-witness',db.query('SELECT r.status,v.lifecycle,v.fingerprint=c.fingerprint FROM kcml_secret_v1.secret_record r JOIN kcml_secret_v1.secret_version v ON v.id=r.active_version_id CROSS JOIN public.owner_api_credential c WHERE r.id='+lit(sid))[0]==['DELETED','ACTIVE','t'])
for label,key in [('fresh','deleted-new-key'),('replay','eligible-current-root')]:
 db.query('BEGIN')
 try:f.build(body,uid(801),uid(1802),uid(2802),2,value['auditHash'],key=key);raise AssertionError('DELETED_ROOT_ACCEPTED')
 except ValueError as e:rec('deleted-root-denies-'+label,str(e)=='OWNER_API_CREDENTIAL_ROOT_NOT_ACTIVE',str(e))
 db.query('ROLLBACK');rec('deleted-denial-'+label+'-no-partial-context-command-root',db.query('SELECT(SELECT count(*)FROM public.generation_job),(SELECT count(*)FROM public.domain_command),(SELECT count(*)FROM public.generation_create_trusted_context)')[0]==['1','1','1'])
assert SSOT.read_bytes()==f.source
report={'status':'PASS','checked':len(checks),'checks':checks,'postgresqlVersion':db.query('SHOW server_version')[0][0],'sourceDocumentSha256':sha(f.source).hex(),'canonicalSecretInputs':{n:f.resources[n]['sha256']for n in ['database/secret-profile-roots.sql','database/secret-owner-binding.sql','database/secret-profile-publication.sql','database/secret-command-chain.sql','database/secret-record-status.sql']},'candidateInputs':{p.name:sha(p.read_bytes()).hex()for p in OUT.glob('*.py')},'wholeOperationClosed':False,'limitations':['Isolated credential genesis CREATED→ACTIVE bootstrap is a fixture, not full production genesis producer','Isolated AES key does not establish encrypted systemd key source','Transport ceiling authority and effective generic wrapper remain OPEN','Complete registered H parent migration and future application runtime separate']}
(OUT/'credential-root-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'PASS','checked':len(checks)}))
