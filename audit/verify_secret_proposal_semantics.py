"""Pending proposals: real isolated parsers with synthetic values, no approval."""
import copy,hashlib,importlib.metadata,json,os,sys
from datetime import datetime,timezone
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from secret_proposal_semantics import ROOT,PROPOSAL,parse_candidate,consume,Rejected
sys.path.insert(0,str(ROOT/'scripts'))
from create_operation_contracts import strict_json

def main():
 source=(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes();p=json.loads(PROPOSAL.read_text());checks=[]
 supported={(c['secretType'],s['properties']['variant']['const']) for c in p['contracts'] for s in c['schema']['oneOf']}
 consumer={'supported':supported,'cookieHosts':['example.invalid'],'origins':['https://example.invalid'],'oauthHosts':['oauth.example.invalid'],'database':'syntheticdb','keyAlgorithmAllowed':lambda key:True,'authenticatedAccountProven':True}
 def positive(id_,fn):
  try:fn();checks.append({'id':id_,'passed':True})
  except Exception as e:checks.append({'id':id_,'passed':False,'unexpectedExceptionType':type(e).__name__,'code':getattr(e,'code',None),'pointer':getattr(e,'pointer',None)})
 def negative(id_,fn,code,pointer):
  try:fn();checks.append({'id':id_,'passed':False,'expectedCode':code,'actual':'ACCEPTED'})
  except Rejected as e:checks.append({'id':id_,'passed':e.code==code and e.pointer==pointer,'expectedCode':code,'actualCode':e.code,'expectedPointer':pointer,'actualPointer':e.pointer})
  except Exception as e:checks.append({'id':id_,'passed':False,'unexpectedExceptionType':type(e).__name__})
 positives={}
 for c in p['contracts']:
  kind=c['secretType'];pos,neg=c['proposedSemanticCases'];valid=copy.deepcopy(pos['value'])
  # Original SSH semanticnegative selectedKEY while positive selectedPASSWORD.
  # Establish a valid KEY positive from the separately declared KEY fixture first.
  if kind=='SSH_CREDENTIAL':
   positive(kind+'/original-password-positive',lambda k=kind,v=copy.deepcopy(valid):parse_candidate(k,v,consumer))
   valid=next(v['value'] for v in c['syntheticCases'] if v['expected']=='SCHEMA_ACCEPT' and v['value']['variant']=='SSH_OPENSSH_PRIVATE_KEY_V1')
  positives[kind]=valid
  positive(kind+'/real-parser-positive',lambda k=kind,v=valid:parse_candidate(k,v,consumer))
  negative(kind+'/specific-semantic-negative',lambda k=kind,v=copy.deepcopy(neg['value']):parse_candidate(k,v,consumer),neg['expectedStableCode'],neg['expectedPointer'])
  # Actual encryption/decryption roundtrip is a fixture mechanism, never a
  # proposed productioncipher selection. The input raw JSON bytes remain exact.
  raw=('  '+json.dumps(valid,ensure_ascii=False,separators=(',',':'))+' \n').encode()
  def roundtrip(k=kind,raw=raw):
   decoded=strict_json(raw);parse_candidate(k,decoded,consumer)
   key=AESGCM.generate_key(bit_length=256);nonce=os.urandom(12);aad=b'SYNTHETIC-IMMUTABLE-VERSION-ONLY'
   ciphertext=AESGCM(key).encrypt(nonce,raw,aad)
   hydrated=AESGCM(key).decrypt(nonce,ciphertext,aad)
   assert hydrated==raw and strict_json(hydrated)==decoded
   parse_candidate(k,strict_json(hydrated),consumer)
  positive(kind+'/exact-byte-encrypted-roundtrip',roundtrip)
  negative(kind+'/consumer-no-fallback',lambda k=kind,v=valid:parse_candidate(k,v,{**consumer,'supported':set()}),'SECRET_VARIANT_UNSUPPORTED','/variant')
 # Native parser, not rejection of a legacy canonicalJsonextra, catches malformed
 # raw HTTP/import JSON and duplicate keys before candidate interpretation.
 from create_operation_contracts import ContractFailure
 valid_json=json.dumps(positives['DATABASE_CREDENTIAL']).encode();assert strict_json(valid_json)
 for name,raw,code,pointer in [('invalid-json',valid_json[:-1],'INVALID_JSON',''),('duplicate',valid_json[:-1]+b',"username":"SYNTHETIC_SECOND"}','DUPLICATE_JSON_KEY','/username')]:
  try:strict_json(raw);okay=False
  except ContractFailure as e:okay=e.code==code and e.pointer==pointer
  checks.append({'id':'actual-import-json/'+name,'passed':okay})
 token=copy.deepcopy(positives['OAUTH_TOKEN_SET']);token['expiresAt']='2020-01-01T00:00:00Z'
 positive('expired-token-can-be-candidate',lambda:parse_candidate('OAUTH_TOKEN_SET',token,consumer))
 negative('expired-token-cannot-be-consumed',lambda:consume('OAUTH_TOKEN_SET',token,consumer,datetime(2026,9,30,tzinfo=timezone.utc)),'OAUTH_TOKEN_EXPIRED','/expiresAt')
 negative('session-account-proof-not-cookie-presence',lambda:consume('SESSION_STATE',positives['SESSION_STATE'],{**consumer,'authenticatedAccountProven':False},datetime.now(timezone.utc)),'BROWSER_STATE_AUTH_POSTCONDITION_FAILED','/consumer/account')
 if (ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()!=source:raise RuntimeError('SSOT_INPUT_CHANGED')
 report={'sourceDocumentSha256':hashlib.sha256(source).hexdigest(),'proposalSha256':hashlib.sha256(PROPOSAL.read_bytes()).hexdigest(),'supportSha256':{name:hashlib.sha256((ROOT/'audit'/name).read_bytes()).hexdigest() for name in ['secret_proposal_semantics.py','verify_secret_proposal_semantics.py']},'dependencies':{name:importlib.metadata.version(name) for name in ['cryptography','jsonschema']},'status':'PENDING_OWNER_FORMAT_REVIEW','checked':len(checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,'sensitiveValuesInReport':False,'proposalSemanticCasesExecuted':18,'originalSSHPositiveCorrection':'KEY negative now starts from valid samevariant KEY witness, not PASSWORD fixture','runtimeAcceptance':'NOT_EVALUATED','excluded':['Provider/OAuth/TLS/DB/SSH liveauthentication','Actualbrowseraccountcondition','ProductionSecretstoragecipherchoice','Consumeralgorithm/securitypolicyapproval','Fullformatapprovalandconsumerpipeline']}
 out=ROOT/'audit/generated/resume-5334/coordinator/secret-semantic-tests.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','checked','failed','proposalSemanticCasesExecuted']}));
 for c in checks:
  if not c['passed']:print(json.dumps(c))
 return int(bool(report['failed']))
if __name__=='__main__':raise SystemExit(main())
