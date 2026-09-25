"""Materialize the component control ACK wire mask from SSOT §44.5 and §49.22."""
import base64
import copy
import gzip
import hashlib
import json

from phase1_repair_contracts import canonical_digest, encoded
from ssot_sources import SSOT, resource_index, resources

SCHEMA = 'https://json-schema.org/draft/2020-12/schema'


def exact(name, fields):
    props = {'schemaId': {'const': name}, **fields}
    return {'$id': name, '$schema': SCHEMA, 'type': 'object',
            'additionalProperties': False, 'properties': props,
            'required': list(props)}


def close(route, defs):
    assert route['routeId'] == 'route.0004' and route['operationId'] == 'component.control.ack'
    id_, uuid, digest = [copy.deepcopy(defs[x]) for x in ('Id','Uuid','Digest')]
    counter, stamp = [copy.deepcopy(defs[x]) for x in ('Counter','Timestamp')]
    lifecycle = copy.deepcopy(defs['SourceEnum000'])
    operational = copy.deepcopy(defs['SourceEnum002'])
    body = exact('urn:kcml:r9:semantic:route.0004:body', {
        'commandId': uuid, 'logicalOperationId': uuid, 'requestDigest': digest,
        'status': {'enum': ['ACCEPTED', 'REJECTED', 'COMPLETED', 'FAILED', 'UNKNOWN']},
        'observedLifecycleMode': lifecycle, 'observedOperationalState': operational,
        'observedStateVersion': counter,
        'runtimeId': id_, 'releaseId': id_, 'serviceGeneration': id_,
        'runtimeGeneration': counter, 'bindingSetRevision': counter,
        'activationEpoch': counter, 'sourceSequence': counter,
        'detail': {'type': ['string', 'null'], 'maxLength': 8192},
        'resultDigest': digest, 'correlationId': uuid, 'observedAt': stamp,
    })
    route['requestSchema']['properties']['body'] = body
    receipt = exact('urn:kcml:r9:semantic:route.0004:ack-receipt', {
        'commandId': uuid, 'sourceSequence': counter, 'ackDigest': digest,
        'disposition': {'enum': ['CURRENT', 'DUPLICATE', 'STALE_EVIDENCE']},
        'recordedAt': stamp,
    })
    route['responseSchema']['properties']['output'] = {
        'oneOf': [{'type': 'null'}, copy.deepcopy(receipt)]}
    route['eventSchema']['properties']['payload'] = copy.deepcopy(receipt)
    abandoned = {'DUPLICATE_SLOT_REJECT', 'CANONICAL_JSON_MUST_MATCH_VALUE_WHEN_NON_NULL',
                 'VALUE_DIGEST_OVER_CANONICAL_VALUE',
                 'PLATFORM_IDENTITY_FIELDS_FORBIDDEN_IN_BUSINESS_BODY'}
    route['semanticRules'] = [rule for rule in route['semanticRules'] if rule not in abandoned
                              and not rule.startswith('ACK_')]
    route['semanticRules'] += [
        'ACK_ADMISSION_STATUSES_ACCEPTED_REJECTED_OUTCOME_STATUSES_COMPLETED_FAILED_UNKNOWN',
        'ACK_ACCEPTED_IS_NOT_TERMINAL_COMPLETED_REQUIRES_EXACT_POSTCONDITION',
        'ACK_UNKNOWN_BLOCKS_CONFLICTING_COMMAND_AND_REQUIRES_RECONCILIATION',
        'ACK_IDENTICAL_COMMAND_SEQUENCE_DIGEST_IS_IDEMPOTENT',
        'ACK_IDENTICAL_COMMAND_SEQUENCE_DIFFERENT_DIGEST_IS_CONFLICT',
        'ACK_STALE_LINEAGE_STORED_AS_EVIDENCE_WITHOUT_PROJECTION_MUTATION',
        'ACK_RECEIPT_IDENTICAL_SCHEMA_FOR_RESPONSE_AND_EVENT',
    ]
    route['maskAuthoritySections'] = ['44.5', '49.22']


def main():
    text = SSOT.read_text(encoding='utf8')
    rs = resource_index(list(resources(text)))
    path = 'contracts/payload-contracts.json'
    payload = json.loads(rs[path]['raw'])
    defs = json.loads(rs['contracts/generation/generation-contracts.schema.json']['raw'])['$defs']
    selected = [r for r in payload['records'] if r['routeId'] == 'route.0004']
    assert len(selected) == 1
    close(selected[0], defs)
    old_payload = json.loads(rs[path]['raw'])
    old_digest = old_payload.pop('canonicalDigest')
    assert old_digest == canonical_digest({**old_payload, 'canonicalDigest': None})
    candidate = copy.deepcopy(payload)
    candidate.pop('canonicalDigest')
    payload['canonicalDigest'] = canonical_digest({**candidate, 'canonicalDigest': None})
    raw = encoded(payload, rs[path]['raw'])
    manifest = json.loads(rs['manifest.json']['raw'])
    manifest['resources'][path].update(sizeBytes=len(raw),
        sha256='sha256:'+hashlib.sha256(raw).hexdigest())
    changed = {path: raw, 'manifest.json': encoded(manifest,rs['manifest.json']['raw'])}
    for name in sorted(changed,key=lambda n:rs[n]['match'].start(),reverse=True):
        r, data = rs[name], changed[name]
        encoding = r['declared'].get('encoding','plain')
        if encoding == 'gzip+base64':
            b64 = base64.b64encode(gzip.compress(data,compresslevel=6,mtime=0)).decode()
            body,lang = '\n'.join(b64[i:i+120] for i in range(0,len(b64),120))+'\n','text'
        else:
            body,lang = data.decode(),'json'
        block = (f'<!-- {r["family"]} path="{name}" kind="{r["declared"]["kind"]}" '
                 f'bytes="{len(data)}" sha256="{hashlib.sha256(data).hexdigest()}" '
                 f'encoding="{encoding}" -->\n```{lang}\n{body}```\n'
                 f'<!-- {r["family"]}-END -->')
        a,b = r['match'].span()
        text = text[:a]+block+text[b:]
    SSOT.write_text(text,encoding='utf8',newline='\n')
    print('R9 control ACK mask materialized: route.0004')


if __name__ == '__main__':
    main()
