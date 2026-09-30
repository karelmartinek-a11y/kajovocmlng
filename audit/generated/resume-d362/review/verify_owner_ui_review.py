from pathlib import Path
import sys,json,hashlib
HERE=Path(__file__).parent; D=HERE.parent/'consumers';ROOT=HERE.parents[3]
for p in [D,HERE.parent/'persistence',ROOT/'scripts']:sys.path.insert(0,str(p))
source=(D/'verify_postgres_owner_ui_bridge.py').read_text().split('checks=[]',1)[0]
source=source.replace("HERE=Path(__file__).parent",f"HERE=Path({str(D)!r})").replace("'-d','postgres'","'-d','generation_independent_review_fixture'").replace('owner_ui_fixture','independent_owner_ui')
g={'__file__':str(HERE/'verify_owner_ui_review.py')};exec(compile(source,'read-only author fixture prefix','exec'),g)
cases=[]
def case(name,pre,call,expected=None):
 r=g['sql'](g['prefix']+g['base']+pre+call+'ROLLBACK;')
 ok=r.returncode==0 if expected is None else r.returncode!=0 and expected in r.stderr
 cases.append({'id':name,'passed':ok,'expected':expected or 'ACCEPTED','actual':r.stdout.strip() if not r.returncode else r.stderr[-1000:]})
case('positive-own-intent-and-worker','',g['accept']+g['worker'])
case('dispatch-start-cannot-become-stop',"UPDATE owner_ui_dispatch_registry SET worker_operation_id='runtime.stop';",g['accept'],'owner_ui_dispatch_registry_check')
case('existing-worker-current-cancel-rechecked','',g['accept']+g['worker']+"UPDATE domain_command SET terminal=true,state='CANCELLED',terminal_at=clock_timestamp(),result_digest=decode(repeat('99',32),'hex');"+g['worker'],'OWNER_UI_WORKER_PARENT_NOT_ADMISSIBLE')
case('durable-intent-survives-origin-session-revocation','',g['accept']+"UPDATE owner_session SET revoked_at=clock_timestamp();"+g['worker'])
# Existing-role setup may not silently trust privileged/login credentials.
r=g['sql']('BEGIN;ALTER ROLE kcml_owner_ui_builder LOGIN;SET search_path=independent_owner_ui,pg_catalog;'+g['roles']+"DO $$BEGIN IF (SELECT rolcanlogin FROM pg_roles WHERE rolname='kcml_owner_ui_builder') THEN RAISE NOTICE 'UNSAFE_EXISTING_ROLE_ACCEPTED';END IF;END$$;ROLLBACK;")
cases.append({'id':'existing-login-builder-role-must-not-be-accepted','passed':r.returncode!=0 and '55000' in r.stderr and 'OWNER_UI_RESERVED_ROLE_PROFILE_UNSAFE' in r.stderr,'expected':'55000: OWNER_UI_RESERVED_ROLE_PROFILE_UNSAFE','actual':r.stderr[-1200:]})
report={'scope':'Independent PG18.6 disposable-schema OWNER bridge reference; auth/schema publisher fixtures synthetic, not source runtime producers or whole UI closure.','checks':len(cases),'failed':sum(not c['passed'] for c in cases),'cases':cases,'consumed':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [D/'owner-ui-intent-worker-proposed.sql',D/'owner-ui-role-bindings-proposed.sql',D/'verify_postgres_owner_ui_bridge.py']}}
(HERE/'owner-ui-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(cases),'failed':report['failed']}))
