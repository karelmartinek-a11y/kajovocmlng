"""Audit-only technical dictionary proposal, not effective SSOT or runtime proof.
Own predicates derive from each operation overlay; no neighboring lifecycle enums.
"""
from jsonschema import Draft202012Validator

class Violation(ValueError):
    def __init__(self,code):self.code=code;super().__init__(code)

def fail(code):raise Violation(code)

def enum(values):return {'type':'string','enum':values}
MASKS={
 'owner.mfa.reset.enrollmentState':{'type':'string','const':'ENROLLMENT_REQUIRED'},
 'acceptance.run.start.state':{'type':'string','const':'QUEUED'},
 'acceptance.run.cancel.state':enum(['CANCEL_REQUESTED','RECONCILING','MANUAL_REVIEW','CANCELLED']),
 'acceptance.run.cancel.cleanupStatus':enum(['PENDING','COMPLETE','FAILED']),
 'acceptance.run.cancel.reconciliationStatus':enum(['PENDING','COMPLETE','UNKNOWN','MANUAL_REVIEW'])}

def mfa_reset_receipt(receipt,commit):
    if list(Draft202012Validator(MASKS['owner.mfa.reset.enrollmentState']).iter_errors(receipt.get('enrollmentState'))):fail('MFA_RESET_RECEIPT_STATE_INVALID')
    required=['epochIncrementedExactlyOnce','priorFactorInvalidated','priorRecoveryInvalidated','boundedChallengeCreated','freshEnrollmentRequired','auditCommitted','outboxCommitted']
    if any(commit.get(k) is not True for k in required):fail('MFA_RESET_COMMIT_INCOMPLETE')
    if commit.get('factorVerifiedAtResetCommit') is not False:fail('MFA_RESET_ALREADY_VERIFIED_CLAIM')
    return 'RESET_RECEIPT_VALID'

def start_receipt(receipt,commit):
    if list(Draft202012Validator(MASKS['acceptance.run.start.state']).iter_errors(receipt.get('state'))):fail('ACCEPTANCE_START_RECEIPT_STATE_INVALID')
    required=['exactReleaseShaPinned','testPlanProfileFrozen','runInserted','queueReserved','auditCommitted','outboxCommitted']
    if any(commit.get(k) is not True for k in required):fail('ACCEPTANCE_START_COMMIT_INCOMPLETE')
    return 'ACCEPTANCE_START_RECEIPT_VALID'

def cancellation_receipt(receipt,facts):
    for field in ['state','cleanupStatus','reconciliationStatus']:
        if list(Draft202012Validator(MASKS['acceptance.run.cancel.'+field]).iter_errors(receipt.get(field))):fail('ACCEPTANCE_CANCEL_'+field.upper()+'_INVALID')
    for k in ['cancelIntentCommitted','freshFence','exactReleaseShaPinned','auditCommitted','outboxCommitted']:
        if facts.get(k) is not True:fail('ACCEPTANCE_CANCEL_COMMIT_INCOMPLETE')
    # Inventory emptiness is observed server evidence, never an omitted list.
    for k in ['pendingCleanup','unknownEffects','pendingReconciliation','orphanCount']:
        if not isinstance(facts.get(k),int) or isinstance(facts[k],bool) or facts[k]<0:fail('ACCEPTANCE_CANCEL_INVENTORY_UNVERIFIED')
    for k in ['inventoryVerified','knownTerminalChecks']:
        if type(facts.get(k)) is not bool:fail('ACCEPTANCE_CANCEL_INVENTORY_UNVERIFIED')
    cleanup=receipt['cleanupStatus'];reconciliation=receipt['reconciliationStatus'];state=receipt['state']
    if cleanup=='COMPLETE' and (not facts['inventoryVerified'] or facts['pendingCleanup'] or facts['orphanCount'] or facts.get('cleanupFailed')):fail('ACCEPTANCE_CLEANUP_COMPLETION_FALSE')
    if cleanup=='FAILED' and facts.get('cleanupFailed') is not True:fail('ACCEPTANCE_CLEANUP_FAILURE_FALSE')
    if reconciliation=='COMPLETE' and (not facts['inventoryVerified'] or facts['unknownEffects'] or facts['pendingReconciliation']):fail('ACCEPTANCE_RECONCILIATION_COMPLETION_FALSE')
    if reconciliation=='UNKNOWN' and facts['unknownEffects']==0:fail('ACCEPTANCE_UNKNOWN_OUTCOME_FALSE')
    if reconciliation=='MANUAL_REVIEW' and facts.get('manualReviewRecorded') is not True:fail('ACCEPTANCE_MANUAL_REVIEW_UNRECORDED')
    if state=='CANCELLED' and (cleanup!='COMPLETE' or reconciliation!='COMPLETE' or not facts['knownTerminalChecks']):fail('ACCEPTANCE_CANCELLED_CLOSURE_INCOMPLETE')
    if state=='MANUAL_REVIEW' and facts.get('manualReviewRecorded') is not True:fail('ACCEPTANCE_MANUAL_REVIEW_UNRECORDED')
    if facts['unknownEffects'] and state=='CANCELLED':fail('ACCEPTANCE_CANCELLED_CLOSURE_INCOMPLETE')
    return 'ACCEPTANCE_CANCEL_RECEIPT_VALID'
