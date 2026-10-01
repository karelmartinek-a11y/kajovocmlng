from pathlib import Path
import sys,json,hashlib
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'audit/generated/resume-34d/auth-crypto'));from libpq_fixture import DB,lit
sys.path.insert(0,str(ROOT/'scripts'));from ssot_sources import SSOT
source=SSOT.read_bytes();db=DB('native_retry_ordered_8cc');checks=[]
def check(n,p):assert p,n;checks.append({'case':n,'passed':True})
check('source-schema-physical-parent-digest-identity',db.query("SELECT count(*) FROM kcml_native_basis_v1.schema_bundle WHERE primary_parent_uuid IS DISTINCT FROM source_job_id OR lock_kind_ordinal<>154 OR lock_stable_id IS DISTINCT FROM digest")[0][0]=='0')
check('source-record-physical-parent-exact-stable-id',db.query("SELECT count(*)FROM kcml_native_basis_v1.record WHERE primary_parent_uuid IS DISTINCT FROM source_job_id OR lock_kind_ordinal<>155 OR lock_stable_id IS DISTINCT FROM record_id")[0][0]=='0')
check('child-lineage-physical-parent-server-child',db.query("SELECT count(*)FROM kcml_native_basis_v1.child_lineage WHERE primary_parent_uuid IS DISTINCT FROM child_job_id OR lock_kind_ordinal<>153 OR lock_stable_id IS DISTINCT FROM uuid_send(child_job_id)")[0][0]=='0')
row=db.query("SELECT encode(digest,'hex'),schema_id,encode(exact_bytes,'hex'),source_job_id FROM kcml_native_basis_v1.schema_bundle ORDER BY digest LIMIT1".replace('LIMIT1','LIMIT 1'))[0]
child=db.query("SELECT id FROM public.generation_job WHERE kind='RETRY'")[0][0]
def b(s):return "decode('"+s+"','hex')"
def lock():
 db.query('BEGIN');db.query('SELECT id FROM public.owner_identity WHERE singleton_key=1 FOR UPDATE');db.query('SELECT id FROM public.generation_job WHERE id IN('+lit(child)+','+lit(row[3])+')ORDER BY uuid_send(id)FOR UPDATE')
insert='INSERT INTO kcml_native_basis_v1.schema_bundle(digest,schema_id,exact_bytes,source_job_id)VALUES('+','.join([b(row[0]),lit(row[1]),b(row[2]),lit(child)])+');'
lock();db.query(insert);check('same-exact-schema-bytes-distinct-source-copy',db.query('SELECT primary_parent_uuid FROM kcml_native_basis_v1.schema_bundle WHERE source_job_id='+lit(child)+'AND digest='+b(row[0]))==[[child]]);db.query('ROLLBACK')
lock()
try:db.query(insert.replace(lit(child),'NULL'));raise AssertionError('NULL_SOURCE_ACCEPTED')
except RuntimeError as e:check('missing-source-parent-specific-not-null',('source_job_id'in str(e)and'null value'in str(e)))
db.query('ROLLBACK')
check('all-scope-copy-tests-rollback-exact-count',db.query('SELECT count(*)FROM kcml_native_basis_v1.schema_bundle WHERE source_job_id='+lit(child))[0][0]=='0')
assert SSOT.read_bytes()==source
(OUT/'physical-parent-proof.json').write_text(json.dumps({'status':'PASS','checked':len(checks),'checks':checks,'sourceDocumentSha256':hashlib.sha256(source).hexdigest(),'candidateSqlSha256':hashlib.sha256((OUT/'native-source-parent.sql').read_bytes()).hexdigest(),'postgresqlVersion':db.query('SHOW server_version')[0][0],'wholeOperationClosed':False},indent=2)+'\n');db.close();print(len(checks))
