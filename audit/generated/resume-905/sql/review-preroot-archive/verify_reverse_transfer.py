"""Independent actual SQL reverse-order binding guard; no invented pending receipt."""
from pathlib import Path
import json,hashlib
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent
program=(OUT/'reproduce_real_transfer.py').read_text().split("\npending_negative('accepted-preroot-missing-archive-binding'",1)[0].replace('independent_crypto_preroot_archive905','independent_reverse_preroot_archive905')
ns={'__file__':str(OUT/'reproduce_real_transfer.py')};exec(compile(program,'independent-direct-success-positive-factory','exec'),ns)
db=ns['db'];rec=ns['rec'];checks=ns['checks'];db.query('BEGIN');positive,meta,plain=ns['ns']['build']();ns['install_protected'](positive,meta);db.query(ns['publication']+ns['archive_bind'](meta));db.query('COMMIT');rec('reverse-baseline-real-direct-success-with-existing-success-archive',True)
pending,envelope=ns['pending_parts'](positive,meta);snapshot=pending['snapshot'];binding=ns['bind_preroot'](meta)
# Successful snapshot/command/crypto nonce already exist. No accepted outcome is
# fabricated. The reverse guard is tested by late exact snapshot+archive binding.
other=json.loads(ns['policy']);other['revision']='INDEPENDENT_OTHER_AVAILABLE_POLICY';raw=ns['canonical'](other)
db.query(ns['publish']('DOMAIN_POLICY',ns['POLICY_ID'],raw));wrong=binding.replace(ns['b'](ns['sha'](ns['policy'])),ns['b'](ns['sha'](raw)))
db.query('BEGIN')
try:db.query(snapshot+wrong);db.query('COMMIT');rec('reverse-order-available-different-policy-rejected',False)
except Exception as e:
 db.query('ROLLBACK');rec('reverse-order-available-different-policy-rejected','FROZEN_PREROOT_ARCHIVE_TRANSFER_MISMATCH'in str(e),'FROZEN_PREROOT_ARCHIVE_TRANSFER_MISMATCH',str(e))
rec('reverse-order-rejection-preserves-existing-success-without-preroot-history',db.query('SELECT(SELECT count(*)FROM generation_job),(SELECT count(*)FROM generation_frozen_policy_binding_v1),(SELECT count(*)FROM generation_create_preroot_snapshot),(SELECT count(*)FROM generation_create_preroot_outcome)')[0]==['1','1','0','0'])
db.query('BEGIN');db.query(snapshot+binding);db.query('COMMIT');rec('reverse-order-exact-success-binding-accepted',True)
rec('reverse-order-exact-binding-does-not-fabricate-pending-outcome',db.query('SELECT(SELECT count(*)FROM generation_create_preroot_outcome),(SELECT count(*)FROM generation_preroot_frozen_policy_binding_v1)')[0]==['0','1'])
# Ensure success table FK and the new pre-root FK are both actually installed.
r=db.query("SELECT conname FROM pg_constraint WHERE conrelid IN('generation_frozen_policy_binding_v1'::regclass,'generation_preroot_frozen_policy_binding_v1'::regclass) AND contype='f'")
rec('existing-success-and-new-preroot-physical-FKs-present',len(r)==8)
record=dict(sourceDocumentSha256=ns['sha'](ns['source']).hex(),candidateExtensionSha256=ns['sha'](ns['extension']).hex(),postgresqlVersion=db.query('SHOW server_version')[0][0],checked=len(checks),failed=sum(not c['passed']for c in checks),checks=checks,scope='Independent reverse direction: actual direct-success canonical auth/crypto/root/archive commit, then late exact protected snapshot/archive binding. Alternate available policy rejected by reverse guard, exact selection accepted, no accepted pending receipt fabricated. This exercises SQL insertion-order/backfill guard only, not a proposed business admission path.',wholeOperationClosed=False)
(OUT/'independent-reverse-transfer-proof.json').write_text(json.dumps(record,indent=2)+'\n');db.close();print(json.dumps(dict(checked=len(checks),failed=record['failed'])))
