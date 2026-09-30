"""Publish reviewed bounded generation root/context/atomic SQL and physical contract."""
import hashlib,json,re
from ssot_sources import ROOT,SSOT,resource_index,resources
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
BASE=ROOT/'audit/generated/resume-d362'
def main():
 text=SSOT.read_text();items=list(resources(text));rs=resource_index(items)
 import importlib.util
 spec=importlib.util.spec_from_file_location('generation_foundations_author',BASE/'persistence/combined_foundations.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 old=(BASE/'events/generation-command-links-proposed.sql').read_text();fixed=(BASE/'review/generation-command-links-corrected.sql').read_text()
 sql=module.foundations();assert sql.count(old)==1;sql=sql.replace(old,fixed)
 locator=rs['database/explicit-entities.sql']['raw'].decode();locator=locator[locator.index('CREATE TABLE idempotency_locator'):];split=sql.index('CREATE FUNCTION kcml_generation_create_atomic_closure_v1');sql=sql[:split]+locator+sql[split:]
 doc={'version':'GENERATION_CREATE_PHYSICAL_HANDOFF_V1','operationId':'generation.job.create','authority':['SSOT25.3','SSOT25.11','SSOT49.4','SSOT49.8','SSOT49.15','SSOT51.11','SSOT51.12','SSOT12.52'],'sqlResource':'database/generation-create-foundations.sql','schemaInstallation':'Fresh PUBLIC schema in an isolated pre-generation PostgreSQL18 fixture; canonical locator definition is included once, never duplicate-install with explicit-entities.sql','root':'generation_job','rootColumns':39,'authenticationRequiredColumns':56,'initialState':'DISCUSSING','generationCommandBinding':{'table':'generation_create_command_binding','columns':['logical_operation_id','trusted_context_id','argument_snapshot_id'],'appliesOnlyTo':'generation.job.create','unrelatedOperations':'No foreign key to generation-only context or snapshot'},'atomicCommit':['protected immutable initial snapshot','generation_job','exact pinned trusted generation context','scoped domain_command binding','immutable creation completion','generation.job.created domain_event','transactional_outbox','audit_event and audit_head','domain_idempotency_record','exact stable idempotency_locator'],'lookupScope':{'operationFamily':'GENERATION','callerAuthority':'OWNER_FULL','callerIdSource':'validated frozen execution descriptor stableCallerObjectId','businessTargetKind':'CREATE_ROOT','businessTargetId':'generation_job','frozenRevisionDigest':'domain_command.scope_digest = SHA256 exact canonical frozen descriptor bytes'},'replay':'Resolve stable locator under lock; retain original descriptor/output/event; never allocate another root or reinterpret current revision','locking':['owner/session/API/incarnation/deployment acceptance source locks','locator/advisory scope serialization','deferred root/context/snapshot/command/receipt identity joins','outbox lease/fence separate from immutable event delivery scope'],'fixtureScope':'Named actual PostgreSQL roots/scoped joins/locator/retention. Structural SQL evidence does not establish token verification or opaque ciphertext authentication.','requiredRemainingBeforeGeneration':['constant-time actual API credential verifier in acceptance transaction','canonical systemd/master-key/R17 crypto fixture and protected plaintext opening','complete locked RETRY phase membership and real classifier registry','failure/pending/unknown before successful root creation persistence','full native graph/consumer/repair/read/UI producer joins','whole generic SQL helper policies'],'implementationProductionAcceptance':'NOT_EVALUATED','wholeOperationClosure':'OPEN'}
 updates={'database/generation-create-foundations.sql':sql.encode(),'contracts/generation/physical-create-handoff.json':(json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode(),'contracts/generation/execution-descriptor.schema.json':(BASE/'persistence/generation-execution-descriptor.schema.json').read_bytes()}
 manifest=json.loads(rs['manifest.json']['raw'])
 for path,raw in updates.items():manifest['resources'][path]={'kind':'SQL' if path.endswith('.sql') else 'JSON','sizeBytes':len(raw),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest()}
 manifest['resourceCount']=len(manifest['resources']);updates['manifest.json']=encoded(manifest,rs['manifest.json']['raw'])
 text=rewrite(text,items,updates)
 text=text.replace('KCML-R9-RESOURCE path="database/generation-create-foundations.sql" kind="JSON"','KCML-R9-RESOURCE path="database/generation-create-foundations.sql" kind="SQL"')
 normative='''### 12.52 Fyzické kořeny a atomická generation create předávka

`contracts/generation/physical-create-handoff.json` a `database/generation-create-foundations.sql` určují konkrétní physical generation_job/domain_command kořeny, source-owned authentication/head fields, serverový contract pin a přesný sedmipolový frozen execution descriptor. Jde o technickou materializaci §§25.3/25.11/49.4/51.11/51.12, bez nového OWNER role nebo plošného terminal-parent guardu. Singleton physical keys jsou SMALLINT1; logické názvy OWNER/CURRENT/OWNER_API nejsou nové primary key hodnoty. FK a deferred guards chrání skutečné identity, initial snapshot, schema pin, context a output/event. Context constructor přijímá pouze serverový current contract pin a exact canonical descriptor bytes, nikoli klientem prohlášenou authority.

`generation_create_command_binding` se vztahuje jen na generation.job.create. Obecný domain_command nesmí požadovat generation-only context ani snapshot pro jiné operace. Command revision/key/scope souhlasí s frozen descriptor. Úspěšný create commit atomicky váže root/snapshot/context/command/completion/event/outbox/audit/idempotency/locator. Locator už při prvním commit musí přesně souhlasit s GENERATION, OWNER_FULL, stableCallerObjectId, CREATE_ROOT:generation_job, request/key/descriptor/frozen revision digests; pozdější immutable ochrana neopravuje chybné původní scope. Audit sequence/previous hash/head a archive-required outbox jsou součástí této předávky. Deklarovaný chain format1 používá SHA256 preimage ASCII("KCML-AUDIT-CHAIN") || uint32BE(1) || previousHash32 || int64BE(positive sequence) || int64BE(canonical byte length) || exact canonical bytes; initial previous hash má32zero bytes. Toto explicitní verzované pravidlo se používá jen pod deklarovaným format1, nikdy implicitně na neznámou historickou verzi. Outbox lease/fence/delivery state mají vlastní mutable concurrency, zatímco event/payload/purpose/consumer scope jsou retained immutable.

SQL modul je konkrétní dependency-ordered isolated pre-generation fixture bootstrap v čerstvém PUBLIC schema PostgreSQL18. Obsahuje převzatý canonical locator právě jednou; nesmí se slepě instalovat podruhé s explicit-entities.sql. Generátor musí vytvářet jedinou autoritativní fyzickou definici každé tabulky a zachovat exact constraints, roles, locks a deferred joins. Fixture používá výhradně syntetická auth/cipher data; opaque verifier_hash/ciphertext ani správné FK nejsou důkazem skutečného constant-time token verifieru nebo authenticated plaintext. Požadované canonical crypto/SQL fixtures podle účinného §73.7/R17 zůstávají povinné před generováním.

Tento modul neuzavírá failure/pending/unknown před vznikem úspěšného rootu, úplný RETRY phase scan, native semantic graph, read/UI/Secret konzumenty ani všechny generic operation SQL helpery. Tyto konkrétní předgenerační závazky zůstávají OPEN. Návrhový PostgreSQL fixture výsledek není akceptací vygenerované aplikace; IMPLEMENTATION_PRODUCTION_ACCEPTANCE zůstává NOT_EVALUATED.

'''
 m=re.search(r'^### 12\.52 .*?(?=^### 12\.|^## 13\.)',text,re.M|re.S)
 if m:text=text[:m.start()]+normative+text[m.end():]
 else:
  m=re.search(r'^## 13\.',text,re.M);assert m;text=text[:m.start()]+normative+text[m.start():]
 SSOT.write_text(text,encoding='utf8',newline='\n')
 for path,raw in updates.items():
  if path=='manifest.json':continue
  p=ROOT/'01_UI_CONTRACT'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 print(json.dumps({'authored':list(updates),'wholeOperationsClosed':0}))
if __name__=='__main__':main()
