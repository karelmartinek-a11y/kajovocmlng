"""Independent actual current SQL acceptance with no pre-root archive bytes."""
from pathlib import Path
import json,hashlib,sys
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent
AUTHOR=ROOT/'audit/generated/resume-34d/failure-sql';original=AUTHOR/'verify_failure_before_root.py'
program=original.read_text().split('\nbase=parts();',1)[0].replace('failure_sql_34d','preroot_archive_gap_sql905')
ns={'__file__':str(original)};exec(compile(program,'independent-current-preroot-factory','exec'),ns)
rs=ns['resources'];archive=rs['database/generation-frozen-archive.sql']['raw'];r=ns['run'](archive.decode());assert r.returncode==0,r.stderr
pending=ns['parts']('ACCEPTED',False);r=ns['case']('independent-current-valid-retained-accepted-pending',pending,commit=True);assert r.returncode==0,r.stderr
rows=ns['run']('SELECT (SELECT count(*) FROM domain_command),(SELECT count(*) FROM generation_create_preroot_snapshot),(SELECT count(*) FROM generation_create_preroot_outcome),(SELECT count(*) FROM generation_job),(SELECT count(*) FROM domain_event),(SELECT count(*) FROM transactional_outbox),(SELECT count(*) FROM generation_frozen_policy_binding_v1),(SELECT count(*) FROM generation_frozen_bundle_v1);')
assert rows.returncode==0,rows.stderr
observed=rows.stdout.strip();assert observed=='1|1|1|0|0|0|0|0',observed
record=dict(sourceDocumentSha256=hashlib.sha256(ns['input_source']).hexdigest(),sourceUnchangedDuringRun=ns['input_source']==ns['SSOT'].read_bytes(),status='CONTRACT_GAP_REPRODUCED',nativePositiveSchemaValidated=True,observedCounts=dict(zip(['command','prerootSnapshot','retainedOutcome','job','event','outbox','archiveBinding','archiveBundle'],map(int,observed.split('|')))),resourceBindings={p:rs[p]['sha256']for p in ['database/generation-create-foundations.sql','database/generation-create-preroot.sql','database/generation-frozen-archive.sql']},postgresqlVersion=ns['run']('SHOW server_version').stdout.strip(),scope='Current canonical SQL accepts legitimate retained pending outcome with no archived schema/policy bytes. This reproduces named OPEN pre-root archive gap; it is not a successful archive completeness proof. Authentication receipts synthetic and protected ciphertext opaque.',wholeOperationClosed=False)
(OUT/'pre-fix-current-archive-gap.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record['observedCounts']))
