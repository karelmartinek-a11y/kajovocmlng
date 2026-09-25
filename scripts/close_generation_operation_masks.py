"""Bind the exact server step boundaries explicitly assigned by SSOT 56.8.

No HTTP route or model proposal is substituted for a server StepInput/Output.
The original unresolved identities are retained, with references to the native
definitions (and their required fields, variants and scoped transitive refs).
"""
import argparse
import base64
import gzip
import hashlib
import json

from phase1_repair_contracts import encoded
from ssot_sources import SSOT, resource_index, resources

OPERATIONS = {
    'generation.workspace.patch': ('MCP_IMPLEMENT', 'AGENT_COMPILE', 'UI_IMPLEMENT',
                                   'SCHEMA_GENERATE', 'TEST_GENERATE'),
    'generation.workspace.validate': ('BUILD',),
    'generation.activation.switch': ('ACTIVATE',),
    'generation.integration.step': ('RUNTIME_PROVISION', 'IDENTITY_REGISTER',
                                    'CONTRACT_BINDING_APPLY', 'SECRET_BINDING_APPLY',
                                    'EXTERNAL_TARGET_APPLY', 'MONITORING_APPLY'),
    # 56.9 S03 is an inner saga operation, not an additional DAG node kind.
    'generation.candidate.publish': (),
}
PATH = 'contracts/operation-contracts.json'
GEN = 'contracts/generation/generation-contracts.schema.json'
CATALOG = 'contracts/generation/step-catalog.json'
SAGA = 'contracts/generation/integration-step-catalog.json'


def expected(rs):
    bundle = json.loads(rs[GEN]['raw'])
    catalog = json.loads(rs[CATALOG]['raw'])
    result = {}
    for operation, kinds in OPERATIONS.items():
        rows = [r for r in catalog if r['canonicalOperationId'] == operation]
        if {r['kind'] for r in rows} != set(kinds):
            raise ValueError('Source operation variant set changed: ' + operation)
        for role, field in [('command', 'inputDefinition'), ('response', 'outputDefinition')]:
            refs = []
            for row in rows:
                definition = row[field]
                if definition not in bundle['$defs']:
                    raise ValueError('Missing native definition: ' + definition)
                refs.append({'$ref': bundle['$id'] + '#/$defs/' + definition})
            if operation in ('generation.integration.step', 'generation.candidate.publish'):
                # 56.9 explicitly distinguishes inner saga steps from whole nodes.
                # Their disjoint required kind/stepId shapes prevent ambiguous dispatch.
                for step in json.loads(rs[SAGA]['raw']):
                    if step['operationId'] != operation:
                        continue
                    definition = 'IntegrationStepInput' if role == 'command' else 'IntegrationStepReceipt'
                    restriction = {'properties': {'stepId': {'const': step['stepId']}}}
                    if role == 'response':
                        restriction['if'] = {'properties': {'state': {'const': 'SUCCEEDED'}}}
                        restriction['then'] = {'properties': {'result': {
                            'properties': {'kind': {'const': step['outputKind']}}}}}
                    refs.append({'allOf': [
                        {'$ref': bundle['$id'] + '#/$defs/' + definition}, restriction]})
            if not refs:
                raise ValueError('Operation has no exact node or saga boundaries: ' + operation)
            result[operation + ':' + role] = {
                '$schema': bundle['$schema'],
                '$id': 'urn:kcml:r9:operation:' + operation + ':' + role,
                'description': 'SSOT 56.8 and 56.9 / ' + CATALOG + ': server-assembled input or '
                               'server-committed receipt; not a model proposal or HTTP body. '
                               'Artifact content hydration and guards remain mandatory (56.4, 56.12).',
                **(refs[0] if len(refs) == 1 else {'oneOf': refs}),
            }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = SSOT.read_text(encoding='utf8')
    rs = resource_index(resources(text))
    doc = json.loads(rs[PATH]['raw'])
    wanted = expected(rs)
    existing = doc.setdefault('$defs', {})
    for key, value in wanted.items():
        if key in existing and existing[key] != value:
            # Only the explanatory source citation changed for already installed masks.
            old = {k: v for k, v in existing[key].items() if k != 'description'}
            new = {k: v for k, v in value.items() if k != 'description'}
            if old != new:
                raise ValueError('Conflicting existing schema: ' + key)
    pending = any(existing.get(k) != v for k, v in wanted.items())
    if args.check:
        print(json.dumps({'pending': pending, 'identities': list(wanted)}))
        return int(pending)
    if not pending:
        print('No changes required')
        return 0
    existing.update(wanted)
    raw = encoded(doc, rs[PATH]['raw'])
    manifest = json.loads(rs['manifest.json']['raw'])
    manifest['resources'][PATH].update(sizeBytes=len(raw), sha256='sha256:' + hashlib.sha256(raw).hexdigest())
    changed = {PATH: raw, 'manifest.json': encoded(manifest, rs['manifest.json']['raw'])}
    for path in sorted(changed, key=lambda p: rs[p]['match'].start(), reverse=True):
        r, raw = rs[path], changed[path]
        encoding = r['declared']['encoding']
        if encoding == 'gzip+base64':
            data = base64.b64encode(gzip.compress(raw, compresslevel=6, mtime=0)).decode()
            body = '\n'.join(data[i:i+120] for i in range(0, len(data), 120)) + '\n'
            language = 'text'
        else:
            body, language = raw.decode(), 'json'
        block = (f'<!-- {r["family"]} path="{path}" kind="{r["declared"]["kind"]}" '
                 f'bytes="{len(raw)}" sha256="{hashlib.sha256(raw).hexdigest()}" encoding="{encoding}" -->\n'
                 f'```{language}\n{body}```\n<!-- {r["family"]}-END -->')
        a, b = r['match'].span()
        text = text[:a] + block + text[b:]
    SSOT.write_text(text, encoding='utf8', newline='\n')
    print(json.dumps({'changed': list(changed), 'schemas': len(wanted),
                      'ssotSha256': hashlib.sha256(SSOT.read_bytes()).hexdigest()}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
