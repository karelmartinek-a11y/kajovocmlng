"""Reproduce actual early OWNER row lock; EXPECTED_GAP is not operation PASS."""
from native_auth_factory import *
import threading
f=Factory('native_auth_order_8cc');db=f.db;events=[];original=db.query
# Observe actual SQL without writing sensitive body, token, verifier or key.
def observed(sql):
 if sql=='SELECT id FROM owner_identity WHERE singleton_key=1 FOR SHARE':events.append({'ordinal':len(events),'acquisition':'OWNER_IDENTITY_FOR_SHARE','lockClass':'E','scope':'owner_identity singleton','source':'scripts/generation_auth_acceptance.py'})
 if sql.startswith('INSERT INTO generation_create_authentication_acceptance'):events.append({'ordinal':len(events),'acquisition':'AUTHENTICATION_ACCEPTANCE_INSERT','lockClass':'IMMUTABLE_CHILD_INSERT_PENDING_EXACT_ORDINAL','scope':'fresh auth receipt with immediate owner FK','source':'scripts/generation_auth_acceptance.py'})
 if sql.startswith('SELECT kcml_generation_create_context_v1'):events.append({'ordinal':len(events),'acquisition':'TRUSTED_CONTEXT_INSERT','lockClass':'IMMUTABLE_CHILD_INSERT_PENDING_EXACT_ORDINAL','scope':'new typed context','source':'canonical context constructor'})
 if sql.startswith('SELECT kcml_generation_lock_retained_locator_v1'):events.append({'ordinal':len(events),'acquisition':'RETAINED_LOCATOR_LOOKUP','lockClass':'C0_C1','scope':'stablebusinesskey/originalscope','source':'canonical locator lock helper'})
 return original(sql)
db.query=observed
db.query('BEGIN');body={'kind':'CREATE','intent':'Synthetic row lock ordering probe','targetKind':'PLATFORM_COMPONENT','sources':[{'kind':'TEXT','text':'No sensitive content'}]};built=f.build(body,uid(1),uid(1001),uid(2001),key='auth-order-only')
contender=DB(f.database);out=[]
def mutate_owner():
 try:contender.query("BEGIN;SET LOCAL lock_timeout='150ms';");contender.query('UPDATE owner_identity SET state_version=state_version+1');out.append('UNEXPECTED_OWNER_WRITE')
 except Exception as ex:out.append('LOCK_TIMEOUT'if'lock timeout'in str(ex)else'UNEXPECTED_EXCEPTION')
 finally:contender.query('ROLLBACK')
t=threading.Thread(target=mutate_owner);t.start();t.join(5)
e=next(v['ordinal']for v in events if v['acquisition']=='OWNER_IDENTITY_FOR_SHARE');c=next(v['ordinal']for v in events if v['acquisition']=='RETAINED_LOCATOR_LOOKUP')
assert e<c and out==['LOCK_TIMEOUT'],(events,out)
report={'status':'CONTRACT_GAP_REPRODUCED','obligationId':'GENERATION.AUTH.API_ACCEPTANCE','sourceDocumentSha256':sha(f.source).hex(),'postgresqlVersion':original('SHOW server_version')[0][0],'authority':['SSOT§51.6 lock total order C before E; immutable child same parent ordinal','SSOT§51.12 public API raw verifier/current credential before API-derived authority'],'actualOrder':events,'realConcurrentOwnerMutation':out,'rootVerifierSha256':sha((ROOT/'scripts/generation_auth_acceptance.py').read_bytes()).hex(),'finding':'OWNER FOR SHARE precedes C0/C1. Removing explicit SHARE alone does not prove conformance: immediate auth-receipt owner FK and fresh immutable auth/context INSERT precede C. Exact ordinal mapping and corrected producer needed.','wholeOperationClosed':False,'fixtureAcceptance':'Not a PASS: diagnostic reproduction only'}
Path(__file__).with_name('auth-lock-order-gap.json').write_text(json.dumps(report,indent=2)+'\n');db.query('ROLLBACK');contender.close();db.close();print(json.dumps({'status':report['status']}))
