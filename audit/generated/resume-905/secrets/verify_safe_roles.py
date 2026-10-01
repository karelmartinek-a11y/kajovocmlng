from pathlib import Path
import subprocess,json,hashlib,sys
ROOT=Path('/workspace/kajovocmlng');sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT
source=SSOT.read_bytes()
OUT=Path(__file__).parent
candidate=(OUT/'secret-profile-publication.sql').read_bytes()
P=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-U','agent','-v','ON_ERROR_STOP=1','-At','-d','secret_publication_905']
cases=[]
for role,code in [('kcml_secret_profile_publisher','PUBLISHER'),('kcml_secret_profile_reader','READER')]:
 marker=b"rolname='"+role.encode()+b"'";m=candidate.index(marker)
 a=candidate.rfind(b'DO $$BEGIN',0,m);z=candidate.index(b'END$$;',m)+len(b'END$$;');installer=candidate[a:z]
 for unsafe in ['LOGIN','SUPERUSER','CREATEDB','CREATEROLE','REPLICATION','BYPASSRLS','INHERIT']:
  # Alter only inside private rolled-back transaction: never persist unsafe
  # attributes or rewrite a pre-existing production/user principal.
  q=subprocess.run(P,input='BEGIN;ALTER ROLE '+role+' '+unsafe+';'+installer.decode()+'ROLLBACK;',text=True,capture_output=True)
  diagnostic='SECRET_PROFILE_'+code+'_ROLE_UNSAFE'
  assert q.returncode!=0 and diagnostic in q.stderr,(role,unsafe,q.stderr)
  cases.append({'id':role+'/reject-existing-'+unsafe,'status':'PASS','expectedDiagnostic':diagnostic,'unsafeMutationRolledBackByConnectionClose':True})
 q=subprocess.run(P,input='BEGIN;'+installer.decode()+'ROLLBACK;',text=True,capture_output=True)
 assert q.returncode==0,q.stderr
 cases.append({'id':role+'/accept-existing-safe-role','status':'PASS'})
report={'status':'PASS','checked':len(cases),'failed':0,'cases':cases,'sourceSha256':hashlib.sha256(source).hexdigest(),'sourceUnchangedDuringRun':source==SSOT.read_bytes(),'postgresVersion':subprocess.run(P,input='SHOW server_version;',text=True,capture_output=True).stdout.strip(),'candidateSqlSha256':hashlib.sha256(candidate).hexdigest(),'proofScope':'Exact candidate role installation clauses for both reserved roles; no alteration of unsafe pre-existing principals, installation refuses them','wholeOperationClosed':False}
(OUT/'safe-role-postgres-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}))
