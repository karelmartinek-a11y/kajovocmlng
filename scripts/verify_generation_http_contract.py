"""Synthetic HTTP DESIGN checks; no deployed transport or complete route closure.

Uses the current local helper against exact embedded source bytes. The baseline
switch deliberately fails if its HTTP resource is absent; it never manufactures
the missing baseline resource by running document() or specialize().
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types

from jsonschema import Draft202012Validator, ValidationError

import generation_http_contract as http
from ssot_sources import ROOT, SSOT, resource_index, resources
from verify_phase2_handoffs import witness

BASELINE = '7006785'
CONTROL = 'scripts/ssot/ssot_control.py'
EVENTS = 'contracts/generation/document-events.schema.json'
UID = '00000000-0000-4000-8000-000000000001'
OTHER = '00000000-0000-4000-8000-000000000099'
DIGEST = 'sha256:' + 'a' * 64
TIME = '2026-09-25T00:00:00.000Z'
# Independent oracle: classification, HTTP status, retry directive, next action,
# applicability. Do not generate this expectation from the helper's CASES.
ERRORS = {
    'API_AUTHENTICATION_FAILED': ('AUTHENTICATION', 401, 'DO_NOT_RETRY', 'AUTHENTICATE', 'ALL'),
    'API_REQUEST_INVALID': ('VALIDATION', 400, 'DO_NOT_RETRY', 'CORRECT_REQUEST', 'ALL'),
    'API_OBJECT_NOT_FOUND': ('NOT_FOUND', 404, 'DO_NOT_RETRY', 'REVIEW_EXACT_TARGET', 'ALL'),
    'STATE_VERSION_CONFLICT': ('CONFLICT', 409, 'REFRESH_AND_RETRY_NEW_COMMAND', 'REVIEW_CURRENT_SNAPSHOT', 'APPROVAL'),
    'SPECIFICATION_DIGEST_STALE': ('CONFLICT', 409, 'REFRESH_AND_RETRY_NEW_COMMAND', 'REVIEW_CURRENT_SNAPSHOT', 'APPROVAL'),
    'CAPABILITY_SNAPSHOT_STALE': ('CONFLICT', 409, 'REFRESH_AND_RETRY_NEW_COMMAND', 'REVIEW_CURRENT_SNAPSHOT', 'APPROVAL'),
    'SPECIFICATION_NOT_APPROVABLE': ('VALIDATION', 422, 'DO_NOT_RETRY', 'REVIEW_PRECHECK', 'APPROVAL'),
    'IDEMPOTENCY_CONFLICT': ('CONFLICT', 409, 'DO_NOT_RETRY', 'LOOKUP_ORIGINAL_APPROVAL', 'APPROVAL'),
    'API_READ_TIMEOUT': ('TIMEOUT', 504, 'RETRY_SAME_OPERATION', 'RETRY_EXACT_READ', 'READ'),
    'API_READ_CANCELLED': ('CANCELLED', 409, 'DO_NOT_RETRY', 'NONE', 'READ'),
    'API_IMMUTABLE_DOCUMENT_INVALID': ('VALIDATION', 500, 'DO_NOT_RETRY', 'OPEN_AUDIT_DETAIL', 'READ'),
    'API_COMMIT_UNCONFIRMED': ('DEPENDENCY', 503, 'RECONCILE_THEN_RETRY', 'LOOKUP_ORIGINAL_APPROVAL', 'APPROVAL'),
    'API_STORAGE_ROLLBACK': ('DEPENDENCY', 503, 'RETRY_SAME_OPERATION', 'RETRY_ORIGINAL_REQUEST', 'ALL'),
    'PLATFORM_RECOVERY_IN_PROGRESS': ('DEPENDENCY', 503, 'RETRY_SAME_OPERATION', 'RETRY_ORIGINAL_REQUEST', 'APPROVAL'),
    'PLATFORM_RECOVERY_BLOCKED': ('MANUAL_REVIEW', 503, 'MANUAL_REVIEW', 'OPEN_AUDIT_DETAIL', 'APPROVAL'),
    'QUEUE_CAPACITY_EXHAUSTED': ('CAPACITY', 503, 'RETRY_SAME_OPERATION', 'RETRY_ORIGINAL_REQUEST', 'APPROVAL'),
    'STORAGE_CAPACITY_EXHAUSTED': ('CAPACITY', 503, 'RETRY_SAME_OPERATION', 'RETRY_ORIGINAL_REQUEST', 'ALL'),
}


def digest(value):
    """Independent canonical digest oracle for JSON fixture values."""
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf8')
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def seal(response):
    result = copy.deepcopy(response)
    result['resultDigest'] = digest({k: result[k] for k in ('status', 'output', 'error')})
    if result.get('meta') is not None:
        result['meta']['resultDigest'] = result['resultDigest']
    return result


def exercise(bundle, payload, contract, check, attempt, native, document):
    original = copy.deepcopy(payload)
    check('resource/exact-document', contract == http.document(bundle, payload))
    specialized = http.specialize(payload, bundle)
    check('specialize/current-resource-already-specialized', specialized == payload)
    check('specialize/idempotent', http.specialize(specialized, bundle) == specialized)
    check('specialize/input-unmodified', payload == original)
    unrelated = [r for r in payload['records'] if r['routeId'] not in http.ROUTES]
    check('specialize/unrelated-routes-present', bool(unrelated))
    check('specialize/unrelated-routes-unchanged', unrelated == [r for r in specialized['records'] if r['routeId'] not in http.ROUTES])
    check('errors/exact-case-set', set(http.CASES) == set(ERRORS) == set(contract['errorBindings']))
    for code, expected in ERRORS.items():
        check('errors/oracle/' + code, tuple(http.CASES[code][:5]) == expected)
    Draft202012Validator.check_schema(contract)
    make_validator = http.validators(bundle, contract, payload)
    validator_cache = {}

    def validate(schema):
        key = json.dumps(schema, sort_keys=True)
        if key not in validator_cache:
            validator_cache[key] = make_validator(schema)
        return validator_cache[key]
    rows = {r['routeId']: r for r in payload['records']}
    defs = copy.deepcopy(bundle['$defs'])
    for key, value in {'Counter': '0', 'PositiveCounter': '1', 'Timestamp': TIME,
                       'RelPath': 'fixture.json', 'JsonPointer': '', 'NonemptyJsonPointer': '/fixture'}.items():
        defs[key] = {'const': value}
    spec = witness(defs['GenerationSpecification'], defs)
    plan = witness(defs['GenerationPlan'], defs)
    plan['specificationDigest'] = plan['scopeLock']['approvedSpecificationDigest']
    approval = {'currentTurnId': UID, 'currentTurnStatus': 'COMPLETED', 'specificationRevisionId': OTHER,
                'specificationDigest': digest(spec), 'capabilitySnapshotId': UID, 'capabilitySnapshotDigest': DIGEST}
    receipt = {'jobId': UID, 'specificationRevisionId': OTHER, 'specificationDigest': digest(spec),
               'executionAuthorityId': UID, 'planningPhaseRunId': OTHER, 'jobState': 'ANALYZING'}
    snapshot = {'jobId': UID, 'jobState': 'DISCUSSING', 'stateVersion': '7', 'eventSequence': '4', **approval}
    outputs = {'route.0234': receipt, 'route.0232': spec, 'route.0237': plan}
    snapshot_validator = validate({'$ref': http.ID + '#/$defs/CurrentSnapshot'})
    check('snapshot/exact', snapshot_validator.is_valid(snapshot))
    for left, right in [('specificationRevisionId', 'specificationDigest'),
                        ('capabilitySnapshotId', 'capabilitySnapshotDigest'), ('currentTurnId', 'currentTurnStatus')]:
        check('snapshot/null-pair/' + left, snapshot_validator.is_valid({**snapshot, left: None, right: None}))
        for field in (left, right):
            check('snapshot/reject-half-null/' + field, not snapshot_validator.is_valid({**snapshot, field: None}))

    for name, raw in [('duplicate', b'{"a":1,"a":2}'), ('nested-duplicate', b'{"x":{"a":1,"a":2}}'),
                      ('nan', b'{"a":NaN}'), ('infinity', b'[Infinity]'), ('utf8', b'\xff'), ('syntax', b'{')]:
        attempt('json/reject/' + name, lambda raw=raw: http.decode_json(raw), reject=True)
    check('json/positive', http.decode_json('{"name":"Kájovo","a":[1,null]}'.encode()) == {'name': 'Kájovo', 'a': [1, None]})
    check('headers/projection', http.application_headers([('Host', 'example'), ('Authorization', 'Bearer fixture'),
          ('Content-Type', 'Application/JSON; charset=UTF-8')]) == {'authorization': 'Bearer fixture', 'content-type': 'application/json'})
    for name, pairs in [('duplicate', [('Authorization', 'Bearer x'), ('authorization', 'Bearer y')]),
                        ('unknown', [('x-authority', 'x')]), ('crlf', [('authorization', 'Bearer x\r\ny')]),
                        ('content-type', [('content-type', 'text/plain')]),
                        ('charset', [('content-type', 'application/json; charset=latin1')])]:
        attempt('headers/reject/' + name, lambda pairs=pairs: http.application_headers(pairs), reject=True)

    for rid, (operation, name) in http.ROUTES.items():
        prefix = rid + '/'
        paths = {'id': UID}
        if rid == 'route.0232':
            paths['revisionId'] = OTHER
        if rid == 'route.0237':
            paths['planId'] = plan['planId']
        headers = {'authorization': 'Bearer fixture'}
        body = None
        if rid == 'route.0234':
            headers.update({'idempotency-key': 'original-key', 'content-type': 'application/json', 'if-match': '"7"'})
            body = copy.deepcopy(approval)
        wire = {'pathParameters': paths, 'query': {}, 'headers': headers, 'body': body}
        frozen_wire = copy.deepcopy(wire)

        def normalize(value=wire, **kwargs):
            return http.normalize(rid, value, validator=validate, **{'authenticated': True, 'csrf_valid': True, **kwargs})

        command = normalize()
        check(prefix + 'normalize/native-request', validate(rows[rid]['requestSchema']).is_valid(command))
        check(prefix + 'normalize/input-unmodified', wire == frozen_wire)
        check(prefix + 'normalize/exact-digest', command['guards']['clientRequestDigest'] == digest({
            'operationId': operation, 'pathParameters': paths, 'body': body,
            'expectedStateVersion': '7' if rid == 'route.0234' else None}))
        check(prefix + 'normalize/query-and-business-body', command['query'] == [] and command['body'] == body)
        attempt(prefix + 'normalize/fresh-auth-required', lambda: normalize(authenticated=False), reject=True)
        for field in ('guards', 'executionAuthorityId', 'clientRequestDigest', 'meta', 'commit', 'logicalOperationId'):
            attempt(prefix + 'wire/server-field/' + field, lambda field=field: normalize({**wire, field: UID}), reject=True)
        attempt(prefix + 'wire/nonempty-query', lambda: normalize({**wire, 'query': {'latest': 'true'}}), reject=True)
        for key in paths:
            attempt(prefix + 'wire/path/' + key, lambda key=key: normalize({**wire, 'pathParameters': {**paths, key: 'latest'}}), reject=True)
        both = {**headers, 'cookie': '__Host-kcml-owner=session'}
        attempt(prefix + 'wire/ambiguous-auth', lambda: normalize({**wire, 'headers': both}), reject=True)
        session = {k: v for k, v in headers.items() if k != 'authorization'}
        session.update(cookie='__Host-kcml-owner=session', origin='https://kaja.hcasc.cz', **{'x-csrf-token': 'csrf'})
        check(prefix + 'session/same-business-digest', normalize({**wire, 'headers': session})['guards']['clientRequestDigest'] == command['guards']['clientRequestDigest'])
        for cookie in ('unrelated=session', '__Host-kcml-owner=', '__Host-kcml-owner=a; __Host-kcml-owner=b'):
            attempt(prefix + 'session/reject/' + cookie, lambda cookie=cookie: normalize({**wire, 'headers': {**session, 'cookie': cookie}}), reject=True)
        if rid == 'route.0234':
            attempt(prefix + 'session/csrf-invalid', lambda: normalize({**wire, 'headers': session}, csrf_valid=False), reject=True)
            for field in ('origin', 'x-csrf-token'):
                attempt(prefix + 'session/missing/' + field, lambda field=field: normalize({**wire, 'headers': {k: v for k, v in session.items() if k != field}}), reject=True)
            body_version = {**wire, 'body': {**body, 'expectedStateVersion': '7'}, 'headers': {k: v for k, v in headers.items() if k != 'if-match'}}
            check(prefix + 'cas/body-equivalent-to-header', normalize(body_version) == command)
            check(prefix + 'cas/both-agree', normalize({**wire, 'body': body_version['body']}) == command)
            attempt(prefix + 'cas/disagreement', lambda: normalize({**wire, 'body': {**body, 'expectedStateVersion': '8'}}), reject=True)
            attempt(prefix + 'cas/missing', lambda: normalize({**body_version, 'body': body}), reject=True)
            for value in ('7', '"01"', '"-1"', '"9223372036854775808"'):
                attempt(prefix + 'cas/invalid/' + value, lambda value=value: normalize({**wire, 'headers': {**headers, 'if-match': value}}), reject=True)
            for field in ('executionAuthorityId', 'planningPhaseRunId', 'jobState', 'clientRequestDigest', 'precheckAccepted', 'commit'):
                attempt(prefix + 'body/server-field/' + field, lambda field=field: normalize({**wire, 'body': {**body, field: UID}}), reject=True)
            for field in body:
                attempt(prefix + 'body/missing/' + field, lambda field=field: normalize({**wire, 'body': {k: v for k, v in body.items() if k != field}}), reject=True)
            altered = normalize({**wire, 'body': {**body, 'specificationDigest': DIGEST}})
            check(prefix + 'digest/changed-argument', altered['guards']['clientRequestDigest'] != command['guards']['clientRequestDigest'])
            check(prefix + 'digest/key-excluded', normalize({**wire, 'headers': {**headers, 'idempotency-key': 'other-key'}})['guards']['clientRequestDigest'] == command['guards']['clientRequestDigest'])
        else:
            check(prefix + 'read/no-mutation-guards', command['guards']['idempotencyKey'] is None and command['guards']['expectedStateVersion'] is None)
            attempt(prefix + 'read/body-forbidden', lambda: normalize({**wire, 'body': {}}), reject=True)
            attempt(prefix + 'read/idempotency-forbidden', lambda: normalize({**wire, 'headers': {**headers, 'idempotency-key': 'x'}}), reject=True)

        meta = witness(defs['ApiConcurrencyEnvelope'], defs)
        meta.update(correlationId=UID, logicalOperationId=UID, commandId=UID,
                    stateVersion='8', eventSequence='5', activationEpoch='2')
        success = seal({'routeId': rid, 'operationId': operation, 'logicalOperationId': UID, 'correlationId': UID,
                        'status': 'SUCCEEDED', 'terminal': True, 'output': outputs[rid], 'error': None, 'meta': meta})
        persisted = copy.deepcopy(success['meta'])

        def response(value, persisted_receipt=receipt, persisted_meta=persisted):
            return http.check_response(rid, value, validator=validate,
                                       persisted_receipt=persisted_receipt, persisted_meta=persisted_meta)

        def public(value, status):
            validate({'$ref': http.ID + '#/$defs/' + name + 'HttpResponse'}).validate({'statusCode': status, 'body': value})
            return response(value)

        attempt(prefix + 'response/native-success', lambda: public(success, 200), expected=200)
        for field in success:
            attempt(prefix + 'response/missing/' + field, lambda field=field: response({k: v for k, v in success.items() if k != field}), reject=True)
        for field, value in [('output', None), ('meta', None), ('terminal', False), ('status', 'ACCEPTED'), ('resultDigest', DIGEST)]:
            attempt(prefix + 'response/invalid/' + field, lambda field=field, value=value: response({**success, field: value}), reject=True)
        attempt(prefix + 'response/server-internals', lambda: response({**success, 'queue': {}}), reject=True)
        for field in ('correlationId', 'logicalOperationId', 'resultDigest'):
            value = DIGEST if field == 'resultDigest' else OTHER
            attempt(prefix + 'meta/mismatch/' + field, lambda field=field, value=value: response({**success, 'meta': {**success['meta'], field: value}}), reject=True)
        for field in ('stateVersion', 'eventSequence', 'activationEpoch'):
            attempt(prefix + 'meta/not-decimal-counter/' + field, lambda field=field: response({**success, 'meta': {**success['meta'], field: 8}}), reject=True)
        if rid == 'route.0234':
            attempt(prefix + 'receipt/persisted-required', lambda: response(success, persisted_receipt=None), reject=True)
            attempt(prefix + 'receipt/changed-authority', lambda: response(seal({**success, 'output': {**receipt, 'executionAuthorityId': OTHER}})), reject=True)
            for field in ('logicalOperationId', 'commandId', 'stateVersion', 'eventSequence', 'activationEpoch', 'resultDigest'):
                altered_meta = {**persisted, field: OTHER if field.endswith('Id') else DIGEST if field == 'resultDigest' else '99'}
                attempt(prefix + 'replay/frozen/' + field, lambda altered_meta=altered_meta: response(success, persisted_meta=altered_meta), reject=True)
            replay = copy.deepcopy(success)
            replay['correlationId'] = replay['meta']['correlationId'] = OTHER
            replay['meta'].update(idempotencyReplay=True, serverTime='2026-09-25T00:00:01.000Z')
            attempt(prefix + 'replay/fresh-correlation-time-frozen-outcome', lambda: public(replay, 200), expected=200)
            check(prefix + 'replay/result-digest-excludes-meta', replay['resultDigest'] == success['resultDigest'])
        else:
            attempt(prefix + 'read/generic-slot-not-document', lambda: response(seal({**success, 'output': {'schemaId': 'urn:generic', 'values': []}})), reject=True)
            check(prefix + 'read/document-and-result-digests-distinct', digest(outputs[rid]) != success['resultDigest'])
            read_args = {'validator': validate, 'native': native, 'document': document, 'path_parameters': paths,
                         'persisted_job_id': outputs[rid]['jobId'],
                         'persisted_document_id': paths.get('revisionId', paths.get('planId')),
                         'persisted_document_digest': digest(outputs[rid]), 'snapshot_meta': success['meta']}

            def read(value=success, **changes):
                return http.check_read_response(rid, value, **{**read_args, **changes})

            attempt(prefix + 'read-handoff/exact-native-content-and-snapshot', read, expected=200)
            for field, value in [('persisted_job_id', OTHER), ('persisted_document_id', UID if rid == 'route.0232' else OTHER),
                                 ('persisted_document_digest', DIGEST)]:
                attempt(prefix + 'read-handoff/reject/' + field, lambda field=field, value=value: read(**{field: value}), reject=True)
            for field in paths:
                attempt(prefix + 'read-handoff/selector/' + field,
                        lambda field=field: read(path_parameters={**paths, field: OTHER if paths[field] != OTHER else UID}), reject=True)
            attempt(prefix + 'read-handoff/consistent-meta', lambda: read(snapshot_meta={**success['meta'], 'stateVersion': '99'}), reject=True)
            replay_read = {**success, 'meta': {**success['meta'], 'idempotencyReplay': True}}
            attempt(prefix + 'read-handoff/no-idempotency-replay', lambda: read(replay_read, snapshot_meta=replay_read['meta']), reject=True)
            altered_doc = copy.deepcopy(outputs[rid])
            if rid == 'route.0232':
                altered_doc['objective']['statement'] = 'Changed immutable document'
            else:
                altered_doc['planId'] = OTHER
            changed_read = seal({**success, 'output': altered_doc})
            attempt(prefix + 'read-handoff/changed-content-despite-resealed-response',
                    lambda: read(changed_read, snapshot_meta=changed_read['meta']), reject=True)
            attempt(prefix + 'read-handoff/approval-route-forbidden',
                    lambda: http.check_read_response('route.0234', success, **read_args), reject=True)
            selector_key = 'revisionId' if rid == 'route.0232' else 'planId'
            attempt(prefix + 'read-handoff/no-latest-fallback',
                    lambda: read(path_parameters={**paths, selector_key: 'latest'}), reject=True)
            attempt(prefix + 'transport/no-missing-selector-fallback',
                    lambda: normalize({**wire, 'pathParameters': {'id': paths['id']}}), reject=True)
            for state in ('ACCEPTED', 'RUNNING', 'UNCONFIRMED'):
                attempt(prefix + 'read-handoff/no-pending-document/' + state,
                        lambda state=state: read(seal({**success, 'status': state})), reject=True)
            kind = 'generation.spec.proposed' if rid == 'route.0232' else 'generation.plan.created'
            id_key = 'specificationRevisionId' if rid == 'route.0232' else 'planId'
            digest_key = 'specificationDigest' if rid == 'route.0232' else 'planDigest'
            event_payload = {id_key: read_args['persisted_document_id'], digest_key: read_args['persisted_document_digest']}
            commit_snapshot = {'jobId': paths['id'], 'eventSequence': '1',
                               'documentId': read_args['persisted_document_id'],
                               'documentDigest': read_args['persisted_document_digest']}
            if rid == 'route.0237':
                event_payload['specificationDigest'] = plan['specificationDigest']
                commit_snapshot['approvedSpecificationDigest'] = plan['specificationDigest']
            event = {'eventId': '1', 'type': kind, 'objectId': paths['id'], 'emittedAt': TIME, 'payload': event_payload}

            def event_read(e=event, snapshot=commit_snapshot, committed=True):
                selected = native.validate_generation_document_event(document, e, outputs[rid],
                    persisted_event=e, commit_snapshot=snapshot, committed=committed)
                return read(path_parameters=selected['pathParameters'], **{k: selected[k] for k in (
                    'persisted_job_id', 'persisted_document_id', 'persisted_document_digest')})

            attempt(prefix + 'event-to-http-read/exact-selected-document', event_read, expected=200)
            attempt(prefix + 'event-to-http-read/uncommitted', lambda: event_read(committed=False), reject=True)
            attempt(prefix + 'event-to-http-read/unknown-commit', lambda: event_read(committed=None), reject=True)
            attempt(prefix + 'event-to-http-read/wrong-job', lambda: event_read(e={**event, 'objectId': OTHER}), reject=True)
            attempt(prefix + 'event-to-http-read/stale-document-digest',
                    lambda: event_read(e={**event, 'payload': {**event_payload, digest_key: DIGEST}}), reject=True)

            def delivery(e=event, **changes):
                return native.generation_event_delivery_action(document, e,
                    **{'stream_job_id': paths['id'], 'last_sequence': '0', **changes})

            attempt(prefix + 'stream/selected-job-next', delivery, expected='APPLY')
            attempt(prefix + 'stream/wrong-job-cannot-share-cursor', lambda: delivery(stream_job_id=OTHER), reject=True)
            attempt(prefix + 'stream/gap-requires-replay', lambda: delivery(e={**event, 'eventId': '3'}), expected='REPLAY_REQUIRED')
            attempt(prefix + 'stream/duplicate', lambda: delivery(last_sequence='1', previous_event_digest=digest(event)), expected='DUPLICATE')
            attempt(prefix + 'stream/changed-duplicate', lambda: delivery(last_sequence='1', previous_event_digest=DIGEST), reject=True)
            attempt(prefix + 'stream/missing-history', lambda: delivery(last_sequence='1'), expected='REPLAY_REQUIRED')
            before_stream = copy.deepcopy(event)
            attempt(prefix + 'recovery/refetch-exact-read', read, expected=200)
            check(prefix + 'recovery/http-meta-does-not-advance-event-cursor', event == before_stream and success['meta']['eventSequence'] == '5')
            attempt(prefix + 'recovery/stream-still-accepts-first-event', delivery, expected='APPLY')

        for code, (classification, status, retry, action, scope) in ERRORS.items():
            details = {'fieldPaths': ['/body'], 'reason': 'Synthetic diagnostic'}
            error = {'stableCode': code, 'classification': classification, 'retryDirective': retry, 'nextAction': action,
                     'message': 'Synthetic diagnostic', 'details': details, 'detailsDigest': digest(details),
                     'currentSnapshot': None if code == 'API_AUTHENTICATION_FAILED' else snapshot}
            failure = seal({**success, 'status': 'UNCONFIRMED' if code == 'API_COMMIT_UNCONFIRMED' else 'CANCELLED' if code == 'API_READ_CANCELLED' else 'FAILED',
                            'terminal': code != 'API_COMMIT_UNCONFIRMED', 'output': None, 'meta': None, 'error': error})
            allowed = scope in ('ALL', 'READ' if rid in http.READS else 'APPROVAL')
            attempt(prefix + 'error/' + code, lambda: public(failure, status), expected=status, reject=not allowed)
            if not allowed:
                continue
            effect = ('READ_ONLY' if rid in http.READS else 'UNKNOWN_COMMIT' if code == 'API_COMMIT_UNCONFIRMED'
                      else 'CONFIRMED_ROLLBACK' if code == 'API_STORAGE_ROLLBACK' else 'NO_DISPATCH')

            def context(value=failure, **changes):
                return http.check_error_context(rid, value, validator=validate,
                    **{'effect': effect, 'dispatched': False, 'current_snapshot': error['currentSnapshot'], **changes})

            attempt(prefix + 'context/positive/' + code, context, expected=status)
            attempt(prefix + 'context/effective-current-snapshot/' + code,
                    lambda: context(current_snapshot={**snapshot, 'stateVersion': '99'}), reject=True)
            if code == 'API_AUTHENTICATION_FAILED':
                attempt(prefix + 'authentication/no-snapshot-disclosure',
                        lambda: response(seal({**failure, 'error': {**error, 'currentSnapshot': snapshot}})), reject=True)
            if code == 'API_STORAGE_ROLLBACK':
                attempt(prefix + 'rollback/no-dispatch-is-not-confirmed-rollback',
                        lambda: context(effect='NO_DISPATCH'), reject=True)
            if rid in http.READS:
                for observation in ('NO_DISPATCH', 'CONFIRMED_ROLLBACK', 'UNKNOWN_COMMIT'):
                    attempt(prefix + 'context/read-cannot-mutate/' + code + '/' + observation,
                            lambda observation=observation: context(effect=observation), reject=True)
                attempt(prefix + 'read-handoff/failure-no-document/' + code,
                        lambda: read(failure), expected=status)
            elif code != 'API_COMMIT_UNCONFIRMED':
                attempt(prefix + 'context/unknown-cannot-be-failure/' + code,
                        lambda: context(effect='UNKNOWN_COMMIT'), reject=True)
            if code == 'PLATFORM_RECOVERY_IN_PROGRESS':
                for observation, dispatched in [('CONFIRMED_ROLLBACK', False), ('READ_ONLY', False), ('NO_DISPATCH', True)]:
                    attempt(prefix + 'context/recovery-only-no-dispatch/' + observation + '/' + str(dispatched),
                            lambda observation=observation, dispatched=dispatched: context(effect=observation, dispatched=dispatched), reject=True)
            if code == 'API_COMMIT_UNCONFIRMED':
                for observation in ('CONFIRMED_ROLLBACK', 'NO_DISPATCH', 'READ_ONLY'):
                    attempt(prefix + 'context/unknown-observation-required/' + observation,
                            lambda observation=observation: context(effect=observation), reject=True)
            if code == 'IDEMPOTENCY_CONFLICT':
                no_snapshot = seal({**failure, 'error': {**error, 'currentSnapshot': None}})
                attempt(prefix + 'context/conflict-requires-snapshot',
                        lambda: context(no_snapshot, current_snapshot=None), reject=True)
                tombstone_details = {**details, 'reason': 'RESULT_RETAINED_AS_TOMBSTONE'}
                tombstone = seal({**no_snapshot, 'error': {**no_snapshot['error'], 'details': tombstone_details,
                                                         'detailsDigest': digest(tombstone_details)}})
                attempt(prefix + 'context/tombstone-may-have-no-snapshot',
                        lambda: context(tombstone, current_snapshot=None), expected=409)
            for observation in (None, 'UNKNOWN', 1):
                attempt(prefix + 'context/exact-effect/' + code + '/' + str(observation),
                        lambda observation=observation: context(effect=observation), reject=True)
            attempt(prefix + 'context/exact-dispatch-bool/' + code, lambda: context(dispatched=1), reject=True)
            for field, value in [('classification', 'UNKNOWN'), ('retryDirective', 'MANUAL_REVIEW' if retry != 'MANUAL_REVIEW' else 'DO_NOT_RETRY'),
                                 ('nextAction', 'RETRY_NEW_KEY'), ('stableCode', 'UNKNOWN_CODE')]:
                bad = seal({**failure, 'error': {**error, field: value}})
                attempt(prefix + 'error-tuple/' + code + '/' + field, lambda bad=bad: response(bad), reject=True)
            attempt(prefix + 'http-status/' + code, lambda: public(failure, 200), reject=True)
            bad = seal({**failure, 'error': {**error, 'detailsDigest': DIGEST}})
            attempt(prefix + 'details-digest/' + code, lambda: response(bad), reject=True)
            attempt(prefix + 'failure/no-output/' + code, lambda: response(seal({**failure, 'output': outputs[rid]})), reject=True)
            attempt(prefix + 'failure/no-meta/' + code, lambda: response({**failure, 'meta': success['meta']}), reject=True)
            if code == 'API_COMMIT_UNCONFIRMED':
                for field, value in [('terminal', True), ('status', 'FAILED'), ('status', 'SUCCEEDED')]:
                    attempt(prefix + 'unknown-commit/' + field + '/' + str(value), lambda field=field, value=value: response(seal({**failure, field: value})), reject=True)
            if code in ('STATE_VERSION_CONFLICT', 'SPECIFICATION_DIGEST_STALE', 'CAPABILITY_SNAPSHOT_STALE', 'SPECIFICATION_NOT_APPROVABLE'):
                attempt(prefix + 'error/current-snapshot-required/' + code,
                        lambda: response(seal({**failure, 'error': {**error, 'currentSnapshot': None}})), reject=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline7006785', '--baseline', dest='baseline', action='store_true')
    args = parser.parse_args()
    current_raw = SSOT.read_bytes()
    raw = subprocess.check_output(['git', 'show', BASELINE + ':00_SSOT/KajovoCMLNG_SSOT.md'], cwd=ROOT) if args.baseline else current_raw
    rs = resource_index(resources(raw.decode('utf8')))
    checks = []
    rejection_types = (ValueError, ValidationError)

    def check(name, condition):
        checks.append({'case': name, 'passed': bool(condition)})

    def attempt(name, function, *, reject=False, expected=None):
        try:
            actual = function()
        except rejection_types as exc:
            checks.append({'case': name, 'passed': reject, 'rejection': type(exc).__name__ + ': ' + str(exc)[:600]})
        except Exception as exc:
            checks.append({'case': name, 'passed': False, 'unexpectedError': type(exc).__name__ + ': ' + str(exc)[:600]})
        else:
            check(name, not reject and (expected is None or actual == expected))

    required = (http.PATH, http.GEN, http.PAYLOAD, CONTROL, EVENTS)
    for path in required:
        check('resource-present/' + path, path in rs)
    if all(path in rs for path in required):
        native = types.ModuleType('generation_http_embedded_control')
        sys.modules[native.__name__] = native
        exec(compile(rs[CONTROL]['raw'], 'SSOT:ssot_control.py', 'exec'), native.__dict__)
        rejection_types += (native.ContractFailure,)
        with tempfile.TemporaryDirectory(prefix='kcml-http-native-') as directory:
            source = Path(directory) / 'SSOT.md'
            source.write_bytes(raw)
            document = native.Document(source)
            attempt('exercise-completed', lambda: exercise(*(json.loads(rs[p]['raw']) for p in (http.GEN, http.PAYLOAD, http.PATH)), check, attempt, native, document))
    report = {
        'evidenceKind': 'DESIGN_CONTRACT_TEST', 'sourceSha256': hashlib.sha256(raw).hexdigest(),
        'currentSourceSha256': hashlib.sha256(current_raw).hexdigest(), 'baseline': args.baseline, 'baselineCommit': BASELINE,
        'resourceVersions': {p: rs[p]['sha256'] if p in rs else None for p in required},
        'resourceEvidence': {p: {'sha256': rs[p]['sha256'], 'line': rs[p]['line'], 'bytes': len(rs[p]['raw'])} if p in rs else None for p in required},
        'scriptSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'helperSha256': hashlib.sha256(Path(http.__file__).read_bytes()).hexdigest(),
        'checked': len(checks), 'failed': sum(not c['passed'] for c in checks), 'checks': checks,
        'wholeRoutesClosed': [], 'productionAcceptance': False,
        'assumptions': [
            'Current local generation_http_contract.py may be tightened by main; helper hash identifies tested bytes.',
            'Independent error tuple oracle reflects the inspected HTTP materialization; changes require explicit review.',
            'Authenticated/CSRF booleans and persisted receipt/meta are trusted fixture inputs, not proven server provenance.',
            'Native fixtures use existing witness generator; schema-valid documents do not establish full semantic plan conformance.',
            'No socket, cookie verification, HTTP framing, SQL, replay locator lookup, worker dispatch or recovery runtime tested.',
            'Read response tests compose the embedded native selector/digest handoff; trusted repository facts remain synthetic.',
            'Native read handoff expects HTTP-validated selectors; missing selector rejection is tested at normalization.',
            'Approval coverage is partial: coordinator/phase/checkpoint error dispatch remains a separate design obligation.',
            'UNCONFIRMED checks establish response contract only, not enforcement of lookup-only recovery in production.',
        ],
    }
    destination = os.environ.get('KCML_AUDIT_OUTPUT')
    out = ROOT / destination if destination else Path(tempfile.mkdtemp(prefix='kcml-generation-http-'))
    out.mkdir(parents=True, exist_ok=True)
    path = out / ('generation-http-baseline7006785.json' if args.baseline else 'generation-http-current.json')
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: report[k] for k in ('sourceSha256', 'helperSha256', 'checked', 'failed', 'baseline')}))
    print(str(path))
    for row in checks:
        if not row['passed']:
            print(json.dumps(row))
    return int(bool(report['failed']))


if __name__ == '__main__':
    raise SystemExit(main())
