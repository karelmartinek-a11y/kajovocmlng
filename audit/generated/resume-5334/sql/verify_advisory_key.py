"""Isolated51.8 SQL syntax+cross-language reference proof; noPostgreSQL execution."""
import hashlib,json,subprocess
from pathlib import Path
import pglast
OUT=Path(__file__).resolve().parent
sql=(OUT/'postgres-advisory-key-proposed.sql').read_text()
pglast.parse_sql(sql);pglast.parse_plpgsql(sql)
# Network-order boundaries cover unsigned values and their signed int4 bitpatterns.
heads=['00000000','00000001','00000100','00010000','01000000','7fffffff','80000000','80000001','ffffffff']
vectors=[]
for prefix in heads:
 raw=bytes.fromhex(prefix)+bytes(range(4,32));expected=int.from_bytes(raw[:4],'big',signed=True)
 vectors.append({'digestHex':raw.hex(),'expectedSignedKey':expected})
# Node's signed big-endian reader is an independent language/library projection.
program='const rows=JSON.parse(process.argv[1]); process.stdout.write(JSON.stringify(rows.map(r=>Buffer.from(r.digestHex,"hex").readInt32BE(0))));'
actual=json.loads(subprocess.check_output(['node','-e',program,json.dumps(vectors)]))
checks=[{'id':'sql.postgresql17-outer-and-plpgsql-parser','status':'PASS','runtime':'NOT_RUN'}]
for i,(v,a) in enumerate(zip(vectors,actual)):
 checks.append({'id':'network-int4/'+v['digestHex'][:8],'status':'PASS' if a==v['expectedSignedKey'] else 'FAIL','expected':v['expectedSignedKey'],'pythonSignedBigEndian':v['expectedSignedKey'],'nodeSignedBigEndian':a})
# A valid32-byte witness precedes the two deliberate invaliddigest variants.
positive=bytes.fromhex(vectors[0]['digestHex'])
def decode(raw):
 if not isinstance(raw,bytes) or len(raw)!=32:raise ValueError('ADVISORY_KEY_REQUIRES_SHA256_DIGEST')
 return int.from_bytes(raw[:4],'big',signed=True)
assert decode(positive)==0
for identity,invalid in [('null',None),('wrong-byte-length',positive[:-1])]:
 try:decode(invalid);rejected=False
 except ValueError as exc:rejected=str(exc)=='ADVISORY_KEY_REQUIRES_SHA256_DIGEST'
 checks.append({'id':'negative/'+identity,'positiveWitnessValid':True,'specificDiagnosticRejected':rejected,'status':'PASS' if rejected else 'FAIL'})
# Two algorithmmutants produce incorrect keys from valid witnesses, not exceptions.
for identity,mutant in [('little-endian',lambda raw:int.from_bytes(raw[:4],'little',signed=True)),('unsigned-overflow',lambda raw:int.from_bytes(raw[:4],'big',signed=False))]:
 witnesses=[v for v in vectors if mutant(bytes.fromhex(v['digestHex']))!=v['expectedSignedKey']]
 checks.append({'id':'negative/'+identity,'validPositiveVectorCount':len(vectors),'counterexampleCount':len(witnesses),'status':'PASS' if witnesses else 'FAIL'})
report={'sourceAuthority':'SSOT51.8','sqlSha256':hashlib.sha256(sql.encode()).hexdigest(),'vectors':vectors,'checks':checks,'checked':len(checks),'failed':sum(c['status']!='PASS' for c in checks),'proofScope':'PostgreSQL17 outer+PLpgSQL AST parse and independent Python/Node reference vectors only. SQLfunction execution is NOT_RUN. Namespace0 singleton, digest-derived signedkey and fullrowunique digest obligations remain distinct.','implementationProductionAcceptance':'NOT_EVALUATED'}
(OUT/'advisory-key-proof.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['checked','failed','proofScope']}))
