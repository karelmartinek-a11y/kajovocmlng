"""Actual native HTTP/profile candidates and canonical crypto primitive fixtures.

Synthetic registry/auth context is reference-only: no actual Secret acceptance or
systemd/SQL/broker authority is claimed. Whole secret.create remains OPEN.
"""
import copy,hashlib,json,os,sys
from ssot_sources import ROOT,SSOT,resource_index
from create_operation_contracts import decode_http,admit,ContractFailure
from secret_profile_import import *
from secret_profile_reference import original_profile_slice,parse_profile,canonical_value_digest
from generation_auth_crypto import seal,open_snapshot
from evidence_scope_reuse import secret_scope_current
sys.path.insert(0,str(ROOT/'audit/generated/resume-34d/secrets-browser'))
from synthetic_profile_fixtures import fixtures,consumer
UID='00000000-0000-4000-8000-000000000001'
HEADERS=[('Content-Type','application/json'),('Idempotency-Key','synthetic-import-key')]
def main():
 source=hashlib.sha256(SSOT.read_bytes()).hexdigest();checks=[];rs=resource_index()
 def check(name,ok):checks.append({'case':name,'passed':bool(ok)})
 def reject_case(name,fn,code,pointer=None):
  try:fn();checks.append({'case':name,'passed':False,'actual':'ACCEPTED','expected':code})
  except (ContractFailure,Rejected) as e:checks.append({'case':name,'passed':e.code==code and (pointer is None or e.pointer==pointer),'actualDiagnostic':e.code,'actualPointer':e.pointer,'expected':code,'expectedPointer':pointer})
  except Exception as e:checks.append({'case':name,'passed':False,'unexpectedException':type(e).__name__})
 def decode(raw,query=None):return decode_http('secret.create','POST','/secrets',query or [],HEADERS,raw)
 def registry(p):return {'secretType':INVENTORY[p]['secretType'],'profileId':p,'schemaId':SCHEMA['$id']+'#/$defs/'+p,'schemaDigest':schema_digest(p),'schemaBytes':compiled_schema_bytes(p),'status':'ACTIVE','normativeSourceDigest':'sha256:'+source,'reviewReceiptDigest':'sha256:'+'2'*64}
 server={'owner':UID,'actor':'OWNER','authenticated':True,'recovery':'READY','stableNames':[],'secretProfileRegistryReader':registry,'secretProfileNormativeSourceDigest':'sha256:'+source,'secretProfileReviewReceiptDigest':'sha256:'+'2'*64}
 for p in APPROVED_PROFILES:
  body={'stableName':'SYNTHETIC','displayName':'Synthetic','type':INVENTORY[p]['secretType'],'value':{'representation':'PROFILE_JSON_V1','profileId':p,'profile':fixtures[p]}}
  raw=json.dumps(body,ensure_ascii=True,indent=2).encode();native=decode(raw);candidate=native['secretImportCandidate'];admitted=admit(native,server)
  check(p+'/actual-http-positive',admitted['action']=='RESERVE_ATOMIC_CREATE')
  check(p+'/exact-original-profile-bytes',candidate['bytes']==original_profile_slice(raw))
  check(p+'/actual-source-schema-pin',schema_digest(p)=='sha256:'+hashlib.sha256(compiled_schema_bytes(p)).hexdigest())
  bad=copy.deepcopy(body);bad['value']['profile']['variant']=None
  reject_case(p+'/null-discriminator',lambda:decode(json.dumps(bad).encode()),'SCHEMA_ONEOF')
  reject_case(p+'/unknown-query',lambda:decode(raw,[('unexpected','1')]),'UNKNOWN_QUERY_PARAMETER')
  duplicate=raw.replace(b'"variant":',b'"variant":"SYNTHETIC_DUPLICATE", "variant":',1)
  reject_case(p+'/actual-duplicate-profile-key',lambda:decode(duplicate),'DUPLICATE_JSON_KEY')
  reject_case(p+'/missing-registry-not-authorized-flag',lambda:admit(native,{**server,'secretProfileRegistryReader':True}),'SECRET_PROFILE_REGISTRY_UNAVAILABLE')
  reject_case(p+'/foreign-review-authority',lambda:admit(native,{**server,'secretProfileReviewReceiptDigest':'sha256:'+'3'*64}),'SECRET_PROFILE_REGISTRY_AUTHORITY_UNRESOLVED')
  # Exact shared canonical primitive, not the historical alternate fixture AES.
  import secrets
  key=secrets.token_bytes(32);meta={'ownerId':UID,'secretId':UID,'secretVersionId':'00000000-0000-4000-8000-000000000002','secretType':candidate['type'],'representation':candidate['representation'],'profileId':p,'schemaId':SCHEMA['$id']+'#/$defs/'+p,'schemaDigest':schema_digest(p),'plaintextByteLength':len(candidate['bytes']),'originalImportBytesDigest':'sha256:'+hashlib.sha256(candidate['bytes']).hexdigest(),'canonicalValueDigest':canonical_value_digest(candidate),'trustedContextId':UID,'logicalOperationId':UID}
  envelope=seal(candidate['bytes'],key,'isolated-fixture-key',meta,'SECRET_IMMUTABLE_VERSION')
  with open_snapshot(envelope,key,'isolated-fixture-key',meta,lambda value:parse_profile(p,value),'SECRET_IMMUTABLE_VERSION') as value:check(p+'/canonical-primitive-exact-byte-hydration',bytes(value)==candidate['bytes'])
  wrong={**meta,'secretVersionId':'00000000-0000-4000-8000-000000000003'}
  try:
   with open_snapshot(envelope,key,'isolated-fixture-key',wrong,lambda value:parse_profile(p,value),'SECRET_IMMUTABLE_VERSION'):check(p+'/wrong-immutable-version',False)
  except ValueError as e:check(p+'/wrong-immutable-version',str(e)=='PROTECTED_INPUT_AUTHENTICATION_FAILED')
  stored={'secretId':meta['secretId'],'versionId':meta['secretVersionId'],'type':meta['secretType'],'representation':meta['representation'],'profileId':p,'schemaId':meta['schemaId'],'schemaDigest':meta['schemaDigest'],'plaintextByteLength':meta['plaintextByteLength'],'valueDigest':meta['originalImportBytesDigest'],'canonicalValueDigest':meta['canonicalValueDigest'],'payloadFormat':'EXACT_SECRET_BYTES_V1'}
  selected={k:stored[k]for k in ['secretId','versionId','type']};declaration=consumer(p)
  for row in declaration['profiles']:row['schemaDigest']=schema_digest(row['profileId'])
  now=datetime(2026,9,30,tzinfo=timezone.utc)
  def load(m):return load_use_profile(candidate['bytes'],m,selected,declaration,now)
  check(p+'/current-load-use-positive',load(stored)['status']=='REFERENCE_PREFLIGHT_PASSED')
  reject_case(p+'/stored-schema-identity',lambda:load({**stored,'schemaId':'urn:kcml:wrong'}),'SECRET_PROFILE_SCHEMA_INVALID','$.schemaId')
  reject_case(p+'/stored-original-bytes-digest',lambda:load({**stored,'valueDigest':'sha256:'+'0'*64}),'SECRET_STORED_BYTES_MISMATCH')
  reject_case(p+'/stored-domain-digest',lambda:load({**stored,'canonicalValueDigest':'sha256:'+'0'*64}),'SECRET_STORED_CANONICAL_DIGEST_MISMATCH')
  foreign_type='PRIVATE_KEY'if stored['type']!='PRIVATE_KEY'else'TOTP_SEED'
  reject_case(p+'/stored-profile-type-even-with-selected-type-changed',lambda:load_use_profile(candidate['bytes'],{**stored,'type':foreign_type},{**selected,'type':foreign_type},declaration,now),'SECRET_PROFILE_SCHEMA_INVALID','$.type')
  reject_case(p+'/actual-invalid-json',lambda:decode(raw[:-1]),'INVALID_JSON')
  extra=copy.deepcopy(body);extra['serverAuthority']=UID
  reject_case(p+'/client-server-authority',lambda:decode(json.dumps(extra).encode()),'SCHEMA_ADDITIONALPROPERTIES')
 body={'stableName':'SYNTHETIC','displayName':'Synthetic','type':'TOTP_SEED','value':{'representation':'PROFILE_JSON_V1','profileId':'TOTP_BASE32_V1','profile':fixtures['TOTP_BASE32_V1']}}
 raw=json.dumps(body).encode();other=raw.replace(b'"periodSeconds": 30',b'"periodSeconds": 30.0')
 check('equivalent-domain-number-distinct-original-request-digest',decode(raw)['requestDigest']!=decode(other)['requestDigest'])
 check('equivalent-domain-number-same-canonical-value-digest',canonical_value_digest(decode(raw)['secretImportCandidate'])==canonical_value_digest(decode(other)['secretImportCandidate']))
 legacy={'stableName':'SYNTHETIC','displayName':'Synthetic','type':'CERTIFICATE','value':{'encoding':'UTF8','text':'SYNTHETIC_LEGACY_RAW'}}
 reject_case('new-complex-raw-not-format-guessed',lambda:decode(json.dumps(legacy).encode()),'SECRET_PROFILE_REQUIRED')
 check('active-import-is-exact-embedded-mask',active_import_document()==json.loads(rs['contracts/secrets/import.schema.json']['raw']))
 evidence=[('independent-native','audit/generated/resume-34d/review/secret-current/secret-native-review.json',21),('canonical-postgresql','audit/generated/resume-34d/failure-sql/secret-profile-current/postgres-tests.json',37),('actual-browser-cookie-member','audit/generated/resume-34d/secrets-browser/partition-current/partition-cookie-tests.json',14)]
 for label,path,count in evidence:
  file=ROOT/path
  if not file.exists():check(label+'/evidence-available',False);continue
  q=json.loads(file.read_text())
  check(label+'/current-consumed-scope-or-new-execution',secret_scope_current(q))
  check(label+'/actual-positive-derived-proof',q.get('checked',0)>=count and q.get('failed')==0)
  for name,d in q.get('rootImplementationDigests',{}).items():check(label+'/root-helper:'+name,hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest()==d)
  for name,d in q.get('supportSha256',{}).items():
   consumed=ROOT/name
   check(label+'/consumed-support:'+name,consumed.exists() and hashlib.sha256(consumed.read_bytes()).hexdigest()==d)
  if label=='canonical-postgresql':
   check(label+'/actual-PG18_6',q.get('canonicalEmbeddedSqlExecuted')is True and q.get('actualPostgresExecuted')is True and q.get('serverVersion','').startswith('PostgreSQL 18.6 '))
   check(label+'/exact-SQL',q.get('ddlSha256')==rs['database/secret-profile-roots.sql']['sha256'])
  elif label=='actual-browser-cookie-member':check(label+'/exact-mask',q.get('canonicalResourceSha256')==rs['contracts/secrets/profile-handoffs.schema.json']['sha256'])
 report={'sourceDocumentSha256':source,'status':'PASS' if all(c['passed']for c in checks)else'BLOCKED','checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'scope':__doc__,'sensitiveValuesInReport':False,'wholeOperationClosed':False,'evidenceReuse':{'executionSourcePreserved':True,'method':'Exact pinned execution document authority sections 8,13.15,72.21, every declared canonical resource/helper/support input; new publication/OWNER producers verified separately','validator':'scripts/evidence_scope_reuse.py'},'authenticationProof':'NOT_EVALUATED_SYNTHETIC_REFERENCE_CONTEXT','implementationAcceptance':'NOT_EVALUATED','sourceResourceSha256':{p:rs[p]['sha256']for p in ['contracts/secrets/import.schema.json','contracts/secrets/profile-handoffs.schema.json','database/secret-profile-roots.sql']}}
 out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/resume-34d/coordinator');out.mkdir(parents=True,exist_ok=True);(out/'secret-profile-native-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','checked','failed']}));return int(report['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
