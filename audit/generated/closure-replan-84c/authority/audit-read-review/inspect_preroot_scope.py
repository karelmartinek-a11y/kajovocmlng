from pathlib import Path
import subprocess,json,hashlib,sys
ROOT=Path('/workspace/kajovocmlng');OWN=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
r=resource_index();query="BEGIN READ ONLY; SELECT a.id,a.domain_event_id,a.logical_operation_id FROM audit_event a ORDER BY a.chain_sequence; SELECT (SELECT count(*) FROM audit_event),(SELECT count(*) FROM audit_event a JOIN domain_event e ON e.id=a.domain_event_id AND e.logical_operation_id=a.logical_operation_id JOIN domain_command c ON c.logical_operation_id=a.logical_operation_id),(SELECT count(*) FROM generation_create_preroot_outcome); SELECT a.id,o.state_version,encode(o.canonical_digest,'hex'),encode(sha256(o.canonical_bytes),'hex') FROM audit_event a JOIN generation_create_preroot_outcome o ON o.audit_id=a.id; COMMIT;"
p=subprocess.run(['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p','55432','-U','agent','-d','archive_preroot_transfer_905','-v','ON_ERROR_STOP=1','-At'],input=query,text=True,capture_output=True);assert p.returncode==0,p.stderr
assert '2|1|1' in p.stdout
out={'inspectionSourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'database':'archive_preroot_transfer_905','mode':'READ_ONLY','postgresVersion':'18.6','query':query,'actualOutput':p.stdout,'finding':'Existing genuine accepted-before-root audit excluded by domain_event inner join; final source changes do not turn historical database into current-source producer proof.','consumedSchemaDigests':{k:r[k]['sha256'] for k in ['database/generation-create-foundations.sql','database/generation-create-preroot.sql']},'wholeOperationsClosed':0}
(OWN/'physical-preroot-counterexample.json').write_text(json.dumps(out,indent=2)+'\n')
print(p.stdout)
