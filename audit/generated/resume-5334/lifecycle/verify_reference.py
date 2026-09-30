"""Exact positive-derived negatives; proof of proposed predicates only."""
import copy,json,hashlib
from pathlib import Path
from jsonschema import Draft202012Validator
from reference_contracts import MASKS,Violation,mfa_reset_receipt,start_receipt,cancellation_receipt
HERE=Path(__file__).resolve().parent
checks=[]
def run(name,fn,witness,expected=None):
    try:fn(*copy.deepcopy(witness));actual=None
    except Violation as e:actual=e.code
    checks.append({'id':name,'expectedDiagnostic':expected,'actualDiagnostic':actual,'status':'PASS' if actual==expected else 'FAIL'})

mfa=({'enrollmentState':'ENROLLMENT_REQUIRED'},{k:True for k in ['epochIncrementedExactlyOnce','priorFactorInvalidated','priorRecoveryInvalidated','boundedChallengeCreated','freshEnrollmentRequired','auditCommitted','outboxCommitted']})
mfa[1]['factorVerifiedAtResetCommit']=False
run('mfa-positive-committed-reset',mfa_reset_receipt,mfa)
for key in ['epochIncrementedExactlyOnce','priorFactorInvalidated','priorRecoveryInvalidated','boundedChallengeCreated','freshEnrollmentRequired','auditCommitted','outboxCommitted']:
    neg=copy.deepcopy(mfa);neg[1][key]=False;run('mfa-incomplete-'+key,mfa_reset_receipt,neg,'MFA_RESET_COMMIT_INCOMPLETE')
neg=copy.deepcopy(mfa);neg[1]['factorVerifiedAtResetCommit']=True;run('mfa-forged-verification',mfa_reset_receipt,neg,'MFA_RESET_ALREADY_VERIFIED_CLAIM')
start=({'state':'QUEUED'},{k:True for k in ['exactReleaseShaPinned','testPlanProfileFrozen','runInserted','queueReserved','auditCommitted','outboxCommitted']})
run('start-positive-frozen-queue-receipt',start_receipt,start)
for key in start[1]:
    neg=copy.deepcopy(start);neg[1][key]=False;run('start-incomplete-'+key,start_receipt,neg,'ACCEPTANCE_START_COMMIT_INCOMPLETE')
base={'cancelIntentCommitted':True,'freshFence':True,'exactReleaseShaPinned':True,'auditCommitted':True,'outboxCommitted':True,'pendingCleanup':0,'unknownEffects':0,'pendingReconciliation':0,'orphanCount':0,'inventoryVerified':True,'knownTerminalChecks':True,'cleanupFailed':False,'manualReviewRecorded':False}
cancel=({'state':'CANCELLED','cleanupStatus':'COMPLETE','reconciliationStatus':'COMPLETE'},base)
run('cancel-terminal-positive',cancellation_receipt,cancel)
for key,expected in [('pendingCleanup','ACCEPTANCE_CLEANUP_COMPLETION_FALSE'),('orphanCount','ACCEPTANCE_CLEANUP_COMPLETION_FALSE'),('pendingReconciliation','ACCEPTANCE_RECONCILIATION_COMPLETION_FALSE'),('unknownEffects','ACCEPTANCE_RECONCILIATION_COMPLETION_FALSE')]:
    neg=copy.deepcopy(cancel);neg[1][key]=1;run('cancel-negative-'+key,cancellation_receipt,neg,expected)
neg=copy.deepcopy(cancel);neg[1]['knownTerminalChecks']=False;run('cancel-checks-nonterminal',cancellation_receipt,neg,'ACCEPTANCE_CANCELLED_CLOSURE_INCOMPLETE')
for key in ['freshFence','exactReleaseShaPinned','cancelIntentCommitted','auditCommitted','outboxCommitted']:
    neg=copy.deepcopy(cancel);neg[1][key]=False;run('cancel-incomplete-'+key,cancellation_receipt,neg,'ACCEPTANCE_CANCEL_COMMIT_INCOMPLETE')
for key in ['pendingCleanup','unknownEffects','pendingReconciliation','orphanCount']:
    for bad in [None,-1,True,'0']:
        neg=copy.deepcopy(cancel);neg[1][key]=bad;run('cancel-invalid-inventory-'+key+'-'+repr(bad),cancellation_receipt,neg,'ACCEPTANCE_CANCEL_INVENTORY_UNVERIFIED')
for name,receipt,changes in [
 ('pending',{'state':'CANCEL_REQUESTED','cleanupStatus':'PENDING','reconciliationStatus':'PENDING'},{'pendingCleanup':1,'pendingReconciliation':1,'knownTerminalChecks':False}),
 ('unknown',{'state':'RECONCILING','cleanupStatus':'PENDING','reconciliationStatus':'UNKNOWN'},{'unknownEffects':1,'pendingCleanup':1,'knownTerminalChecks':False}),
 ('manual',{'state':'MANUAL_REVIEW','cleanupStatus':'FAILED','reconciliationStatus':'MANUAL_REVIEW'},{'manualReviewRecorded':True,'cleanupFailed':True,'pendingCleanup':1,'unknownEffects':1,'knownTerminalChecks':False})]:
    facts={**base,**changes};run('cancel-'+name+'-positive',cancellation_receipt,(receipt,facts))
    neg=copy.deepcopy((receipt,facts));neg[0]['state']='CANCELLED';run('cancel-'+name+'-cannot-terminalize',cancellation_receipt,neg,'ACCEPTANCE_CANCELLED_CLOSURE_INCOMPLETE')
for field,mask in MASKS.items():
    for bad in [None,True,1,{},[], 'UNRECOGNIZED']:
        valid=Draft202012Validator(mask).is_valid(bad);checks.append({'id':'mask-reject-'+field+'-'+repr(bad),'status':'FAIL' if valid else 'PASS'})
result={'status':'PASS' if all(r['status']=='PASS' for r in checks) else 'FAIL','checkCount':len(checks),'failed':sum(c['status']!='PASS' for c in checks),'coverage':'PROPOSED_TECHNICAL_RECEIPT_DICTIONARIES_REFERENCE_ONLY','effectiveSsotClosure':'NOT_VERIFIED_PENDING_NORMATIVE_INTEGRATION','implementationProductionAcceptance':'NOT_EVALUATED','sourceBindings':json.loads((HERE/'source-bindings.json').read_text()),'modelSha256':hashlib.sha256((HERE/'reference_contracts.py').read_bytes()).hexdigest(),'checks':checks}
(HERE/'reference-tests.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','checkCount','failed','coverage']}))
raise SystemExit(bool(result['failed']))
