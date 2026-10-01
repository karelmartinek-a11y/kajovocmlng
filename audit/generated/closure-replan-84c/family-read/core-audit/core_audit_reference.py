"""Bounded immutable audit-byte inspector and strict CORE200 HTTP decoder.

No query-origin/cursor/completeness or authenticated actor is fabricated here.
The SQL projection below consumes already-authorized rows in a fresh read snapshot;
the caller still owns actual OWNER authorization and access-audit publication.
"""
import base64,hashlib,json,re,struct,uuid
from pathlib import Path
from urllib.parse import unquote_to_bytes
from datetime import datetime
from jsonschema import Draft202012Validator,FormatChecker
O=Path(__file__).parent
S=json.loads((O/'core-audit-read.schema.json').read_text())
class AuditError(ValueError):pass
def fail(code):raise AuditError(code)
def valid(name,value,code):
 schema={'$schema':S['$schema'],'$defs':S['$defs'],'$ref':'#/$defs/'+name}
 if list(Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(value)):fail(code)
 return value
def text(v):
 if re.search(b'%(?![0-9A-Fa-f]{2})',v):fail('AUDIT_QUERY_ENCODING_INVALID')
 try:return unquote_to_bytes(v.replace(b'+',b' ')).decode('utf-8','strict')
 except UnicodeError:fail('AUDIT_QUERY_ENCODING_INVALID')
def decode(operation,path,query,body=b'',method='GET'):
 if method!='GET' or body:fail('AUDIT_TRANSPORT_INVALID')
 if operation=='audit.event.read':
  if query:fail('AUDIT_QUERY_UNKNOWN_PARAMETER')
  m=re.fullmatch(r'/audit/events/([0-9a-f-]{36})',path)
  if not m:fail('AUDIT_PATH_INVALID')
  try:id=str(uuid.UUID(m[1]))
  except ValueError:fail('AUDIT_PATH_INVALID')
  if id!=m[1]:fail('AUDIT_PATH_INVALID')
  return {'auditId':id}
 if operation!='audit.event.list' or path!='/audit/events':fail('AUDIT_PATH_INVALID')
 fields=S['$defs']['CoreQuery']['properties'];pairs={};kinds=[]
 for token in query.split(b'&') if query else []:
  if b'=' not in token:fail('AUDIT_QUERY_ENCODING_INVALID')
  key,value=map(text,token.split(b'=',1))
  if key not in fields:fail('AUDIT_QUERY_UNKNOWN_PARAMETER')
  if key=='recordKinds':
   if value in kinds:fail('AUDIT_QUERY_DUPLICATE_RECORD_KIND')
   kinds.append(value);continue
  if key in pairs:fail('AUDIT_QUERY_DUPLICATE_PARAMETER')
  pairs[key]=value
 native={'recordKinds':kinds}
 for name,schema in fields.items():
  if name=='recordKinds':continue
  nullable='null' in schema.get('type',[])
  if name not in pairs:
   if nullable:native[name]=None;continue
   fail('AUDIT_QUERY_REQUIRED_PARAMETER')
  value=pairs[name]
  if name=='limit':
   if not re.fullmatch('[1-9][0-9]*',value):fail('AUDIT_QUERY_INVALID')
   value=int(value)
  native[name]=value
 valid('CoreQuery',native,'AUDIT_QUERY_INVALID')
 try:a=datetime.fromisoformat(native['from'].replace('Z','+00:00'));b=datetime.fromisoformat(native['to'].replace('Z','+00:00'))
 except ValueError:fail('AUDIT_QUERY_INVALID')
 if a>=b:fail('AUDIT_QUERY_INTERVAL_INVALID')
 return native

def raw(v):
 try:b=base64.b64decode(v,validate=True)
 except (ValueError,TypeError):fail('AUDIT_BYTE_ENCODING_INVALID')
 if base64.b64encode(b).decode()!=v:fail('AUDIT_BYTE_ENCODING_INVALID')
 return b

def framed_hash(version,previous,sequence,data):
 if version!=1 or not isinstance(previous,bytes) or len(previous)!=32 or not isinstance(sequence,int) or isinstance(sequence,bool) or not 1<=sequence<=9223372036854775807 or not isinstance(data,bytes):fail('AUDIT_HASH_INPUT_INVALID')
 return hashlib.sha256(b'KCML-AUDIT-CHAIN'+struct.pack('!i',version)+previous+struct.pack('!q',sequence)+struct.pack('!q',len(data))+data).digest()

def json_bytes(data,code):
 def pairs(values):
  out={}
  for k,v in values:
   if k in out:fail(code+'_DUPLICATE_KEY')
   out[k]=v
  return out
 try:return json.loads(data.decode('utf-8'),object_pairs_hook=pairs)
 except (UnicodeError,json.JSONDecodeError):fail(code+'_INVALID')

def inspect(row,requested_id=None):
 if row.get('recordKind')=='UNRESOLVED_AUDIT_STREAM':fail('AUDIT_STORED_STREAM_UNRESOLVED')
 valid('AuditRecord',row,'AUDIT_RECORD_MASK_INVALID')
 if requested_id is not None and row['auditId']!=requested_id:fail('AUDIT_RECORD_IDENTITY_MISMATCH')
 audit=raw(row['canonicalAuditBytesBase64'])
 h=framed_hash(row['chainFormatVersion'],bytes.fromhex(row['previousHash'][7:]),int(row['chainSequence']),audit)
 if 'sha256:'+h.hex()!=row['eventHash']:fail('AUDIT_CHAIN_HASH_MISMATCH')
 if row['recordKind']=='DOMAIN_EVENT_AUDIT':
  payload=raw(row['eventPayloadBytesBase64'])
  if not payload:fail('AUDIT_EVENT_PAYLOAD_EMPTY')
  if 'sha256:'+hashlib.sha256(payload).hexdigest()!=row['eventPayloadDigest']:fail('AUDIT_EVENT_PAYLOAD_DIGEST_MISMATCH')
  return {'auditId':row['auditId'],'recordKind':row['recordKind'],'chainSequence':row['chainSequence'],'eventHash':row['eventHash'],'verifiedCanonicalAuditBytes':audit,'verifiedEventPayloadBytes':payload,'capability':'IMMUTABLE_BYTE_INSPECTION_ONLY','businessPayloadHydrated':False}
 outcome_bytes=raw(row['retainedOutcomeBytesBase64'])
 if 'sha256:'+hashlib.sha256(outcome_bytes).hexdigest()!=row['retainedOutcomeDigest']:fail('AUDIT_RETAINED_OUTCOME_DIGEST_MISMATCH')
 outcome=json_bytes(outcome_bytes,'AUDIT_RETAINED_OUTCOME_JSON')
 valid('PrerootOutcome',outcome,'AUDIT_RETAINED_OUTCOME_MASK_INVALID')
 if outcome!=row['retainedOutcome']:fail('AUDIT_RETAINED_OUTCOME_PROJECTION_MISMATCH')
 if outcome['logicalOperationId']!=row['logicalOperationId']:fail('AUDIT_RETAINED_OUTCOME_IDENTITY_MISMATCH')
 # Actual deferred §12.54 typed-link assertions. This is the logical command,
 # never the prospective (possibly now-created) generation root.
 summary=json_bytes(audit,'AUDIT_PREROOT_CANONICAL_JSON')
 if not isinstance(summary,dict) or summary.get('objectId')!=row['logicalOperationId'] or summary.get('actorId')!=row['actorId'] or summary.get('afterDigest')!=row['retainedOutcomeDigest']:fail('AUDIT_PREROOT_COMMAND_BINDING_MISMATCH')
 if outcome['status']=='ACCEPTED' and (outcome['terminal'] or outcome['error'] is not None):fail('AUDIT_RETAINED_OUTCOME_STATE_MISMATCH')
 if outcome['status']!='ACCEPTED' and outcome['error'] is None:fail('AUDIT_RETAINED_OUTCOME_STATE_MISMATCH')
 if outcome['status']!='ACCEPTED':
  error=outcome['error']
  terminal=error['classification']!='UNKNOWN' and error['retryDirective']!='RETRY_SAME_OPERATION'
  if outcome['terminal']!=terminal or (outcome['status']=='CANCELLED')!=(error['stableCode']=='CREATE_CANCELLED'):fail('AUDIT_RETAINED_OUTCOME_STATE_MISMATCH')
  if outcome['status']=='FAILED' and not terminal and error['retryDirective'] not in ['RECONCILE_THEN_RETRY','RETRY_SAME_OPERATION']:fail('AUDIT_RETAINED_OUTCOME_STATE_MISMATCH')
 return {'auditId':row['auditId'],'recordKind':row['recordKind'],'chainSequence':row['chainSequence'],'eventHash':row['eventHash'],'verifiedCanonicalAuditBytes':audit,'verifiedRetainedOutcomeBytes':outcome_bytes,'retainedOutcome':outcome,'capability':'IMMUTABLE_COMMAND_OUTCOME_INSPECTION_ONLY','businessPayloadHydrated':False,'generationRootCreatedByThisOutcome':False}

def exact_secret_audit_projection(row):
 """Separate named producer's 13-field JSON bytes. Never assumed for all audit rows."""
 if row.get('recordKind')!='DOMAIN_EVENT_AUDIT':fail('AUDIT_CANONICAL_PROFILE_NOT_APPLICABLE')
 audit=inspect(row)['verifiedCanonicalAuditBytes']
 def pairs(values):
  out={}
  for k,v in values:
   if k in out:fail('AUDIT_CANONICAL_DUPLICATE_KEY')
   out[k]=v
  return out
 try:v=json.loads(audit.decode('utf-8'),object_pairs_hook=pairs)
 except (UnicodeError,json.JSONDecodeError):fail('AUDIT_CANONICAL_JSON_INVALID')
 valid('CanonicalAuditBytes',v,'AUDIT_CANONICAL_PROFILE_INVALID')
 joins={'logicalOperationId':'logicalOperationId','eventId':'domainEventId','correlationId':'correlationId','causationId':'causationId','chainSequence':'chainSequence','previousHash':'previousHash','objectId':'aggregateId','actorId':'actorId'}
 if any(v[a]!=row[b] for a,b in joins.items()):fail('AUDIT_CANONICAL_ROW_BINDING_MISMATCH')
 return v

# Exact physical FK joins. No canonical_json cast/format rewrite or read-time hash
# mutation. Scoped filtering/authentication belongs to the declared producer.
SQL_PROJECTION="""SELECT CASE
WHEN a.domain_event_id IS NOT NULL AND e.id IS NOT NULL THEN
 jsonb_build_object('recordKind','DOMAIN_EVENT_AUDIT',
 'auditId',a.id::text,'chainSequence',a.chain_sequence::text,
 'previousHash','sha256:'||encode(a.previous_hash,'hex'),'eventHash','sha256:'||encode(a.event_hash,'hex'),'chainFormatVersion',a.chain_format_version,
 'canonicalAuditBytesBase64',replace(encode(a.canonical_bytes,'base64'),E'\\n',''),
 'logicalOperationId',a.logical_operation_id::text,'actorId',c.owner_id::text,'domainEventId',a.domain_event_id::text,
 'aggregateId',e.aggregate_id::text,'aggregateKind',e.aggregate_kind,'eventType',e.event_type,'eventSchemaId',e.event_schema_id,
 'eventSchemaDigest','sha256:'||encode(e.event_schema_digest,'hex'),
 'eventPayloadBytesBase64',replace(encode(e.payload_bytes,'base64'),E'\\n',''),
 'eventPayloadDigest','sha256:'||encode(e.payload_digest,'hex'),'correlationId',e.correlation_id::text,'causationId',e.causation_id::text,
 'occurredAt',to_char(e.occurred_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'archiveRequired',a.archive_required)
WHEN a.domain_event_id IS NULL AND o.audit_id IS NOT NULL AND c.operation_id='generation.job.create' THEN
 jsonb_build_object('recordKind','GENERATION_PREROOT_OUTCOME_AUDIT',
 'auditId',a.id::text,'chainSequence',a.chain_sequence::text,
 'previousHash','sha256:'||encode(a.previous_hash,'hex'),'eventHash','sha256:'||encode(a.event_hash,'hex'),'chainFormatVersion',a.chain_format_version,
 'canonicalAuditBytesBase64',replace(encode(a.canonical_bytes,'base64'),E'\\n',''),
 'logicalOperationId',a.logical_operation_id::text,'actorId',c.owner_id::text,'archiveRequired',a.archive_required,
 'operationId',c.operation_id,'domainEventId',NULL,'prospectiveJobId',c.target_aggregate_id::text,
 'retainedStateVersion',o.state_version::text,'retainedOutcomeDigest','sha256:'||encode(o.canonical_digest,'hex'),
 'retainedOutcomeBytesBase64',replace(encode(o.canonical_bytes,'base64'),E'\\n',''),
 'retainedOutcome',convert_from(o.canonical_bytes,'UTF8')::jsonb)
ELSE jsonb_build_object('recordKind','UNRESOLVED_AUDIT_STREAM','auditId',a.id::text) END
FROM audit_event a JOIN domain_command c ON c.logical_operation_id=a.logical_operation_id
LEFT JOIN domain_event e ON e.id=a.domain_event_id AND e.logical_operation_id=a.logical_operation_id
LEFT JOIN generation_create_preroot_outcome o ON o.audit_id=a.id AND o.logical_operation_id=a.logical_operation_id"""

def project_sql_values(values):
 if len(values)!=1:fail('AUDIT_SQL_PROJECTION_ARITY')
 row=json.loads(values[0]);inspect(row);return row

def validate_core_result(native,result):
 valid('CoreResult',result,'AUDIT_RESULT_MASK_INVALID')
 if result['resolvedInterval']!={'from':native['from'],'to':native['to']}:fail('AUDIT_RESULT_INTERVAL_BINDING_MISMATCH')
 if len(result['items'])>native['limit']:fail('AUDIT_RESULT_PAGE_LIMIT_MISMATCH')
 ids=set()
 for row in result['items']:
  inspect(row)
  if row['auditId'] in ids:fail('AUDIT_RESULT_DUPLICATE_AUDIT_ID')
  ids.add(row['auditId'])
 # Validation of a declared coverage/result mask does not authenticate its producer.
 return result
