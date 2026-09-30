#!/usr/bin/env python3
"""Actual PG18.6 extension KATs, not canonical Secret AEAD/master-key acceptance."""
from pathlib import Path
import subprocess,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'scripts'));from ssot_sources import SSOT
source_document_bytes=SSOT.read_bytes();source_self_bytes=Path(__file__).read_bytes()
p=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-d','postgres','-X','-A','-t','-q','-v','ON_ERROR_STOP=1']
def run(s):return subprocess.run(p,input=s,text=True,capture_output=True)
r=run('CREATE EXTENSION IF NOT EXISTS citext;CREATE EXTENSION IF NOT EXISTS pgcrypto;SHOW server_version;');assert r.returncode==0 and r.stdout.strip()=='18.6'
cases=[('sha256-standard-abc',"encode(digest('abc','sha256'),'hex')='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'"),('sha256-bytes-native-equality',"digest(decode('00616263ff','hex'),'sha256')=sha256(decode('00616263ff','hex'))"),('hmac-sha256-rfc4231-case1',"encode(hmac(convert_to('Hi There','UTF8'),decode(repeat('0b',20),'hex'),'sha256'),'hex')='b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7'"),('bcrypt-synthetic-positive',"crypt('SyntheticOnly',crypt('SyntheticOnly',gen_salt('bf',4))) IS NOT NULL"),('bcrypt-synthetic-wrong-value',"crypt('WrongSynthetic',crypt('SyntheticOnly',gen_salt('bf',4)))<>crypt('SyntheticOnly',gen_salt('bf',4))"),('citext-case-insensitive-not-owner-acceptance',"'KRMAR78'::citext='krmar78'::citext"),('owner-uses-explicit-case-sensitive-text',"NOT('KRMAR78'::citext::text COLLATE \"C\"='krmar78')")]
# Ensure password-check comparison reuses one salt/hash, not a new salt witness.
cases[3]=('bcrypt-synthetic-positive',"(SELECT crypt('SyntheticOnly',h)=h FROM(SELECT crypt('SyntheticOnly',gen_salt('bf',4))h)x)")
cases[4]=('bcrypt-synthetic-wrong-value',"(SELECT crypt('WrongSynthetic',h)<>h FROM(SELECT crypt('SyntheticOnly',gen_salt('bf',4))h)x)")
checks=[]
for name,predicate in cases:
 r=run('SELECT '+predicate+';');ok=r.returncode==0 and r.stdout.strip()=='t';checks.append({'id':name,'status':'PASS' if ok else 'FAIL','testValues':'synthetic/public-known-answer; values not recorded'});assert ok,(name,r.stderr)
r=run("SELECT extname||':'||extversion FROM pg_extension WHERE extname IN('citext','pgcrypto') ORDER BY extname;")
report={'format':'KCML-PG-EXTENSION-PRIMITIVE-PROOF/1','sourceDocumentSha256':hashlib.sha256(source_document_bytes).hexdigest(),'postgresVersion':'18.6','extensions':r.stdout.strip().splitlines(),'openssl':subprocess.check_output(['openssl','version'],text=True).strip(),'sharedObjectSha256':{f:hashlib.sha256(Path('/tmp/kcml-pg18/lib/postgresql',f+'.so').read_bytes()).hexdigest() for f in ['citext','pgcrypto']},'verifierSha256':hashlib.sha256(source_self_bytes).hexdigest(),'checks':checks,'summary':{'checks':len(checks),'failed':sum(c['status']!='PASS' for c in checks)},'notProven':['canonical authenticated Secret encryption profile','systemd master-key provisioning/materialization','actual deployed token/password verifier','complete R17 fixture universe'],'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
assert SSOT.read_bytes()==source_document_bytes, 'SOURCE_DOCUMENT_CHANGED_DURING_PROOF'
assert Path(__file__).read_bytes()==source_self_bytes, 'VERIFIER_CHANGED_DURING_PROOF'
HERE.joinpath('postgres-extension-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']))
