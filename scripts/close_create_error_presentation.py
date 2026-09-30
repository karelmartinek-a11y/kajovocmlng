"""Author exact CREATE_*/FOLLOW_UP_* presentation/predicates; preserve legacy rows.

Only the coordinator runs authoring. --check verifies idempotence without writes.
The new predicate rows are design definitions, never current test/runtime receipts.
"""
import argparse
import copy
import hashlib
import json
from jsonschema import Draft202012Validator
from author_resource_updates import rewrite
from ssot_sources import ROOT, SSOT, resources, resource_index

PRESENTATION = 'ui/contracts/error-presentation.json'
COMPLETION = 'contracts/create-completion.json'
REGISTRY = '01_UI_CONTRACT/ui/contracts/error-message-registry.json'
TEXT = {
 'CREATE_CANCELLED': (
    'Vytvoření bylo zrušeno před uložením. Nový objekt nebyl vytvořen.',
    'Creation was cancelled before commit. No new object was created.',
    'Cancelled creation is terminal; submit a new intent only when desired.'),
 'CREATE_INPUT_INVALID': (
    'Vstup pro vytvoření není platný. Opravte uvedená chybná pole nebo formát požadavku.',
    'The creation input is invalid. Correct the reported fields or request encoding.',
    'Correct the rejected input; do not automatically repeat the unchanged request.'),
 'CREATE_AUTHENTICATION_REQUIRED': (
    'Vytvoření vyžaduje platné přihlášení vlastníka. Přihlaste se a ověřte aktuální požadavek.',
    'Creation requires a current authenticated owner session. Sign in and review the current request.',
    'Resolve OWNER authentication; refresh current guards before submitting.'),
 'CREATE_REFERENCE_INVALID': (
    'Odkazovaný podklad nebo objekt nelze ověřit. Zkontrolujte jeho identitu, dostupnost a obsah.',
    'A referenced source or object could not be verified. Check its identity, availability and content.',
    'Resolve the exact failed reference guard; do not trust client-declared identity or digests.'),
 'CREATE_POLICY_UNRESOLVED': (
    'Vytvoření je blokováno nevyřešeným povinným pravidlem. Otevřete podrobnosti chybějícího kontraktu.',
    'Creation is blocked by an unresolved mandatory policy. Open the missing-contract details.',
    'Resolve the indicated authoritative type, credential or parent/target admission policy before dispatch.'),
 'CREATE_RECOVERY_BARRIER': (
    'Obnova platformy ještě není dokončena. Vytvoření může pokračovat až po ověřeném návratu do připraveného stavu.',
    'Platform recovery has not completed. Creation can proceed only after a verified return to the ready state.',
    'Resolve the recovery barrier and refresh current authority; do not bypass recovery.'),
 'CREATE_STABLE_NAME_CONFLICT': (
    'Tento stabilní název tajemství již existuje, včetně případného smazaného záznamu. Zvolte dostupný název.',
    'This secret stable name already exists, including a possible deleted record. Choose an available name.',
    'Choose an available stableName; a soft-deleted name remains reserved by the existing uniqueness contract.'),
 'CREATE_PERSISTENCE_FAILED': (
    'Vytvoření se neuložilo; je ověřeno úplné vrácení transakce. Opakování musí zachovat původní operaci a platná pravidla.',
    'Creation was not committed; full transaction rollback is verified. A retry must preserve the original operation and valid policy.',
    'Canonical same-operation retry is permitted only with positive full-rollback evidence, pinned input and current authority; the bounded default profile never grants permission.'),
}


# Each wording names the exact rejected guard; source state terminality alone is
# never a rejection, and these codes are generation-only.
FOLLOW_UP_REASON = {
 'ATOMIC_ADMISSION_UNVERIFIED': ('Atomický snímek pro přijetí není ověřen.', 'The atomic admission snapshot is unverified.', 'server.atomicGenerationAdmission is not true'),
 'BASIS_BYTES_DIGEST_MISMATCH': ('Skutečné bajty podkladu neodpovídají uloženému digestu.', 'The actual basis bytes do not match the stored digest.', 'SHA256(actual source bytes) differs from persisted contentDigest'),
 'BASIS_BYTES_UNAVAILABLE': ('Skutečné bajty podkladu nejsou dostupné.', 'The actual basis bytes are unavailable.', 'source.bytes is not available as bytes'),
 'BASIS_DIGEST_CONFLICT': ('Očekávaný digest podkladu neodpovídá jeho ověřenému obsahu.', 'The expected basis digest differs from its verified content.', 'caller expectedDigest differs from SHA256(actual persisted source bytes)'),
 'BASIS_IDENTITY_MISMATCH': ('Podklad nepatří k vybranému zdrojovému úkolu nebo variantě.', 'The basis does not belong to the selected source job or variant.', 'persisted jobId/basisKind/revisionId/artifactId differs from the caller selector'),
 'BASIS_INCONSISTENT': ('Podklad není potvrzen jako konzistentní.', 'The basis is not confirmed consistent.', 'source.consistent is not true'),
 'BASIS_INSUFFICIENT': ('Podklad není potvrzen jako dostatečný pro navazující práci.', 'The basis is not confirmed sufficient for follow-up work.', 'source.sufficient is not true'),
 'BASIS_INVALID': ('Volba podkladu neodpovídá přesné vstupní variantě.', 'The basis selector does not match an exact input variant.', 'followUpBasis fails the exact request_schema variant'),
 'BASIS_NOT_IMMUTABLE': ('Podklad není neměnným uloženým snímkem.', 'The basis is not an immutable persisted snapshot.', 'source.immutable is not true'),
 'BASIS_UNAVAILABLE': ('Vybraný uložený podklad není dostupný.', 'The selected persisted basis is unavailable.', 'selected source snapshot is absent or source.available is not true'),
 'FINAL_OUTPUT_UNPUBLISHED': ('Vybraný finální výstup není potvrzen jako publikovaný.', 'The selected final output is not confirmed published.', 'PUBLISHED_FINAL_OUTPUT source.publishedFinal is not true'),
 'FROZEN_DESCRIPTOR_INVALID': ('Uložený popis zmrazeného podkladu nemá platný formát.', 'The persisted frozen-basis descriptor has an invalid format.', 'hydrated descriptor fails frozen_basis_schema'),
 'FROZEN_IDENTITY_MISMATCH': ('Identita uloženého podkladu neodpovídá zmrazenému popisu.', 'The persisted basis identity differs from the frozen descriptor.', 'selected persisted snapshot identities differ from descriptor sourceJobId/basisKind/contentDigest/revisionId/artifactId/publicationReceiptId'),
 'FROZEN_LINEAGE_DIGEST_MISMATCH': ('Digest neměnné návaznosti podkladu neodpovídá jeho popisu.', 'The immutable basis lineage digest does not match its descriptor.', 'descriptor.lineageDigest differs from SHA256(canonical descriptor excluding lineageDigest)'),
 'FROZEN_SNAPSHOT_UNAVAILABLE': ('Zmrazený snímek podkladu nelze jednoznačně načíst.', 'The frozen basis snapshot cannot be uniquely loaded.', 'snapshotId resolves to other than exactly one retained source snapshot'),
 'KIND_REQUIRED': ('Tato předávka vyžaduje variantu FOLLOW_UP.', 'This handoff requires the FOLLOW_UP variant.', 'request.kind is not FOLLOW_UP'),
 'PARENT_REQUIRED': ('Chybí platná identita zdrojového úkolu.', 'A valid source job identity is required.', 'parentJobId is absent or not a UUID'),
 'PUBLICATION_RECEIPT_MISMATCH': ('Publikační potvrzení neodpovídá vybranému výstupu a jeho obsahu.', 'The publication receipt differs from the selected output and its content.', 'committed receipt identity/job/artifact/contentDigest differs from selected persisted output'),
 'PUBLICATION_RECEIPT_UNVERIFIED': ('Publikační potvrzení není ověřeno jako uložené a dokončené.', 'The publication receipt is not verified as persisted and committed.', 'publicationReceiptId is invalid, receipt missing or outcome is not COMMITTED'),
 'SNAPSHOT_IDENTITY_INVALID': ('Uložený podklad nemá platnou identitu snímku.', 'The persisted basis lacks a valid snapshot identity.', 'source.snapshotId is not a UUID'),
 'SOURCE_OWNER_MISMATCH': ('Zdrojový úkol nebo podklad nepatří ověřenému vlastníkovi.', 'The source job or basis does not belong to the authenticated owner.', 'server-owned source/parent owner differs from current authenticated OWNER'),
 'SOURCE_STATE_INVALID': ('Zdrojový úkol nemá stav z vlastního platného lifecycle.', 'The source job state is outside its own valid lifecycle.', 'parent.state is not in follow_up_contracts.STATES; completed/failed/cancelled states themselves are allowed'),
}
for suffix, (cs, en, guard) in FOLLOW_UP_REASON.items():
    TEXT['FOLLOW_UP_' + suffix] = ('Navazující generování: ' + cs, 'Follow-up generation: ' + en,
        'Resolve this exact guard before admission/hydration: ' + guard + '. Preserve the immutable source; never retry blindly or infer execution authority from client selectors.')


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf8')


def prepare(text, registry_raw):
    items = list(resources(text))
    rs = resource_index(items)
    completion = json.loads(rs[COMPLETION]['raw'])
    presentation = json.loads(rs[PRESENTATION]['raw'])
    schema = json.loads(rs['ui/contracts/error-presentation.schema.json']['raw'])
    registry = json.loads(registry_raw)
    record_schema = json.loads((ROOT/'01_UI_CONTRACT/ui/contracts/error-record.schema.json').read_bytes())
    predicates = {r['stableCode']: (i, r) for i, r in enumerate(completion['errorPredicates']) if r['stableCode'].startswith(('CREATE_', 'FOLLOW_UP_'))}
    if set(predicates) != set(TEXT):
        raise ValueError('CREATE_ERROR_PRESENTATION_SOURCE_SET_CHANGED')
    source_codes = {c for index in range(107, 117) for c in json.loads(rs['contracts/generation/generation-contracts.schema.json']['raw'])['$defs']['SourceEnum' + str(index)]['enum']}
    if not set(TEXT) <= source_codes:
        raise ValueError('CREATE_ERROR_CODES_NOT_IN_EFFECTIVE_SOURCE_ENUMS')
    originals = [copy.deepcopy(row) for row in presentation['entries'] if row['error_code'] not in TEXT]
    prior_registry = [copy.deepcopy(row) for row in registry['records'] if row['error_code'] not in TEXT]
    no_retry = {'mode': 'DO_NOT_RETRY', 'maxAttempts': 0, 'delayMs': 0,
        'stop': 'This canonical create predicate prohibits automatic retry.',
        'sideEffects': 'No blind retry. Preserve canonical locator and inspect the exact persisted outcome before any further decision.'}
    canonical_retry = copy.deepcopy(next(r['automatic_retry_policy'] for r in originals
        if r['automatic_retry_policy']['mode'] == 'CANONICAL_OPERATION_POLICY_ONLY'))
    new_presentations = []
    new_predicates = []
    for code in sorted(TEXT):
        index, predicate = predicates[code]
        cs, en, recovery = TEXT[code]
        pointer = COMPLETION + '#/errorPredicates/' + str(index)
        is_follow_up = code.startswith('FOLLOW_UP_')
        if is_follow_up and predicate['operationIds'] != ['generation.job.create']:
            raise ValueError('FOLLOW_UP_ERROR_OPERATION_SCOPE_MISMATCH:' + code)
        exact_condition = predicate['predicate']
        if is_follow_up:
            exact_condition += '; exact guard: ' + FOLLOW_UP_REASON[code[len('FOLLOW_UP_'):]][2]
        source_section = '12.49' if is_follow_up else '12.48'
        retry = copy.deepcopy(canonical_retry if predicate['retryDirective'] == 'RETRY_SAME_OPERATION' else no_retry)
        if predicate['retryDirective'] == 'RETRY_SAME_OPERATION':
            retry['authoritySections'] = list(dict.fromkeys(retry.get('authoritySections', []) + predicate['sources']))
            retry['missingPolicy'] = recovery
        row = {'error_code': code, 'source': 'FOLLOW_UP' if is_follow_up else 'CREATE', 'category': predicate['classification'].lower(),
            'severity': 'WARNING' if code == 'CREATE_CANCELLED' else 'ERROR',
            'operator_detail': exact_condition + '; operations: ' + ', '.join(predicate['operationIds']) +
                '. Inspect server-authored correlation, failed guard and canonical persistence evidence; a design test is not a runtime receipt.',
            'recoverability': recovery, 'manual_recovery': recovery,
            'logging_requirements': 'Structured condition, canonical code, operation identity and correlation/evidence digests per SSOT19/32; preserve existing Secrets/trusted-perimeter rules.',
            'user_message_cs': cs, 'user_message_en': en, 'messageKey': 'error.' + code.lower(),
            'technical_condition': {'match': 'CANONICAL_STABLE_CODE_EQUALS', 'value': code, 'authorityRef': pointer},
            'correlation_requirements': ['operationId', 'requestId', 'correlationId', 'logicalOperationId or explicit null before admission', 'evidenceRef'],
            'automatic_retry_policy': retry}
        new_presentations.append(row)
        new_predicates.append({'error_code': code, 'source': 'follow-up' if is_follow_up else 'create', 'category': predicate['classification'].lower(),
            'severity': 'warning' if code == 'CREATE_CANCELLED' else 'error',
            'technical_condition': {'sourceRecord': code, 'sourceSection': source_section, 'sourceRef': pointer,
                'condition': exact_condition, 'predicateStatus': 'EXPLICIT',
                'operationIds': predicate['operationIds'], 'httpStatus': predicate['httpStatus'],
                'producerHelperRef': 'scripts/follow_up_contracts.py#admit_follow_up-and-hydrate_frozen_basis' if is_follow_up else 'scripts/create_completion_contracts.py#http_failure',
                'canonicalRetryDirective': predicate['retryDirective'],
                'definitionScope': 'Only generation.job.create and/or secret.create as explicitly listed; no global closure of legacy codes.',
                'verificationRequired': ('scripts/verify_follow_up_contracts.py plus ' if is_follow_up else '') + 'scripts/verify_create_http_errors.py current source/helper/environment-bound design proof; runtime NOT_EVALUATED'},
            'user_message_cs': cs, 'user_message_en': en,
            'operator_detail': {'stableCondition': code, 'predicateRef': pointer,
                'required': ['operationId', 'requestId', 'correlationId', 'canonicalOutcome', 'failedGuardOrRollbackEvidence'],
                'designPredicateSha256': hashlib.sha256(encoded(predicate)).hexdigest()},
            'recoverability': recovery, 'automatic_retry_policy': copy.deepcopy(retry),
            'manual_recovery': {'action': recovery, 'sameCommandMayRepeat': predicate['retryDirective'] == 'RETRY_SAME_OPERATION',
                'guard': 'Only canonical same-locator/input policy with positive rollback evidence and current authority; unknown outcome requires reconciliation.'},
            'correlation_requirements': copy.deepcopy(row['correlation_requirements']),
            'logging_requirements': ['exact producer predicate and canonical code', 'operation and request correlation',
                'failed guard or canonical persistence evidence', 'existing Secrets/trusted-perimeter logging policy']})
    presentation['entries'] = originals + new_presentations
    registry['records'] = prior_registry + new_predicates
    registry['recordCount'] = len(registry['records'])
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(presentation)
    v = Draft202012Validator(record_schema)
    for row in new_predicates:
        v.validate(row)
    if {r['error_code'] for r in presentation['entries']} != source_codes:
        raise ValueError('ERROR_PRESENTATION_EXACT_SOURCE_COVERAGE_MISMATCH')
    if len({r['error_code'] for r in presentation['entries']}) != len(presentation['entries']):
        raise ValueError('DUPLICATE_ERROR_PRESENTATION_CODE')
    if len({r['error_code'] for r in registry['records']}) != len(registry['records']):
        raise ValueError('DUPLICATE_ERROR_REGISTRY_CODE')
    updates = {PRESENTATION: encoded(presentation)}
    return items, updates, encoded(registry), {
        'sourceDocumentSha256': hashlib.sha256(text.encode('utf8')).hexdigest(),
        'completionResourceSha256': rs[COMPLETION]['sha256'],
        'managedCodes': sorted(TEXT), 'createCodeCount': sum(code.startswith('CREATE_') for code in TEXT),
        'followUpCodeCount': sum(code.startswith('FOLLOW_UP_') for code in TEXT),
        'legacyPresentationRowsPreserved': len(originals),
        'legacyRegistryRowsPreserved': len(prior_registry),
        'explicitNewPredicates': len(new_predicates),
        'existingPendingPredicateRowsUnchanged': sum(r['technical_condition']['predicateStatus'] != 'EXPLICIT' or bool(r.get('presentationCompleteness')) for r in prior_registry),
        'runtimeAcceptance': 'NOT_EVALUATED'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--preview-module', action='store_true', help='Preview prospective current authoring module in memory; requires --preview')
    parser.add_argument('--preview', type=str, help='Write only a diagnostic summary to this path, without authoring')
    args = parser.parse_args()
    text = SSOT.read_text(encoding='utf8')
    registry_path = ROOT/REGISTRY
    registry_raw = registry_path.read_bytes()
    if args.preview_module:
        if not args.preview:
            raise ValueError('PREVIEW_MODULE_REQUIRES_PREVIEW_NO_AUTHORING')
        from create_completion_contracts import contract
        prospective_items = list(resources(text))
        prospective_rs = resource_index(prospective_items)
        generation = json.loads(prospective_rs['contracts/generation/generation-contracts.schema.json']['raw'])
        generation['$defs']['SourceEnum110']['enum'] = list(dict.fromkeys(generation['$defs']['SourceEnum110']['enum'] + sorted(TEXT)))
        text = rewrite(text, prospective_items, {COMPLETION: encoded(contract()),
            'contracts/generation/generation-contracts.schema.json': encoded(generation)})
    items, updates, new_registry, summary = prepare(text, registry_raw)
    new_text = rewrite(text, items, updates)
    if args.preview:
        preview = ROOT/args.preview
        preview.parent.mkdir(parents=True, exist_ok=True)
        preview.write_bytes(encoded(summary))
    elif args.check:
        if new_text != text or new_registry != registry_raw:
            raise ValueError('CREATE_ERROR_PRESENTATION_NOT_AUTHORED')
    else:
        if SSOT.read_text(encoding='utf8') != text or registry_path.read_bytes() != registry_raw:
            raise ValueError('CREATE_ERROR_INPUT_CHANGED')
        SSOT.write_text(new_text, encoding='utf8', newline='\n')
        registry_path.write_bytes(new_registry)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
