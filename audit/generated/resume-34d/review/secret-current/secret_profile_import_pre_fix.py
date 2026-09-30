"""Current-source profile import adapter; no credentials, grants, network or cipher choice."""
import copy,hashlib,json
from datetime import datetime,timezone
from secret_profile_reference import (SCHEMA,INVENTORY,Rejected,reject,strict_json,compiled_schema_bytes,
 schema_digest,canonical_b64,original_profile_slice,parse_profile,canonical_value_digest,use_profile)
APPROVED_PROFILES=tuple(p for p in INVENTORY if p!='BROWSER_AUTH_STATE_GRAPH_V1')

def active_import_document():
 return json.loads((__import__('pathlib').Path(__file__).resolve().parents[1]/'01_UI_CONTRACT/contracts/secrets/import.schema.json').read_text())

def candidate_from_http(raw):
 """Parse exact current HTTP bytes; no reserialization between decode and import."""
 from jsonschema import Draft202012Validator,FormatChecker
 body=strict_json(raw)
 errors=list(Draft202012Validator(active_import_document(),format_checker=FormatChecker()).iter_errors(body))
 if errors:reject('SECRET_PROFILE_SCHEMA_INVALID',errors[0].json_path)
 value=body['value']
 if 'encoding'in value:
  if body['type']in {INVENTORY[p]['secretType']for p in APPROVED_PROFILES}:reject('SECRET_PROFILE_REQUIRED','/value')
  original=value['text'].encode('utf8')if value['encoding']=='UTF8'else canonical_b64(value['base64'],'/value/base64')
  return {'type':body['type'],'representation':'RAW_UTF8'if value['encoding']=='UTF8'else'RAW_BINARY','profileId':None,'bytes':original}
 profile=value['profileId'];original=original_profile_slice(raw);parse_profile(profile,original)
 return {'type':body['type'],'representation':'PROFILE_JSON_V1','profileId':profile,'bytes':original}

def registry_profile(profile,read_registry,expected_normative_source_digest,expected_review_receipt_digest):
 """read_registry is an internal locked DB reader, never a field of native request."""
 if profile not in APPROVED_PROFILES:reject('SECRET_PROFILE_NOT_ACTIVE','/value/profileId')
 if not callable(read_registry):reject('SECRET_PROFILE_REGISTRY_UNAVAILABLE','/registry')
 row=read_registry(profile)
 required={'secretType','profileId','schemaId','schemaDigest','schemaBytes','status','normativeSourceDigest','reviewReceiptDigest'}
 if not isinstance(row,dict)or set(row)!=required:reject('SECRET_PROFILE_REGISTRY_UNAVAILABLE','/registry')
 if row['profileId']!=profile or row['secretType']!=INVENTORY[profile]['secretType']or row['status']!='ACTIVE':reject('SECRET_PROFILE_NOT_ACTIVE','/registry')
 if row['schemaId']!=SCHEMA['$id']+'#/$defs/'+profile or row['schemaBytes']!=compiled_schema_bytes(profile)or row['schemaDigest']!=schema_digest(profile):reject('SECRET_PROFILE_REGISTRY_SCHEMA_MISMATCH','/registry')
 # Normative source/review receipt authority is resolved by trusted acceptance
 # context; presence alone never grants DB role/context or marks owner approval.
 for field in ['normativeSourceDigest','reviewReceiptDigest']:
  if not isinstance(row[field],str)or not __import__('re').fullmatch('sha256:[0-9a-f]{64}',row[field]):reject('SECRET_PROFILE_REGISTRY_AUTHORITY_UNRESOLVED','/registry/'+field)
 if row['normativeSourceDigest']!=expected_normative_source_digest or row['reviewReceiptDigest']!=expected_review_receipt_digest:reject('SECRET_PROFILE_REGISTRY_AUTHORITY_UNRESOLVED','/registry')
 return row

def request_digest(raw,operation_id='secret.create'):
 candidate=candidate_from_http(raw);body=strict_json(raw)
 # Parsed semantic body alone would collapse 30 and 30.0, or unicode escape
 # spelling. Exact encrypted import bytes are therefore separately bound.
 original='sha256:'+hashlib.sha256(candidate['bytes']).hexdigest()
 semantic=json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
 return 'sha256:'+hashlib.sha256(b'KCML_SECRET_REQUEST_V1\0'+operation_id.encode()+b'\0'+semantic+b'\0'+original.encode()).hexdigest()

RAW_CONSUMER_SCHEMA={'type':'object','additionalProperties':False,'properties':{'consumerId':{'type':'string','minLength':1},'consumerRevision':{'type':'string','minLength':1},'purposeKind':{'type':'string','minLength':1},'rawTypes':{'type':'array','uniqueItems':True,'items':{'enum':['PASSWORD','API_KEY','BEARER_TOKEN','OAUTH_CLIENT','OAUTH_TOKEN_SET','TOTP_SEED','CERTIFICATE','PRIVATE_KEY','WEBHOOK_SECRET','DATABASE_CREDENTIAL','SESSION_STATE','COOKIE_JAR','SSH_CREDENTIAL','GENERIC_TEXT','GENERIC_BINARY']}}},'required':['consumerId','consumerRevision','purposeKind','rawTypes']}

def load_use_profile(raw,metadata,expected_version,consumer,now):
 """Plaintext is supplied only by canonical authenticated open, with trusted metadata."""
 if metadata['secretId']!=expected_version['secretId']or metadata['versionId']!=expected_version['versionId']:reject('SECRET_STORED_REFERENCE_MISMATCH','/metadata')
 if metadata['type']!=expected_version['type']:reject('SECRET_STORED_TYPE_MISMATCH','/metadata/type')
 if metadata['representation']=='PROFILE_JSON_V1':
  profile=metadata['profileId']
  if metadata['schemaDigest']!=schema_digest(profile):reject('SECRET_STORED_SCHEMA_MISMATCH','/metadata/schemaDigest')
  return use_profile(profile,raw,consumer,now)
 # Immutable historical RAW complex versions retain their own original type.
 # No promotion, JSON guessing or reinterpretation under edited root metadata.
 if metadata['representation']not in ['RAW_UTF8','RAW_BINARY']:reject('SECRET_STORED_REPRESENTATION_UNSUPPORTED','/metadata/representation')
 from jsonschema import Draft202012Validator
 if list(Draft202012Validator(RAW_CONSUMER_SCHEMA).iter_errors(consumer)):reject('SECRET_RAW_CONSUMER_DECLARATION_INVALID','/consumer')
 declarations=consumer['rawTypes']
 if metadata['type']not in declarations:reject('SECRET_RAW_CONSUMER_UNSUPPORTED','/consumer/rawTypes')
 if metadata['representation']=='RAW_UTF8':
  try:raw.decode('utf8',errors='strict')
  except UnicodeDecodeError:reject('SECRET_IMPORT_UTF8_INVALID','/metadata')
 return {'status':'RAW_REFERENCE_PREFLIGHT_PASSED','runtimeAuthenticated':False}
