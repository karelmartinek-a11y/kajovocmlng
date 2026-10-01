from pathlib import Path
import sys,json,hashlib
ROOT=Path('/workspace/kajovocmlng');HERE=Path(__file__).parent;AUTHOR=ROOT/'audit/generated/closure-replan-84c/sql';sys.dont_write_bytecode=True
names=['owner-query-helpers.sql','owner-query-original-wrappers.sql','owner-query-family.json','owner_query_context.py','verify_owner_query_family_pg.py','owner-query-install-acl.sql'];inputs={n:(AUTHOR/n).read_bytes()for n in names};program=inputs['verify_owner_query_family_pg.py'].decode().replace("OUT=Path(__file__).resolve().parent","OUT=Path("+repr(str(AUTHOR))+")").replace('helper_owner_queries_utf8_84c','peer_helper_owner_queries_final_utf8_84c')
original_write=Path.write_text
Path.write_text=lambda p,data,*a,**kw:original_write(HERE/p.name,data,*a,**kw)
try:ns={'__file__':str(AUTHOR/'verify_owner_query_family_pg.py')};exec(compile(program,str(AUTHOR/'verify_owner_query_family_pg.py'),'exec'),ns)
finally:Path.write_text=original_write
db=ns['db'];lit=ns['lit'];checks=[]
def rec(id,ok,**kw):checks.append({'id':id,'passed':bool(ok),**kw})
rec('actual-author-cases-reproduced',all(x['passed']for x in ns['checks']),count=len(ns['checks']))
# Exact narrow functions are unavailable to PUBLIC. Candidate role mapping is not fabricated.
functions=db.query("SELECT proname,prosecdef::text,proconfig::text,has_function_privilege('kcml_domain_writer',p.oid,'EXECUTE')::text FROM pg_proc p WHERE proname IN('kcml_owner_query_context_v1','kcml_assert_operation_descriptor_v1','kcml_assert_recovery_and_incarnation_v1','kcml_lock_exact_root_plan_v1','kcml_apply_exact_domain_plan_v1')ORDER BY proname")
rec('nonmember-domain-role-has-no-helper-execute',len(functions)==5 and all(x[3]=='false'for x in functions),catalog=functions)
# Metadata query itself leaves audit unchanged; no audited-disclosure claim.
db.query('UPDATE public.owner_session SET revoked_at=NULL WHERE id='+lit(ns['session']))
count_before=db.query('SELECT count(*)FROM public.audit_event')[0][0];ns['begin']();ctx=ns['prepare'](db,'ownerApiKey.read',ns['cookie'],'OWNER_SESSION',ns['byop']['ownerApiKey.read']['descriptorDigest']);ns['invoke']('ownerApiKey.read',ctx);ns['end']();count_after=db.query('SELECT count(*)FROM public.audit_event')[0][0]
rec('scoped-SQL-does-not-pretend-audit-producer',count_before==count_after,auditCountBefore=count_before,auditCountAfter=count_after,actualDisclosureDispatchComplete=False)
# A genuine trusted positive context under a wrong profile must fail specifically.
ns['create_temp'](db);db.query('BEGIN ISOLATION LEVEL READ COMMITTED READ ONLY')
ctx=ns['prepare'](db,'ownerApiKey.read',ns['cookie'],'OWNER_SESSION',ns['byop']['ownerApiKey.read']['descriptorDigest'])
try:ns['invoke']('ownerApiKey.read',ctx);rec('READ_COMMITTED-is-not-RR',False)
except RuntimeError as e:rec('READ_COMMITTED-is-not-RR','OWNER_QUERY_PROFILE_MISMATCH'in str(e),diagnostic=str(e).splitlines()[0])
db.query('ROLLBACK');ns['finish'](db)
ns['create_temp'](db);db.query('BEGIN ISOLATION LEVEL REPEATABLE READ READ WRITE');ctx=ns['prepare'](db,'ownerApiKey.read',ns['cookie'],'OWNER_SESSION',ns['byop']['ownerApiKey.read']['descriptorDigest'])
try:ns['invoke']('ownerApiKey.read',ctx);rec('READ_WRITE-is-not-readonly',False)
except RuntimeError as e:rec('READ_WRITE-is-not-readonly','OWNER_QUERY_PROFILE_MISMATCH'in str(e),diagnostic=str(e).splitlines()[0])
db.query('ROLLBACK');ns['finish'](db)
# Owner-mismatched temp authority cannot satisfy the private issuer, even exact copied shape.
ns['create_temp'](db);db.query('ALTER TABLE pg_temp.kcml_verified_owner_query OWNER TO agent');db.query('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
try:ns['invoke']('ownerApiKey.read',ns['uid'](990));rec('caller-owned-TEMP-not-trusted',False)
except RuntimeError as e:rec('caller-owned-TEMP-not-trusted','OWNER_QUERY_TRUSTED_CONTEXT_REQUIRED'in str(e),diagnostic=str(e).splitlines()[0])
db.query('ROLLBACK');ns['finish'](db)
ns['begin']();ctx=ns['prepare'](db,'ownerApiKey.read',ns['cookie'],'OWNER_SESSION',ns['byop']['ownerApiKey.read']['descriptorDigest'])
try:db.query('SELECT public.kcml_assert_operation_descriptor_v1('+lit(ctx)+"::public.kcml_operation_context_v1,'chat.turn.create','sha256:"+'0'*64+"')");rec('unsupported-sibling-not-generic-dispatched',False)
except RuntimeError as e:rec('unsupported-sibling-not-generic-dispatched','SQL_OPERATION_TYPED_HANDLER_UNRESOLVED'in str(e),diagnostic=str(e).splitlines()[0])
ns['end']()
# Execute exact additional installation ACL bytes, not a fixture-only shortcut.
wrappers=[x['functionName'] for x in ns['family']];db.query('BEGIN')
for fn in wrappers:db.query('GRANT EXECUTE ON FUNCTION public.'+fn+'(public.kcml_operation_context_v1) TO PUBLIC')
before_acl=[db.query("SELECT has_function_privilege('kcml_domain_writer','public."+fn+"(public.kcml_operation_context_v1)','EXECUTE')")[0][0] for fn in wrappers]
db.query(inputs['owner-query-install-acl.sql'].decode())
after_acl=[db.query("SELECT has_function_privilege('kcml_domain_writer','public."+fn+"(public.kcml_operation_context_v1)','EXECUTE')")[0][0] for fn in wrappers]
rec('exact-installation-ACL-closes-original-PUBLIC-default',before_acl==['t','t'] and after_acl==['f','f'],before=before_acl,after=after_acl)
db.query('ROLLBACK')
db.query('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;SET LOCAL ROLE kcml_domain_writer')
try:db.query('SELECT public.'+wrappers[0]+'('+lit(ns['uid'](992))+'::public.kcml_operation_context_v1)');rec('nonmember-cannot-invoke-scoped-wrapper',False)
except RuntimeError as e:rec('nonmember-cannot-invoke-scoped-wrapper','permission denied'in str(e),diagnostic=str(e).splitlines()[0])
db.query('ROLLBACK')
report={'sourceDocumentSha256':hashlib.sha256(ns['f'].source).hexdigest(),'sourceUnchanged':ns['f'].source==ns['SSOT'].read_bytes(),'authorAssertionsReproduced':len(ns['checks']),'checks':checks,'passed':sum(x['passed']for x in checks),'failed':sum(not x['passed']for x in checks),'inputs':{n:hashlib.sha256(b).hexdigest()for n,b in inputs.items()},'inputsUnchanged':all(b==(AUTHOR/n).read_bytes()for n,b in inputs.items()),'postgresVersion':db.query('SHOW server_version')[0][0],'scope':'Candidate exact two original wrappers/four helpers, issuer TEMP ownership and RR readonly only. No public dispatch, actual session issuer, audited plaintext read, canonical key hydration or260otherplans closure.','wholeOperationClosed':False,'implementationAcceptance':'NOT_EVALUATED'};(HERE/'owner-query-independent-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['authorAssertionsReproduced','passed','failed','inputsUnchanged']}));db.close()
