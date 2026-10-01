"""Frozen structural+domain policy dispatch. No eval/network/current fallback."""
import hashlib,json,re
from pathlib import Path
import generation_request_policy_v1 as policy_v1
from generation_frozen_schema_compiler import compile_frozen
from create_operation_contracts import strict_json,ContractFailure
POLICY_ID='urn:kcml:generation-create:domain-policy:1'
RULES=['NONEMPTY_INTENT','UNIQUE_ARTIFACT_REFERENCES']
def sha(raw):return 'sha256:'+hashlib.sha256(raw).hexdigest()
def fail(code):raise ContractFailure(code,'')
def policy_bytes(authority_bytes,implementation_bytes):
    return json.dumps({'policyId':POLICY_ID,'operationId':'generation.job.create',
      'revision':'GENERATION_CREATE_REQUEST_SEMANTICS_V1','rules':RULES,
      'authorityDigest':sha(authority_bytes),'implementationDigest':sha(implementation_bytes)},
      sort_keys=True,separators=(',',':')).encode()
def compile_archived_request(binding,bundles,*,policy_implementations):
    """binding from immutable SQL snapshot binding; bundle repository returns bytes.
    policy_implementations maps actual archived code digest to trusted loaded code;
    it is built by service deployment, never request/model JSON. This bounded
    dispatcher has exactly current established two domain rules; other revisions
    require their real implementation and fail BLOCKED instead of being migrated.
    """
    required={'schemaId','schemaDigest','policyId','policyDigest','dependencies'}
    if not isinstance(binding,dict) or set(binding)!=required:fail('FROZEN_POLICY_BINDING_INVALID')
    if any(not isinstance(binding[k],str)for k in required-{'dependencies'})or not isinstance(binding['dependencies'],list):fail('FROZEN_POLICY_BINDING_INVALID')
    if any(re.fullmatch(r'sha256:[0-9a-f]{64}',binding[k])is None for k in ['schemaDigest','policyDigest']):fail('FROZEN_POLICY_BINDING_INVALID')
    if not isinstance(bundles,dict)or not isinstance(policy_implementations,dict):fail('FROZEN_POLICY_REPOSITORY_UNAVAILABLE')
    raw=bundles.get(binding['policyDigest'])
    if not isinstance(raw,bytes):fail('FROZEN_DOMAIN_POLICY_UNAVAILABLE')
    if sha(raw)!=binding['policyDigest']:fail('FROZEN_DOMAIN_POLICY_DIGEST_MISMATCH')
    p=strict_json(raw)
    if not isinstance(p,dict)or set(p)!={'policyId','operationId','revision','rules','authorityDigest','implementationDigest'}:fail('FROZEN_DOMAIN_POLICY_SHAPE_INVALID')
    if p['policyId']!=binding['policyId']or p['policyId']!=POLICY_ID or p['operationId']!='generation.job.create':fail('FROZEN_DOMAIN_POLICY_IDENTITY_MISMATCH')
    if any(not isinstance(p[k],str)or re.fullmatch(r'sha256:[0-9a-f]{64}',p[k])is None for k in ['authorityDigest','implementationDigest']):fail('FROZEN_DOMAIN_POLICY_SHAPE_INVALID')
    authority=bundles.get(p['authorityDigest'])
    if not isinstance(authority,bytes)or sha(authority)!=p['authorityDigest']:fail('FROZEN_DOMAIN_POLICY_AUTHORITY_UNAVAILABLE')
    implementation=policy_implementations.get(p['implementationDigest'])
    if not isinstance(implementation,bytes)or sha(implementation)!=p['implementationDigest']:fail('FROZEN_DOMAIN_POLICY_IMPLEMENTATION_UNAVAILABLE')
    # Only this exact implementation revision is executable here; a supplied
    # arbitrary script is not evaluated, and matching $id does not select latest.
    if implementation!=DOMAIN_IMPLEMENTATION or p['revision']!='GENERATION_CREATE_REQUEST_SEMANTICS_V1'or p['rules']!=RULES:fail('FROZEN_DOMAIN_POLICY_REVISION_UNSUPPORTED')
    structural=compile_frozen({'schemaId':binding['schemaId'],'bundleDigest':binding['schemaDigest'],'definition':None},bundles,dependencies=binding['dependencies'])
    def validate(value):
        structural(value)
        policy_v1.validate(value)
        return value
    return validate
# Real loaded, versioned implementation source bytes are archived verbatim.
# An old unsupported implementation is never evaluated from untrusted storage.
DOMAIN_IMPLEMENTATION=Path(policy_v1.__file__).read_bytes()
