"""Actual isolated PG18 fixture using current embedded canonical foundation bytes."""
import hashlib,json,os,subprocess,re,sys
from pathlib import Path
from ssot_sources import ROOT,SSOT,resource_index
BASE=ROOT/'audit/generated/resume-d362';HERE=BASE/'review'
def main():
 raw=SSOT.read_bytes();rs=resource_index();sql=rs['database/generation-create-foundations.sql']['raw'].decode();checks=[]
 out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/resume-d362/coordinator');out.mkdir(parents=True,exist_ok=True)
 psql=Path('/tmp/kcml-pg18/bin/psql');database='generation_canonical_design_fixture';version=None
 def save(status,reason=None):
  report={'sourceDocumentSha256':hashlib.sha256(raw).hexdigest(),'canonicalSqlSha256':rs['database/generation-create-foundations.sql']['sha256'],'status':status,'postgresqlVersion':version,'reason':reason,'checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'scope':__doc__,'wholeOperationClosed':False,'requiredRemaining':'Actual token verifier/crypto/complete locked RETRY scan/full consumers/failure-before-root remain mandatory before generation','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
  report['supportSha256']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),HERE/'verify_scoped_generation_links.py',BASE/'events/verify_combined_generation.py',BASE/'persistence/generation_descriptor_registry.py',BASE/'persistence/context_fixture_exports.py']}
  (out/'generation-physical-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed','reason']}));return int(status!='PASS')
 if not psql.exists():return save('BLOCKED','AUDIT_ENVIRONMENT_POSTGRESQL18_FIXTURE_BINARY_UNAVAILABLE')
 args=[str(psql),'-h','/tmp/kcml-pg18-socket','-p','55432','-d','postgres','-X','-At','-v','ON_ERROR_STOP=1']
 probe=subprocess.run(args,input='SELECT version();',text=True,capture_output=True)
 if probe.returncode:return save('BLOCKED','AUDIT_ENVIRONMENT_ISOLATED_POSTGRESQL_NOT_AVAILABLE')
 version=probe.stdout.strip()
 if 'PostgreSQL 18.' not in probe.stdout:return save('BLOCKED','REQUIRED_POSTGRESQL18_FIXTURE_VERSION_UNAVAILABLE')
 exists=subprocess.run(args,input="SELECT 1 FROM pg_database WHERE datname='"+database+"';",text=True,capture_output=True)
 if not exists.stdout.strip():
  created=subprocess.run(args,input='CREATE DATABASE '+database+';',text=True,capture_output=True)
  if created.returncode:return save('BLOCKED','ISOLATED_FIXTURE_DATABASE_CREATE_FAILED')
 # Execute independently authored positive/mutants in an OWN disposable DB,
 # replacing its proposal assembly with exactly canonical embedded bytes.
 program=(HERE/'verify_scoped_generation_links.py').read_text().split("# Commit the positive",1)[0]
 program=program.replace('generation_independent_review_fixture',database)
 needle="ns={'__file__':str(HERE/'verify_scoped_generation_links.py')};exec"
 assert needle in program
 program=program.replace(needle,"source=re.sub(r'foundation=module\\.foundations\\(\\).*?\\n','foundation=canonical_sql\\n',source,count=1)\nns={'__file__':str(HERE/'verify_scoped_generation_links.py'),'canonical_sql':canonical_sql};exec")
 namespace={'__file__':str(HERE/'verify_scoped_generation_links.py'),'canonical_sql':sql};exec(compile(program,'current canonical PostgreSQL fixture','exec'),namespace)
 checks.extend({'case':c['id'],'passed':c['passed'],'expectedDiagnostic':c['expectedDiagnostic'],'actualDiagnostic':c['actualDiagnostic']}for c in namespace['cases'])
 ns=namespace['ns'];assert ns['foundation']==sql,'CANONICAL_SQL_NOT_EXECUTED';base=namespace['base'];test=namespace['test']
 for name,before,after in [('foreign-caller',ns['owner'],'99999999-9999-4999-8999-999999999999'),('wrong-family',"'GENERATION'","'CONFIG'"),('wrong-authority',"'OWNER_FULL'","'INTERNAL'"),('wrong-business-target',"'generation_job'","'another_target'"),('wrong-frozen-revision',ns['b'](ns['scope']),ns['b'](bytes(32)))]:
  wrong=base.copy();wrong['locator']=wrong['locator'].replace(before,after);test('locator-'+name,wrong,'GENERATION_CREATE_ATOMIC_CLOSURE_INCOMPLETE');c=namespace['cases'][-1];checks.append({'case':c['id'],'passed':c['passed'],'expectedDiagnostic':c['expectedDiagnostic'],'actualDiagnostic':c['actualDiagnostic']})
 committed=ns['run']('BEGIN;'+''.join(base.values())+'COMMIT;');checks.append({'case':'actual-canonical-commit','passed':committed.returncode==0,'diagnostic':committed.stderr[-1200:]})
 if committed.returncode:return save('BLOCKED','CANONICAL_POSITIVE_COMMIT_FAILED')
 for name,mutation,expected in [('locator-scope-retained',"UPDATE idempotency_locator SET business_target_id='untrusted';",'CREATE_LOCATOR_FROZEN_SCOPE'),('outbox-retarget',"UPDATE transactional_outbox SET consumer_scope='untrusted';",'CREATE_OUTBOX_FROZEN_DELIVERY'),('outbox-delete',"DELETE FROM transactional_outbox;",'CREATE_OUTBOX_RETENTION_AUTHORITY_REQUIRED'),('terminal-outcome-rewrite',"UPDATE domain_idempotency_record SET canonical_outcome_digest=decode(repeat('00',32),'hex');",'CREATE_IDEMPOTENCY_FROZEN_SCOPE'),('audit-byte-change',"UPDATE audit_event SET canonical_bytes=convert_to('{}','UTF8');",'CREATE_IMMUTABLE_RECORD')]:
  q=ns['run']('BEGIN;'+mutation+'ROLLBACK;');checks.append({'case':name,'passed':q.returncode!=0 and expected in q.stderr,'expectedDiagnostic':expected,'actualDiagnostic':q.stderr[-1200:]})
 for table,expected in [('generation_job',39)]:
  q=ns['run']("SELECT count(*) FROM information_schema.columns WHERE table_schema='public'AND table_name='"+table+"';");checks.append({'case':table+'/physical-column-count','passed':q.returncode==0 and int(q.stdout.strip())==expected})
 assert raw==SSOT.read_bytes(),'SSOT_INPUT_CHANGED'
 return save('PASS' if all(c['passed']for c in checks)else 'BLOCKED')
if __name__=='__main__':raise SystemExit(main())
