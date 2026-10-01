"""Read-only post-run UUID operands/provenance; does not rerun or relabel tests."""
from pathlib import Path
import sys,json,hashlib,uuid
from datetime import datetime,timezone
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'audit/generated/resume-34d/auth-crypto')]
from ssot_sources import SSOT
from libpq_fixture import DB
EXPECTED='2577dacf6024e4666ba98b11eb9c7ffa6e7f225e60630697db740129615cc536'
assert hashlib.sha256(SSOT.read_bytes()).hexdigest()==EXPECTED
source='00000000-0000-4000-8000-000000000001'
python='/tmp/ssot-audit-venv/bin/python'
invocations=[
 ('nativeSourceFirst37','native/verify_ordered_chain.py',[], 'key_final_native_ordered_peer_8cc','native/native-retry-ordered-chain-proof.json','native/final-source-first.log'),
 ('nativeChildFirst37','native/verify_ordered_chain.py',['--child-first'],'key_final_native_ordered_childfirst_peer_8cc','native/native-retry-ordered-child-first-proof.json','native/final-child-first.log'),
 ('credentialRoot9','credential/credential-root/verify_credential_root.py',[],'key_final_credential_credential_peer_8cc','credential/credential-root/credential-root-proof.json','credential/credential-root/final-root9.log'),
 ('credentialSourceFirst27','credential/credential-root/verify_credential_native_chain.py',[],'key_final_credential_cred_join_peer_8cc','credential/credential-root/native-credential-chain-proof.json','credential/credential-root/final-source-first.log'),
 ('credentialChildFirst27','credential/credential-root/verify_credential_native_chain.py',['--child-first'],'key_final_credential_cred_childfirst_peer_8cc','credential/credential-root/native-credential-child-first-proof.json','credential/credential-root/final-child-first.log'),
]
records=[];sql="SELECT id,kind,parent_job_id,encode(uuid_send(id),'hex') FROM public.generation_job ORDER BY id"
joined="SELECT j.id,j.parent_job_id,s.source_job_id,n.source_job_id,d.target_aggregate_id,c.job_id FROM public.generation_job j JOIN kcml_retry_v1.child_scan s ON s.child_job_id=j.id JOIN kcml_native_basis_v1.child_lineage n ON n.child_job_id=j.id JOIN public.generation_job_create_completion c ON c.job_id=j.id JOIN public.domain_command d ON d.logical_operation_id=c.logical_operation_id WHERE j.kind='RETRY'"
for name,runner,args,database,proof,log in invocations:
 raw=(OUT/proof).read_bytes();v=json.loads(raw);assert v['sourceDocumentSha256']==EXPECTED
 db=DB(database)
 try:
  db.query('BEGIN READ ONLY');rows=db.query(sql)
  entry={'id':name,'argv':[python,str((OUT/runner).relative_to(ROOT)),*args],'cwd':str(ROOT),'environmentOverrides':{'PYTHONDONTWRITEBYTECODE':'1'},'invocationEvidenceBasis':'Exact coordinator tools.exec_command argv/environment and redirected log; post-run persisted operands independently read now, not a reconstructed execution claim','runnerSha256':hashlib.sha256((OUT/runner).read_bytes()).hexdigest(),'outputSha256':hashlib.sha256(raw).hexdigest(),'stdoutStderrLog':log,'logSha256':hashlib.sha256((OUT/log).read_bytes()).hexdigest(),'checked':v['checked'],'postgresDatabase':database,'observedAtUtc':datetime.now(timezone.utc).isoformat(),'readOnlyObservationSQL':sql,'observedPersistedRoots':[dict(zip(['id','kind','parentJobId','uuidRawHex'],r))for r in rows]}
  if name=='credentialRoot9':
   assert len(rows)==1 and rows[0][:3]==['00000000-0000-4000-8000-000000000800','CREATE',None]
   entry['UUIDOrderScope']='NOT_APPLICABLE_SINGLE_CREATE_ROOT';entry['sourceJobId']=None;entry['childJobId']=None
  else:
   actual=db.query(joined);assert len(actual)==1
   child,parent,scan_source,lineage_source,command_target,completion_job=actual[0]
   expectedchild='00000000-0000-4000-8000-'+('000000000000'if args else'000000000600')
   assert child==expectedchild and parent==scan_source==lineage_source==source and command_target==completion_job==child
   assert len(rows)==2 and any(r[:3]==[source,'CREATE',None]for r in rows)
   relation='CHILD_BEFORE_SOURCE'if uuid.UUID(child).bytes<uuid.UUID(source).bytes else'SOURCE_BEFORE_CHILD'
   assert relation==('CHILD_BEFORE_SOURCE'if args else'SOURCE_BEFORE_CHILD')
   entry.update({'sourceJobId':source,'childJobId':child,'sourceUuidRawHex':uuid.UUID(source).bytes.hex(),'childUuidRawHex':uuid.UUID(child).bytes.hex(),'actualRawUuidOrder':relation,'readOnlyCommittedChainObservationSQL':joined,'observedCommittedRootScanLineageCommandCompletion':dict(zip(['childId','parentId','scanSourceId','lineageSourceId','commandTargetId','completionJobId'],actual[0]))})
  db.query('COMMIT');records.append(entry)
 finally:db.close()
assert hashlib.sha256(SSOT.read_bytes()).hexdigest()==EXPECTED
# Existing proofbytes and deliveryhash requirements remain untouched.
delivery=json.loads((OUT/'DELIVERY.json').read_text())
for r in records:assert delivery['evidence'][r['id']]['sha256']==r['outputSha256']
report={'status':'PASS_READ_ONLY_POST_RUN_OPERAND_ATTESTATION','sourceDocumentSha256':EXPECTED,'sourceStable':True,'invocations':records,'identicalReportHashesExplanation':'Both UUID-order executions intentionally serialize the same case names/Boolean results, diagnostics, source/resource/helper hashes. Original reports omit argv/database/UUID operands, so successful distinct runs produce identical report bytes. This separate manifest preserves all original report hashes and independently distinguishes actual committed databases, exact invocation argv and physical root/scan/lineage/command/completion UUID operands. It adds provenance, not new test PASS or full H order certification.','scope':'Only finite post-run read-only observations of actual isolated fixtures; no key/plaintext output, no new application/runtime/systemd/global H acceptance','originalEvidenceBytesPreserved':True,'wholeOperationClosed':False,'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
(OUT/'INVOCATION_UUID_OPERANDS.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'runs':len(records),'rawUUIDOrders':[r.get('actualRawUuidOrder',r['UUIDOrderScope']if'UUIDOrderScope'in r else None)for r in records]}))
