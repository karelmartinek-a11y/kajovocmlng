"""Materialize reviewed producer/archive/authority modules; no whole-operation certification."""
import hashlib,json,re
from ssot_sources import ROOT,SSOT,resources,resource_index
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
BASE=ROOT/'audit/generated/resume-905'
SQL={'database/generation-frozen-archive.sql':'archive/generation-frozen-archive.sql','database/generation-retry-producer-child.sql':'retry/producer-child.sql','database/generation-locator-lock.sql':'sql/generation-locator-lock-proposed.sql','database/generation-protected-registry-link.sql':'key/generation-protected-registry-link.sql','database/generation-preroot-frozen-archive.sql':'archive/preroot-transfer/generation-preroot-frozen-archive.sql','database/secret-profile-publication.sql':'secrets/secret-profile-publication.sql','database/secret-owner-binding.sql':'secrets/owner-secret-binding.sql'}
NORM='''### 12.55 Frozen producers and transactional child handoffs

The exact embedded modules in `contracts/generation/producer-archive-handoffs.json` are effective technical materializations under §§12.48,12.51,49.4,49.8,51.8,51.10,51.12,51.20. Install each module exactly once after its declared physical dependencies. Their fields/constraints/functions are authoritative for this bounded handoff; generic operation helpers and the full operation remain separately mandatory. No client/model declaration grants archive, classifier, key or caller authority.

`database/generation-frozen-archive.sql` stores exact immutable SCHEMA/DOMAIN_POLICY/AUTHORITY/POLICY_IMPLEMENTATION bytes under kind/id/digest. Producer verifies exact bytes, declared dependency closure and source identity; accepted successful snapshot and logical command must bind to that frozen policy in the same commit. Historical hydration uses archived bytes and the exact statically loaded implementation revision via `scripts/generation_read_hydration_archive.py`; unavailable/unsupported code or authority is BLOCKED, never current-mask substitution or execution of arbitrary archived Python. This version materializes request hydration rules only. Full kind admission and authenticated release authority remain mandatory explicit obligations.

`database/generation-preroot-frozen-archive.sql` requires a separate immutable archive binding to the accepted protected pre-root snapshot, in the same commit as retained command/outcome/audit. No job or created event is manufactured for pending/failure. If that same snapshot later becomes successful, both insertion orders enforce identical logical command, schema, policy and dependency closure; replacing them with another available policy is forbidden. Rollback of later success leaves the earlier retained snapshot/outcome/archive untouched. Successful snapshot FK remains mandatory. Archive-only read is scoped by exact snapshot and logical command; actual authenticated retained-outcome reader, decision producers and full kind policy remain distinct obligations.

`database/generation-retry-producer-child.sql` captures actual persisted phase membership and requires a frozen scan reservation under the source/phase gate through RETRY child commit. Completeness includes all persisted selected members, actual current evidence bytes/classifier and fence; UNKNOWN/incomplete/stale members cannot authorize a child. Reservation, lineage/root and canonical command/event/outbox/audit/locator commit atomically, or all roll back. Two requests and source writers must serialize under the same gate. This does not replace full §49.8 intent/attempt/dispatch/checkpoint/raw-evidence producer or authenticate a fixture receipt. Native caller/crypto admission and full lifecycle producer remain separate prerequisites. Approved FOLLOW_UP nonterminal semantics and UPDATE/REPAIR own rules are preserved.

`database/generation-locator-lock.sql` resolves retained stable locator C0 then original frozen scoped idempotency row C1 from an already authenticated class-B context, before class-E source locks. It grants neither fresh admission nor caller-derived class-A advisory locks after B. Missing context or conflicting request/retained scope rejects explicitly; replay never changes the old frozen scope.

`database/generation-protected-registry-link.sql` defers successful/pre-root protected snapshot to global reservation joins until commit and checks both directions, canonical profile/key/version/purpose, ciphertext digest and exact command/context-derived AAD. The actual root-owned encrypted systemd credential/invocation/key producer and Secret typed context joins remain mandatory; synthetic manager fixtures do not satisfy them.

'''
SECRET_NORM='''### 8.14 Trusted profile publication and reserved OWNER binding

`database/secret-profile-publication.sql` atomically publishes the ten already effective limited profiles with exact schema and review bytes, source identity and immutable archive. Only the declared safe publisher capability can publish; the distinct safe reader capability returns the exact archive-joined descriptor, not client declarations. A pre-existing LOGIN/SUPERUSER/CREATEDB/CREATEROLE/REPLICATION/BYPASSRLS/INHERIT reserved role causes explicit installation failure; its privileges must not be silently rewritten. Unique-index first publication serializes identical/conflicting concurrent attempts. No new advisory namespace or format guessing is introduced. Actual trusted review/release and locked caller/context/command producers remain required.

`database/secret-owner-binding.sql` materializes the §51.20 composite OWNER credential→Secret/version FK and deferred reserved KCML_OWNER_API_KEY/API_KEY/current ACTIVE/version/fingerprint consistency on both sides. This does not assert numeric equality of version and activation epoch or substitute for the atomic authenticated rotation producer. Immutable RAW, exact sensitive bytes, the ten import masks and explicit OWNER reveal remain unchanged.

'''
def main():
 text=SSOT.read_text();items=list(resources(text));rs=resource_index(items);updates={p:(BASE/q).read_bytes()for p,q in SQL.items()}
 doc={'version':'GENERATION_PRODUCER_ARCHIVE_HANDOFFS_V1','authority':['SSOT12.55','SSOT8.14','SSOT49.8','SSOT51.12','SSOT51.20'],'generationInstallationOrder':['database/generation-create-foundations.sql','database/canonical-crypto-registry.sql','database/generation-create-authentication.sql','database/generation-create-preroot.sql','database/generation-create-read.sql','database/generation-locked-retry.sql',*[p for p in SQL if 'secret-'not in p]],'secretInstallationOrder':['database/secret-profile-roots.sql','database/secret-profile-publication.sql','database/secret-owner-binding.sql'],'ownerBindingPrerequisite':'Exact canonical owner_api_credential table and bootstrap/rotation producer; isolated root/credential fixture does not prove whole owner authority','historicalRead':'scripts/generation_read_hydration_archive.py','currentOnlyReadAdapter':'scripts/generation_read_hydration.py is prior bounded current-policy reference, not a substitute for required archived hydration','uiRead':'scripts/owner_ui_terminal_read.py requires actual command/context/target/artifact joins; display remains BLOCKED_PENDING_EFFECT_HYDRATION until semantic effect proof','wholeOperationsClosed':[],'SSOT_CONTRACT_READY':'BLOCKED','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 updates['contracts/generation/producer-archive-handoffs.json']=(json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode()
 # Preserve the common installer when an older author is subsequently rerun.
 chain=json.loads(rs['contracts/generation/create-chain-handoffs.json']['raw'])
 for p in [p for p in SQL if 'secret-'not in p]:
  if p not in chain['sqlInstallationOrder']:chain['sqlInstallationOrder'].append(p)
 chain['producerArchive']='contracts/generation/producer-archive-handoffs.json'
 updates['contracts/generation/create-chain-handoffs.json']=(json.dumps(chain,ensure_ascii=False,indent=2)+'\n').encode()
 manifest=json.loads(rs['manifest.json']['raw'])
 for p,raw in updates.items():manifest['resources'][p]={'kind':'SQL'if p.endswith('.sql')else'JSON','sizeBytes':len(raw),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest()}
 manifest['resourceCount']=len(manifest['resources']);updates['manifest.json']=encoded(manifest,rs['manifest.json']['raw']);text=rewrite(text,items,updates)
 for p in SQL:text=text.replace('KCML-R9-RESOURCE path="'+p+'" kind="JSON"','KCML-R9-RESOURCE path="'+p+'" kind="SQL"')
 for header,norm,next_header in [('12.55',NORM,'13.'),('8.14',SECRET_NORM,'9.')]:
  match=re.search(r'^### '+re.escape(header)+r' .*?(?=^### |^## )',text,re.M|re.S)
  if match:text=text[:match.start()]+norm+text[match.end():]
  else:
   pos=re.search(r'^## '+re.escape(next_header),text,re.M);assert pos;text=text[:pos.start()]+norm+text[pos.start():]
 SSOT.write_text(text,encoding='utf8',newline='\n')
 for p,raw in updates.items():
  if p=='manifest.json':continue
  target=ROOT/'01_UI_CONTRACT'/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 print(json.dumps({'resources':list(updates),'wholeClosed':0}))
if __name__=='__main__':main()
