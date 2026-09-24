"""Close evidenced Phase 3 UI schema-identity and Counter defects."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from ssot_sources import ROOT, SSOT, resource_index, resources

EXPERIENCE = 'ui/contracts/live-experience.json'
COUNTER = {
    'type': 'string', 'minLength': 1, 'maxLength': 19,
    'pattern': r'^(?:0|[1-9][0-9]{0,17}|[1-8][0-9]{18}|9[0-1][0-9]{17}|92[0-1][0-9]{16}|922[0-2][0-9]{15}|9223[0-2][0-9]{14}|92233[0-6][0-9]{13}|922337[0-1][0-9]{12}|92233720[0-2][0-9]{10}|922337203[0-5][0-9]{9}|9223372036[0-7][0-9]{8}|92233720368[0-4][0-9]{7}|922337203685[0-3][0-9]{6}|9223372036854[0-6][0-9]{5}|92233720368547[0-6][0-9]{4}|922337203685477[0-4][0-9]{3}|9223372036854775[0-7][0-9]{2}|922337203685477580[0-6]|9223372036854775807)$(?![\s\S])',
}
POSITIVE_COUNTER = {**COUNTER, 'pattern': COUNTER['pattern'].replace('(?:0|', '(?:')}


def canonical_digest(value):
    return 'sha256:'+hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def updates(rs):
    contract = json.loads(rs[EXPERIENCE]['raw'])
    live_path = ROOT/'01_UI_CONTRACT/ui/contracts/live-event.schema.json'
    query_path = ROOT/'01_UI_CONTRACT/ui/contracts/history-query.schema.json'
    live = json.loads(live_path.read_text(encoding='utf-8'))
    query = json.loads(query_path.read_text(encoding='utf-8'))
    expected_live_id = 'urn:kcml:live-event:1'
    expected_query_id = 'urn:kcml:history-query:1'
    if live.get('$id') != expected_live_id or query.get('$id') != expected_query_id:
        raise ValueError('Unexpected existing projection identity')
    if contract['eventSchema'].get('$id') not in (expected_live_id, 'urn:kcml:experience-event:1'):
        raise ValueError('Unexpected experience event identity')
    if contract['observability']['querySchema'].get('$id') not in (expected_query_id, 'urn:kcml:experience-history-query:1'):
        raise ValueError('Unexpected experience query identity')

    # Same $id currently denotes incompatible dashboard stream and experience
    # event objects, and likewise two unrelated history-query request shapes.
    contract['eventSchema']['$id'] = 'urn:kcml:experience-event:1'
    contract['observability']['querySchema']['$id'] = 'urn:kcml:experience-history-query:1'
    contract['liveStreamSchema'] = live
    contract['observability']['historyQuerySchema'] = query

    # Section 56.3/56.13 defines platform counters as bounded decimal strings.
    # The dashboard stream's sequence starts at one; the experience stream's
    # sequence and state version retain their existing inclusive zero domain.
    live['properties']['sequence'] = dict(POSITIVE_COUNTER)
    live['properties']['stateVersion'] = dict(COUNTER)
    contract['eventSchema']['properties']['sequence'] = dict(COUNTER)
    contract['eventSchema']['properties']['stateVersion'] = dict(COUNTER)

    result = {EXPERIENCE: contract}

    # SSOT 6.7 fixes SUCCEEDED => terminal=true and ACCEPTED => false. The
    # route-local response schema had only status/error and failure/output
    # implications, so it admitted the reproduced impossible success tuple.
    payload_path = 'contracts/payload-contracts.json'
    payloads = json.loads(rs[payload_path]['raw'])
    bounded_event_sequences = 0
    route = next(r for r in payloads['records'] if r['operationId'] == 'secret.value.read')
    response = route['responseSchema']
    conditions = response.setdefault('allOf', [])
    required_rules = [
        {'if': {'properties': {'status': {'const': 'SUCCEEDED'}}},
         'then': {'properties': {'terminal': {'const': True}}}},
        {'if': {'properties': {'status': {'const': 'ACCEPTED'}}},
         'then': {'properties': {'terminal': {'const': False}}}},
        {'if': {'properties': {'status': {'const': 'CANCELLED'}}},
         'then': {'properties': {'terminal': {'const': True}, 'error': {'not': {'type': 'null'}}}}},
        {'if': {'properties': {'status': {'const': 'FAILED'}}},
         'then': {'properties': {'error': {'not': {'type': 'null'}}}}},
    ]
    for rule in required_rules:
        if rule not in conditions:
            conditions.append(rule)
    # R9 event envelopes use an event-stream sequence, governed by SSOT
    # Counter, not an unbounded decimal digit string.
    for record in payloads['records']:
        event = record.get('eventSchema')
        if event and 'sequence' in event.get('properties', {}):
            event['properties']['sequence'] = dict(POSITIVE_COUNTER)
            bounded_event_sequences += 1
    if bounded_event_sequences != len(payloads['records']):
        raise ValueError(f'Expected an event sequence on every R9 route; found {bounded_event_sequences}/{len(payloads["records"])}')
    original = json.loads(rs[payload_path]['raw'])
    old_digest = original.pop('canonicalDigest')
    candidate = copy.deepcopy(payloads); candidate.pop('canonicalDigest')
    if old_digest == canonical_digest(original):
        payloads['canonicalDigest'] = canonical_digest(candidate)
    elif old_digest == canonical_digest(original['records']):
        payloads['canonicalDigest'] = canonical_digest(candidate['records'])
    elif old_digest == canonical_digest({**original, 'canonicalDigest': None}):
        payloads['canonicalDigest'] = canonical_digest({**candidate, 'canonicalDigest': None})
    else:
        raise ValueError('Unknown payload canonicalDigest recipe; do not guess')
    result[payload_path] = payloads

    # R14's browser allocation/host-slot versions are platform stateVersion
    # values; reuse the exact normative Counter definition, not the former
    # unbounded decimal-string patterns.
    browser_path = 'r14/contracts/browser-interaction.schema.json'
    browser = json.loads(rs[browser_path]['raw'])
    browser['$defs']['Counter'] = json.loads(rs['contracts/generation/generation-contracts.schema.json']['raw'])['$defs']['Counter']
    for definition in ('BrowserAllocationSnapshot', 'BrowserHostSlot'):
        browser['$defs'][definition]['properties']['stateVersion'] = {'$ref': '#/$defs/Counter'}
    result[browser_path] = browser
    manifest_path = 'manifest.json'
    manifest = json.loads(rs[manifest_path]['raw'])
    manifest['resources'][payload_path].update(sizeBytes=0, sha256='')
    result[manifest_path] = manifest
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    rs = resource_index(list(resources()))
    source = rs[EXPERIENCE]
    candidate = updates(rs)
    encoded = {}
    for path, value in candidate.items():
        original = rs[path]['raw']
        pretty = original.lstrip().startswith(b'{\n')
        raw = (json.dumps(value, ensure_ascii=False, sort_keys=True,
            indent=2 if pretty else None, separators=None if pretty else (',', ':'))+'\n').encode()
        if path == 'contracts/payload-contracts.json':
            import copy as _copy
            manifest = candidate['manifest.json']
            manifest['resources'][path].update(sizeBytes=len(raw), sha256='sha256:'+hashlib.sha256(raw).hexdigest())
        encoded[path] = raw
    # Re-encode manifest after inserting the payload's final byte digest.
    manifest_original = rs['manifest.json']['raw']
    pretty = manifest_original.lstrip().startswith(b'{\n')
    encoded['manifest.json'] = (json.dumps(candidate['manifest.json'], ensure_ascii=False, sort_keys=True,
        indent=2 if pretty else None, separators=None if pretty else (',', ':'))+'\n').encode()
    changed = {p:raw for p,raw in encoded.items() if raw != rs[p]['raw']}
    if args.check:
        print(json.dumps({'reproducible': not changed, 'resources': list(changed)}))
        return int(bool(changed))
    if changed:
        import base64, gzip, re
        items = list(resources())
        text = SSOT.read_text(encoding='utf-8')
        for r in sorted(items, key=lambda x:x['match'].start(), reverse=True):
            path = r['path']
            if path not in changed: continue
            raw = changed[path]; encoding = r['declared'].get('encoding', 'plain')
            if encoding == 'gzip+base64':
                data = base64.b64encode(gzip.compress(raw, compresslevel=6, mtime=0)).decode()
                body = '\n'.join(data[i:i+120] for i in range(0, len(data), 120))+'\n'
                language = 'text'
            else:
                body = raw.decode(); language = 'json'
            header = f'<!-- {r["family"]} path="{path}" kind="{r["declared"]["kind"]}" bytes="{len(raw)}" sha256="{hashlib.sha256(raw).hexdigest()}" encoding="{encoding}" -->'
            replacement = header+'\n'+r['fence']+language+'\n'+body+r['fence']+'\n<!-- '+r['family']+'-END -->'
            text = text[:r['match'].start()]+replacement+text[r['match'].end():]
        SSOT.write_text(text, encoding='utf-8', newline='\n')
    print(json.dumps({'changed': list(changed)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
