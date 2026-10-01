"""OWNER metadata hydration; derived status remains display data, never authority.
Called under the same canonical OWNER value-read getter held credential/root
locks, using actual fresh bearer verification before any metadata diagnostic.
No API path to reveal KCML_OWNER_API_KEY; metadata has no value/verifier.
"""
from generation_auth_crypto import extract_owner_api_token,verify_token
from secret_value_read_transport import UUID,fail

def decode_metadata_read(method,path_parameters,raw_query,body):
 if method!='GET':fail('SECRET_METADATA_READ_METHOD_INVALID')
 if type(path_parameters)is not dict or set(path_parameters)!={'id'} or not isinstance(path_parameters['id'],str) or not UUID.fullmatch(path_parameters['id']):fail('SECRET_METADATA_READ_PATH_INVALID')
 if raw_query!=b'':fail('SECRET_METADATA_READ_QUERY_NOT_ALLOWED')
 if body not in (None,b''):fail('SECRET_METADATA_READ_BODY_NOT_ALLOWED')
 return {'operationId':'secret.metadata.read','secretId':path_parameters['id']}
def hydrate_owner_metadata(snapshot,headers,header_ceiling):
 token=extract_owner_api_token(headers,header_ceiling)
 if verify_token(token,snapshot['verifierHash'],header_ceiling)!=snapshot['fingerprint']:fail('OWNER_VALUE_READ_VERIFIER_FINGERPRINT_MISMATCH')
 # value-read non-ready diagnostics do not authorize a value or block valid
 # metadata for INACTIVE/DELETED roots. Exact integrity errors remain failures.
 allowed={'VALUE_READ_READY','SECRET_OWNER_VERSION_UNAVAILABLE','SECRET_OWNER_VALUE_REFERENCE_UNAVAILABLE','OWNER_CREDENTIAL_REVEAL_REQUIRES_OWNER_SESSION','SECRET_PROTECTED_ROW_AUTHORITY_UNAVAILABLE'}
 if snapshot['diagnostic'] not in allowed:fail(snapshot['diagnostic'])
 record=snapshot.get('recordMetadata');status=snapshot.get('recordStatus')
 if not isinstance(record,dict) or status not in ('INACTIVE','ACTIVE','DELETED'):fail('SECRET_METADATA_REFERENCE_UNAVAILABLE')
 if record['status']!=status:fail('SECRET_METADATA_STATUS_BINDING_MISMATCH')
 result=dict(record)
 for field in ('state_version','secret_activation_epoch'):
  val=result[field]
  if type(val)is not int or not 0<=val<=9223372036854775807:fail('SECRET_METADATA_COUNTER_INVALID')
  result[field]=str(val)
 return result

def hydrate_status_ui(metadata,value_response=None):
 # Both inputs are authenticated server responses. No ROOT ACTIVE flag may
 # substitute for request authorization or runtime consumer activation checks.
 if metadata['status'] not in ('INACTIVE','ACTIVE','DELETED'):fail('SECRET_UI_ROOT_STATUS_INVALID')
 if value_response is not None:
  if metadata['status']=='DELETED':fail('SECRET_UI_DELETED_VALUE_FORBIDDEN')
  if value_response['secretId']!=metadata['id'] or value_response['recordStateVersion']!=metadata['state_version'] or value_response['recordStatus']!=metadata['status']:fail('SECRET_UI_STATUS_SNAPSHOT_MISMATCH')
 return {'secretId':metadata['id'],'recordStatus':metadata['status'],'recordStateVersion':metadata['state_version'],'activeVersionId':metadata['active_version_id'],'valueVersionId':None if value_response is None else value_response['versionId'],'valueRevealed':value_response is not None}
