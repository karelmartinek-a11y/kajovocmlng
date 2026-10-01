from pathlib import Path
import json,sys,copy,hashlib
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
OUT=Path(__file__).parent;ROOT=Path('/workspace/kajovocmlng');sys.path[:0]=[str(OUT),str(ROOT/'scripts')]
from ssot_sources import SSOT,resource_index
from contract_delta import retained_error_reason
j=json.loads((OUT/'effective-contracts.json').read_text());cases=[]
def valid(s,v):Draft202012Validator(s,format_checker=FormatChecker()).validate(v)
def ok(i):cases.append({'id':i,'status':'PASS'})
def negative(i,s,w,mutate):
 valid(s,w);bad=copy.deepcopy(w);mutate(bad)
 try:valid(s,bad)
 except ValidationError as e:cases.append({'id':i,'status':'PASS','validator':e.validator,'path':list(e.absolute_path)});return
 raise AssertionError(i+' accepted')
u='abcdef12-3456-4789-8abc-abcdef123456';time='2026-10-01T00:00:00Z';digest='sha256:'+'a'*64
out={'secretId':u,'stableName':'SYNTHETIC_TEST','type':'PASSWORD','versionId':u,'versionNumber':'1','versionState':'CREATED','recordStatus':'INACTIVE','activeVersionId':None,'stateVersion':'0','createdAt':time}
r={'routeId':'route.0386','operationId':'secret.create','logicalOperationId':u,'correlationId':u,'status':'SUCCEEDED','terminal':True,'output':out,'error':None,'resultDigest':digest,'stateVersion':'0','eventSequence':'1','activationEpoch':'0','idempotencyReplay':False}
valid(j['response'],r);ok('exact-effective-success-mask-domain-witness')
for name,fn in [('active-on-create',lambda x:x['output'].update(recordStatus='ACTIVE')),('secret-value-echo',lambda x:x['output'].update(value='SYNTHETIC_FORBIDDEN_ECHO')),('root-lifecycle-borrowing',lambda x:x['output'].update(recordStatus='CREATED')),('client-authority-receipt',lambda x:x['output'].update(authorized=True)),('success-error',lambda x:x.update(error={'stableCode':'CREATE_INPUT_INVALID'}))]:negative(name,j['response'],r,fn)
e={'routeId':'route.0386','operationId':'secret.create','logicalOperationId':u,'correlationId':u,'immutableEventId':u,'aggregateId':u,'occurredAt':time,'sequence':'1','eventType':'OPERATION_TERMINAL','payload':out,'payloadDigest':digest}
valid(j['event'],e);ok('exact-effective-committed-success-event')
negative('rootless-failure-not-a-success-aggregate-event',j['event'],e,lambda x:x.update(payload=None))
negative('event-no-value-echo',j['event'],e,lambda x:x['payload'].update(value='SYNTHETIC_FORBIDDEN_ECHO'))
unknown=copy.deepcopy(r);unknown.update(status='FAILED',terminal=False,output=None,stateVersion=None,eventSequence=None,error={'stableCode':'SIDE_EFFECT_OUTCOME_UNKNOWN','classification':'UNKNOWN','retryDirective':'RECONCILE_THEN_RETRY','message':'Outcome reconciliation required','detailsDigest':None})
valid(j['response'],unknown);ok('effective-unknown-is-nonterminal-no-output')
negative('unknown-cannot-terminalize',j['response'],unknown,lambda x:x.update(terminal=True))
proposed=retained_error_reason(j['response']);tomb=copy.deepcopy(unknown);tomb.update(terminal=True,error={'stableCode':'IDEMPOTENCY_CONFLICT','classification':'CONFLICT','retryDirective':'DO_NOT_RETRY','message':'Retained terminal detail unavailable','detailsDigest':None,'machineReason':'RESULT_RETAINED_AS_TOMBSTONE'})
valid(proposed,tomb);ok('proposed-sourced-tombstone-machine-reason')
negative('tombstone-reason-not-validation-error',proposed,tomb,lambda x:x['error'].update(stableCode='CREATE_INPUT_INVALID',classification='VALIDATION'))
negative('unknown-machine-reason-rejected',proposed,tomb,lambda x:x['error'].update(machineReason='SILENT_CREATE_NEW'))
(OUT/'response-with-retained-reason.proposed.schema.json').write_text(json.dumps(proposed,indent=2)+'\n')
report={'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'checked':len(cases),'failed':0,'cases':cases,'scope':'Definition-only schema witnesses and positive-derived field violations; no SQL/key/retention producer or runtime proof','proposedDeltaActivated':False,'wholeOperationClosed':False,'implementationAcceptance':'NOT_EVALUATED'}
(OUT/'definition-fixtures.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'definition-only checks PASS')
