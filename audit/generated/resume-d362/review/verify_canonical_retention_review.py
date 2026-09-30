from pathlib import Path
import sys,json,subprocess,hashlib
HERE=Path(__file__).parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
r=resource_index();raw=SSOT.read_bytes();sql=r['database/generation-create-foundations.sql']['raw'];assert sql==(HERE/'combined-foundations.sql').read_bytes()
cmd=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p55432','-d','generation_independent_canonical_review_fixture','-X','-At','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose']
def run(s):return subprocess.run(cmd,input=s,text=True,capture_output=True)
assert run('SELECT count(*) FROM generation_job;').stdout.strip()=='1'
q=run("BEGIN;UPDATE transactional_outbox SET state='CLAIMED',state_version=state_version+1,delivery_fence=delivery_fence+1,lease_owner_id='00000000-0000-4000-8000-000000000005',lease_expires_at=clock_timestamp()+interval '1 hour';UPDATE transactional_outbox SET state='DELIVERED',state_version=state_version+1;COMMIT;");assert q.returncode==0,q.stderr
source=(HERE/'verify_postgres_retention.py').read_text().split('report={',1)[0].replace('generation_independent_review_fixture','generation_independent_canonical_review_fixture');ns={'__file__':str(HERE/'verify_canonical_retention_review.py')};exec(compile(source,'actual canonical retention mutants','exec'),ns)
report={'scope':'Fresh canonical embedded SQL installed by independent canonical-handoff verifier, exact installation equality checked; eight specific postcommit retention mutants. No source proposal module SQL acceptance or production certificate.','database':'generation_independent_canonical_review_fixture','version':ns['version'],'checks':ns['rows'],'unexpectedAccepted':sum(not x['rejected']for x in ns['rows']),'sourceDocumentSha256':hashlib.sha256(raw).hexdigest(),'canonicalSqlSha256':hashlib.sha256(sql).hexdigest(),'physicalHandoffContractSha256':r['contracts/generation/physical-create-handoff.json']['sha256'],'executedMutantProgramSha256':hashlib.sha256(source.encode()).hexdigest(),'installationByteEqualityVerified':True,'wholeOperationClosed':False,'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
assert raw==SSOT.read_bytes(),'SSOT_CHANGED_DURING_REVIEW'
(HERE/'canonical-retention-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(ns['rows']),'unexpectedAccepted':report['unexpectedAccepted']}))
