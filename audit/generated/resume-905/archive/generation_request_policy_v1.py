"""Versioned existing generation create request semantic rules (§12.47)."""
from create_operation_contracts import ContractFailure
REVISION='GENERATION_CREATE_REQUEST_SEMANTICS_V1'
RULES=['NONEMPTY_INTENT','UNIQUE_ARTIFACT_REFERENCES']
def validate(value):
    if not value['intent'].strip():raise ContractFailure('EMPTY_INTENT','$.intent')
    ids=[s['artifactId']for s in value.get('sources',[])if 'artifactId'in s]
    if len(ids)!=len(set(ids)):raise ContractFailure('DUPLICATE_ARTIFACT_REFERENCE','$.sources')
    return value
