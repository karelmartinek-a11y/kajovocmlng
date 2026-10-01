"""Author/check six OWNER session list/revoke boundaries, without final receipts.

Coordinator executes publication after independent semantic review. This script
never grants runtime readiness; manifests/integrity are regenerated after evidence.
"""
import argparse,copy,hashlib,json
from ssot_sources import ROOT,SSOT,resources,resource_index
from owner_session_family_contracts import contracts,NORMATIVE
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
PAYLOAD='contracts/payload-contracts.json'
CATALOG='contracts/operation-contracts.json'
PROFILE='contracts/owner-session-family.json'
SCHEMA='contracts/owner-session-family.schema.json'
MAPPING='closure/contracts/owner-session-family-map.json'
BEGIN='<!-- KCML-OWNER-SESSION-FAMILY-V1-BEGIN -->'
END='<!-- KCML-OWNER-SESSION-FAMILY-V1-END -->'

def digest(value):
 return 'sha256:'+hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def redigest(old,new):
 if 'canonicalDigest' not in old:return new
 previous=copy.deepcopy(old);wanted=previous.pop('canonicalDigest')
 if digest(previous)==wanted:
  after=copy.deepcopy(new);after.pop('canonicalDigest',None);new['canonicalDigest']=digest(after)
 elif 'records' in old and digest(old['records'])==wanted:new['canonicalDigest']=digest(new['records'])
 elif digest({**previous,'canonicalDigest':None})==wanted:new['canonicalDigest']=digest({**new,'canonicalDigest':None})
 else:raise ValueError('UNRESOLVED_CANONICAL_DIGEST_RECIPE')
 return new

def updates(rs):
 package=contracts(rs);package['publicationStatus']='COORDINATOR_REVIEWED_BOUNDARY_DEFINITIONS';package['projectionGuarantee']='Effective profiles, native registry and physical projections are enforced by scripts/close_owner_session_family.py --check; whole operation closure is separately BLOCKED on the explicit A/B obligations.'
 for operation in package['operations']:operation['eventApplicability'].pop('technicalAllocationNeedsCoordinatorReview',None)
 payload=json.loads(rs[PAYLOAD]['raw']);old=copy.deepcopy(payload)
 cat=json.loads(rs[CATALOG]['raw']); before=copy.deepcopy(cat)
 definitions={}; mappings=[]
 for operation in package['operations']:
  oid=operation['operationId']; matches=[r for r in payload['records']if r['operationId']==oid];assert len(matches)==1,'PAYLOAD_OPERATION_NOT_UNIQUE'
  row=matches[0]
  for role,field in [('command','requestSchema'),('response','responseSchema'),('event','eventSchema')]:
   row[field]=copy.deepcopy(operation[field]);native=copy.deepcopy(operation[field]);native['$id']='urn:kcml:r9:operation:'+oid+':'+role
   definitions[oid+':'+role]=native
   mappings.append({'operationId':oid,'boundary':field,'schemaId':native['$id'],'payloadPointer':PAYLOAD+'#/records/'+str(payload['records'].index(row))+'/'+field,'registryPointer':CATALOG+'#/$defs/'+oid+':'+role,'projectionPath':'01_UI_CONTRACT/'+PAYLOAD})
  row['eventApplicability']='AGGREGATE_STREAM'if oid.endswith('revoke')else'NOT_APPLICABLE'
  row['eventApplicabilityAuthority']=operation['eventApplicability']
  row['transportPolicy']=operation['transport'];row['domainContractRef']=PROFILE+'#/operations/'+str(package['operations'].index(operation))
  row['semanticRules']=['OWNER_CURRENT_CREDENTIAL_AND_CHANNEL_BINDING','HTTP_CLOSED_QUERY_AND_NO_BODY','SERVER_ONLY_OWNER_CURRENT_TIME_AND_DIGEST','SOURCE_BOUND_DOMAIN_POLICY_REQUIRED','CANONICAL_IMMUTABLE_RESULT_AND_EVENT_HYDRATION','NO_PRIVATE_AUTHENTICATION_FIELDS_IN_PUBLIC_READ']
  if oid.endswith('revoke'):row['semanticRules']+=['SELECTED_SESSION_STATE_VERSION_CAS','SAME_TARGET_IRREVOCABLE_CONFLICT_DO_NOT_RETRY','SCOPED_IDEMPOTENT_REPLAY_CURRENT_AUTH','ROOT_SESSION_COMMAND_EVENT_OUTBOX_AUDIT_LOCATOR_ATOMIC','UNKNOWN_COMMIT_REQUIRES_RECONCILIATION']
  cm=[r for r in cat['records']if r['operationId']==oid];assert len(cm)==1,'CATALOG_OPERATION_NOT_UNIQUE';cr=cm[0];prior=copy.deepcopy(cr)
  cr['commandSchemaRef']='urn:kcml:r9:operation:'+oid+':command';cr['responseSchemaRef']='urn:kcml:r9:operation:'+oid+':response';cr['eventSchemaRef']='urn:kcml:r9:operation:'+oid+':event';cr['domainContractRef']=row['domainContractRef'];redigest(prior,cr)
 cat.setdefault('$defs',{}).update(definitions)
 profiles={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:owner-session-record-admin:1','$defs':{'SessionPublic':package['sessionPublicSchema'],'AdmissionFailure':package['admissionFailureSchema'],**definitions}}
 mapping={'format':'KCML-OWNER-SESSION-FAMILY-MAP/1','familyId':package['familyId'],'boundaries':mappings,'admissionFailurePointer':SCHEMA+'#/$defs/AdmissionFailure','authoring':'scripts/close_owner_session_family.py --check','wholeOperationsClosed':0,'sharedDependencies':package['sharedObligations'],'implementationAcceptance':'NOT_EVALUATED'}
 return {PAYLOAD:encoded(redigest(old,payload),rs[PAYLOAD]['raw']),CATALOG:encoded(redigest(before,cat),rs[CATALOG]['raw']),PROFILE:(json.dumps(package,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode(),SCHEMA:(json.dumps(profiles,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode(),MAPPING:(json.dumps(mapping,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()}

def published_norm():
 return NORMATIVE.replace('84-case reference proof','source-bound reference proof').replace('`operation-mask-delta.json` replaces','`contracts/owner-session-family.json` replaces').replace('It is an author proposal, not effective canonical authority. Coordinator must publish it, its native codecs, registry/schema projections and authoring rules together.','This effective technical supplement publishes exact boundary profiles, registry projections and authoring rules together. It does not mark shared A/B obligations or whole operations as closed.').replace('Device metadata proposes exact','Device metadata exposes exact').replace('The proposed exact domain event is','The exact domain event is').replace('Stable event type is a technical allocation requiring coordinator publication, not a new business capability.','Stable event type is a published technical allocation for the existing local mutation.').replace('Before design closure, the coordinator must publish/review the technical metadata/event/error/cursor/CAS specializations; bind','Before whole-operation design closure, bind')

def normative(text):
 block=BEGIN+'\n'+published_norm()+'\n'+END
 if BEGIN in text:
  a=text.index(BEGIN);b=text.index(END,a)+len(END);return text[:a]+block+text[b:]
 return text+'\n\n'+block+'\n'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
 text=SSOT.read_text();items=list(resources(text));rs=resource_index(items);wanted=updates(rs)
 pending=[p for p,raw in wanted.items()if p not in rs or rs[p]['raw']!=raw]
 projections={ROOT/'01_UI_CONTRACT'/p:raw for p,raw in wanted.items()}
 pending+=['projection:'+p.relative_to(ROOT).as_posix()for p,raw in projections.items()if not p.exists()or p.read_bytes()!=raw]
 norm_present=BEGIN+'\n'+published_norm()+'\n'+END in text
 if args.check:
  print(json.dumps({'status':'PASS'if not pending and norm_present else'BLOCKED','pending':pending,'normativePresent':norm_present,'boundaries':6,'wholeOperationsClosed':0}));return int(bool(pending)or not norm_present)
 SSOT.write_text(normative(rewrite(text,items,wanted)),encoding='utf8',newline='\n')
 for p,raw in projections.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 print(json.dumps({'authored':list(wanted),'boundaries':6,'wholeOperationsClosed':0,'finalManifestReceipt':'PENDING_AFTER_EVIDENCE'}));return 0
if __name__=='__main__':raise SystemExit(main())
