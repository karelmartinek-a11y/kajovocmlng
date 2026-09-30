from pathlib import Path
import sys,json,copy,hashlib
HERE=Path(__file__).parent;D=HERE.parent/'secrets';sys.path.insert(0,str(D))
import profile_reference as s
source=(D/'verify_reference.py').read_text();prefix=source.split('for profile,value in fixtures.items():')[0];ns={};exec(compile(prefix,'readonly-secret-fixtures','exec'),ns)
v=copy.deepcopy(ns['fixtures']['TOTP_BASE32_V1']);v['periodSeconds']=30
a=json.dumps(v,separators=(',',':')).encode();v['periodSeconds']=30.0;b=json.dumps(v,indent=2).encode()
c=lambda raw:{'type':'TOTP_SEED','representation':'PROFILE_JSON_V1','profileId':'TOTP_BASE32_V1','bytes':raw}
cases=[]
for label,raw in [('integer',a),('integral-json-float',b)]:
 try:s.parse_profile('TOTP_BASE32_V1',raw);actual='ACCEPTED'
 except s.Rejected as e:actual=e.code
 cases.append({'id':label+'-same-domain-positive','actual':actual,'passed':actual=='ACCEPTED'})
cases.append({'id':'same-integer-domain-value-canonical-digest','passed':s.canonical_value_digest(c(a))==s.canonical_value_digest(c(b)),'interpretation':'Original lexical bytes differ and must remain separately preserved; canonical typed integer value is the same.'})
cases.append({'id':'byte-digest-preserves-lexical-distinction','passed':s.digest(a)!=s.digest(b)})
raw={'type':'PASSWORD','representation':'RAW_UTF8','profileId':None,'bytes':b' SYNTHETIC '};other={**raw,'type':'API_KEY'}
cases.append({'id':'type-domain-separation','passed':s.canonical_value_digest(raw)!=s.canonical_value_digest(other)})
report={'scope':'Independent import-byte versus typed semantic digest checks. Synthetic values/digests are not emitted.','cases':cases,'failed':sum(not c['passed']for c in cases),'helperSha256':hashlib.sha256((D/'profile_reference.py').read_bytes()).hexdigest()}
(HERE/'secret-digest-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(cases),'failed':report['failed']}))
