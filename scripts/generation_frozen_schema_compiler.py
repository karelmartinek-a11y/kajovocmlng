"""Version-scoped compiler; exact digest address, no global latest/$id alias."""
import json,hashlib
from referencing import Registry,Resource
from jsonschema.validators import validator_for
from jsonschema import FormatChecker
from generation_create_consumer import fail
from create_operation_contracts import strict_json

def sha(raw):return 'sha256:'+hashlib.sha256(raw).hexdigest()

def compile_frozen(address,bundles,*,dependencies=()):
    """definition is native $defs name; null selects entire schema document.

    dependencies are exact {schemaId,bundleDigest} server frozen closure entries.
    Each invocation constructs its own registry. Two archived revisions with
    same $id coexist across calls; conflicting aliases in one closure reject.
    No network retrieval or current-resource fallback.
    """
    if not isinstance(address,dict)or set(address)!={'schemaId','bundleDigest','definition'}:fail('FROZEN_SCHEMA_ADDRESS_INVALID')
    raw=bundles.get(address['bundleDigest'])
    if not isinstance(raw,bytes):fail('FROZEN_SCHEMA_BUNDLE_UNAVAILABLE')
    if sha(raw)!=address['bundleDigest']:fail('FROZEN_SCHEMA_BUNDLE_DIGEST_MISMATCH')
    bundle=strict_json(raw)
    if not isinstance(bundle,dict)or bundle.get('$id')!=address['schemaId']:fail('FROZEN_SCHEMA_ID_MISMATCH')
    cls=validator_for(bundle,default=None)
    if cls is None:fail('FROZEN_SCHEMA_DIALECT_UNSUPPORTED')
    try:cls.check_schema(bundle)
    except Exception:fail('FROZEN_SCHEMA_INVALID')
    registry=Registry().with_resource(address['schemaId'],Resource.from_contents(bundle))
    declared={address['schemaId']:address['bundleDigest']}
    for entry in dependencies:
        if not isinstance(entry,dict)or set(entry)!={'schemaId','bundleDigest'}:fail('FROZEN_SCHEMA_DEPENDENCY_ADDRESS_INVALID')
        uri=entry['schemaId'];expected=entry['bundleDigest']
        if uri in declared:
            if declared[uri]!=expected:fail('FROZEN_SCHEMA_DEPENDENCY_ALIAS_CONFLICT')
            fail('FROZEN_SCHEMA_DEPENDENCY_DUPLICATE')
        depraw=bundles.get(expected)
        if not isinstance(depraw,bytes):fail('FROZEN_SCHEMA_DEPENDENCY_UNAVAILABLE')
        if sha(depraw)!=expected:fail('FROZEN_SCHEMA_DEPENDENCY_DIGEST_MISMATCH')
        dep=strict_json(depraw)
        if not isinstance(dep,dict)or dep.get('$id')!=uri:fail('FROZEN_SCHEMA_DEPENDENCY_ID_MISMATCH')
        depcls=validator_for(dep,default=None)
        if depcls is None:fail('FROZEN_SCHEMA_DEPENDENCY_DIALECT_UNSUPPORTED')
        try:depcls.check_schema(dep)
        except Exception:fail('FROZEN_SCHEMA_DEPENDENCY_INVALID')
        declared[uri]=expected;registry=registry.with_resource(uri,Resource.from_contents(dep))
    name=address['definition']
    if name is not None:
        if not isinstance(name,str)or name not in bundle.get('$defs',{}):fail('FROZEN_SCHEMA_DEFINITION_UNRESOLVED')
        fragment=name.replace('~','~0').replace('/','~1')
        selected={'$ref':address['schemaId']+'#/$defs/'+fragment}
    else:selected=bundle
    validator=cls(selected,registry=registry,format_checker=FormatChecker())
    def validate(value):
        try:errors=list(validator.iter_errors(value))
        except Exception:fail('FROZEN_SCHEMA_REFERENCE_UNRESOLVED')
        if errors:fail('FROZEN_SCHEMA_CONTENT_INVALID',errors[0].json_path)
        return value
    return validate
