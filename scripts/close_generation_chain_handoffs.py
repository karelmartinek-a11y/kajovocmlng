"""Publish reviewed generation chain modules without replacing its canonical roots."""
import hashlib,json,re
from ssot_sources import ROOT,SSOT,resources,resource_index
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
BASE=ROOT/'audit/generated/resume-34d'
SQL={
 'database/canonical-crypto-registry.sql':'auth-crypto/canonical-crypto-registry-proposed.sql',
 'database/generation-create-authentication.sql':'auth-crypto/authentication-request-binding-proposed.sql',
 'database/generation-create-preroot.sql':'failure-sql/failure-before-root-extension.sql',
 'database/generation-create-read.sql':'read-ui/generation-create-read-storage.sql',
 'database/generation-locked-retry.sql':'retry-graph/locked-retry-ledger.sql',
}
NORM='''### 12.54 Authenticated generation chain modules

`contracts/generation/create-chain-handoffs.json` stanoví dependency order konkrétních SQL modulů po canonical generation-create-foundations. Tyto moduly jsou účinné omezené technické předávky, nikoli náhrada unresolved generic operation helpers ani uzavření celé operace. Každý modul musí být instalován právě jednou; authoring původních foundations je nesmí přepsat ani odstranit. Referenční auditní Python adapters jsou návrhové důkazy; nejsou vygenerovanou aplikací.

'''

def main():
 text=SSOT.read_text();items=list(resources(text));rs=resource_index(items)
 updates={path:(BASE/owned).read_bytes() for path,owned in SQL.items()}
 for path,owned in {
  'contracts/generation/root-storage-read.schema.json':'read-ui/generation-root-storage-read.schema.json',
  'contracts/generation/create-consumer-projections.json':'read-ui/consumer-projections.proposed.json',
  'contracts/generation/protected-input-metadata.schema.json':'auth-crypto/protected-input-metadata.schema.json',
  'contracts/generation/protected-input-crypto-profile.json':'auth-crypto/protected-input-crypto-profile.json',
  'contracts/generation/owner-api-verifier-profile.json':'auth-crypto/owner-api-verifier-profile.json',
 }.items():updates[path]=(BASE/owned).read_bytes()
 doc={'version':'GENERATION_CREATE_CHAIN_HANDOFFS_V1','operationId':'generation.job.create','authority':['SSOT7.2','SSOT8.4','SSOT12.48','SSOT12.51','SSOT12.52','SSOT12.54','SSOT49.4','SSOT49.8','SSOT51.12','SSOT51.20'],
  'sqlInstallationOrder':['database/generation-create-foundations.sql',*SQL],
  'authentication':{'source':'database/generation-create-authentication.sql','materialVerifier':'scripts/generation_auth_acceptance.py','requestBinding':['authenticated_request_digest','authenticated_descriptor_digest','api_credential_activation_epoch'],'locksUntil':'complete accepted command/root/queue/event/outbox/audit COMMIT','replay':'Authenticate current material before retained locator read; frozen receipt is not new request authority','ownerApiExpiry':'NOT_APPLICABLE_BY_SSOT7.2','status':'BOUNDED_REFERENCE_VERIFIED_FULL_CHAIN_OPEN'},
  'protectedInput':{'reference':'scripts/generation_auth_crypto.py','productionKeySource':'SSOT8.4/50.30 encrypted systemd credential source, read-only per invocation','status':'BLOCKED_ACTUAL_SYSTEMD_SOURCE_GLOBAL_KEY_NONCE_REGISTRY_AND_EFFECTIVE_TRANSPORT_POLICY'},
  'beforeRoot':{'source':'database/generation-create-preroot.sql','preAcceptance':'No durable command/root/event; logicalOperationId=null','acceptedOutcomes':['ACCEPTED','FAILED_RETRY_SAME_OPERATION','FAILED_UNKNOWN_RECONCILE','FAILED_TERMINAL','CANCELLED_TERMINAL'],'atomicMembers':['trusted context','protected pre-root input','domain command','immutable retained outcome','locator','business idempotency','typed command audit','archive outbox when pinned policy requires'],'createdEvent':'Forbidden without successful root','status':'BOUNDED_SQL_REFERENCE_VERIFIED_RECOVERY_PRODUCER_AND_PENDING_TRANSFER_OPEN'},
  'read':{'source':'database/generation-create-read.sql','internalRootMask':'contracts/generation/root-storage-read.schema.json','visibility':'SERVER_REPOSITORY_ONLY','consumerProjections':'contracts/generation/create-consumer-projections.json','retainedSchemaResolution':'Exact retained bundle digest/schema identity/declared dependency closure; never substitute current mask','status':'BOUNDED_READ_VERIFIED_ARCHIVED_POLICY_PRODUCER_FULL_PUBLIC_UI_OPEN'},
  'retry':{'source':'database/generation-locked-retry.sql','scanner':'scripts/generation_locked_retry.py','writerGate':'Same selected phase FOR UPDATE for membership/current-state/evidence changes','lockLifetime':'scan, actual bytes validation, frozen child persistence COMMIT','stages':['ADMISSION_DISCUSSION','EXECUTION_DISPATCH'],'status':'BOUNDED_PROJECTION_VERIFIED_FULL49_8_PRODUCER_CHILD_COMMIT_WIRING_OPEN'},
  'wholeOperationClosed':False,'SSOT_CONTRACT_READY':'BLOCKED','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 for path in ['database/generation-frozen-archive.sql','database/generation-retry-producer-child.sql','database/generation-locator-lock.sql','database/generation-protected-registry-link.sql']:
  if path in rs and path not in doc['sqlInstallationOrder']:doc['sqlInstallationOrder'].append(path)
 if 'contracts/generation/producer-archive-handoffs.json'in rs:doc['producerArchive']='contracts/generation/producer-archive-handoffs.json'
 updates['contracts/generation/create-chain-handoffs.json']=(json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode()
 manifest=json.loads(rs['manifest.json']['raw'])
 for path,raw in updates.items():manifest['resources'][path]={'kind':'SQL' if path.endswith('.sql') else 'JSON','sizeBytes':len(raw),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest()}
 manifest['resourceCount']=len(manifest['resources']);updates['manifest.json']=encoded(manifest,rs['manifest.json']['raw'])
 text=rewrite(text,items,updates)
 for path in SQL:text=text.replace('KCML-R9-RESOURCE path="'+path+'" kind="JSON"','KCML-R9-RESOURCE path="'+path+'" kind="SQL"')
 norm=NORM+(BASE/'auth-crypto/normative-amendment.md').read_text()+'\n'+(BASE/'failure-sql/normative-preroot-amendment.md').read_text()+'\n'+(BASE/'retry-graph/normative-amendment.md').read_text()+'\n'+(BASE/'read-ui/normative-read-handoff.md').read_text()+'\n'
 # Nested agent headings do not introduce competing top-level SSOT sections.
 norm=norm.replace('This proposal selects explicit technical primitive/codec details absent from the', 'This technical materialization selects explicit primitive/codec details absent from the').replace('Root reviews and authors it into effective normative\nsections and embedded resources.', 'These explicit technical details are effective under this section and its embedded resources; activation still requires all named authority/fixture prerequisites.')
 norm=re.sub(r'^#{1,4} (?!12\.54)(.*)$',r'##### \1',norm,flags=re.M)
 norm=norm.replace('##### 12.54 Authenticated generation chain modules','### 12.54 Authenticated generation chain modules')
 m=re.search(r'^### 12\.54 .*?(?=^### 12\.|^## 13\.)',text,re.M|re.S)
 if m:text=text[:m.start()]+norm+'\n'+text[m.end():]
 else:
  m=re.search(r'^## 13\.',text,re.M);assert m;text=text[:m.start()]+norm+'\n'+text[m.start():]
 SSOT.write_text(text,encoding='utf8',newline='\n')
 for path,raw in updates.items():
  if path=='manifest.json':continue
  p=ROOT/'01_UI_CONTRACT'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 print(json.dumps({'authored':list(updates),'wholeOperationsClosed':0}))
if __name__=='__main__':main()
