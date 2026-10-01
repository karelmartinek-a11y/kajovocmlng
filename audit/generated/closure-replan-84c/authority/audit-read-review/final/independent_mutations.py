from pathlib import Path
import sys,json,subprocess,copy,hashlib
ROOT=Path('/workspace/kajovocmlng');A=ROOT/'audit/generated/closure-replan-84c/family-read/core-audit';sys.path[:0]=[str(A),str(ROOT/'scripts')]
from core_audit_reference import SQL_PROJECTION,project_sql_values,inspect,AuditError
from ssot_sources import SSOT
source=hashlib.sha256(SSOT.read_bytes()).hexdigest()
p=subprocess.run(['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-U','agent','-d','archive_preroot_transfer_905','-At','-v','ON_ERROR_STOP=1'],input='BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;'+SQL_PROJECTION+' ORDER BY a.chain_sequence;COMMIT;',text=True,capture_output=True);assert p.returncode==0,p.stderr
rows=[project_sql_values([line])for line in p.stdout.splitlines()if line.startswith('{')];pending,success=rows
cases=[]
def reject(name,row,code):
 try:inspect(row)
 except AuditError as e:assert str(e)==code,(name,str(e),code)
 else:raise AssertionError(name+' accepted')
 cases.append({'id':name,'status':'PASS','specificDiagnostic':code,'positiveDerived':True})
def alter(row,k,v):return {**copy.deepcopy(row),k:v}
reject('pending-authoritative-actor-substitution',alter(pending,'actorId','00000000-0000-4000-8000-000000000088'),'AUDIT_PREROOT_COMMAND_BINDING_MISMATCH')
reject('pending-exact-digest-substitution',alter(pending,'retainedOutcomeDigest','sha256:'+'12'*32),'AUDIT_RETAINED_OUTCOME_DIGEST_MISMATCH')
reject('pending-stage-missing-bytes',{k:v for k,v in pending.items()if k!='retainedOutcomeBytesBase64'},'AUDIT_RECORD_MASK_INVALID')
reject('domain-stage-cannot-carry-command-outcome',{**success,'retainedOutcome':pending['retainedOutcome']},'AUDIT_RECORD_MASK_INVALID')
reject('pending-chain-zero',alter(pending,'chainSequence','0'),'AUDIT_RECORD_MASK_INVALID')
reject('domain-audit-byte-swap-from-previous-stage',alter(success,'canonicalAuditBytesBase64',pending['canonicalAuditBytesBase64']),'AUDIT_CHAIN_HASH_MISMATCH')
assert source==hashlib.sha256(SSOT.read_bytes()).hexdigest()
(Path(__file__).parent/'independent-mutation-tests.json').write_text(json.dumps({'sourceSha256':source,'checked':6,'failed':0,'cases':cases,'mode':'fresh actual read-only PG witness, Python mutation only','wholeOperationsClosed':0},indent=2)+'\n');print('Independent6 specific negative PASS')
