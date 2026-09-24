"""Regression checks for Phase 3 schema identities and bounded wire counters."""
import copy
import hashlib
import json
import sys

from jsonschema import Draft202012Validator
from ssot_sources import ROOT, resource_index
from project_experience import project
from phase1_schema_closure import Inventory
from ssot_sources import SSOT, resources


def run():
    rs = resource_index()
    canonical = json.loads(rs['ui/contracts/live-experience.json']['raw'])
    physical_event = json.loads((ROOT/'01_UI_CONTRACT/ui/contracts/live-event.schema.json').read_text(encoding='utf-8'))
    physical_query = json.loads((ROOT/'01_UI_CONTRACT/ui/contracts/history-query.schema.json').read_text(encoding='utf-8'))
    experience_event = canonical['eventSchema']
    experience_query = canonical['observability']['querySchema']
    checks = []

    def check(name, fn):
        try:
            fn(); checks.append({'id': name, 'status': 'PASS'})
        except Exception as exc:
            checks.append({'id': name, 'status': 'FAIL', 'reason': str(exc)})

    def require(condition, reason):
        if not condition:
            raise AssertionError(reason)

    def identities():
        ids = [experience_event['$id'], physical_event['$id'], experience_query['$id'], physical_query['$id']]
        require(len(ids) == len(set(ids)), 'one active identity denotes more than one contract')
        require(physical_event == canonical['liveStreamSchema'], 'live stream projection differs from canonical source')
        require(physical_query == canonical['observability']['historyQuerySchema'], 'history query projection differs from canonical source')
        for schema in (experience_event, experience_query, physical_event, physical_query):
            Draft202012Validator.check_schema(schema)
        # Extend the SSOT resolver's identity registry with physical UI JSON
        # projections; the historical Phase 2 scanner only indexed embeddings.
        inventory = Inventory(SSOT.read_text(encoding='utf-8'))
        registry = {}
        def add(schema, source):
            if isinstance(schema, dict):
                identity = schema.get('$id')
                if identity:
                    canonical = json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
                    registry.setdefault(identity, {}).setdefault(canonical, []).append(source)
                for value in schema.values():
                    add(value, source)
            elif isinstance(schema, list):
                for value in schema: add(value, source)
        for identity, candidates in inventory.ids.items():
            for source, _fragment, schema in candidates:
                add(schema, source)
        for path in (ROOT/'01_UI_CONTRACT').rglob('*.json'):
            try: document = json.loads(path.read_text(encoding='utf-8'))
            except (UnicodeDecodeError, json.JSONDecodeError): continue
            add(document, str(path.relative_to(ROOT)))
        conflicts = {identity: sources for identity, variants in registry.items() if len(variants) > 1
                     for sources in variants.values()}
        require(not conflicts, 'conflicting schema identities: '+str({k:v for k,v in conflicts.items()}))
        project(check=True)
    check('identity.distinct-and-projections-exact', identities)

    maximum = '9223372036854775807'
    over = '9223372036854775808'
    stream_counter = Draft202012Validator(physical_event['properties']['sequence'])
    version_counter = Draft202012Validator(physical_event['properties']['stateVersion'])
    experience_sequence = Draft202012Validator(experience_event['properties']['sequence'])
    experience_version = Draft202012Validator(experience_event['properties']['stateVersion'])
    payload_contracts = json.loads(rs['contracts/payload-contracts.json']['raw'])
    route_event_schemas = [r['eventSchema'] for r in payload_contracts['records'] if r.get('eventSchema')]
    browser_contract = json.loads(rs['r14/contracts/browser-interaction.schema.json']['raw'])

    def counter_cases():
        require(len(route_event_schemas) == len(payload_contracts['records']) == 509,
                'R9 operation event inventory differs from 509 records')
        for event_schema in route_event_schemas:
            definition = event_schema['properties']['sequence']
            require(definition == physical_event['properties']['sequence'],
                    'R9 event sequence is not the exact positive Counter mask')
        require(browser_contract['$defs']['BrowserAllocationSnapshot']['properties']['stateVersion'] == {'$ref':'#/$defs/Counter'} and
                browser_contract['$defs']['BrowserHostSlot']['properties']['stateVersion'] == {'$ref':'#/$defs/Counter'},
                'R14 platform stateVersion not bound to exact Counter')
        browser_counter = Draft202012Validator(browser_contract['$defs']['Counter'])
        require(not list(browser_counter.iter_errors(maximum)), 'R14 Counter upper boundary rejected')
        require(bool(list(browser_counter.iter_errors(over))), 'R14 Counter overflow accepted')
        for validator in (stream_counter, version_counter, experience_sequence, experience_version):
            require(not list(validator.iter_errors('0' if validator is not stream_counter else '1')), 'lower bound rejected')
            require(not list(validator.iter_errors(maximum)), 'upper bound rejected')
            for bad in (over, '-1', '+1', ' 1', '01', '1.0', '1e3', 1, None):
                require(bool(list(validator.iter_errors(bad))), 'invalid counter accepted: '+repr(bad))
            # Values above 2^53 remain exact strings and are not coerced to JS Number.
            require(not list(validator.iter_errors('9007199254740992')), '2^53 decimal counter rejected')
        require(bool(list(stream_counter.iter_errors('0'))), 'sequence zero accepted although stream schema is positive')
    check('counter.int64-range-and-wire-type', counter_cases)

    route = next(r for r in json.loads(rs['contracts/payload-contracts.json']['raw'])['records']
                 if r['operationId'] == 'secret.value.read')
    response_schema = route['responseSchema']
    response_validator = Draft202012Validator(response_schema)
    error = {'stableCode': 'FAILED', 'classification': 'DEPENDENCY', 'retryDirective': 'DO_NOT_RETRY',
             'message': 'failed', 'detailsDigest': None}
    def response(status, terminal, output, err):
        return {'routeId': 'route.0390', 'operationId': 'secret.value.read',
                'logicalOperationId': '00000000-0000-4000-8000-000000000001',
                'correlationId': '00000000-0000-4000-8000-000000000002',
                'status': status, 'terminal': terminal, 'output': output, 'error': err,
                'resultDigest': 'sha256:'+'0'*64}

    def outcomes():
        # This exactly reproduces the historical mismatch and is rejected now.
        require(bool(list(response_validator.iter_errors(response('SUCCEEDED', False, None, None)))),
                'SUCCEEDED/terminal=false/null output incorrectly accepted')
        valid = [response('SUCCEEDED', True, None, None), response('ACCEPTED', False, None, None),
                 response('FAILED', False, None, error), response('CANCELLED', True, None, error)]
        for sample in valid:
            errors = list(response_validator.iter_errors(sample))
            require(not errors, 'normative response branch rejected: '+str(errors))
        for sample in [response('SUCCEEDED', True, None, error), response('ACCEPTED', True, None, None),
                       response('FAILED', False, None, None), response('CANCELLED', False, None, error)]:
            require(bool(list(response_validator.iter_errors(sample))), 'contradictory status/result accepted')
    check('response.status-terminal-error-branches', outcomes)

    operation_payloads = json.loads(rs['closure/contracts/operation-payloads.json']['raw'])
    state_fields = {
        'owner.mfa.reset': ['enrollmentState'],
        'chat.turn.steer': ['checkpointDisposition'],
        'config.rollback': ['state'],
        'backup.restore': ['state'],
        'acceptance.run.start': ['state'],
        'acceptance.run.cancel': ['state', 'cleanupStatus', 'reconciliationStatus'],
    }
    def state_probes():
        for operation, fields in state_fields.items():
            row = next(r for r in operation_payloads['records'] if r['operationId'] == operation)
            for field in fields:
                schema = row['responseSchema']['properties'][field]
                validator = Draft202012Validator(schema)
                require(not list(validator.iter_errors('NOT_A_VALID_STATE')),
                        f'{operation}.{field}: behavior changed; check whether authoritative state enum was found')
    check('state-fields-confirmed-open-unbounded-identifiers', state_probes)

    result = {'scope': 'Schema identity, counter and named status/outcome probes; state dictionaries and hydration remain open.',
              'checks': checks}
    output = ROOT/'audit/generated/phase3-semantic-checks.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return int(any(c['status'] == 'FAIL' for c in checks))


if __name__ == '__main__':
    raise SystemExit(run())
