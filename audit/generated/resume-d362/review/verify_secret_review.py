from pathlib import Path
import sys,json,copy,hashlib
HERE=Path(__file__).parent;D=HERE.parent/'secrets';sys.path.insert(0,str(D))
import profile_reference as s
# Execute only fixture construction/function declarations before the author
# verifier's testing loop. No report writes or author tests run in this import.
source=(D/'verify_reference.py').read_text();prefix=source.split('for profile,value in fixtures.items():')[0];ns={};exec(compile(prefix,'readonly-secret-fixtures','exec'),ns)
full=ns['full'];consumer=ns['consumer'];now=ns['now'];checks=[]
def attempt(name,value,expected=None):
 try:s.parse_profile(value['variant'],json.dumps(value).encode());actual='ACCEPTED'
 except s.Rejected as exc:actual=exc.code
 except Exception as exc:actual=type(exc).__name__+':'+str(exc)
 checks.append({'id':name,'actual':actual,'expected':expected,'passed':actual==expected if expected else None})
attempt('full-browser-independent-positive',full,'ACCEPTED')
mut=copy.deepcopy(full);graph=mut['origins'][0]['indexedDB'][0]['objectStores'][0]['records'][0]['value'];graph['rootNodeId']='map';graph['nodes'].append({'id':'map','kind':'MAP','entries':[{'keyNodeId':'text','valueNodeId':'buf'},{'keyNodeId':'text','valueNodeId':'obj'}]})
attempt('duplicate-map-key-node',mut,'BROWSER_STATE_DUPLICATE_MAP_KEY')
mut=copy.deepcopy(full);graph=mut['origins'][0]['indexedDB'][0]['objectStores'][0]['records'][0]['value'];graph['rootNodeId']='set';graph['nodes'].append({'id':'set','kind':'SET','items':[{'nodeId':'text'},{'nodeId':'text'}]})
attempt('duplicate-set-node',mut,'BROWSER_STATE_DUPLICATE_SET_VALUE')
try:s.use_profile('UNSUPPORTED_PROFILE',json.dumps(full).encode(),consumer(full['variant']),now);actual='ACCEPTED'
except s.Rejected as exc:actual=exc.code
except Exception as exc:actual=type(exc).__name__
checks.append({'id':'unsupported-use-profile-structured-error','actual':actual,'expected':'SECRET_VARIANT_UNSUPPORTED','passed':actual=='SECRET_VARIANT_UNSUPPORTED'})
candidate={'type':'SESSION_STATE','profileId':full['variant'],'representation':'PROFILE_JSON_V1','bytes':json.dumps(full).encode()}
k=s.AESGCM.generate_key(bit_length=256);secret='aa4c859b-9bdc-4bf9-ab2c-543b3e61696f';version='27e7eed8-ef55-4a35-a2d2-bf6dad99adea';wrongversion='27e7eed8-ef55-4a35-a2d2-bf6dad99adeb'
r=s.store_reference(candidate,secret,version,k);checks.append({'id':'selected-exact-secret-version-positive','passed':s.load_reference(r,k,secret,version)==candidate['bytes']})
r2=s.store_reference(candidate,secret,wrongversion,k)
try:s.load_reference(r2,k,secret,version);actual='ACCEPTED'
except s.Rejected as exc:actual=exc.code
checks.append({'id':'substituted-valid-other-version','actual':actual,'expected':'SECRET_STORED_REFERENCE_MISMATCH','passed':actual=='SECRET_STORED_REFERENCE_MISMATCH'})
report={'scope':'Independent synthetic browser clone-graph and consumer dispatch mutants. Accepted cases identify current gaps, not PASS. No runtime browser/crypto acceptance.','checks':checks,'failed':sum(c['passed']is False for c in checks),'consumedSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in [D/'profile_reference.py',D/'verify_reference.py',D/'secret-profile-handoffs.schema.json']}}
(HERE/'secret-review-results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(checks),'failed':report['failed']}))
