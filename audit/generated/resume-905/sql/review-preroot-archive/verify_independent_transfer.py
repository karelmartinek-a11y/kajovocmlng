"""Independent actual PostgreSQL SQL transfer fixture; no auth/crypto substitution claim."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;AUTHOR=ROOT/'audit/generated/resume-905/archive/preroot-transfer'
source=(ROOT/'audit/generated/resume-34d/failure-sql/verify_pending_transfer.py').read_text().split('\nreport=',1)[0]
source=source.replace('pending_transfer_34d','independent_preroot_archive_sql905')
needle="pending=ns['parts']('ACCEPTED',False);q=case('accepted-pending-actual-commit',pending,commit=True);assert q.returncode==0,q.stderr"
assert needle in source
injection='''
from ssot_sources import resource_index
from generation_frozen_archive import policy_bytes,DOMAIN_IMPLEMENTATION,POLICY_ID
rs=resource_index();candidate=(author_out/'generation-preroot-frozen-archive.sql').read_bytes();embedded=rs.get('database/generation-preroot-frozen-archive.sql');newsql=embedded['raw']if embedded else candidate
assert newsql==candidate,'PREROOT_ARCHIVE_CANONICAL_CANDIDATE_BYTE_MISMATCH'
r=run(rs['database/generation-frozen-archive.sql']['raw'].decode()+newsql.decode());assert r.returncode==0,r.stderr
x=ns['ns'];mask=x['row']['requestSchema']['properties']['body'];schema=x['canonical_bytes'](mask);schema_digest=hashlib.sha256(schema).digest();authority=ns['input_source'];policy=policy_bytes(authority,DOMAIN_IMPLEMENTATION);policy_digest=hashlib.sha256(policy).digest()
def lit(s):return "'"+s.replace("'","''")+"'"
def publish(kind,id,raw):return 'SELECT kcml_archive_publish_v1('+','.join([lit(kind),lit(id),b(hashlib.sha256(raw).digest()),b(raw),lit('SSOT:'+hashlib.sha256(authority).hexdigest()),b(hashlib.sha256(authority).digest())])+');'
publication=publish('SCHEMA',mask['$id'],schema)+publish('DOMAIN_POLICY',POLICY_ID,policy)+publish('AUTHORITY','SSOT',authority)+publish('POLICY_IMPLEMENTATION','GENERATION_CREATE_REQUEST_SEMANTICS_V1',DOMAIN_IMPLEMENTATION)
r=run(publication);assert r.returncode==0,r.stderr
prerootbinding="INSERT INTO generation_preroot_frozen_policy_binding_v1(snapshot_id,logical_operation_id,schema_id,schema_digest,policy_id,policy_digest,dependency_closure)VALUES('"+x['snap']+"','"+x['op']+"',"+lit(mask['$id'])+','+b(schema_digest)+','+lit(POLICY_ID)+','+b(policy_digest)+",'[]');"
successbinding=prerootbinding.replace('generation_preroot_frozen_policy_binding_v1','generation_frozen_policy_binding_v1')
pending=ns['parts']('ACCEPTED',False)
q=case('independent-accepted-pending-missing-archive-specific-rejection',pending,'FROZEN_PREROOT_ARCHIVE_REQUIRED');assert q.returncode!=0 and 'FROZEN_PREROOT_ARCHIVE_REQUIRED'in q.stderr
r=run('SELECT(SELECT count(*)FROM domain_command),(SELECT count(*)FROM generation_create_preroot_snapshot),(SELECT count(*)FROM generation_create_preroot_outcome);');assert r.stdout.strip()=='0|0|0'
ns['checks'].append({'case':'independent-missing-archive-rolls-back-command-protected-snapshot-and-outcome','passed':True})
pending={**{k:v for k,v in pending.items()if k!='audit'},'archive-binding':prerootbinding,'audit':pending['audit']}
q=case('accepted-pending-actual-commit',pending,commit=True);assert q.returncode==0,q.stderr
retained=run("SELECT kcml_preroot_archive_read_v1('"+x['snap']+"','"+x['op']+"');").stdout.strip();assert retained
r=run('SELECT(SELECT count(*)FROM generation_job),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM transactional_outbox);');assert r.stdout.strip()=='0|0|0'
ns['checks'].append({'case':'independent-pending-archive-does-not-fabricate-job-event-outbox','passed':True})
'''
source=source.replace(needle,injection)
needle="# Mutation uses the valid native transfer"
source=source.replace(needle,"parts={**{k:v for k,v in parts.items()if k!='audit'},'archive-binding':successbinding,'audit':parts['audit']}\n"+needle)
# Same schema and real available policy content but changed policy digest must not transfer.
needle="q=case('pending-to-success-same-identity-actual-commit',parts,commit=True)"
additional='''
variant=json.loads(policy);variant['reviewerSyntheticRevision']='different-but-available';alternate=x['canonical_bytes'](variant);otherdigest=hashlib.sha256(alternate).digest();r=run(publish('DOMAIN_POLICY',POLICY_ID,alternate));assert r.returncode==0,r.stderr
wrong=parts.copy();wrong['archive-binding']=wrong['archive-binding'].replace(b(policy_digest),b(otherdigest));q=case('independent-available-different-policy-exact-transfer-rejection',wrong,'FROZEN_PREROOT_ARCHIVE_TRANSFER_MISMATCH');assert q.returncode!=0 and 'FROZEN_PREROOT_ARCHIVE_TRANSFER_MISMATCH'in q.stderr
q=case('independent-valid-success-rollback',parts)
r=run('SELECT(SELECT count(*)FROM generation_job),(SELECT count(*)FROM domain_event),(SELECT count(*)FROM generation_preroot_frozen_policy_binding_v1);');assert r.stdout.strip()=='0|0|1'
assert run("SELECT kcml_preroot_archive_read_v1('"+x['snap']+"','"+x['op']+"');").stdout.strip()==retained
ns['checks'].append({'case':'independent-transfer-rollback-preserves-earlier-pending-archive','passed':True})
'''
source=source.replace(needle,additional+needle)
ns={'__file__':str(ROOT/'audit/generated/resume-34d/failure-sql/verify_pending_transfer.py'),'author_out':AUTHOR,'review_out':OUT};exec(compile(source,'independent-preroot-archive-transfer','exec'),ns)
checks=ns['ns']['checks'];assert all(c['passed']for c in checks)
record=dict(sourceDocumentSha256=hashlib.sha256(ns['ns']['input_source']).hexdigest(),sourceUnchangedDuringRun=ns['ns']['input_source']==ns['ns']['SSOT'].read_bytes(),candidateSqlSha256=hashlib.sha256(ns['candidate']).hexdigest(),canonicalExtensionExecuted=ns['embedded']is not None,postgresqlVersion=ns['run']('SHOW server_version').stdout.strip(),checks=checks,checked=len(checks),failed=0,scope='Independent actual canonical foundation/preroot/success archive SQL plus exact new candidate extension. True atomic pending with archive, actual retained no-root state, same frozen snapshot+archive success commit, available alternate policy rejection and rollback. Synthetic server authentication and opaque ciphertext are explicit bounded SQL fixtures, not actual credential/canonical crypto source proof.',wholeOperationClosed=False)
(OUT/'independent-transfer-proof.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(checked=len(checks),failed=0,canonicalExtensionExecuted=record['canonicalExtensionExecuted'])))
