"""49.4 stable lookup and frozen create scope; executable design model only."""
import hashlib,json
from create_operation_contracts import ContractFailure
from create_completion_contracts import canonical_digest

FIELDS={'operationContractId','operationContractRevision','callerAuthorityKind',
        'stableCallerObjectId','stableCallerRevisionId','stableBusinessTargetKey','clientKeyDigest'}

def locator(request,owner):
 roots={'generation.job.create':('GENERATION','generation_job'),
        'secret.create':('SECRET','secret_record')}
 family,root=roots[request['operationId']]
 return {'operationFamilyId':family,'callerAuthorityKind':'OWNER_FULL','stableCallerObjectId':owner,
         'stableBusinessTargetKey':'CREATE_ROOT:'+root,
         'clientKeyDigest':'sha256:'+hashlib.sha256(request['idempotencyKey'].encode('utf8')).hexdigest()}

def freeze_descriptor(request,server,contract_revision):
 """Revision argument is a trusted server catalog field, never client input."""
 loc=locator(request,server['owner'])
 return {'operationContractId':request['operationId'],'operationContractRevision':contract_revision,
         **{k:loc[k] for k in ['callerAuthorityKind','stableCallerObjectId','stableBusinessTargetKey','clientKeyDigest']},
         'stableCallerRevisionId':None}

def verify_record(request,server,replay):
 expected=locator(request,server['owner'])
 if replay.get('locator')!=expected:raise ContractFailure('REPLAY_LOCATOR_UNVERIFIED','/replay/locator')
 descriptor=replay.get('executionDescriptor')
 if not isinstance(descriptor,dict) or set(descriptor)!=FIELDS:raise ContractFailure('REPLAY_DESCRIPTOR_UNVERIFIED','/replay/executionDescriptor')
 if replay.get('executionDescriptorDigest')!=canonical_digest(descriptor):raise ContractFailure('REPLAY_DESCRIPTOR_DIGEST_MISMATCH','/replay/executionDescriptorDigest')
 if not isinstance(descriptor['operationContractRevision'],str) or not descriptor['operationContractRevision']:
  raise ContractFailure('REPLAY_DESCRIPTOR_UNVERIFIED','/replay/executionDescriptor/operationContractRevision')
 # Current contract revision is deliberately absent from this comparison.
 if descriptor['operationContractId']!=request['operationId'] or descriptor['stableCallerRevisionId'] is not None or any(descriptor[k]!=expected[k] for k in ['callerAuthorityKind','stableCallerObjectId','stableBusinessTargetKey','clientKeyDigest']):
  raise ContractFailure('REPLAY_FROZEN_SCOPE_MISMATCH','/replay/executionDescriptor')
 return descriptor
