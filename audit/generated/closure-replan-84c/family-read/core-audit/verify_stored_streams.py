"""Actual preserved canonical pre-root→success fixture; strictly read-only.

Does not reset or mutate the peer fixture database. Derived byte mutations use
its valid persisted row as the baseline and remain Python-only.
"""
import sys,json,copy,hashlib,base64,subprocess
from pathlib import Path
from core_audit_reference import *
ROOT=Path('/workspace/kajovocmlng');sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
from generation_auth_crypto import canonical
cases=[]
def ok(id):cases.append({'id':id,'status':'PASS'})
def bad(id,fn,code):
 try:fn()
 except AuditError as e:assert str(e)==code,(id,str(e),code)
 else:raise AssertionError(id+' accepted')
 cases.append({'id':id,'status':'PASS','specificDiagnostic':code,'positiveDerived':True})
PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-U','agent','-d','archive_preroot_transfer_905','-At','-v','ON_ERROR_STOP=1']
query='BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;SHOW server_version;SELECT count(*) FROM audit_event;'+SQL_PROJECTION+' ORDER BY a.chain_sequence; SELECT state FROM domain_command; COMMIT;'
p=subprocess.run(PSQL,input=query,text=True,capture_output=True);assert p.returncode==0,p.stderr
lines=p.stdout.splitlines();assert '18.6' in lines and '2' in lines and 'SUCCEEDED' in lines
rows=[project_sql_values([line])for line in lines if line.startswith('{')];assert len(rows)==2
pending,success=rows;assert pending['recordKind']=='GENERATION_PREROOT_OUTCOME_AUDIT' and success['recordKind']=='DOMAIN_EVENT_AUDIT';ok('actual-PG18.6-global-projection-both-audits-no-inner-join-omission')
assert pending['domainEventId'] is None and 'aggregateId' not in pending and 'eventPayloadBytesBase64'not in pending;ok('actual-pre-root-row-no-fabricated-aggregate-event')
assert pending['retainedOutcome']['status']=='ACCEPTED' and pending['retainedOutcome']['terminal']is False;ok('historical-ACCEPTED-outcome-after-command-SUCCEEDED-not-overwritten')
assert pending['logicalOperationId']==success['logicalOperationId'] and pending['auditId']!=success['auditId'];ok('same-command-two-immutable-stream-rows')
assert inspect(pending)['verifiedRetainedOutcomeBytes']==raw(pending['retainedOutcomeBytesBase64']);ok('actual-original-retained-outcome-bytes-preserved')
assert inspect(success)['verifiedEventPayloadBytes']==raw(success['eventPayloadBytesBase64']);ok('actual-original-domain-event-bytes-preserved')

def changed(field,value):return {**copy.deepcopy(pending),field:value}
bad('wrong-stream-discriminator',lambda:inspect(changed('recordKind','DOMAIN_EVENT_AUDIT')),'AUDIT_RECORD_MASK_INVALID')
bad('no-fake-created-domain-event',lambda:inspect(changed('domainEventId',success['domainEventId'])),'AUDIT_RECORD_MASK_INVALID')
bad('no-fake-created-aggregate-extra',lambda:inspect({**pending,'aggregateId':pending['prospectiveJobId']}),'AUDIT_RECORD_MASK_INVALID')
bad('command-outcome-byte-corruption',lambda:inspect(changed('retainedOutcomeBytesBase64',base64.b64encode(raw(pending['retainedOutcomeBytesBase64'])+b' ').decode())),'AUDIT_RETAINED_OUTCOME_DIGEST_MISMATCH')
bad('retained-projection-silent-state-rewrite',lambda:inspect(changed('retainedOutcome',{**pending['retainedOutcome'],'status':'FAILED'})),'AUDIT_RETAINED_OUTCOME_PROJECTION_MISMATCH')
bad('prospective-root-cannot-be-audit-object',lambda:inspect(changed('logicalOperationId',pending['prospectiveJobId'])),'AUDIT_RETAINED_OUTCOME_IDENTITY_MISMATCH')
bad('unknown-null-event-stream-fails-not-omitted',lambda:inspect({'recordKind':'UNRESOLVED_AUDIT_STREAM','auditId':pending['auditId']}),'AUDIT_STORED_STREAM_UNRESOLVED')
# Construct correctly byte-bound valid source-retained error variants from one
# real persisted baseline. Their SQL producer commits are not claimed here.
def outcome_variant(outcome):
 row=copy.deepcopy(pending);ob=canonical(outcome);row['retainedOutcome']=outcome;row['retainedOutcomeBytesBase64']=base64.b64encode(ob).decode();row['retainedOutcomeDigest']='sha256:'+hashlib.sha256(ob).hexdigest()
 audit=json.loads(raw(row['canonicalAuditBytesBase64']));audit['afterDigest']=row['retainedOutcomeDigest'];ab=canonical(audit);row['canonicalAuditBytesBase64']=base64.b64encode(ab).decode();row['eventHash']='sha256:'+framed_hash(1,bytes.fromhex(row['previousHash'][7:]),int(row['chainSequence']),ab).hex();return row
variants={}
for status,terminal,code,classification,retry in [('FAILED',True,'CREATE_INPUT_INVALID','VALIDATION','DO_NOT_RETRY'),('FAILED',False,'SIDE_EFFECT_OUTCOME_UNKNOWN','UNKNOWN','RECONCILE_THEN_RETRY'),('FAILED',False,'CREATE_PERSISTENCE_FAILED','INTERNAL','RETRY_SAME_OPERATION'),('CANCELLED',True,'CREATE_CANCELLED','CANCELLED','DO_NOT_RETRY')]:
 outcome={**pending['retainedOutcome'],'status':status,'terminal':terminal,'error':{'stableCode':code,'classification':classification,'retryDirective':retry,'message':'Synthetic retained outcome','detailsDigest':None}}
 row=outcome_variant(outcome);inspect(row);ok('source-retained-mask-'+code+'-positive-byte-bound');variants[code]=row
v=variants['SIDE_EFFECT_OUTCOME_UNKNOWN'];bad('unknown-cannot-be-terminal',lambda:inspect(outcome_variant({**v['retainedOutcome'],'terminal':True})),'AUDIT_RETAINED_OUTCOME_STATE_MISMATCH')
v=variants['CREATE_CANCELLED'];bad('cancel-code-cannot-be-failed',lambda:inspect(outcome_variant({**v['retainedOutcome'],'status':'FAILED'})),'AUDIT_RETAINED_OUTCOME_STATE_MISMATCH')
v=variants['CREATE_INPUT_INVALID'];bad('wrong-retained-error-tuple',lambda:inspect(outcome_variant({**v['retainedOutcome'],'error':{**v['retainedOutcome']['error'],'classification':'UNKNOWN'}})),'AUDIT_RECORD_MASK_INVALID')
outcome=pending['retainedOutcome'];bad('accepted-cannot-be-terminal',lambda:inspect(outcome_variant({**outcome,'terminal':True})),'AUDIT_RETAINED_OUTCOME_STATE_MISMATCH')

def with_raw(data):
 row=copy.deepcopy(pending);row['retainedOutcomeBytesBase64']=base64.b64encode(data).decode();row['retainedOutcomeDigest']='sha256:'+hashlib.sha256(data).hexdigest();return row
bad('actual-retained-JSON-UTF8-boundary',lambda:inspect(with_raw(b'\xff')),'AUDIT_RETAINED_OUTCOME_JSON_INVALID')
bad('actual-retained-JSON-duplicate-key-boundary',lambda:inspect(with_raw(raw(pending['retainedOutcomeBytesBase64'])[:-1]+b',"status":"ACCEPTED"}')),'AUDIT_RETAINED_OUTCOME_JSON_DUPLICATE_KEY')
# SQL stream coverage denominator is actual persisted audit count; no filtered
# count or null-row omission is relabeled a complete universe.
R=resource_index();report={'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'consumedCanonicalDigests':{k:R[k]['sha256']for k in ['database/generation-create-foundations.sql','database/generation-create-preroot.sql','database/generation-preroot-frozen-archive.sql']},'postgresVersion':'18.6','database':'archive_preroot_transfer_905','readOnlyTransaction':True,'actualAuditRows':2,'projectedAuditRows':2,'checked':len(cases),'failed':0,'cases':cases,'actualCanonicalFixtureProducer':'audit/generated/resume-905/archive/preroot-transfer/verify_preroot_archive_transfer.py','originalUnsafeProjectionExcludedRows':1,'newProjectionExcludesRows':0,'actualRowsSummary':[{'auditId':r['auditId'],'recordKind':r['recordKind'],'logicalOperationId':r['logicalOperationId'],'byteDigests':{'audit':hashlib.sha256(raw(r['canonicalAuditBytesBase64'])).hexdigest()}}for r in rows],'scope':'Actual retained ACCEPTED after success and actual domain event bytes; error/unknown/cancel mutations are source-derived reference masks, not separate PG commit producers. No whole read operation/runtime claim.','wholeOperationsClosed':0}
(O/'stored-stream-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'PASS; actual PG rows2/2; original inner join omitted1')
