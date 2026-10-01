"""Actual PG18.6 execution of §51.8 candidate, not generic-helper closure."""
import hashlib,json,os,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
OUT=Path(__file__).resolve().parent
PSQL=['/tmp/kcml-pg18/bin/psql','-X','-h','/tmp/kcml-pg18-socket','-p','55432','-d','postgres','-v','ON_ERROR_STOP=1','-At']
checks=[]
def run(sql,success=True):
 r=subprocess.run(PSQL,input=sql,text=True,capture_output=True,timeout=15)
 if success and r.returncode:raise RuntimeError(r.stderr)
 return r
schema='sql_helpers_'+uuid.uuid4().hex[:12]
sql=(OUT/'postgres-advisory-key-proposed.sql').read_text()
run('CREATE SCHEMA '+schema+';SET search_path='+schema+',pg_catalog;'+sql)
version=run('SELECT version()').stdout.strip();assert version.startswith('PostgreSQL 18.6 ')
heads=['00000000','00000001','00000100','00010000','01000000','7fffffff','80000000','80000001','ffffffff']
vectors=[]
def check(identity,ok,**details):
 checks.append(dict(id=identity,status='PASS' if ok else 'FAIL',**details))
for head in heads:
 raw=bytes.fromhex(head)+bytes(range(4,32));expected=int.from_bytes(raw[:4],'big',signed=True)
 actual=int(run("SELECT "+schema+".kcml_postgres_advisory_key_v1(decode('"+raw.hex()+"','hex'))").stdout.strip())
 vectors.append(dict(digestHex=raw.hex(),expected=expected,actual=actual));check('signed-network-key/'+head,actual==expected)
for identity,value in [('null','NULL'),('short',"decode('"+vectors[0]['digestHex'][:-2]+"','hex')"),('long',"decode('"+vectors[0]['digestHex']+"00','hex')")]:
 r=run('SELECT '+schema+'.kcml_postgres_advisory_key_v1('+value+')',False)
 check('positive-derived-negative/'+identity,r.returncode!=0 and 'ADVISORY_KEY_REQUIRES_SHA256_DIGEST' in r.stderr,positiveWitness='signed-network-key/00000000',specificDiagnostic='ADVISORY_KEY_REQUIRES_SHA256_DIGEST')
# Independent Node cross-language implementation uses its native signed reader.
node=json.loads(subprocess.check_output(['node','-e','const a=JSON.parse(process.argv[1]);process.stdout.write(JSON.stringify(a.map(x=>Buffer.from(x.digestHex,"hex").readInt32BE(0))))',json.dumps(vectors)]))
check('node-pg-cross-language',node==[v['actual'] for v in vectors])
# Both first-create Secret and idempotency namespaces use actual xact-only locks.
# Hold session via stdin, retaining transaction between independent queries.
for namespace in [1020,1030]:
 tag='helper_'+uuid.uuid4().hex[:10];env=dict(os.environ,PGAPPNAME=tag)
 holder=subprocess.Popen(PSQL,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
 holder.stdin.write('BEGIN;SELECT pg_advisory_xact_lock('+str(namespace)+',-2147483648);\n');holder.stdin.flush()
 found=False
 for _ in range(50):
  if run("SELECT count(*) FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid WHERE a.application_name='"+tag+"' AND l.locktype='advisory' AND l.granted").stdout.strip()=='1':found=True;break
  time.sleep(.02)
 blocked=run('SELECT pg_try_advisory_xact_lock('+str(namespace)+',-2147483648)').stdout.strip()=='f'
 holder.stdin.write('COMMIT;\n');holder.stdin.flush()
 released=False
 for _ in range(50):
  if run("SELECT count(*) FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid WHERE a.application_name='"+tag+"' AND l.locktype='advisory'").stdout.strip()=='0':released=True;break
  time.sleep(.02)
 reacquired=run('SELECT pg_try_advisory_xact_lock('+str(namespace)+',-2147483648)').stdout.strip()=='t'
 holder.stdin.close();holder.wait(timeout=5)
 check('xact-contention-and-commit-release/'+str(namespace),found and blocked and released and reacquired,heldRowObserved=found,contendingConnectionRejected=blocked,releasedWhileHolderSessionAlive=released,nextTransactionAcquired=reacquired)
report=dict(sourceDocumentSha256=hashlib.sha256(SSOT.read_bytes()).hexdigest(),entryCommit='905555e47f3547516439a699e262df62cbbec229',candidateSqlSha256=hashlib.sha256(sql.encode()).hexdigest(),canonicalEmbedded=False,postgresVersion=version,checks=checks,vectors=vectors,checked=len(checks),failed=sum(x['status']!='PASS' for x in checks),scope='§51.8 exact signed-key SQL candidate and real transaction lock release only. Four generic helpers, namespace canonical-key producer, stored full-digest uniqueness, operation authority and whole create transaction remain OPEN.',implementationProductionAcceptance='NOT_EVALUATED')
(OUT/'advisory-key-postgres-proof.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['checked','failed','postgresVersion','scope']}))
raise SystemExit(bool(report['failed']))
