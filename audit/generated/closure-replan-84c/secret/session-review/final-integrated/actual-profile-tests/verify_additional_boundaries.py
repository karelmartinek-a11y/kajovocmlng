from pathlib import Path
import sys,json,copy,hashlib
OUT=Path(__file__).parent;sys.path.insert(0,str(OUT))
from family_reference import *
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
checks=[]
def ok(i):checks.append({'id':i,'status':'PASS'})
def neg(i,s,v,fn):
 d=Draft202012Validator(s,format_checker=FormatChecker());d.validate(v);bad=copy.deepcopy(v);fn(bad)
 try:d.validate(bad)
 except ValidationError as e:checks.append({'id':i,'status':'PASS','validator':e.validator,'path':list(e.absolute_path)});return
 raise AssertionError(i+' accepted')
s=Store();sid,_=s.add();api=s.authenticate(s.api,'OWNER_API_KEY');r=s.revoke(api,sid,'0','independent-extended');event=s.events[-1];mask=OPS['owner.session.revoke']['eventSchema'];Draft202012Validator(mask,format_checker=FormatChecker()).validate(event)
assert event['immutableEventId']==s.outbox[-1]['eventId'];ok('event-immutable-id-exact-outbox-dedup-id')
assert event['aggregateId']==s.owner_id and event['occurredAt']==stamp(s.now);ok('event-owner-root-and-server-time-bindings')
for field in ['immutableEventId','aggregateId','occurredAt']:neg('event-missing-'+field,mask,event,lambda x,f=field:x.pop(f))
u='abcdef12-3456-4789-8abc-abcdef123456';ad={'routeId':'route.0018','operationId':'owner.session.list','correlationId':u,'logicalOperationId':None,'admission':'REJECTED_BEFORE_COMMAND','status':'FAILED','terminal':True,'output':None,'error':{'stableCode':'UNAUTHENTICATED','classification':'AUTHENTICATION','retryDirective':'DO_NOT_RETRY','message':'Synthetic unaccepted request','detailsDigest':None},'resultDigest':None};am=PACK['admissionFailureSchema'];Draft202012Validator(am,format_checker=FormatChecker()).validate(ad);ok('pre-admission-exact-null-business-identity-positive')
neg('admission-phantom-logical-operation',am,ad,lambda x:x.update(logicalOperationId=u));neg('admission-fabricated-result-digest',am,ad,lambda x:x.update(resultDigest='sha256:'+'a'*64));neg('admission-crossed-route-op',am,ad,lambda x:x.update(operationId='owner.session.revoke'))
for code in ['CSRF_INVALID','REAUTHENTICATION_REQUIRED']:neg('read-no-mutation-only-error/'+code,am,ad,lambda x,c=code:x['error'].update(stableCode=c))
neg('admission-no-extra-auth-flag',am,ad,lambda x:x.update(authorized=True))
response=copy.deepcopy(r);response.update(status='FAILED',output=None,error={'stableCode':'SESSION_ALREADY_REVOKED','classification':'CONFLICT','retryDirective':'DO_NOT_RETRY','message':'Synthetic existing revoked row','detailsDigest':None});Draft202012Validator(OPS['owner.session.revoke']['responseSchema'],format_checker=FormatChecker()).validate(response);ok('fixed-revoked-target-no-retry-positive')
neg('fixed-revoked-target-no-blind-new-command',OPS['owner.session.revoke']['responseSchema'],response,lambda x:x['error'].update(retryDirective='REFRESH_AND_RETRY_NEW_COMMAND'))
for op in PACK['operations']:
 metadata=next(x for x in PACK['perFieldAuthority']if x['operationId']==op['operationId']and x['pointer'].endswith('/deviceMetadata'));assert metadata['nullable']is False;ok('top-level-device-metadata-nullability/'+op['operationId'])
native=decode('owner.session.revoke','DELETE','/owner/sessions/'+sid,[],[('If-Match','"0"'),('Idempotency-Key','a'*512)]);neg('preserve-native-idempotency-header-cap512',OPS['owner.session.revoke']['requestSchema'],native,lambda x:x['guards'].update(idempotencyKey='a'*513))
report={'packageSha256':hashlib.sha256((OUT/'operation-mask-delta.json').read_bytes()).hexdigest(),'checked':len(checks),'failed':0,'checks':checks,'scope':'Independent bounded definition/reference fixes; no PostgreSQL/deployed auth/runtime acceptance','wholeOperationClosed':False};(OUT/'additional-boundaries.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checks),'additional independent checks PASS')
