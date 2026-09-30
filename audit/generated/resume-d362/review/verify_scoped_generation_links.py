from pathlib import Path
import subprocess,json,hashlib,re
HERE=Path(__file__).parent;ROOT=HERE.parents[3]
PSQL=['/tmp/kcml-pg18/bin/psql','-h','/tmp/kcml-pg18-socket','-p55432','-d','generation_independent_review_fixture','-X','-At','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose']
q=subprocess.run(PSQL,input='DROP SCHEMA public CASCADE; CREATE SCHEMA public;',text=True,capture_output=True);assert q.returncode==0,q.stderr
# Re-execute final actual foundations plus the scoped correction in OUR disposable
# database. No source-agent DB/report or shared repository file is modified.
source=(HERE.parent/'events/verify_combined_generation.py').read_text().split('# All negatives mutate')[0]
source=source.replace("'generation_combined_fixture'","'generation_independent_review_fixture'")
source=source.replace('from ssot_sources import resource_index,SSOT','from ssot_sources import resource_index,SSOT\nsys.path.insert(0,str(ROOT/"audit/generated/resume-d362/persistence"))\nfrom generation_descriptor_registry import pin,descriptor as pinned_descriptor\nfrom context_fixture_exports import common as auth_common,call as auth_call')
source=source.replace("descriptor=canonical_bytes(freeze_descriptor(native,{'owner':owner},'fixture-pinned-v1'));","pinned=pin();descriptor=pinned_descriptor(owner,'sha256:'+key.hex(),pinned);")
source=source.replace('foundation=module.foundations();',"foundation=module.foundations().replace((ROOT/'audit/generated/resume-d362/events/generation-command-links-proposed.sql').read_text(),(HERE/'generation-command-links-corrected.sql').read_text());")
ns={'__file__':str(HERE/'verify_scoped_generation_links.py')};exec(compile(source,'independent-combined-foundations','exec'),ns)
base=ns['base']
base['auth']=ns['auth_common'](ns['owner'],ns['owner'],1)+f"INSERT INTO owner_api_credential(singleton_key,secret_id,secret_version_id,verifier_hash,fingerprint,credential_version,state_version,credential_activation_epoch,created_at) VALUES(1,'90000000-0000-4000-8000-000000000001','90000000-0000-4000-8000-000000000002','SYNTHETIC_HASH_NOT_VERIFIER','synthetic-fingerprint',1,0,1,clock_timestamp());INSERT INTO generation_create_authentication_acceptance(id,owner_id,access_channel,api_credential_version,api_credential_fingerprint,accepted_at)VALUES('{ns['auth']}','{ns['owner']}','OWNER_API_KEY',1,'synthetic-fingerprint',clock_timestamp());"
base['context']=ns['auth_call'](ns['owner'],ns['auth'],ns['request_digest'].hex(),'sha256:'+ns['key'].hex())
base['command']=base['command'].replace('fixture-pinned-v1',ns['pinned']['operationRevision'])
base['typed-binding']=f"INSERT INTO generation_create_command_binding VALUES('{ns['op']}',{ns['context']},'{ns['snap']}');"
cases=[]
def test(name,parts,expected=None):
 sql='BEGIN;'+''.join(parts.values())+'SET CONSTRAINTS ALL IMMEDIATE;ROLLBACK;'
 q=ns['run'](sql);passed=q.returncode==0 if expected is None else q.returncode!=0 and expected in q.stderr
 cases.append({'id':name,'passed':passed,'expectedDiagnostic':expected,'actualDiagnostic':q.stderr.strip()[-1200:]})
test('generation-full-positive-with-scoped-binding',base)
test('generation-missing-typed-binding',{k:v for k,v in base.items()if k!='typed-binding'},'GENERATION_COMMAND_TYPED_BINDING_REQUIRED')
othercmd=base['command'].replace("'generation.job.create'","'config.rollback'").replace(ns['context'],"'99999999-9999-4999-8999-999999999999'").replace("'"+ns['snap']+"'","'88888888-8888-4888-8888-888888888888'")
test('other-operation-has-no-generation-only-FK',{'auth':base['auth'],'command':othercmd})
wrong=base.copy();wrong['command']=wrong['command'].replace("'generation.job.create'","'config.rollback'")
test('other-operation-cannot-acquire-generation-binding',wrong,'GENERATION_BINDING_OPERATION_KIND_INVALID')
wrong=base.copy();wrong['typed-binding']=wrong['typed-binding'].replace(ns['context'],"'99999999-9999-4999-8999-999999999999'")
test('generation-context-binds-command-selector',wrong,'GENERATION_COMMAND_TRUSTED_LINKAGE_INVALID')
wrong=base.copy();wrong['change-binding']="UPDATE generation_create_command_binding SET trusted_context_id='99999999-9999-4999-8999-999999999999';"
test('typed-binding-retained-immutable',wrong,'CREATE_IMMUTABLE_RECORD')
wrong=base.copy();wrong['command']=wrong['command'].replace("'"+ns['op']+"','"+ns['pinned']['operationRevision']+"','OWNER_API_KEY'", "'"+ns['op']+"','MODEL_REVISION','OWNER_API_KEY'")
test('command-revision-must-match-server-pin',wrong,'GENERATION_COMMAND_TRUSTED_LINKAGE_INVALID')
wrong=base.copy();old=","+ns['b'](ns['scope'])+","+ns['b'](ns['key'])+",NULL";wrong['command']=wrong['command'].replace(old,","+ns['b'](bytes(32))+","+ns['b'](ns['key'])+",NULL")
test('command-scope-must-match-frozen-descriptor',wrong,'GENERATION_COMMAND_TRUSTED_LINKAGE_INVALID')
wrong=base.copy();wrong['command']=wrong['command'].replace(old,","+ns['b'](ns['scope'])+","+ns['b'](bytes(32))+",NULL")
test('command-key-must-match-frozen-descriptor',wrong,'GENERATION_COMMAND_TRUSTED_LINKAGE_INVALID')
# Commit the positive only in OUR database, then exercise the eight independent
# retention mutations against exactly these final joined roots/context tables.
q=ns['run']('BEGIN;'+''.join(base.values())+'COMMIT;');assert q.returncode==0,q.stderr
q=ns['run']("BEGIN;UPDATE transactional_outbox SET state='CLAIMED',state_version=state_version+1,delivery_fence=delivery_fence+1,lease_owner_id='00000000-0000-4000-8000-000000000005',lease_expires_at=clock_timestamp()+interval '1hour';UPDATE transactional_outbox SET state='DELIVERED',state_version=state_version+1;COMMIT;");assert q.returncode==0,q.stderr
bindings={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'generation-command-links-corrected.sql',HERE/'combined-foundations.sql',HERE.parent/'persistence/generation-root-proposed.sql',HERE.parent/'persistence/trusted-generation-context-proposed.sql',HERE.parent/'persistence/authentication-roots-proposed.sql',HERE.parent/'persistence/generation-contract-pin-proposed.sql',HERE.parent/'persistence/generation_descriptor_registry.py',HERE.parent/'persistence/context_fixture_exports.py',HERE.parent/'persistence/generation-context-role-bindings.sql',HERE.parent/'events/generation-event-storage-proposed.sql']}
report={'scope':'Final joined DDL independently reexecuted in disposable OWN database. Other-operation case proves removal of irrelevant generation FK, not correctness of that other operation.','database':'generation_independent_review_fixture','version':ns['run']('SELECT version();').stdout.strip(),'sourceSha256':hashlib.sha256(ns['source']).hexdigest(),'filesSha256':bindings,'checks':cases,'failed':sum(not c['passed']for c in cases),'wholeOperationClosed':False}
(HERE/'scoped-generation-links-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(cases),'failed':report['failed']}))
