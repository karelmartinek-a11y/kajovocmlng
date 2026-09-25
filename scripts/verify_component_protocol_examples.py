"""Witnesses that the four concrete R9 component masks accept valid exchanges.

Run after materializing all four masks. Also checks rejection of the old
empty-body request and inconsistent control admission/event states.
"""
import copy
import json

from jsonschema import Draft202012Validator, FormatChecker
from ssot_sources import load_resource

UUID = '11111111-1111-4111-8111-111111111111'
DIGEST = 'sha256:' + 'a'*64
TIME = '2026-09-25T00:00:00.000Z'


def validate(schema, instance):
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)


def envelope(route, body):
    req = route['requestSchema']
    guards = {
        'idempotencyKey': 'control-1', 'expectedStateVersion': '1',
        'expectedRevisionId': 'revision-1', 'expectedReleaseId': 'release-1',
        'expectedBindingSetRevision': 'binding-1', 'expectedActivationEpoch': '1',
        'deadlineAt': TIME, 'clientRequestDigest': DIGEST,
    }
    # Other protocol routes retain the existing nullable common guards.
    for key, definition in req['properties']['guards']['properties'].items():
        if key not in guards:
            guards[key] = None if 'null' in definition.get('type',[]) else DIGEST
    return {'routeId': route['routeId'], 'operationId': route['operationId'],
            'pathParameters': {}, 'query': [], 'body': body, 'guards': guards}


def control(route):
    body_schema = route['requestSchema']['properties']['body']
    body = {
        'schemaId': body_schema['$id'], 'commandId': UUID,
        'logicalOperationId': UUID,
        'desiredState': body_schema['properties']['desiredState']['const'],
        'reason': 'Owner requested change', 'correlationId': UUID,
        'causationId': UUID, 'componentId': 'component-1',
        'runtimeGeneration': '1', 'expectedActivationStateVersion': '1',
    }
    req = envelope(route, body)
    validate(route['requestSchema'], req)
    result_schema = route['responseSchema']['properties']['output']['oneOf'][1]
    result = {
        'schemaId': result_schema['$id'], 'commandId': UUID,
        'logicalOperationId': UUID, 'requestDigest': DIGEST,
        'desiredState': body['desiredState'], 'admission': 'ACCEPTED',
        'outcome': 'PENDING', 'componentStateVersion': '1',
        'activationStateVersion': '1', 'runtimeGeneration': '1',
        'releaseId': 'release-1', 'bindingSetRevision': 'binding-1',
        'activationEpoch': '1', 'recordedAt': TIME,
    }
    response = {'routeId': route['routeId'], 'operationId': route['operationId'],
                'logicalOperationId': UUID, 'correlationId': UUID,
                'status': 'ACCEPTED', 'terminal': False,
                'output': result, 'error': None, 'resultDigest': DIGEST}
    validate(route['responseSchema'], response)
    event = {'routeId': route['routeId'], 'operationId': route['operationId'],
             'eventType': 'ACCEPTED', 'logicalOperationId': UUID,
             'correlationId': UUID, 'sequence': '1',
             'payload': result, 'payloadDigest': DIGEST}
    validate(route['eventSchema'], event)
    assert route['responseSchema']['properties']['output']['oneOf'][1] == route['eventSchema']['properties']['payload']
    bad = copy.deepcopy(req)
    bad['body'] = None
    assert not Draft202012Validator(route['requestSchema']).is_valid(bad)
    bad = copy.deepcopy(event)
    bad['payload']['outcome'] = 'COMPLETED'
    assert not Draft202012Validator(route['eventSchema']).is_valid(bad)


def heartbeat(route):
    body = {
        'componentCode': 'KCML0001', 'executionId': UUID,
        'releaseId': 'release-1', 'runtimeId': 'runtime-1',
        'serviceGeneration': 'generation-1', 'runtimeGeneration': '1',
        'activationEpoch': '1', 'bindingSetRevision': '1',
        'heartbeatSequence': '1', 'lifecycleMode': 'ACTIVE',
        'operationalState': 'HEALTHY', 'ready': True,
        'dependencySummary': {'dependencies': []},
        'queueDepth': '0', 'activeRuns': '0',
        'resourceUsage': {'cpuMillis': '0', 'memoryMiB': 0, 'openFiles': '0'},
        'lastSuccessfulOperationAt': None, 'emittedAt': TIME,
        'nonce': 'nonce-1',
    }
    validate(route['requestSchema'], envelope(route, body))
    receipt = route['eventSchema']['properties']['payload']
    result = {'schemaId': receipt['$id'], 'disposition': 'ACCEPTED',
              'acceptedAt': TIME, 'receivedSequence': '1', 'nextDueAt': TIME,
              'effectiveBindingSetRevision': '1', 'effectiveActivationEpoch': '1',
              'pendingControlIntentReferences': []}
    validate(receipt, result)
    assert route['responseSchema']['properties']['output']['oneOf'][1] == receipt


def acknowledgement(route):
    body_schema = route['requestSchema']['properties']['body']
    body = {'schemaId': body_schema['$id'], 'commandId': UUID,
            'logicalOperationId': UUID, 'requestDigest': DIGEST,
            'status': 'COMPLETED', 'observedLifecycleMode': 'ACTIVE',
            'observedOperationalState': 'HEALTHY',
            'observedStateVersion': '1', 'runtimeId': 'runtime-1',
            'releaseId': 'release-1', 'serviceGeneration': 'generation-1',
            'runtimeGeneration': '1', 'bindingSetRevision': '1',
            'activationEpoch': '1', 'sourceSequence': '1',
            'detail': None, 'resultDigest': DIGEST,
            'correlationId': UUID, 'observedAt': TIME}
    validate(route['requestSchema'], envelope(route, body))
    receipt = route['eventSchema']['properties']['payload']
    result = {'schemaId': receipt['$id'], 'commandId': UUID,
              'sourceSequence': '1', 'ackDigest': DIGEST,
              'disposition': 'CURRENT', 'recordedAt': TIME}
    validate(receipt, result)
    assert route['responseSchema']['properties']['output']['oneOf'][1] == receipt


def main():
    routes = {r['routeId']:r for r in json.loads(load_resource('contracts/payload-contracts.json')['raw'])['records']}
    for rid in ('route.0000','route.0001'):
        control(routes[rid])
    heartbeat(routes['route.0003'])
    acknowledgement(routes['route.0004'])
    print('PASS: four component request/result examples and negative controls')


if __name__ == '__main__':
    main()
