from pathlib import Path
import sys,json,hashlib,copy
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
HERE=Path(__file__).parent;D=HERE.parent/'secrets';sys.path.insert(0,str(D))
import profile_reference as s
source=(D/'verify_reference.py').read_text().split('for profile,value in fixtures.items():')[0];ns={};exec(compile(source,'readonly synthetic fixtures','exec'),ns)
profile='TOTP_BASE32_V1';raw=s.compiled_schema_bytes(profile);document=json.loads(raw);value=copy.deepcopy(ns['fixtures'][profile]);validator=Draft202012Validator(document,format_checker=FormatChecker());cases=[]
def record(name,ok):cases.append({'id':name,'passed':bool(ok)})
Draft202012Validator.check_schema(document);record('compiled-document-is-2020-12-schema',True)
record('advertised-digest-is-actual-compiled-document-bytes',s.schema_digest(profile)==s.digest(raw))
record('selected-root-ref-is-exact-profile',document['$ref']=='#/$defs/'+profile)
validator.validate(value);record('actual-domain-positive-validates-through-compiled-root',True)
for name,edit in [('other-discriminator',lambda v:v.update(variant='OAUTH_CLIENT_SECRET_V1')),('missing-domain-seed',lambda v:v.pop('seedBase32'))]:
 v=copy.deepcopy(value);edit(v)
 try:validator.validate(v);ok=False
 except ValidationError as e:ok=e.validator=='const' if name=='other-discriminator' else e.validator=='required'
 record(name+'-specific-root-rejection',ok)
wrong=copy.deepcopy(document);wrong['$ref']='#/$defs/OAUTH_CLIENT_SECRET_V1';wrongraw=json.dumps(wrong,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();record('other-root-changes-exact-schema-digest',s.digest(wrongraw)!=s.schema_digest(profile))
report={'scope':'Independent exact compiled schema byte digest, Draft2020-12 meta validation, actual root/domain positive and specific constraint negatives. Not all profiles parser/use semantics or runtime crypto proof.','checks':len(cases),'failed':sum(not c['passed']for c in cases),'cases':cases,'compiledSchemaDigest':s.digest(raw),'consumed':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in [D/'profile_reference.py',D/'secret-profile-handoffs.schema.json',D/'verify_reference.py']}}
(HERE/'secret-compiled-schema-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(cases),'failed':report['failed']}))
