"""Author reviewed bounded Secret producers; no complete-operation attestation."""
import hashlib,json,re
from pathlib import Path
from ssot_sources import ROOT,SSOT,resources,resource_index
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
BASE=ROOT/'audit/generated/resume-8cc'
SQL={
 'database/secret-command-chain.sql':'secrets/credential-eligibility/secret-command-chain-eligible.sql',
 'database/secret-record-status.sql':'secrets/status/secret-record-status.sql',
 'database/secret-owner-api-value-read.sql':'broker/secret-owner-api-value-read.sql',
}
NORM='''### 8.16 Derived Secret root persistence and typed OWNER hydration

`database/secret-record-status.sql` implements only the OWNER-approved derived projection in §§8.3,25.6 (OWNER-SECRET-ROOT-STATUS-2026-10-01). The root has no separately editable lifecycle. Create/import output and its frozen event receipt carry `recordStatus = INACTIVE`; version lifecycle remains CREATED/ACTIVE/RETIRED. Existing valid rows migrate their status projection without rewriting immutable IDs, bytes, versions or active pointers. Invalid lineage blocks migration. Root/version mutations validate the final committed projection; the deferred validator performs no late lower-class mutation after the audit head. Activation, rotation, deactivation and deletion retain their own command/authorization/invalidation requirements. DELETED takes precedence but cannot conceal invalid pointer integrity.

`database/secret-command-chain.sql` and `scripts/secret_command_chain.py` specify the bounded genuine API-token/strict import, C0 locator/C1 idempotency claim, ordered OWNER/root locks, immutable context/command/version/receipt/event/outbox and last audit-head transaction. Context issuance is a separate safe trusted capability. A create context grants no broker or reveal authority. The frozen semantic-result bytes must equal the exact canonical response projection and their digest must bind command/completion/idempotency; mutually equal arbitrary digests are insufficient. Missing required artifacts or contradictory semantic bytes abort the complete transaction. The bounded reference producer still cannot dispatch the full operation while authoritative retention/failure/unknown producers, API-use evidence, target authority, complete rotation invalidation and genuine key/nonce invocation remain unresolved. Fixture retention dates and fixture key injection are not those producers.

`contracts/secrets/owner-value-read.schema.json` and `scripts/secret_value_read_transport.py` define the existing OWNER GET /secrets/{id}/value transport: canonical UUID path, no body, empty query selects CURRENT and exactly one versionId UUID selects IMMUTABLE_VERSION. Unknown/duplicate query (including duplicate percent-decoded names), malformed URI encoding and extra native fields reject. This is the explicit OWNER reveal boundary, never a create/event/log response. Authorized hydration uses the persisted root/version and derived status under locks. DELETED cannot be revived by selecting history; an explicit retained version of an INACTIVE root does not activate it. The reserved OWNER API credential still requires its distinct OWNER-session reveal contract. REVEAL and COPY use the same revealed immutable version and exact original bytes; COPY does not re-resolve current activation. PROFILE response includes its exact typed approved profile and original bytes, without format guessing; no unactivated full-browser profile is exposed. Complete browser §13.15 and backend/UI effect pipelines remain mandatory.

'''
def main():
 decision=json.loads((ROOT/'audit/OWNER_SECRET_ROOT_STATUS_DECISION.json').read_text())
 if decision.get('approved') is not True or decision.get('decisionId')!='OWNER-SECRET-ROOT-STATUS-2026-10-01' or decision.get('values')!=['INACTIVE','ACTIVE','DELETED']:
  raise ValueError('SECRET_ROOT_STATUS_OWNER_DECISION_REQUIRED')
 text=SSOT.read_text();items=list(resources(text));rs=resource_index(items)
 updates={name:(BASE/path).read_bytes()for name,path in SQL.items()}
 # One exact projection shared with native output/event masks, not a new status authority.
 raw=updates['database/secret-command-chain.sql'].decode()
 old="'versionNumber',v.version_number::text,'versionState','CREATED','activeVersionId'"
 if raw.count(old)!=1 and raw.count("'versionNumber',v.version_number::text,'versionState','CREATED','recordStatus','INACTIVE','activeVersionId'")!=1:raise ValueError('SECRET_RECEIPT_PROJECTION_SOURCE_CHANGED')
 updates['database/secret-command-chain.sql']=raw.replace(old,"'versionNumber',v.version_number::text,'versionState','CREATED','recordStatus','INACTIVE','activeVersionId'").encode()
 helper=(BASE/'secrets/credential-eligibility/secret_command_chain_eligible.py').read_text()
 helper=helper.replace("'versionState':'CREATED','activeVersionId'","'versionState':'CREATED','recordStatus':'INACTIVE','activeVersionId'")
 helper=helper.replace("fail('SECRET_RECORD_STATUS_AUTHORITY_UNRESOLVED')","fail('SECRET_RETENTION_AUTHORITY_UNRESOLVED')")
 helper=helper.replace('normative vocabulary/default is still OPEN; this bounded producer does not\n borrow version.CREATED as record lifecycle.', 'approved vocabulary/default is INACTIVE; the argument must match that exact\n server projection and does not borrow version.CREATED as record lifecycle.')
 helper=helper.replace(' native=decode_http('," if root_status!='INACTIVE':fail('SECRET_CREATE_RECORD_MUST_BE_INACTIVE')\n native=decode_http(",1)
 (ROOT/'scripts/secret_command_chain.py').write_text(helper)
 for name in ['secret_owner_value_read.py','secret_value_read_transport.py']:
  (ROOT/'scripts'/name).write_bytes((BASE/'broker'/name).read_bytes())
 read=json.loads((BASE/'broker/secret-value-read.schema.json').read_bytes())
 updates['contracts/secrets/owner-value-read.schema.json']=(json.dumps(read,ensure_ascii=False,indent=2)+'\n').encode()
 root_schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:secret-root-status:1','type':'string','enum':['INACTIVE','ACTIVE','DELETED'],'readOnly':True,'x-authority':['SSOT8.3','SSOT25.6',decision['decisionId']],'x-derived':True}
 updates['contracts/secrets/root-status.schema.json']=(json.dumps(root_schema,indent=2)+'\n').encode()
 handoff={'contractId':'SECRET_EFFECTIVE_HANDOFFS_V1','authority':['SSOT8.3','SSOT8.15','SSOT8.16','SSOT25.6','SSOT49.4','SSOT51.6','SSOT51.20','SSOT72.21'],
  'installationDependencies':['database/generation-create-foundations.sql','database/canonical-crypto-registry.sql','database/secret-profile-roots.sql','database/secret-profile-publication.sql','database/secret-owner-binding.sql',*SQL],
  'createReceipt':'urn:kcml:create-operation-design:1#/$defs/SecretCreated','recordStatusSchema':'contracts/secrets/root-status.schema.json','valueReadSchema':'contracts/secrets/owner-value-read.schema.json',
  'ui':{'page':'13','revealAction':'REVEAL','copyAction':'COPY','copyPostcondition':'same revealed immutable version original bytes; no current-version re-resolution','statusInput':'locked authoritative root projection; never version lifecycle inference'},
  'open':['SECRET.AUTH.API_USAGE','SECRET.ERROR.RETAINED_OUTCOME','SECRET.OWNER_CREDENTIAL.INVALIDATION','SECRET.CONSUMER.TARGET','SECRET.CONSUMER.ACTIVATION_BROKER','SHARED.CRYPTO.SYSTEMD_SOURCE','SHARED.BROWSER.FULL_CONTRACT'],
  'wholeOperationClosed':False,'SSOT_CONTRACT_READY':'BLOCKED','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 updates['contracts/secrets/effective-handoffs.json']=(json.dumps(handoff,indent=2)+'\n').encode()
 publisher=json.loads(rs['contracts/generation/producer-archive-handoffs.json']['raw'])
 for module in SQL:
  if module not in publisher['secretInstallationOrder']:publisher['secretInstallationOrder'].append(module)
 updates['contracts/generation/producer-archive-handoffs.json']=encoded(publisher,rs['contracts/generation/producer-archive-handoffs.json']['raw'])
 manifest=json.loads(rs['manifest.json']['raw'])
 for name,raw in updates.items():manifest['resources'][name]={'kind':'SQL'if name.endswith('.sql')else'JSON','sizeBytes':len(raw),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest()}
 manifest['resourceCount']=len(manifest['resources']);updates['manifest.json']=encoded(manifest,rs['manifest.json']['raw'])
 text=rewrite(text,items,updates)
 for name in SQL:text=text.replace('KCML-R9-RESOURCE path="'+name+'" kind="JSON"','KCML-R9-RESOURCE path="'+name+'" kind="SQL"')
 match=re.search(r'^### 8.16 .*?(?=^### |^## )',text,re.M|re.S)
 if match:text=text[:match.start()]+NORM+text[match.end():]
 else:
  end=re.search(r'^## 9\.',text,re.M);assert end;text=text[:end.start()]+NORM+text[end.start():]
 SSOT.write_text(text,encoding='utf8',newline='\n')
 for name,raw in updates.items():
  if name=='manifest.json':continue
  p=ROOT/'01_UI_CONTRACT'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 print(json.dumps({'authored':list(updates),'wholeOperationsClosed':0}))
if __name__=='__main__':main()
