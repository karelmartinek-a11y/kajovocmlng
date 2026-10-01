"""Finite create-chain duties, with exact gaps; inventory never certifies closure."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 source=hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest()
 groups={
 'generation.job.create':[
 ('GENERATION.AUTH.API_ACCEPTANCE','7.2/49.4/51.20','Complete actual acceptance adapter binds caller/channel/purpose/target to current locked token receipt','Actual token→canonical transaction→replay fixture'),
 ('GENERATION.AUTH.SESSION','7.1/49.4/51.20','Actual OWNER session material/expiry/invalidation verifier and channel binding','Valid session and expiry/revocation/cross-channel negatives'),
 ('GENERATION.AUTH.TRANSPORT','12.47/51.20','Effective gateway Authorization header ceiling and strict transport policy','Current HTTP boundary positives/oversize/repeated header negatives'),
 ('GENERATION.BASIS.UPDATE','12.41/12.49/12.51','Exact source-spec revision relation and usable native graph for UPDATE','Actual immutable spec/graph bytes and wrong lineage/content negatives'),
 ('GENERATION.BASIS.RETRY_PRODUCER','49.8/51.12','Full intent/attempt/checkpoint/dispatch outbox/evidence producer, authoritative completeness and classification','PG18.6 complete/incomplete source ledger, stale fence and competing writer fixtures'),
 ('GENERATION.BASIS.RETRY_CHILD_COMMIT','12.51/25.16/49.8/51.12','Locked completeness scan through actual child frozen-lineage/root atomic commit','PG18.6 two RETRY, changed source, rollback, idempotent replay'),
 ('GENERATION.BASIS.REPAIR','12.49/12.51/49.8','Actual repair evidence and kind-specific native graph/delegation predicates','Valid repair bytes and invalid evidence/authority/graph negatives'),
 ('GENERATION.BASIS.FOLLOW_UP','12.41/12.49/12.53','Frozen source availability/content validators with real producer wiring, preserve approved nonterminal rule','324 native-byte cases plus actual frozen-lineage child persistence'),
 ('GENERATION.ADMISSION.STAGE','12.51/49.8','All kind selectors distinguish discussion admission from execution activation prerequisites','Each kind/state/available basis matrix and actual selector fixtures'),
 ('GENERATION.ATOMIC.ALL_KINDS','12.48/12.52/49.5/51.12','Authenticated native decision→protected input→root/command/event/outbox/audit/locator for all kinds','Joined actual canonical SQL success fixture each kind'),
 ('GENERATION.PREROOT.DECISION_PRODUCERS','12.48/49.3/49.4/49.25','Actual failure-before-root/pending/cancel/unknown/reconciliation decisions and retained outcomes','Authenticated joined negative/retention/recovery matrix; no partial root/event'),
 ('GENERATION.REPLAY.RECOVERY','12.48/49.4/51.12','Actual current auth on retained replay, unknown/rollback/cancel reconciliation and audit archive producer','Concurrent replay/conflict/recovery outcomes from persisted bytes'),
 ('GENERATION.ARCHIVE.PRODUCER','12.54/49.4/51.10','Durable exact frozen schema/domain-policy bytes and dependency closure producer, identity and availability','Actual PG archive→snapshot binding→historical read/replay'),
 ('GENERATION.ARCHIVE.HISTORICAL_POLICY','12.54/51.10','Digest-pinned historical domain validator/consumer dispatcher without current-mask substitution','Same id/different immutable bytes, historical accept/reject and unavailable policy'),
 ('GENERATION.READ.FULL_NATIVE','12.48/25.11/51.2/51.10','Complete native children, persisted receipt/errors/events hydration and kind-specific consumers','Actual producer bytes→read→consumer positives and substitution/corruption negatives'),
 ],
 'secret.create':[
 ('SECRET.REGISTRY.PUBLICATION','8.12/51.20/72.21','Trusted reviewed profile publication/context/command producer; no bare registry insertion authority','Canonical PG publication material/identity/schema/review negatives'),
 ('SECRET.AUTH.LOCKED_ACCEPTANCE','7.2/8.12/49.4/51.20','Actual caller authentication/context/target and registry locks through Secret command commit','Actual native import→locked auth/registry→command transaction'),
 ('SECRET.ATOMIC.COMMAND_ROOT','8.4/8.12/49.5/51.12','Operation-specific physical Secret trusted context/domain command/root/version/event/outbox/audit/locator joins','Canonical PG integrated success/rollback/no-partial-output fixture'),
 ('SECRET.OWNER_CREDENTIAL','7.2/8.4/8.12','Reserved OWNER credential publication/type/version/activation consistency','Actual credential→immutable Secret version scoped FK/concurrent rotation/replay'),
 ('SECRET.CONSUMER.TARGET','8.8/8.12/49.22.1/51.20','Authoritative target/endpoint binding and declared supported profile/algorithm policies','Hydrated bytes against actual server consumer declaration; wrong target/variant negatives'),
 ('SECRET.CONSUMER.ACTIVATION_BROKER','8.8/49.22.1/51.20','Activation epoch, immutable selected version, actual broker grant/use/result producer joins','Actual PG broker/context/epoch transaction and expired/wrong-purpose/use negatives'),
 ('SECRET.READ.IMMUTABLE','8.4/8.8/8.12/51.10','Actual protected-row open→exact stored metadata→read/use current/historical version producer','Canonical key/SQL joined original bytes/type/schema/digest and legacy RAW fixtures'),
 ('SECRET.ERROR.RECOVERY','8.12/49.4/49.25/51.12','Operation-specific failure/unknown/cancel/replay producers and exact retained errors','Joined persistence/read recovery matrix, no secret disclosure'),
 ('SECRET.UI.REVEAL','8.5/8.6.1/8.8/72.11','Import/activation/read UI results; explicit OWNER reveal keeps own authentication contract','Actual command→read/UI result and unauthorized reveal negatives'),
 ],
 'shared':[
 ('SHARED.CRYPTO.SYSTEMD_SOURCE','8.4/50.30/73.7','Actual root-owned encrypted systemd credential read-only invocation','Actual systemd fixture or precise environment BLOCKED report'),
 ('SHARED.CRYPTO.KEY_INVOCATION','8.4/50.30/51.20','Key identity/version→invocation→protected row authority→authenticated open','Actual key producer/invocation/row joins, key/context/purpose substitution negatives'),
 ('SHARED.CRYPTO.GLOBAL_NONCE','8.4/12.54','Actual global key/nonce producer bound to generation and Secret ciphertext rows','Canonical PG duplicate/reuse/corrupt/missing-authority transaction tests'),
 ('UI.DASHBOARD_START.JOIN','43.3/49.3/49.5/72.11','Frozen worker→command→runtime result→read identity/epoch joins','Actual HTTP/PG command/result/read fixture and cross-runtime negatives'),
 ('UI.DASHBOARD_STOP.JOIN','43.3/49.3/49.5/72.11','Frozen worker→command→stop result→read identity/epoch joins','Actual HTTP/PG command/result/read fixture and wrong-target/replay negatives'),
 ('UI.GEN_EDIT_SPEC.JOIN','43.3/49.3/49.5/72.11','Frozen worker→command→spec revision result→read identity joins','Actual job/spec/revision command/result/read fixture'),
 ('UI.MANUAL_VISUAL','72.11/73.7','Mandatory actual visual review, distinct from automatic renderer and backend acceptance','Manual reviewed current screenshots/conditions; render alone insufficient'),
 ('BROWSER.BUNDLE.CAS','13.15','Full capture barrier/encrypted bundle/epoch-CAS producer and restore consumer','Actual named browser bundle transaction and concurrent stale CAS fixtures'),
 ('BROWSER.ACCOUNT_POSTCONDITIONS','13.15','Actual expected account/tenant marker binding after restore','Actual declared consumer marker observation, no fixture valid flag'),
 ('BROWSER.BRIDGE','13.15','Required client-certificate and OWNER Device Bridge capture/restore authority','Exact bridge/permission/certificate context fixtures'),
 ('BROWSER.SERIALIZER_KEYS_GENERATORS','13.15','All required clone/key/generator/IDB/WebAuthn capture and restore postconditions','Real engine fixtures each required supported member; cookies14 not full proof'),
 ('SQL.HELPERS.CONCRETE_CALL_SITES','25.11/51.8/51.12/51.20','Four generic helper definitions and all262 actual scoped call-site plans','Executable canonical PG18.6 helpers against real physical roots/context; no generic slots'),
 ]}
 obligations=[]
 for area,rows in groups.items():
  for id,authority,gap,verify in rows:
   obligations.append({'id':id,'area':area,'layer':'SHARED_DEPENDENCY'if area=='shared'else'OPERATION_DESIGN','state':'BLOCKED'if id=='SHARED.CRYPTO.SYSTEMD_SOURCE'else'OPEN','authority':['00_SSOT/KajovoCMLNG_SSOT.md#section.'+s for s in authority.split('/')],'missing':gap,'verification':verify,'dependencies':[],'sourceSha256':source,'independentReview':'PENDING_INTEGRATED_CURRENT_RESULT','implementationAcceptance':'NOT_EVALUATED'})
 report={'format':'CREATE_CHAIN_CLOSURE_CHECKLIST_V1','sourceSha256':source,'scope':'Known complete admission/persistence/read chain duties for these two create operations; cross-environment duties scoped explicitly below. Field-level completeness and integrated review remain required.','ownOperationDuties':sum(x['area']!='shared'for x in obligations),'sharedDependencies':sum(x['area']=='shared'for x in obligations),'obligations':obligations,'futureImplementationAcceptance':{'state':'NOT_EVALUATED','scope':'Generated backend/runtime/live consumer acceptance after mandatory A/B design and named fixtures. No A/B obligation moved here.'},'wholeOperationsClosed':[],'SSOT_CONTRACT_READY':'BLOCKED','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 (ROOT/'audit/SSOT_CREATE_CLOSURE_CHECKLIST.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'source':source,'duties':len(obligations),'wholeClosed':0}))
if __name__=='__main__':main()
