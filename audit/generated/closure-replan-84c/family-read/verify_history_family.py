import sys,json,copy,uuid,hashlib
from pathlib import Path
from urllib.parse import urlencode
O=Path(__file__).parent;ROOT=Path('/workspace/kajovocmlng');sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(O))
from history_read_reference import decode_read,select_summaries,validate_result,present_summary,load_summary_bytes,S
from ssot_sources import SSOT,resource_index
cases=[]
def ok(name):cases.append({'id':name,'status':'PASS'})
def reject(name,fn,code):
 try:fn();raise AssertionError(name+' accepted')
 except ValueError as e:assert str(e)==code,(name,e);ok(name);cases[-1]['diagnostic']=code
uid=str(uuid.uuid4());params={};queries={};natives={};q=[('fromInclusive','2026-10-01T00:00:00Z'),('toExclusive','2026-10-02T00:00:00Z'),('timezone','Europe/Prague')]
for route,mask in S['transportSchemas'].items():
 pp={k:uid for k in mask['properties']['pathParameters']['properties']};params[route]=pp
 raw=b'' if route=='route.0452'else urlencode(q).encode();queries[route]=raw;natives[route]=decode_read(route,pp,raw,b'');ok(route+'/positive-exact-native-scope')
 reject(route+'/unknown-query',lambda:decode_read(route,pp,raw+(b'&'if raw else b'')+b'authorized=true',b''),'HISTORY_QUERY_INVALID')
 reject(route+'/body-JSON-not-permitted',lambda:decode_read(route,pp,raw,b'{"valid":true}'),'HISTORY_QUERY_INVALID')
 if pp:reject(route+'/wrong-path-parent',lambda:decode_read(route,{**pp,'foreignId':uid},raw,b''),'HISTORY_QUERY_INVALID')
 if route!='route.0452':
  reject(route+'/scalar-duplicate',lambda:decode_read(route,pp,raw+b'&limit=100&limit=100',b''),'HISTORY_QUERY_INVALID')
  reject(route+'/duplicate-domain-severity',lambda:decode_read(route,pp,raw+b'&severity=INFO&severity=INFO',b''),'HISTORY_QUERY_INVALID')
  reject(route+'/limit-lower-bound',lambda:decode_read(route,pp,raw+b'&limit=0',b''),'HISTORY_QUERY_INVALID')
for label,extra in [('bad-percent',b'&cursor=%GG'),('bad-UTF8',b'&cursor=%ff'),('limit-overflow',b'&limit=501'),('bad-channel',b'&channel=UNIVERSAL'),('bad-severity',b'&severity=PASS')]:reject(label,lambda:decode_read('route.0451',{},queries['route.0451']+extra,b''),'HISTORY_QUERY_INVALID')
for label,fields in [('reversed-interval',{**dict(q),'fromInclusive':'2026-10-03T00:00:00Z'}),('invalid-IANA',{**dict(q),'timezone':'Moon/Tranquility'}),('nonUTC-wire',{**dict(q),'fromInclusive':'2026-10-01T00:00:00+03:00'})]:reject(label,lambda:decode_read('route.0451',{},urlencode(fields).encode(),b''),'HISTORY_QUERY_INVALID')
item={'eventId':uid,'occurredAt':'2026-10-01T01:00:00Z','recordedAt':'2026-10-01T01:00:01Z','runId':uid,'correlationId':uid,'componentId':uid,'clientId':None,'operationId':'generation.job.create','eventType':'OPERATION_ADMITTED','severity':'INFO','source':'CANONICAL_AUDIT','payloadReference':'artifact:synthetic-event-1','provenanceRefs':['artifact:synthetic-provenance-1'],'durationMs':None,'direction':'INTERNAL'}
assert select_summaries(natives['route.0452'],[item])==item;ok('single-event-path-identity-positive');assert select_summaries(natives['route.0451'],[item,item])==[item];ok('exact-duplicate-canonical-event-returned-once')
for route in ['route.0063','route.0159']:assert select_summaries(natives[route],[item])==[item];ok(route+'/same-domain-parent-read-positive')
for route in ['route.0222','route.0263']:reject(route+'/no-guessed-job-run-equivalence',lambda:select_summaries(natives[route],[item]),'HISTORY_GENERATION_JOB_MEMBERSHIP_PRODUCER_REQUIRED')
changed=copy.deepcopy(item);changed['eventType']='OPERATION_TERMINAL';reject('same-ID-conflicting-bytes',lambda:select_summaries(natives['route.0451'],[item,changed]),'HISTORY_EVENT_ID_CONFLICT')
foreign=copy.deepcopy(item);foreign['eventId']=str(uuid.uuid4());reject('single-exact-ID-not-found-not-an-empty-success',lambda:select_summaries(natives['route.0452'],[foreign]),'HISTORY_RECORD_NOT_FOUND')
filtered=decode_read('route.0451',{},queries['route.0451']+b'&channel=EMAIL',b'');reject('no-channel-guess-from-source-label',lambda:select_summaries(filtered,[item]),'HISTORY_CHANNEL_CLASSIFICATION_PRODUCER_REQUIRED')
result={'items':[item],'nextCursor':None,'snapshotWatermark':'synthetic-frozen-watermark-1','resolvedInterval':{'fromInclusive':dict(q)['fromInclusive'],'toExclusive':dict(q)['toExclusive'],'timezone':'Europe/Prague'},'coverageFrom':dict(q)['fromInclusive'],'coverageTo':dict(q)['toExclusive'],'completeness':'COMPLETE','missingSources':[],'provenanceRefs':['artifact:synthetic-provenance-1']};assert validate_result(natives['route.0451'],result)==result;assert present_summary(result)['rows'][0]['payloadHydration']=='NOT_REQUESTED_SUMMARY_ONLY';ok('exact-complete-summary-native-to-UI-preserves-reference-not-payload')
partial={**copy.deepcopy(result),'completeness':'PARTIAL','missingSources':['synthetic-archive-gap']};validate_result(natives['route.0451'],partial);ok('partial-retains-explicit-gap')
unavail={**copy.deepcopy(result),'completeness':'UNAVAILABLE','items':[],'coverageFrom':None,'coverageTo':None,'missingSources':['synthetic-store'],'nextCursor':None};validate_result(natives['route.0451'],unavail);ok('unavailable-no-items-no-coverage-no-cursor')
for label,change,code in [('complete-missing-source',{'missingSources':['gap']},'HISTORY_RESULT_INVALID'),('complete-insufficient-coverage',{'coverageTo':'2026-10-01T03:00:00Z'},'HISTORY_COMPLETE_COVERAGE_MISMATCH'),('unavailable-has-records',{'completeness':'UNAVAILABLE','coverageFrom':None,'coverageTo':None,'missingSources':['gap']},'HISTORY_RESULT_INVALID')]:reject(label,lambda:validate_result(natives['route.0451'],{**copy.deepcopy(result),**change}),code)
changed=copy.deepcopy(result);changed['resolvedInterval']['timezone']='UTC';reject('response-exact-interval-binding',lambda:validate_result(natives['route.0451'],changed),'HISTORY_INTERVAL_BINDING_MISMATCH')
summary_bytes=json.dumps(item,separators=(',',':')).encode();assert load_summary_bytes(summary_bytes)==item;ok('native-summary-actual-JSON-bytes-positive')
reject('native-summary-duplicate-JSON-keys',lambda:load_summary_bytes(summary_bytes[:-1]+b',\"eventId\":\"'+uid.encode()+b'\"}'),'HISTORY_RECORD_DUPLICATE_JSON_KEY')
reject('native-summary-invalid-JSON-encoding',lambda:load_summary_bytes(b'\xff'),'HISTORY_RECORD_JSON_INVALID')
reject('native-summary-invalid-JSON-syntax',lambda:load_summary_bytes(summary_bytes[:-1]),'HISTORY_RECORD_JSON_INVALID')
report={'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'consumedCanonicalDigests':{'ui/contracts/live-experience.json':resource_index()['ui/contracts/live-experience.json']['sha256']},'checked':len(cases),'failed':0,'cases':cases,'scope':'Exact transport/native/summary/result semantics and named fail-closed missing actual producer dependencies; no fixture boolean authority','selectedRoutes':6,'selectedOperations':4,'wholeOperationsClosed':0,'designGapsRemain':True,'runtimeAcceptance':'NOT_EVALUATED','sourcePublicationAndContinuousCoverageProven':False,'payloadReferenceHydrated':False}
(O/'history-family-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'history family checks PASS; whole operations0')
