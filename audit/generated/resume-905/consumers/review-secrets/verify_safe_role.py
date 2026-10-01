from pathlib import Path
import subprocess,json,hashlib
D=Path(__file__).parent
P=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-U','agent','-v','ON_ERROR_STOP=1','-At','-d','secret_publication_review_905']
s=(D/'secret-profile-publication-safe-role.proposed.sql').read_bytes();a=s.index(b'DO $$BEGIN');z=s.index(b'END$$;',a)+len(b'END$$;');installer=s[a:z]
cases=[]
for unsafe in ['LOGIN','SUPERUSER','CREATEDB','CREATEROLE','REPLICATION','BYPASSRLS','INHERIT']:
 q=subprocess.run(P,input='BEGIN;ALTER ROLE kcml_secret_profile_publisher '+unsafe+';'+installer.decode()+'ROLLBACK;',text=True,capture_output=True)
 assert q.returncode!=0 and 'SECRET_PROFILE_PUBLISHER_ROLE_UNSAFE' in q.stderr,(unsafe,q.stderr)
 cases.append({'id':'reject-preexisting-'+unsafe,'status':'PASS','diagnostic':'SECRET_PROFILE_PUBLISHER_ROLE_UNSAFE','globalRoleMutationRolledBackByConnectionClose':True})
q=subprocess.run(P,input='BEGIN;'+installer.decode()+'ROLLBACK;',text=True,capture_output=True);assert q.returncode==0,q.stderr
cases.append({'id':'accept-existing-safe-role','status':'PASS'})
report={'checks':len(cases),'failed':0,'cases':cases,'correctedCandidateSha256':hashlib.sha256(s).hexdigest(),'installerOnlyProof':True,'wholeOperationClosed':False}
(D/'safe-role-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'PASS')
