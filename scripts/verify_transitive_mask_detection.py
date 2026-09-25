"""Regression: a $ref wrapper must not hide an unbound domain slot."""
import hashlib
import json

from phase1_schema_closure import Inventory
from ssot_sources import ROOT, SSOT


def main():
    doc = {'$id': 'urn:mask-regression', '$schema': 'https://json-schema.org/draft/2020-12/schema',
           '$defs': {'generic': {'type': 'object', 'properties': {
               'schemaId': {'type': 'string'}, 'values': {'type': 'array', 'items': {}}}},
               'wrapper': {'$ref': '#/$defs/generic'},
               'nested': {'allOf': [{'$ref': '#/$defs/wrapper'}]},
               'exact': {'type': 'object', 'additionalProperties': False,
                         'properties': {'name': {'type': 'string'}}, 'required': ['name']},
               'missing': {'$ref': '#/$defs/absent'}}}
    text = '<!-- KCML-EMBEDDED path="regression.json" -->\n```json\n' + json.dumps(doc) + \
           '\n```\n<!-- KCML-EMBEDDED-END -->'
    inv = Inventory(text)
    checks = []
    for name, generic in [('generic', True), ('wrapper', True), ('nested', True), ('exact', False)]:
        row = inv.boundary('request', 'regression.json#/$defs/' + name, 'regression')
        actual = row.get('concreteness') == 'GENERIC_ENVELOPE'
        checks.append({'case': name, 'expectedGeneric': generic, 'actualGeneric': actual,
                       'passed': row['resolution']=='RESOLVED' and actual == generic})
    row = inv.boundary('request', 'regression.json#/$defs/missing', 'regression')
    checks.append({'case': 'unresolved-transitive-ref', 'passed': bool(row['nestedReferenceFailures'])})
    report = {'sourceSha256': hashlib.sha256(SSOT.read_bytes()).hexdigest(),
              'scope': __doc__, 'checks': checks, 'failed': sum(not c['passed'] for c in checks)}
    (ROOT/'audit/generated/transitive-mask-tests.json').write_text(
        json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps(report))
    return int(bool(report['failed']))


if __name__ == '__main__':
    raise SystemExit(main())
