"""Materialize the already normative ComponentHeartbeat and its receipt (§44.1).

The request mask is copied verbatim from the embedded generation contract;
all of its recursive $defs are pinned inside the route's body schema.
"""
import base64
import copy
import gzip
import hashlib
import json

from phase1_repair_contracts import canonical_digest, encoded
from ssot_sources import SSOT, resource_index, resources

SCHEMA = 'https://json-schema.org/draft/2020-12/schema'


def definitions(defs, key):
    needed = set()
    def visit(name):
        if name in needed:
            return
        needed.add(name)
        def walk(item):
            if isinstance(item, dict):
                ref = item.get('$ref', '')
                if ref.startswith('#/$defs/'):
                    visit(ref[len('#/$defs/'):])
                for value in item.values():
                    walk(value)
            elif isinstance(item, list):
                for value in item:
                    walk(value)
        walk(defs[name])
    visit(key)
    return {name: copy.deepcopy(defs[name]) for name in sorted(needed)}


def close(route, source_defs):
    assert route['routeId'] == 'route.0003'
    req = route['requestSchema']
    req['properties']['body'] = {
        '$id': 'urn:kcml:r9:semantic:route.0003:body',
        '$schema': SCHEMA,
        '$ref': '#/$defs/ComponentHeartbeat',
        '$defs': definitions(source_defs, 'ComponentHeartbeat'),
    }
    receipt_id = 'urn:kcml:r9:semantic:route.0003:heartbeat-receipt'
    counter = copy.deepcopy(source_defs['Counter'])
    timestamp = copy.deepcopy(source_defs['Timestamp'])
    identity = copy.deepcopy(source_defs['Id'])
    receipt = {
        '$id': receipt_id, '$schema': SCHEMA, 'type': 'object',
        'additionalProperties': False,
        'properties': {
            'schemaId': {'const': receipt_id},
            'disposition': {'enum': ['ACCEPTED', 'DUPLICATE']},
            'acceptedAt': timestamp,
            'receivedSequence': counter,
            'nextDueAt': timestamp,
            'effectiveBindingSetRevision': counter,
            'effectiveActivationEpoch': counter,
            'pendingControlIntentReferences': {
                'type': 'array', 'items': identity, 'maxItems': 4096,
                'uniqueItems': True,
            },
        },
    }
    receipt['required'] = list(receipt['properties'])
    route['responseSchema']['properties']['output'] = {
        'oneOf': [{'type': 'null'}, copy.deepcopy(receipt)],
    }
    route['eventSchema']['properties']['payload'] = copy.deepcopy(receipt)
    abandoned = {'DUPLICATE_SLOT_REJECT', 'CANONICAL_JSON_MUST_MATCH_VALUE_WHEN_NON_NULL',
                 'VALUE_DIGEST_OVER_CANONICAL_VALUE',
                 'PLATFORM_IDENTITY_FIELDS_FORBIDDEN_IN_BUSINESS_BODY'}
    route['semanticRules'] = [rule for rule in route['semanticRules']
                              if rule not in abandoned and not rule.startswith('HEARTBEAT_')]
    route['semanticRules'] += [
        'HEARTBEAT_SOURCE_LINEAGE_FROM_TRUSTED_EXECUTION_CONTEXT_ONLY',
        'HEARTBEAT_EXACT_DUPLICATE_DIGEST_REPLAYS_RECEIPT',
        'HEARTBEAT_STALE_LINEAGE_ONLY_STALE_EVIDENCE_NO_FRESHNESS',
        'HEARTBEAT_SAME_SEQUENCE_DIFFERENT_DIGEST_IS_CONFLICT',
        'HEARTBEAT_RECEIPT_IS_DURABLE_EVIDENCE_NOT_CONTROL_OUTCOME_OR_BUSINESS_LEASE',
        'HEARTBEAT_RECEIPT_IDENTICAL_SCHEMA_FOR_RESPONSE_AND_EVENT',
    ]
    route['maskAuthoritySections'] = ['44.1', '6.13', '49.22']


def main():
    text = SSOT.read_text(encoding='utf8')
    rs = resource_index(list(resources(text)))
    name = 'contracts/payload-contracts.json'
    payload = json.loads(rs[name]['raw'])
    defs = json.loads(rs['contracts/generation/generation-contracts.schema.json']['raw'])['$defs']
    selected = [r for r in payload['records'] if r['routeId'] == 'route.0003']
    assert len(selected) == 1 and selected[0]['operationId'] == 'component.heartbeat'
    close(selected[0], defs)
    original = json.loads(rs[name]['raw'])
    old = original.pop('canonicalDigest')
    assert old == canonical_digest({**original, 'canonicalDigest': None})
    candidate = copy.deepcopy(payload)
    candidate.pop('canonicalDigest')
    payload['canonicalDigest'] = canonical_digest({**candidate, 'canonicalDigest': None})
    raw = encoded(payload, rs[name]['raw'])
    manifest = json.loads(rs['manifest.json']['raw'])
    manifest['resources'][name].update(sizeBytes=len(raw),
        sha256='sha256:'+hashlib.sha256(raw).hexdigest())
    updates = {name: raw, 'manifest.json': encoded(manifest, rs['manifest.json']['raw'])}
    for path in sorted(updates, key=lambda p: rs[p]['match'].start(), reverse=True):
        r, data = rs[path], updates[path]
        encoding = r['declared'].get('encoding', 'plain')
        if encoding == 'gzip+base64':
            b64 = base64.b64encode(gzip.compress(data, compresslevel=6, mtime=0)).decode()
            body, language = '\n'.join(b64[i:i+120] for i in range(0,len(b64),120))+'\n', 'text'
        else:
            body, language = data.decode(), 'json'
        block = (f'<!-- {r["family"]} path="{path}" kind="{r["declared"]["kind"]}" '
                 f'bytes="{len(data)}" sha256="{hashlib.sha256(data).hexdigest()}" '
                 f'encoding="{encoding}" -->\n```{language}\n{body}```\n'
                 f'<!-- {r["family"]}-END -->')
        a,b = r['match'].span()
        text = text[:a]+block+text[b:]
    SSOT.write_text(text, encoding='utf8', newline='\n')
    print('R9 heartbeat mask materialized: route.0003')


if __name__ == '__main__':
    main()
