"""Canonical embedded Secret SQL fixture; no service/auth/outbox closure claim."""
from pathlib import Path
import sys,hashlib,json,subprocess
ROOT=Path('/workspace/kajovocmlng');OUT=Path('/tmp/ssot-secret-pg-current');SOURCE=ROOT/'audit/generated/resume-34d/secrets-browser'
sys.path[:0]=[str(ROOT/'scripts'),str(SOURCE)]
from ssot_sources import SSOT,resource_index
raw=SSOT.read_bytes();rs=resource_index();sql=rs['database/secret-profile-roots.sql']['raw']
assert sql==(SOURCE/'secret-profile-roots.sql').read_bytes(),'CURRENT_CANONICAL_SQL_AND_REVIEWED_CANDIDATE_DIFFER'
import secret_profile_reference
assert secret_profile_reference.SCHEMA==json.loads(rs['contracts/secrets/profile-handoffs.schema.json']['raw']),'ACTUAL_CURRENT_PROFILE_REFERENCE_MASK_DIFFERS'
psql=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-U','agent','-d','postgres','-v','ON_ERROR_STOP=1','-At']
q=subprocess.run(psql+['-c',"SELECT 1 FROM pg_database WHERE datname='secret_pg_integrated'"],capture_output=True,text=True)
assert q.returncode==0,q.stderr
if not q.stdout.strip():
 q=subprocess.run(psql+['-c','CREATE DATABASE secret_pg_integrated'],capture_output=True,text=True);assert q.returncode==0,q.stderr
text=(SOURCE/'verify_postgres.py').read_text().replace("'kcml_secret_34d'","'secret_pg_integrated'").replace('from profile_reference import','from secret_profile_reference import')
needle="setup=subprocess.run(PSQL+['-f',str(D/'secret-profile-roots.sql')],text=True,capture_output=True);assert setup.returncode==0,setup.stderr"
assert needle in text
text=text.replace(needle,"setup=subprocess.run(PSQL,input=canonical_sql.decode(),text=True,capture_output=True);assert setup.returncode==0,setup.stderr")
text=text.replace("(D/'postgres-tests.json').write_text","(canonical_output/'postgres-tests.json').write_text")
# The existing fixture records exact SQLSTATE/constraint, not generic exception.
ns={'__file__':str(SOURCE/'verify_postgres.py'),'canonical_sql':sql,'canonical_output':OUT}
try:exec(compile(text,'current canonical embedded Secret SQL fixture','exec'),ns)
except SystemExit as exc:
 if exc.code:raise
report=json.loads((OUT/'postgres-tests.json').read_text());report['sourceSha256']=hashlib.sha256(raw).hexdigest();report['sourceUnchangedDuringRun']=raw==SSOT.read_bytes();report['canonicalEmbeddedSqlExecuted']=True
report['canonicalResourceSha256']={'database/secret-profile-roots.sql':hashlib.sha256(sql).hexdigest(),'contracts/secrets/profile-handoffs.schema.json':rs['contracts/secrets/profile-handoffs.schema.json']['sha256']}
report['adaptation']='Fixture SQL -f candidate loading replaced with subprocess stdin of actual canonical resource bytes; byte equality asserted. Current canonical secret_profile_reference module supplies current effective Cookie and SecretCreateBody masks; original proposal mask equality was correctly rejected. Private output/database changed; no SQL constraint or fixture weakening.'
report['supportSha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [SOURCE/'verify_postgres.py',SOURCE/'profile_reference.py',SOURCE/'secret_value_parsers.py',SOURCE/'verify_reference.py',SOURCE/'synthetic_profile_fixtures.py',SOURCE/'input-source.json',ROOT/'requirements-audit.txt',ROOT/'scripts/secret_profile_reference.py',ROOT/'scripts/secret_profile_parsers.py',ROOT/'01_UI_CONTRACT/contracts/secrets/profile-handoffs.schema.json']}
report['historicalProposalSchemaSha256']=report['schemaSha256'];report['schemaSha256']=rs['contracts/secrets/profile-handoffs.schema.json']['sha256'];report['originalFixtureScriptSha256']=report['scriptSha256'];report['scriptSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
report['historicalProposalInput']=report.pop('currentWorkingRepairInput');report['inputSourceMeaning']='Current sourceSha256/canonicalResourceSha256 bind this run; historicalProposalInput and inputCommit identify reused fixture origin only'
report['invocationDiagnostics']=[{'stage':'Initial current-mask equality check','result':'REJECTED_STALE_PROPOSAL_MASK','actualDifference':['Cookie','SecretCreateBody'],'resolution':'Use current integrated secret_profile_reference and assert loaded SCHEMA equals effective canonical resource; no schema requirement removed.'}]
report['adapterSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();report['executedAdaptedFixtureSha256']=hashlib.sha256(text.encode()).hexdigest();report['wholeOperationClosed']=False;report['IMPLEMENTATION_PRODUCTION_ACCEPTANCE']='NOT_EVALUATED';report['status']='PASS'if report['failed']==0 and report['sourceUnchangedDuringRun']else'BLOCKED'
(OUT/'executed-adapted-fixture.py').write_text(text)
(OUT/'postgres-tests.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k]for k in ['status','checked','failed','sourceSha256','canonicalEmbeddedSqlExecuted','sourceUnchangedDuringRun']}))
