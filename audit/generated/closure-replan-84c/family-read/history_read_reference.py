"""DESIGN REFERENCE for exact six-route history read transport and summaries.
No service auth, source publication, persistent cursor or coverage authority.
Producer trust is never granted by this parser; opaque pointers are not payloads.
"""
import json,re,copy
from datetime import datetime,timezone
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
from urllib.parse import parse_qsl
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
S=json.loads((Path(__file__).parent/'history-read-family.schema.json').read_text())
def fail(code):raise ValueError(code)
def valid(schema,value,code='HISTORY_QUERY_INVALID'):
 errors=list(Draft202012Validator({'$schema':S['$schema'],'$defs':S['$defs'],**schema},format_checker=FormatChecker()).iter_errors(value))
 if errors:fail(code)
def utc(value):
 try:d=datetime.fromisoformat(value.replace('Z','+00:00'))
 except (ValueError,AttributeError):fail('HISTORY_QUERY_INVALID')
 if d.tzinfo is None or d.utcoffset().total_seconds()!=0:fail('HISTORY_QUERY_INVALID')
 return d

def decode_read(route_id,path_parameters,raw_query,body):
 if route_id not in S['transportSchemas']:fail('HISTORY_ROUTE_UNSUPPORTED')
 if body not in (None,b''):fail('HISTORY_QUERY_INVALID')
 transport=S['transportSchemas'][route_id]
 valid(transport['properties']['pathParameters'],path_parameters)
 try:text=raw_query.decode('ascii');assert not re.search(r'%(?![0-9a-fA-F]{2})',text);pairs=parse_qsl(text,keep_blank_values=True,strict_parsing=True,encoding='utf8',errors='strict',separator='&')if text else[]
 except (UnicodeError,ValueError,AssertionError,AttributeError):fail('HISTORY_QUERY_INVALID')
 native={'operationId':S['requestSchemas'][route_id]['properties']['operationId']['const'],'scope':{'routeId':route_id,'pathParameters':path_parameters}}
 if native['operationId']=='audit.event.read':
  if pairs:fail('HISTORY_QUERY_INVALID')
 else:
  query={'runId':None,'correlationId':None,'componentId':None,'operationId':None,'clientId':None,'channel':'ALL','severity':[],'cursor':None,'limit':100};seen=set()
  for name,value in pairs:
   if name not in S['$defs']['Query']['properties']:fail('HISTORY_QUERY_INVALID')
   if name in seen and name!='severity':fail('HISTORY_QUERY_INVALID')
   if name=='severity':
    if value in query['severity']:fail('HISTORY_QUERY_INVALID')
    query['severity'].append(value)
   elif name=='limit':
    if not re.fullmatch(r'[1-9][0-9]*',value):fail('HISTORY_QUERY_INVALID')
    query[name]=int(value)
   else:query[name]=value
   seen.add(name)
  valid(S['$defs']['Query'],query)
  if not utc(query['fromInclusive'])<utc(query['toExclusive']):fail('HISTORY_QUERY_INVALID')
  try:ZoneInfo(query['timezone'])
  except (ZoneInfoNotFoundError,ValueError):fail('HISTORY_QUERY_INVALID')
  if route_id=='route.0063'and query['componentId']not in (None,path_parameters['id']):fail('HISTORY_QUERY_INVALID')
  if route_id=='route.0159'and query['runId']not in (None,path_parameters['runId']):fail('HISTORY_QUERY_INVALID')
  native['filters']=query
 valid(S['requestSchemas'][route_id],native)
 return native

def select_summaries(native,persisted_items):
 # These are typed summary bytes from an authenticated source reader, not
 # caller declarations and not proof of root scope/source/coverage authority.
 items=[];seen={}
 route=native['scope']['routeId'];path=native['scope']['pathParameters']
 if route in ('route.0222','route.0263'):fail('HISTORY_GENERATION_JOB_MEMBERSHIP_PRODUCER_REQUIRED')
 for item in persisted_items:
  valid(S['$defs']['Item'],item,'HISTORY_RECORD_INVALID')
  identity=item['eventId'];canonical=json.dumps(item,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
  if identity in seen:
   if seen[identity]!=canonical:fail('HISTORY_EVENT_ID_CONFLICT')
   continue
  seen[identity]=canonical
  if native['operationId']=='audit.event.read':
   if identity==native['scope']['pathParameters']['id']:items.append(copy.deepcopy(item))
   continue
  f=native['filters']
  if route=='route.0063'and item['componentId']!=path['id']:continue
  if route=='route.0159'and item['runId']!=path['runId']:continue
  if not utc(f['fromInclusive'])<=utc(item['occurredAt'])<utc(f['toExclusive']):continue
  if any(f[name]is not None and item[name]!=f[name]for name in ['runId','correlationId','componentId','operationId','clientId']):continue
  if f['severity']and item['severity']not in f['severity']:continue
  # channel is not in the normative Item projection. Never infer it from
  # source/eventType or silently treat a filtered query as ALL.
  if f['channel']!='ALL':fail('HISTORY_CHANNEL_CLASSIFICATION_PRODUCER_REQUIRED')
  items.append(copy.deepcopy(item))
 items.sort(key=lambda x:(utc(x['recordedAt']),x['eventId'].encode('utf8')))
 if native['operationId']=='audit.event.read':
  if not items:fail('HISTORY_RECORD_NOT_FOUND')
  return items[0]
 return items[:native['filters']['limit']]

def validate_result(native,result):
 valid(S['$defs']['Result'],result,'HISTORY_RESULT_INVALID')
 f=native['filters'];interval=result['resolvedInterval']
 if any(interval[k]!=f[k]for k in ['fromInclusive','toExclusive','timezone']):fail('HISTORY_INTERVAL_BINDING_MISMATCH')
 if result['completeness']=='COMPLETE'and not(utc(result['coverageFrom'])<=utc(f['fromInclusive'])and utc(result['coverageTo'])>=utc(f['toExclusive'])):fail('HISTORY_COMPLETE_COVERAGE_MISMATCH')
 selected=select_summaries(native,result['items'])
 if selected!=result['items']:fail('HISTORY_RESULT_ORDER_FILTER_OR_DUPLICATE_MISMATCH')
 return result

def present_summary(result):
 # No fake hydration: the payload remains an explicit unresolved reference.
 return {'completeness':result['completeness'],'missingSources':result['missingSources'],'snapshotWatermark':result['snapshotWatermark'],'rows':[{'eventId':x['eventId'],'eventType':x['eventType'],'occurredAt':x['occurredAt'],'payloadReference':x['payloadReference'],'payloadHydration':'NOT_REQUESTED_SUMMARY_ONLY'}for x in result['items']]}

def load_summary_bytes(raw):
 # Actual native JSON bytes under the declared summary mask. This parser is
 # not used for GET bodies and confers no publisher/provenance authority.
 def pairs(items):
  out={}
  for key,value in items:
   if key in out:fail('HISTORY_RECORD_DUPLICATE_JSON_KEY')
   out[key]=value
  return out
 try:obj=json.loads(raw.decode('utf8',errors='strict'),object_pairs_hook=pairs,parse_constant=lambda x:fail('HISTORY_RECORD_JSON_INVALID'))
 except ValueError as e:
  if str(e) in ['HISTORY_RECORD_DUPLICATE_JSON_KEY','HISTORY_RECORD_JSON_INVALID']:raise
  fail('HISTORY_RECORD_JSON_INVALID')
 except (UnicodeError,AttributeError):fail('HISTORY_RECORD_JSON_INVALID')
 valid(S['$defs']['Item'],obj,'HISTORY_RECORD_INVALID')
 return obj

def decode_profiled_read(route_id,path_parameters,raw_query,body):
 # Proposed explicit technical binding; NOT an activated public endpoint.
 # No profile selection grants authorization or substitutes for scoped context.
 # Both exact schema profiles were frozen from the same authoritative source.
 try:text=raw_query.decode('ascii');assert not re.search(r'%(?![0-9a-fA-F]{2})',text);pairs=parse_qsl(text,keep_blank_values=True,strict_parsing=True,encoding='utf8',errors='strict',separator='&')if text else[]
 except (UnicodeError,ValueError,AssertionError,AttributeError):fail('HISTORY_QUERY_INVALID')
 selectors=[v for k,v in pairs if k=='queryProfile']
 if len(selectors)!=1 or selectors[0]not in ('EXPERIENCE_HISTORY_V1','HISTORY_QUERY_V1'):fail('HISTORY_QUERY_INVALID')
 profile=selectors[0];filters=[p for p in pairs if p[0]!='queryProfile']
 from urllib.parse import urlencode
 if profile=='EXPERIENCE_HISTORY_V1':native=decode_read(route_id,path_parameters,urlencode(filters).encode(),body)
 else:
  if body not in(None,b'')or route_id=='route.0452':fail('HISTORY_QUERY_INVALID')
  valid(S['transportSchemas'][route_id]['properties']['pathParameters'],path_parameters)
  mask=S['$defs']['HistoryQuery'];query={k:None for k,v in mask['properties'].items()if isinstance(v,dict)and 'null'in v.get('type',[])};query.update({'recordKinds':[],'limit':100});seen=set()
  for key,value in filters:
   if key not in mask['properties']or(key in seen and key!='recordKinds'):fail('HISTORY_QUERY_INVALID')
   if key=='recordKinds':
    if value in query[key]:fail('HISTORY_QUERY_INVALID')
    query[key].append(value)
   elif key=='limit':
    if not re.fullmatch(r'[1-9][0-9]*',value):fail('HISTORY_QUERY_INVALID')
    query[key]=int(value)
   else:query[key]=value
   seen.add(key)
  valid(mask,query)
  if not utc(query['from'])<utc(query['to']):fail('HISTORY_QUERY_INVALID')
  native={'operationId':S['requestSchemas'][route_id]['properties']['operationId']['const'],'scope':{'routeId':route_id,'pathParameters':path_parameters},'filters':query}
 native['queryProfile']=profile
 return native
