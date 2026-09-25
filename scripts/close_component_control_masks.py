"""Materialize SSOT §42.1.1, §44.4–44.5 and §49.22 in R9 control masks.

This edit is deterministic. The embedded SSOT, not this script, remains the
authority after materialization. Run the R9 inventory again after applying.
"""
import base64
import copy
import gzip
import hashlib
import json

from phase1_repair_contracts import canonical_digest, encoded
from ssot_sources import SSOT, resource_index, resources

SCHEMA = 'https://json-schema.org/draft/2020-12/schema'
UUID = {'type': 'string', 'format': 'uuid'}
DIGEST = {'type': 'string', 'pattern': '^sha256:[0-9a-f]{64}$'}
ID = {'type': 'string', 'minLength': 1, 'maxLength': 256}
COUNTER = {'type': 'string', 'pattern': '^(0|[1-9][0-9]*)$'}
STAMP = {'type': 'string', 'format': 'date-time'}


def exact(schema_id, fields):
    properties = {'schemaId': {'const': schema_id}, **fields}
    return {'$id': schema_id, '$schema': SCHEMA, 'type': 'object',
            'additionalProperties': False, 'properties': properties,
            'required': list(properties)}


def close(route):
    rid = route['routeId']
    desired = 'ENABLED' if route['operationId'].endswith('.enable') else 'DISABLED'
    req = route['requestSchema']
    req['properties']['body'] = exact('urn:kcml:r9:semantic:'+rid+':body', {
        'commandId': UUID, 'logicalOperationId': UUID,
        'desiredState': {'const': desired},
        'reason': {'type': 'string', 'minLength': 1, 'maxLength': 8192},
        'correlationId': UUID, 'causationId': UUID,
        'componentId': ID, 'revisionId': ID, 'releaseId': ID,
        'runtimeGeneration': COUNTER, 'bindingSetRevision': ID,
        'activationEpoch': COUNTER, 'expectedComponentStateVersion': COUNTER,
        'expectedActivationStateVersion': COUNTER,
        'deadlineAt': STAMP, 'requestDigest': DIGEST,
        'idempotencyKey': {'type': 'string', 'minLength': 1, 'maxLength': 512},
    })
    guards = req['properties']['guards']['properties']
    for key in ('deadlineAt', 'expectedActivationEpoch', 'expectedBindingSetRevision',
                'expectedReleaseId', 'expectedRevisionId', 'expectedStateVersion',
                'idempotencyKey'):
        guards[key]['type'] = 'string'
    req['properties']['guards']['required'] = list(guards)
    fields = {
        'commandId': UUID, 'logicalOperationId': UUID, 'requestDigest': DIGEST,
        'desiredState': {'const': desired},
        'admission': {'enum': ['ACCEPTED', 'REJECTED']},
        'outcome': {'enum': ['PENDING', 'COMPLETED', 'FAILED', 'UNKNOWN']},
        'componentStateVersion': COUNTER, 'activationStateVersion': COUNTER,
        'runtimeGeneration': COUNTER, 'releaseId': ID,
        'bindingSetRevision': ID, 'activationEpoch': COUNTER,
        'recordedAt': STAMP,
    }
    result = exact('urn:kcml:r9:semantic:'+rid+':control-result', fields)
    result['allOf'] = [
        {'if': {'properties': {'admission': {'const': 'REJECTED'}}},
         'then': {'properties': {'outcome': {'const': 'FAILED'}}}},
        {'if': {'properties': {'outcome': {'const': 'PENDING'}}},
         'then': {'properties': {'admission': {'const': 'ACCEPTED'}}}},
    ]
    route['responseSchema']['properties']['output'] = {'oneOf': [{'type': 'null'}, copy.deepcopy(result)]}
    route['eventSchema']['properties']['payload'] = copy.deepcopy(result)
    route['responseSchema']['allOf'] = [
        {'if': {'properties': {'status': {'const': 'ACCEPTED'}}},
         'then': {'properties': {'terminal': {'const': False},
                                 'output': copy.deepcopy(result), 'error': {'type': 'null'}}}},
    ]
    route['eventSchema']['allOf'] = [
        {'if': {'properties': {'eventType': {'const': 'ACCEPTED'}}},
         'then': {'properties': {'payload': {'properties': {'admission': {'const': 'ACCEPTED'},
                                                             'outcome': {'const': 'PENDING'}}}}}},
        {'if': {'properties': {'eventType': {'const': 'RECONCILING'}}},
         'then': {'properties': {'payload': {'properties': {'outcome': {'const': 'UNKNOWN'}}}}}},
    ]
    discarded = {'DUPLICATE_SLOT_REJECT', 'CANONICAL_JSON_MUST_MATCH_VALUE_WHEN_NON_NULL',
                 'VALUE_DIGEST_OVER_CANONICAL_VALUE',
                 'PLATFORM_IDENTITY_FIELDS_FORBIDDEN_IN_BUSINESS_BODY'}
    route['semanticRules'] = [x for x in route['semanticRules'] if x not in discarded and
        not x.startswith(('CONTROL_', 'ACCEPTED_', 'COMPLETED_', 'PENDING_'))]
    route['semanticRules'] += [
        'CONTROL_COMMAND_FIELDS_AND_GUARDS_MUST_MATCH_EXACTLY',
        'ACCEPTED_IS_DURABLE_ADMISSION_ONLY_NOT_EFFECTIVE_OUTCOME',
        'COMPLETED_REQUIRES_FENCED_OUTCOME_AND_CURRENT_ROUTE_STATE_HEARTBEAT',
        'PENDING_NOT_TERMINAL_UNKNOWN_REQUIRES_RECONCILIATION',
        'CONTROL_RESULT_IDENTICAL_SCHEMA_FOR_RESPONSE_AND_EVENT',
        'CONTROL_TARGET_IDENTITY_FROM_TRUSTED_COMPONENT_ORIGIN_ONLY',
    ]
    route['maskAuthoritySections'] = ['42.1.1', '44.4', '44.5', '49.22']


def main():
    text = SSOT.read_text(encoding='utf8')
    rs = resource_index(list(resources(text)))
    name = 'contracts/payload-contracts.json'
    payload = json.loads(rs[name]['raw'])
    selected = [r for r in payload['records'] if r['operationId'] in
                ('component.control.enable', 'component.control.disable')]
    assert len(selected) == 2
    for route in selected:
        close(route)
    original = json.loads(rs[name]['raw'])
    old = original.pop('canonicalDigest')
    assert old == canonical_digest({**original, 'canonicalDigest': None})
    copy_without_digest = copy.deepcopy(payload)
    copy_without_digest.pop('canonicalDigest')
    payload['canonicalDigest'] = canonical_digest({**copy_without_digest, 'canonicalDigest': None})
    raw = encoded(payload, rs[name]['raw'])
    manifest = json.loads(rs['manifest.json']['raw'])
    manifest['resources'][name].update(sizeBytes=len(raw),
        sha256='sha256:'+hashlib.sha256(raw).hexdigest())
    changed = {name: raw, 'manifest.json': encoded(manifest, rs['manifest.json']['raw'])}
    for path in sorted(changed, key=lambda p: rs[p]['match'].start(), reverse=True):
        r, data = rs[path], changed[path]
        encoding = r['declared'].get('encoding', 'plain')
        if encoding == 'gzip+base64':
            data64 = base64.b64encode(gzip.compress(data, compresslevel=6, mtime=0)).decode()
            body, language = '\n'.join(data64[i:i+120] for i in range(0,len(data64),120))+'\n', 'text'
        else:
            body, language = data.decode(), 'json'
        block = (f'<!-- {r["family"]} path="{path}" kind="{r["declared"]["kind"]}" '
                 f'bytes="{len(data)}" sha256="{hashlib.sha256(data).hexdigest()}" '
                 f'encoding="{encoding}" -->\n```{language}\n{body}```\n'
                 f'<!-- {r["family"]}-END -->')
        a,b = r['match'].span()
        text = text[:a]+block+text[b:]
    SSOT.write_text(text,encoding='utf8',newline='\n')
    print('R9 component control masks materialized:', *(r['routeId'] for r in selected))


if __name__ == '__main__':
    main()
