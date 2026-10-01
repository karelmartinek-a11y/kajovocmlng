from pathlib import Path
import copy,json,hashlib,sys,threading
from datetime import timedelta
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
from family_reference import *
ROOT=Path('/workspace/kajovocmlng');sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
ENTRY=SSOT.read_bytes();checks=[]
def check(i,v,actual=None):checks.append({'id':i,'status':'PASS'if v else'FAIL','actualDiagnostic':actual})
def rejects(i,fn,expected):
 try:fn();check(i,False,'UNEXPECTED_ACCEPT')
 except Violation as ex:check(i,str(ex)==expected,str(ex))
 except ValidationError as ex:check(i,expected=='SCHEMA_REJECT',{'validator':ex.validator,'path':list(ex.absolute_path)})
store=Store();s1,t1=store.add();s2,t2=store.add();expired,_=store.add(expired=True);revoked,_=store.add(revoked=True);stale,_=store.add(epoch=1);api=store.authenticate(store.api,'OWNER_API_KEY');web=store.authenticate(t1,'OWNER_SESSION')
listnative=decode('owner.session.list','GET','/owner/sessions',[],[]);before=len(store.events);first=store.listing(api,listnative['query']);out=store.hydrate(first);check('positive-list-persisted-row-to-server-bytes-to-consumer',len(out['sessions'])==2);check('read-events-NOT_APPLICABLE-derived-read-only',len(store.events)==before);check('api-key-does-not-invent-current-web-session',all(not x['current']for x in out['sessions']))
seen=out['sessions'];cursor=out['nextCursor']
while cursor:
 page=store.hydrate(store.listing(api,{'cursor':cursor,'limit':None}));seen+=page['sessions'];cursor=page['nextCursor']
check('positive-immutable-cursor-all-rows-once-deterministic-order',[x['id']for x in seen]==sorted(store.rows))
webfull=store.hydrate(store.listing(web,{'cursor':None,'limit':'100'}));check('current-flag-only-from-verified-server-session',[x['id']for x in webfull['sessions']if x['current']]==[s1]);check('private-session-lookup-and-hash-never-in-read-bytes',not any(k in first['output']['sessions'][0]for k in ['lookupDigest','sessionHash','ownerIdentityId','mfaVerifiedAt']))
# Actual current native bounds, not legacy canonicalJson parser claims.
rejects('unknown-query',lambda:decode('owner.session.list','GET','/owner/sessions',[('bogus','1')],[]),'HTTP_QUERY_UNKNOWN')
rejects('duplicate-query',lambda:decode('owner.session.list','GET','/owner/sessions',[('limit','1'),('limit','2')],[]),'HTTP_QUERY_DUPLICATE')
rejects('zero-query-limit',lambda:decode('owner.session.list','GET','/owner/sessions',[('limit','0')],[]),'SCHEMA_REJECT')
rejects('bad-cursor-type',lambda:decode('owner.session.list','GET','/owner/sessions',[('cursor','true')],[]),'SCHEMA_REJECT')
rejects('noncanonical-counter',lambda:decode('owner.session.list','GET','/owner/sessions',[('limit','01')],[]),'SCHEMA_REJECT')
rejects('invalid-bytes-body-no-parser-input',lambda:decode('owner.session.list','GET','/owner/sessions',[],[],b'\xff{'),'HTTP_BODY_NOT_ALLOWED')
if first['output']['nextCursor']:
 rejects('cursor-bound-to-original-channel-context',lambda:store.listing(web,{'cursor':first['output']['nextCursor'],'limit':None}),'CURSOR_QUERY_MISMATCH')
 rejects('cursor-limit-change',lambda:store.listing(api,{'cursor':first['output']['nextCursor'],'limit':'3'}),'CURSOR_QUERY_MISMATCH')
rejects('unissued-cursor',lambda:store.listing(api,{'cursor':uid(),'limit':None}),'CURSOR_INVALID')
for name in PACK['sessionPublicSchema']['properties']:
 witness=copy.deepcopy(webfull['sessions'][0]);Draft202012Validator(PACK['sessionPublicSchema'],format_checker=FormatChecker()).validate(witness)
 mutant=copy.deepcopy(witness);del mutant[name]
 rejects('missing-public-field/'+name,lambda m=mutant:Draft202012Validator(PACK['sessionPublicSchema'],format_checker=FormatChecker()).validate(m),'SCHEMA_REJECT')
for value in [{'lookupDigest':digest(b'synthetic')},{'sessionHash':'not allowed'},{'permission':'OWNER_FULL'}]:
 mutant=copy.deepcopy(webfull['sessions'][0]);mutant.update(value);rejects('extra-server-or-credential-field/'+next(iter(value)),lambda m=mutant:Draft202012Validator(PACK['sessionPublicSchema'],format_checker=FormatChecker()).validate(m),'SCHEMA_REJECT')
mutant=copy.deepcopy(first);mutant['output']['sessions'][0]['current']=True;mutant['resultDigest']=digest({k:v for k,v in mutant.items()if k!='resultDigest'});rejects('changed-valid-digest-current-authority-receipt',lambda:store.hydrate(mutant),'SERVER_RECEIPT_BYTES_MISMATCH')
for key in ['id','createdAt','lastSeenAt','expiresAt','sessionEpoch','stateVersion','deviceMetadata','current']:
 mutant=copy.deepcopy(webfull['sessions'][0]);mutant[key]=None;rejects('forbidden-null/'+key,lambda m=mutant:Draft202012Validator(PACK['sessionPublicSchema'],format_checker=FormatChecker()).validate(m),'SCHEMA_REJECT')
headers=[('If-Match','"0"'),('Idempotency-Key','synthetic-exact')];native=decode('owner.session.revoke','DELETE','/owner/sessions/'+s2,[],headers);before=(len(store.events),len(store.outbox),len(store.audit));receipt=store.revoke(api,s2,'0','synthetic-exact');result=store.hydrate(receipt);check('positive-revoke-state-event-outbox-audit-read-hydration',result['stateVersion']=='1'and store.rows[s2]['revokedAt']==result['revokedAt']and(len(store.events),len(store.outbox),len(store.audit))==tuple(x+1 for x in before));check('precise-event-payload-identities-digest',store.events[-1]['payload']=={k:result[k]for k in ['sessionId','revokedAt','stateVersion','ownerStateVersion']}and store.events[-1]['payloadDigest']==digest(store.events[-1]['payload']))
replay=store.revoke(api,s2,'0','synthetic-exact');check('exact-retained-idempotent-replay-no-new-effect',replay==receipt and(len(store.events),len(store.outbox),len(store.audit))==tuple(x+1 for x in before))
rejects('changed-native-replay-conflict',lambda:store.revoke(api,s2,'1','synthetic-exact'),'IDEMPOTENCY_CONFLICT')
rejects('already-revoked-new-command',lambda:store.revoke(api,s2,'1','other'),'SESSION_ALREADY_REVOKED')
rejects('missing-selected-target',lambda:store.revoke(api,uid(),'0','missing'),'SESSION_NOT_FOUND')
rejects('expired-selected-target',lambda:store.revoke(api,expired,'0','expired'),'SESSION_EXPIRED')
rejects('epoch-invalidated-selected-target',lambda:store.revoke(api,stale,'0','stale'),'SESSION_EPOCH_INVALIDATED')
rejects('stale-state-version',lambda:store.revoke(api,s1,'7','cas-stale'),'STATE_VERSION_CONFLICT')
rejects('client-selected-owner-forged-context',lambda:store.listing(Context(object(),store.owner_id,'OWNER_API_KEY',None,1),listnative['query']),'UNAUTHENTICATED')
rejects('wrong-real-credential-bytes',lambda:store.authenticate(b'wrong','OWNER_API_KEY'),'UNAUTHENTICATED')
rejects('missing-CSRF-web-mutation',lambda:store.revoke(web,s1,'0','csrf'),'CSRF_INVALID')
store.rows[s1]['reauthenticatedAt']=stamp(store.now-timedelta(hours=1));rejects('expired-reference-policy-reauthentication',lambda:store.revoke(web,s1,'0','reauth',store.csrf[s1]),'REAUTHENTICATION_REQUIRED');store.rows[s1]['reauthenticatedAt']=stamp(store.now)
rejects('missing-IfMatch',lambda:decode('owner.session.revoke','DELETE','/owner/sessions/'+s1,[],[('Idempotency-Key','x')]),'HTTP_IF_MATCH_REQUIRED')
rejects('unquoted-IfMatch',lambda:decode('owner.session.revoke','DELETE','/owner/sessions/'+s1,[],[('If-Match','0'),('Idempotency-Key','x')]),'HTTP_IF_MATCH_INVALID')
rejects('duplicate-IfMatch',lambda:decode('owner.session.revoke','DELETE','/owner/sessions/'+s1,[],headers+[('if-match','"1"')]),'HTTP_HEADER_DUPLICATE')
rejects('revoke-unknown-query',lambda:decode('owner.session.revoke','DELETE','/owner/sessions/'+s1,[('limit','1')],headers),'HTTP_QUERY_UNKNOWN')
# Positive witness before exact fault cutpoint; it is rolled back by a fresh model
# snapshot so no invalid starting fixture can turn into successful negative proof.
cut,_=store.add();baseline=copy.deepcopy((store.rows,store.events,store.outbox,store.audit,store.commands,store.responses,store.owner_version,store.owner_sequence));store.revoke(api,cut,'0','cut-positive');store.rows,store.events,store.outbox,store.audit,store.commands,store.responses,store.owner_version,store.owner_sequence=copy.deepcopy(baseline)
rejects('rollback-after-outbox-cutpoint',lambda:store.revoke(api,cut,'0','cut-positive',failpoint='AFTER_OUTBOX'),'SYNTHETIC_ROLLBACK_CUTPOINT');check('rollback-no-row-command-event-outbox-audit-receipt-fragments',(store.rows,store.events,store.outbox,store.audit,store.commands,store.responses,store.owner_version,store.owner_sequence)==baseline)
# Actual Python reference-model threads, explicitly not PostgreSQL lock evidence.
race,_=store.add();barrier=threading.Barrier(3);results=[]
def contender(k):
 barrier.wait()
 try:store.revoke(api,race,'0',k);results.append('SUCCESS')
 except Violation as ex:results.append(str(ex))
threads=[threading.Thread(target=contender,args=(k,))for k in ['race-a','race-b']]
for t in threads:t.start()
barrier.wait()
for t in threads:t.join()
check('reference-concurrent-distinct-revoke-commands-one-mutation',sorted(results)==['SESSION_ALREADY_REVOKED','SUCCESS']and store.rows[race]['stateVersion']=='1',results)
# Every failure mask has a domain-shaped positive witness, then a related mutant.
errorSchema=OPS['owner.session.revoke']['responseSchema'];base=copy.deepcopy(receipt);base['status']='FAILED';base['output']=None
for code,branch in [(x['properties']['stableCode']['const'],x)for x in errorSchema['properties']['error']['oneOf'][0]['oneOf']]:
 witness=copy.deepcopy(base);witness['terminal']=branch['properties']['retryDirective']['const']not in ['RETRY_SAME_OPERATION','RECONCILE_THEN_RETRY'];witness['status']='FAILED';witness['error']={k:(v['const']if 'const'in v else None if k=='detailsDigest'else 'Synthetic typed failure')for k,v in branch['properties'].items()};witness['resultDigest']=digest({k:v for k,v in witness.items()if k!='resultDigest'});Draft202012Validator(errorSchema,format_checker=FormatChecker()).validate(witness);check('positive-error-mask/'+code,True)
 mutant=copy.deepcopy(witness);mutant['error']['classification']='INTERNAL';rejects('wrong-error-predicate-classification/'+code,lambda m=mutant:Draft202012Validator(errorSchema,format_checker=FormatChecker()).validate(m),'SCHEMA_REJECT')
# Read-only operation has its own cursor/dependency error boundary; target mutation errors are forbidden.
list_errors=OPS['owner.session.list']['responseSchema'];lbase=copy.deepcopy(first);lbase.update(status='FAILED',output=None)
for branch in list_errors['properties']['error']['oneOf'][0]['oneOf']:
 code=branch['properties']['stableCode']['const'];witness=copy.deepcopy(lbase);witness['terminal']=branch['properties']['retryDirective']['const']!='RETRY_SAME_OPERATION';witness['error']={k:(v['const']if 'const'in v else None if k=='detailsDigest'else 'Synthetic read failure')for k,v in branch['properties'].items()};witness['resultDigest']=digest({k:v for k,v in witness.items()if k!='resultDigest'});Draft202012Validator(list_errors,format_checker=FormatChecker()).validate(witness);check('positive-read-error-mask/'+code,True)
 mutant=copy.deepcopy(witness);mutant['error']['stableCode']='SESSION_ALREADY_REVOKED';rejects('read-rejects-target-mutation-error/'+code,lambda m=mutant:Draft202012Validator(list_errors,format_checker=FormatChecker()).validate(m),'SCHEMA_REJECT')
# Independent review defects: positive witnesses first, targeted fault second.
ev=copy.deepcopy(store.events[0]);check('positive-event-consumer-immutable-bytes-outbox',store.hydrate_event(ev)==ev['payload'])
for field,value in [('sequence','0'),('payloadDigest',ev['payloadDigest']+'\n'),('immutableEventId',ev['immutableEventId']+'\n')]:
 mutant=copy.deepcopy(ev);mutant[field]=value;rejects('review-event-invalid/'+field,lambda m=mutant:store.hydrate_event(m),'SCHEMA_REJECT')
for field in ['immutableEventId','aggregateId','occurredAt']:
 mutant=copy.deepcopy(ev);del mutant[field];rejects('review-public-event-missing/'+field,lambda m=mutant:store.hydrate_event(m),'SCHEMA_REJECT')
mutant=copy.deepcopy(ev);mutant['aggregateId']=uid();rejects('review-event-substituted-owner',lambda:store.hydrate_event(mutant),'EVENT_AGGREGATE_MISMATCH')
mutant=copy.deepcopy(ev);mutant['immutableEventId']=uid();rejects('review-event-unpublished-id',lambda:store.hydrate_event(mutant),'EVENT_BYTES_UNAVAILABLE')
mutant=copy.deepcopy(ev);mutant['sequence']='2';rejects('review-event-changed-authoritative-counter',lambda:store.hydrate_event(mutant),'EVENT_IMMUTABLE_BYTES_MISMATCH')
mutant=copy.deepcopy(receipt);mutant['resultDigest']+='\n';rejects('review-result-digest-trailing-newline',lambda:store.hydrate(mutant),'SCHEMA_REJECT')
frozen_first=store.listing(api,{'cursor':None,'limit':'1'});snapshot=(frozen_first['output']['ownerStateVersion'],frozen_first['output']['ownerSessionEpoch']);store.owner_version+=7;store.owner_epoch+=1
nextpage=store.listing(api,{'cursor':frozen_first['output']['nextCursor'],'limit':None});check('review-cursor-owner-counters-same-frozen-snapshot',(nextpage['output']['ownerStateVersion'],nextpage['output']['ownerSessionEpoch'])==snapshot);store.owner_version-=7;store.owner_epoch-=1
failure=copy.deepcopy(receipt);failure.update(status='FAILED',terminal=False,output=None,error={'stableCode':'DEPENDENCY_UNAVAILABLE','classification':'DEPENDENCY','retryDirective':'RETRY_SAME_OPERATION','message':'Synthetic dependency unavailable','detailsDigest':None});failure['resultDigest']=digest({k:v for k,v in failure.items()if k!='resultDigest'});Draft202012Validator(errorSchema,format_checker=FormatChecker()).validate(failure);check('review-positive-transient-failure-nonterminal',True)
mutant=copy.deepcopy(failure);mutant['terminal']=True;rejects('review-transient-business-terminal-forbidden',lambda:Draft202012Validator(errorSchema,format_checker=FormatChecker()).validate(mutant),'SCHEMA_REJECT')
for branch in PACK['admissionFailureSchema']['properties']['error']['oneOf']:
 code=branch['properties']['stableCode']['const'];admission={'routeId':'route.0019','operationId':'owner.session.revoke','correlationId':uid(),'logicalOperationId':None,'admission':'REJECTED_BEFORE_COMMAND','status':'FAILED','terminal':True,'output':None,'error':{k:(v['const']if 'const'in v else None if k=='detailsDigest'else 'Synthetic pre-command diagnostic')for k,v in branch['properties'].items()},'resultDigest':None};validator=Draft202012Validator(PACK['admissionFailureSchema'],format_checker=FormatChecker());validator.validate(admission);check('positive-before-command-diagnostic/'+code,True)
 mutant=copy.deepcopy(admission);mutant['logicalOperationId']=uid();rejects('review-no-fabricated-operation-before-command/'+code,lambda m=mutant:validator.validate(m),'SCHEMA_REJECT')
for route,oid in [('route.0018','owner.session.list'),('route.0019','owner.session.revoke')]:
 witness=copy.deepcopy(admission);witness.update(routeId=route,operationId=oid);witness['error']={'stableCode':'UNAUTHENTICATED','classification':'AUTHENTICATION','retryDirective':'DO_NOT_RETRY','message':'Synthetic unauthorized','detailsDigest':None};validator.validate(witness);check('positive-admission-route-operation-pair/'+oid,True)
 mutant=copy.deepcopy(witness);mutant['routeId']='route.0019'if route=='route.0018'else'route.0018';rejects('review-admission-wrong-route-pair/'+oid,lambda m=mutant:validator.validate(m),'SCHEMA_REJECT')
 if oid.endswith('list'):
  mutant=copy.deepcopy(witness);mutant['error']['stableCode']='CSRF_INVALID';rejects('review-read-cannot-report-mutation-CSRF',lambda m=mutant:validator.validate(m),'SCHEMA_REJECT')
  mutant['error']['stableCode']='REAUTHENTICATION_REQUIRED';rejects('review-read-no-invented-mutation-reauth',lambda m=mutant:validator.validate(m),'SCHEMA_REJECT')
rejects('review-existing-idempotency-header-cap-preserved',lambda:decode('owner.session.revoke','DELETE','/owner/sessions/'+s1,[],[('If-Match','"0"'),('Idempotency-Key','x'*513)]),'SCHEMA_REJECT')
store.credential_version+=1;rejects('current-auth-required-before-replay-after-credential-rotation',lambda:store.revoke(api,s2,'0','synthetic-exact'),'UNAUTHENTICATED')
report={'inputCommit':'84c41ba','sourceDocumentSha256':hashlib.sha256(ENTRY).hexdigest(),'sourceUnchangedDuringRun':ENTRY==SSOT.read_bytes(),'canonicalSemanticResultHelperSha256':hashlib.sha256((ROOT/'scripts/create_completion_contracts.py').read_bytes()).hexdigest(),'packageSha256':hashlib.sha256((OUT/'operation-mask-delta.json').read_bytes()).hexdigest(),'helperSha256':hashlib.sha256((OUT/'family_reference.py').read_bytes()).hexdigest(),'proofScriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'checkCount':len(checks),'failedCount':sum(x['status']!='PASS'for x in checks),'checks':checks,'wholeOperationsClosed':0,'evidenceClass':'DESIGN_REFERENCE_SEMANTICS','limitations':['No actual canonical auth/session producer or runtime evidence','No PostgreSQL transaction/lock/outbox/audit implementation proof','Fixture policy page-size/reauth-age values are not normative approval','Proposed metadata/event technical allocation requires coordinator review'],'noLiveAccountsOrApi':True};(OUT/'family-reference-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(checks),'failed':report['failedCount']}));sys.exit(report['failedCount']!=0 or not report['sourceUnchangedDuringRun'])
