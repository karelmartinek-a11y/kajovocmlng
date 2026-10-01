"""Validate native server boundaries; fixtures are synthetic, not runtime evidence."""
import copy
import hashlib
import json
import os
import sys

from close_generation_operation_masks import OPERATIONS, PATH, GEN, CATALOG, SAGA, expected
from close_mcp_list_operation_masks import NATIVE, definitions as mcp_list_definitions
from phase1_schema_closure import Inventory
from ssot_sources import ROOT, SSOT
from verify_phase2_handoffs import witness


def main():
    inv = Inventory(SSOT.read_text(encoding='utf8'))
    bundle = inv.docs[GEN]
    fixture_defs = copy.deepcopy(bundle['$defs'])
    for key, value in {'Counter': '0', 'PositiveCounter': '1',
                       'Timestamp': '2026-09-25T00:00:00.000Z', 'RelPath': 'fixture.json',
                       'JsonPointer': '', 'NonemptyJsonPointer': '/fixture'}.items():
        fixture_defs[key] = {'const': value}
    checks, fixtures = [], {}

    def record(name, actual, expected_value=True):
        checks.append({'case': name, 'expected': expected_value, 'actual': actual,
                       'passed': actual == expected_value})

    validators = {}

    def valid(identity, sample):
        if identity not in validators:
            validators[identity] = inv.validator(identity)
        return validators[identity].is_valid(sample)

    expected_masks = expected(inv.rs)
    if NATIVE in inv.rs:
        expected_masks.update(mcp_list_definitions(json.loads(inv.rs[NATIVE]['raw'])))
    # Six native OWNER definitions are derived from their published source
    # contract, not accepted by reading the actual operation registry back.
    if 'contracts/owner-session-family.json' in inv.rs:
        from owner_session_family_contracts import contracts as owner_contracts
        for operation in owner_contracts(inv.rs)['operations']:
            oid = operation['operationId']
            for role, field in [('command', 'requestSchema'), ('response', 'responseSchema'), ('event', 'eventSchema')]:
                mask = copy.deepcopy(operation[field])
                mask['$id'] = 'urn:kcml:r9:operation:' + oid + ':' + role
                expected_masks[oid + ':' + role] = mask
    # Four reviewed native MCP read aliases have an exact pinned package; its
    # authoring validation still checks native and operation identities.
    package_path = ROOT / 'audit/generated/closure-replan-84c/references/native-read-reference-patch.json'
    if package_path.exists():
        import importlib.util
        author_path = package_path.with_name('author_native_read_refs.py')
        spec = importlib.util.spec_from_file_location('reviewed_mcp_read_alias_author', author_path)
        author = importlib.util.module_from_spec(spec); spec.loader.exec_module(author)
        package = json.loads(package_path.read_text())
        author.updates(SSOT.read_text(), package)
        identities = {operation + ':' + role for operation in ('mcp.prompts.get', 'mcp.resources.read') for role in ('command', 'response')}
        aliases = {item['path'].split('/', 2)[2]: item['value'] for item in package['jsonPatch']}
        assert aliases.keys() == identities, 'EXACT_FOUR_REVIEWED_MCP_ALIASES_REQUIRED'
        expected_masks.update(aliases)
    record('exact-source-derived-variant-set', inv.docs[PATH].get('$defs') == expected_masks)
    extra=copy.deepcopy(inv.docs[PATH]['$defs']);extra['unexpected.variant']={'type':'object'}
    record('unexpected-definition-still-rejected',extra==expected_masks,False)
    missing=copy.deepcopy(inv.docs[PATH]['$defs']);missing.pop(next(iter(expected_masks)))
    record('missing-definition-still-rejected',missing==expected_masks,False)
    if inv.docs[PATH].get('$defs') != expected_masks:
        actual_masks = inv.docs[PATH].get('$defs', {})
        actual_keys = set(actual_masks) if isinstance(actual_masks, dict) else set()
        diagnostics = {'code': 'OPERATION_SCHEMA_REGISTRY_MISMATCH',
                       'missingDefinitions': sorted(set(expected_masks) - actual_keys),
                       'unexpectedDefinitions': sorted(actual_keys - set(expected_masks)),
                       'mismatchedDefinitions': sorted(key for key in actual_keys & set(expected_masks)
                                                       if actual_masks[key] != expected_masks[key])}
        # Fail on the specific registry boundary before fixture dispatch can
        # raise an unrelated unresolved-reference exception. No later fixture
        # is reported executed on this invalid source.
        report = {'sourceSha256': hashlib.sha256(SSOT.read_bytes()).hexdigest(),
                  'status': 'BLOCKED', 'diagnostics': [diagnostics],
                  'checks': checks, 'checked': len(checks),
                  'failed': sum(not c['passed'] for c in checks),
                  'scope': __doc__, 'fixturesExecuted': False,
                  'remaining': ['Restore the exact source-derived schema registry before running native fixture dispatch.'],
                  'wholeOperationsClosed': 0, 'implementationAcceptance': 'NOT_EVALUATED'}
        directory = ROOT / os.environ.get('KCML_AUDIT_OUTPUT', 'audit/generated')
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'generation-operation-mask-tests.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        print(json.dumps({'status': 'BLOCKED', 'checked': report['checked'],
                          'failed': report['failed'], 'diagnostics': [diagnostics]}))
        return 1
    for row in inv.docs[CATALOG]:
        operation, kind = row['canonicalOperationId'], row['kind']
        if operation not in OPERATIONS:
            continue
        command = 'urn:kcml:r9:operation:' + operation + ':command'
        response = 'urn:kcml:r9:operation:' + operation + ':response'
        native_input = bundle['$id'] + '#/$defs/' + row['inputDefinition']
        request = witness(fixture_defs[row['inputDefinition']], fixture_defs)
        outputs = []
        for branch in fixture_defs[row['outputDefinition']]['oneOf']:
            shape = copy.deepcopy(branch)
            shape.pop('allOf', None)  # Fixture generation only; validator uses full native schema.
            outputs.append(witness(shape, fixture_defs))
        success, failure = outputs
        fixtures[kind] = {'request': request, 'success': success, 'failure': failure}
        record(kind + '/native-input', valid(native_input, request))
        record(kind + '/operation-input', valid(command, request))
        record(kind + '/success-receipt', valid(response, success))
        record(kind + '/failure-receipt', valid(response, failure))
        record(kind + '/input-is-not-server-output', valid(response, request), False)
        record(kind + '/output-is-not-input', valid(command, success), False)
        record(kind + '/generic-slot', valid(command, {'schemaId': command, 'values': []}), False)
        for field in request:
            bad = copy.deepcopy(request)
            del bad[field]
            record(kind + '/missing/' + field, valid(command, bad), False)
            bad = copy.deepcopy(request)
            bad[field] = None
            record(kind + '/null/' + field, valid(command, bad), False)
        for slot in request['inputs']:
            bad = copy.deepcopy(request)
            bad['inputs'][slot]['kind'] = 'NOT_THE_REQUIRED_ARTIFACT'
            record(kind + '/wrong-kind/' + slot, valid(command, bad), False)
        bad = copy.deepcopy(request); bad['kind'] = 'BUILD' if kind != 'BUILD' else 'ACTIVATE'
        record(kind + '/wrong-dispatch-variant', valid(command, bad), False)
        bad = copy.deepcopy(success); bad['effectOutcome'] = 'UNKNOWN'
        record(kind + '/unknown-effect-is-not-success', valid(response, bad), False)
        bad = copy.deepcopy(success); bad['checks'][0]['verdict'] = 'FAIL'
        record(kind + '/failed-check-is-not-success', valid(response, bad), False)
        bad = copy.deepcopy(failure); del bad['recoveryCheckpoint']
        record(kind + '/missing-recovery', valid(response, bad), False)
        bad = copy.deepcopy(failure); bad['status'] = 'SUCCEEDED'
        record(kind + '/failure-is-not-success', valid(response, bad), False)
        bad = copy.deepcopy(success); bad['commit'] = None
        record(kind + '/missing-server-commit', valid(response, bad), False)
    saga_rows = []
    for step in inv.docs[SAGA]:
        operation = step['operationId']
        if operation not in OPERATIONS:
            continue
        command = 'urn:kcml:r9:operation:' + operation + ':command'
        response = 'urn:kcml:r9:operation:' + operation + ':response'
        wrong_step = 'S04' if operation == 'generation.candidate.publish' else 'S03'
        sid = step['stepId']
        request = witness(fixture_defs['IntegrationStepInput'], fixture_defs)
        request['stepId'] = sid
        record(sid + '/saga-input', valid(command, request))
        bad = copy.deepcopy(request); bad['kind'] = 'RUNTIME_PROVISION'
        record(sid + '/ambiguous-node-and-saga-dispatch', valid(command, bad), False)
        bad = copy.deepcopy(request); bad['stepId'] = wrong_step
        record(sid + '/wrong-operation-step', valid(command, bad), False)
        receipts = []
        for branch in fixture_defs['IntegrationStepReceipt']['oneOf']:
            receipt = witness(branch, fixture_defs)
            receipt['stepId'] = sid
            if receipt['state'] == 'SUCCEEDED':
                receipt['result']['kind'] = step['outputKind']
                bad = copy.deepcopy(receipt); bad['result']['kind'] = 'WRONG_OUTPUT'
                record(sid + '/wrong-output-kind', valid(response, bad), False)
                bad = copy.deepcopy(receipt); bad['effectOutcome'] = 'UNKNOWN'
                record(sid + '/unknown-not-success', valid(response, bad), False)
            if receipt['state'] == 'MANUAL_REVIEW':
                receipt['effectOutcome'] = 'UNKNOWN'
                receipt['problem']['retryDirective'] = 'MANUAL_REVIEW'
            record(sid + '/' + receipt['state'], valid(response, receipt))
            bad = copy.deepcopy(receipt); bad['stepId'] = wrong_step
            record(sid + '/receipt-wrong-operation/' + receipt['state'], valid(response, bad), False)
            receipts.append(receipt)
        fixtures[sid] = {'request': request, 'receipts': receipts}
        saga_rows.append({**step, 'input': 'IntegrationStepInput', 'output': 'IntegrationStepReceipt',
                          'compatibility': 'NATIVE_SCHEMA_AND_STEP_OUTPUT_KIND_CHECKED',
                          'runtimeEvidence': 'NOT_RUN',
                          'remaining': 'Hydrate predecessor receipts and prove current snapshot, commit, '
                                       'cancellation and recovery guards against DB facts.'})
    # Absence of an identity must fail independently of instance validity.
    record('missing-schema', inv.boundary('request', 'urn:kcml:missing', 'test')['resolution'], 'UNRESOLVED')
    report = {'sourceSha256': hashlib.sha256(SSOT.read_bytes()).hexdigest(),
              'resourceSha256': {p: inv.rs[p]['sha256'] for p in (PATH, GEN, CATALOG, SAGA, 'contracts/owner-session-family.json', NATIVE) if p in inv.rs},
              'reviewedAliasPackageSha256': hashlib.sha256(package_path.read_bytes()).hexdigest() if package_path.exists() else None,
              'scope': __doc__, 'checks': checks, 'fixtures': fixtures,
              'checked': len(checks), 'failed': sum(not c['passed'] for c in checks),
              'sagaBoundaries': saga_rows,
              'remaining': ['Artifact hydration, current DB guards, producer-consumer content lineage, '
                            'runtime cancellation/retry/recovery are not proven by these shape tests.']}
    directory = ROOT / os.environ.get('KCML_AUDIT_OUTPUT', 'audit/generated')
    directory.mkdir(parents=True, exist_ok=True)
    out = directory / 'generation-operation-mask-tests.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: report[k] for k in ('sourceSha256', 'checked', 'failed')}))
    for check in checks:
        if not check['passed']:
            print(json.dumps(check))
    return int(bool(report['failed']))


if __name__ == '__main__':
    sys.exit(main())
