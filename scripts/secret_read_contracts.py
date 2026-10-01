"""Deterministic exact OWNER read mask projection from effective typed resources."""
import copy,json

def canonical_uuids(value):
 if isinstance(value,dict):
  if value.get('format')=='uuid':value['pattern']=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$(?![\s\S])'
  for child in value.values():canonical_uuids(child)
 elif isinstance(value,list):
  for child in value:canonical_uuids(child)

def specialize(payload,rs):
 read=json.loads(rs['contracts/secrets/owner-value-read.schema.json']['raw']);metadata=json.loads(rs['contracts/secrets/metadata-read.schema.json']['raw'])
 # Request/response domain masks are projections of these exact closed schemas.
 # Event applicability and missing full metadata producers remain OPEN.
 payload=copy.deepcopy(payload)
 for row in payload['records']:
  if row['operationId']not in ['secret.metadata.read','secret.value.read']:continue
  req=row['requestSchema'];props=req['properties']
  props['body']={'type':'null'}
  props['guards']={'type':'object','additionalProperties':False,'properties':{},'required':[]}
  props['pathParameters']={'type':'object','additionalProperties':False,'properties':{'id':{'type':'string','format':'uuid'}},'required':['id']}
  props['query']={'type':'object','additionalProperties':False,'properties':{},'required':[]}
  mask=metadata if row['operationId']=='secret.metadata.read'else read
  if row['operationId']=='secret.value.read':props['query']['properties']['versionId']={'type':'string','format':'uuid'}
  canonical_uuids(req)
  output={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:r9:semantic:'+row['routeId']+':output',**mask['response']}
  if '$defs'in mask:output['$defs']=mask['$defs']
  row['responseSchema']['properties']['output']={'oneOf':[{'type':'null'},output]}
  row['responseSchema']['allOf']=[v for v in row['responseSchema'].get('allOf',[]) if v.get('if',{}).get('properties',{}).get('status',{}).get('const')!='SUCCEEDED']
  row['responseSchema']['allOf'].append({'if':{'properties':{'status':{'const':'SUCCEEDED'}}},'then':{'properties':{'output':output,'error':{'type':'null'}}}})
  row['semanticRules']=list(dict.fromkeys(row.get('semanticRules',[])+['OWNER_FRESH_AUTH_BEFORE_DIAGNOSTIC','DERIVED_ROOT_STATUS_NOT_VERSION_LIFECYCLE','IMMUTABLE_REVEAL_BYTES_NO_CURRENT_FALLBACK','METADATA_HEADER_NOT_FULL_READ_PIPELINE']))
 # Deterministic idempotency: retain one exact success constraint after author rerun.
 for row in payload['records']:
  if row['operationId']in ['secret.metadata.read','secret.value.read']:
   unique=[]
   for v in row['responseSchema'].get('allOf',[]):
    if v not in unique:unique.append(v)
   row['responseSchema']['allOf']=unique
 from create_completion_contracts import canonical_digest
 payload['canonicalDigest']=canonical_digest({**payload,'canonicalDigest':None})
 return payload
