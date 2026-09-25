"""Counter domain and response/event parity, sourced from SSOT 56.3/56.13."""
import hashlib
import json
import subprocess
import sys

from jsonschema import Draft202012Validator
from ssot_sources import ROOT, SSOT, resource_index, resources


def main():
    baseline = '--baseline' in sys.argv
    raw = subprocess.check_output(['git','show','e025079:00_SSOT/KajovoCMLNG_SSOT.md']) if baseline else SSOT.read_bytes()
    rs = resource_index(resources(raw.decode('utf8')))
    payload = json.loads(rs['contracts/payload-contracts.json']['raw'])
    checks = []
    values = [('0', True), ('1', True), ('9223372036854775807', True),
              ('9223372036854775808', False), ('01', False), ('-1', False),
              ('binding-1', False), (1, False), (None, False)]
    for route in payload['records']:
        if route['operationId'] not in ('component.control.enable', 'component.control.disable'):
            continue
        schemas = {'guards': route['requestSchema']['properties']['guards'],
                   'body': route['requestSchema']['properties']['body'],
                   'result': route['responseSchema']['properties']['output']['oneOf'][1],
                   'event': route['eventSchema']['properties']['payload']}
        fields = {'guards': ['expectedStateVersion','expectedBindingSetRevision','expectedActivationEpoch'],
                  'body': ['runtimeGeneration','expectedActivationStateVersion'],
                  'result': ['componentStateVersion','activationStateVersion','runtimeGeneration',
                             'bindingSetRevision','activationEpoch']}
        fields['event'] = fields['result']
        checks.append({'case': route['routeId']+'/result-event-identity',
                       'passed': schemas['result'] == schemas['event']})
        for location, names in fields.items():
            for name in names:
                validator = Draft202012Validator(schemas[location]['properties'][name])
                for value, expected in values:
                    actual = validator.is_valid(value)
                    checks.append({'case': '/'.join((route['routeId'],location,name)), 'value':value,
                                   'expectedValid':expected,'actualValid':actual,'passed':actual==expected})
    report = {'sourceSha256':hashlib.sha256(raw).hexdigest(),'baseline':baseline,
              'scope':__doc__,'checked':len(checks),'failed':sum(not c['passed'] for c in checks),'checks':checks}
    suffix = 'baseline' if baseline else 'current'
    (ROOT/f'audit/generated/control-counter-{suffix}.json').write_text(
        json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:report[k] for k in ('sourceSha256','baseline','checked','failed')}))
    return int(bool(report['failed']))


if __name__ == '__main__':
    raise SystemExit(main())
