from native_auth_factory import *
import threading,time
f=Factory('generation_native_auth_8cc');db=f.db;checks=[]
def rec(n,ok,actual=None):checks.append({'case':n,'passed':bool(ok),'actualDiagnostic':actual});assert ok,(n,actual)
body={'kind':'CREATE','targetKind':'PLATFORM_COMPONENT','intent':'Produce isolated synthetic bytes','sources':[{'kind':'TEXT','text':'Fixture source'}]}
db.query('BEGIN');built=f.build(body,uid(1),uid(1001),uid(2001),key='native-parent');f.insert(built);db.query('COMMIT');rec('actual-owner-auth-precise-create-root-commit',True)
# Native RETRY fixture selectors are actual current byte digests; no eligibility claim.
sys.path.insert(0,str(ROOT/'audit/generated/resume-d362/admission'))
from generation_retry_inventory_fixtures import fixture,bodies
repo,phase,rd,plan,ind,physical,classifiers=fixture()
retry=copy.deepcopy(bodies['RETRY']);retry['parentJobId']=uid(1)
# Fix old plan fixture stale bytes at the source, not by hiding digest mismatch.
planraw=canonical_bytes(plan);repo.records[phase['planId']]['bytes']=planraw;repo.records[phase['planId']]['contentDigest']='sha256:'+sha(planraw).hex()
retry['generationBasis'].update(expectedDigest=rd,expectedPlanDigest='sha256:'+sha(planraw).hex())
db.query('BEGIN');child=f.build(retry,uid(600),uid(1600),uid(2600),2,built['auditHash'],'native-child');rec('retry-plaintext-is-native-retry-not-create',strict_json(child['plain'])['kind']=='RETRY' and strict_json(child['plain'])['generationBasis']==retry['generationBasis'])
# Serialize exactly once, encryption preserves native HTTP body and full selector identity.
with open_snapshot(child['envelope'],f.key,f.keyid,child['meta'],lambda v:validate_body('generation.job.create',strict_json(v)))as view:rec('retry-authenticated-snapshot-opens-exact-native-input',bytes(view)==child['plain'])
# Source bound via true owner/context server verifier; class B credential lock held.
contender=DB(f.database);codes=[];started=threading.Event()
def rotate():
 try:
  contender.query("BEGIN;SET LOCAL lock_timeout='150ms';");started.set();contender.query('UPDATE owner_api_credential SET state_version=state_version+1,credential_version=credential_version+1,credential_activation_epoch=credential_activation_epoch+1');codes.append('UNEXPECTED_UPDATE')
 except Exception as e:codes.append('LOCK_TIMEOUT'if'lock timeout'in str(e)else str(e))
 finally:contender.query('ROLLBACK')
t=threading.Thread(target=rotate);t.start();started.wait(3);t.join(4);rec('credential-share-held-through-native-retry-snapshot',codes==['LOCK_TIMEOUT'],codes)
db.query('ROLLBACK');rec('uncommitted-native-child-context-rolls-back',db.query("SELECT count(*)FROM generation_create_trusted_context WHERE client_request_digest="+b(bytes.fromhex(child['native']['requestDigest'][7:])))[0][0]=='0')
# Secret material is never written to fixture report.
report={'status':'PASS','checked':len(checks),'failed':0,'checks':checks,'sourceDocumentSha256':sha(f.source).hex(),'postgresqlVersion':db.query('SHOW server_version')[0][0],'canonicalInputs':{n:f.resources[n]['sha256']for n in ['database/generation-create-foundations.sql','database/generation-create-authentication.sql','database/canonical-crypto-registry.sql','database/generation-protected-registry-link.sql','database/generation-locator-lock.sql']},'consumedSupportSha256':{str(p.relative_to(ROOT)):sha(p.read_bytes()).hex()for p in [Path(__file__),Path(__file__).with_name('native_auth_factory.py'),ROOT/'scripts/generation_auth_acceptance.py',ROOT/'scripts/generation_auth_crypto.py']},'wholeOperationClosed':False,'limits':['No current trusted transport-ceiling producer; isolated fixture value4096 is not normative','Key issuance is random isolated fixture, not systemd credential-source evidence','Native RETRY locked eligibility/producer/child commit is next integration dependency; no relabelled CREATE snapshot proof','Historical native selector fixture only supplies source bytes; actual server phase/approval producers not asserted']}
Path(__file__).with_name('native-auth-factory-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checked':report['checked']}));db.close();contender.close()
