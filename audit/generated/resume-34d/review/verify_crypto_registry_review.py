from pathlib import Path
import sys,hashlib,json
HERE=Path(__file__).parent;ROOT=HERE.parents[3];AUTHOR=ROOT/'audit/generated/resume-34d/auth-crypto';sys.path.insert(0,str(AUTHOR));sys.path.insert(0,str(ROOT/'scripts'))
p=AUTHOR/'verify_crypto_registry.py';original=p.read_text();program=original.replace("database='auth_crypto_nonce_34d'","database='review_crypto_nonce_34d'").replace('from auth_crypto_reference import *','from generation_auth_crypto import *').replace("(HERE/'crypto-registry-proof.json').write_text","(review_out/'crypto-registry-review.json').write_text")
needle='report={'
addition='''
for field in ['purpose','keyId']:
 value=json.loads(metadata);del value[field];mutated=canonical(value)
 query=profile+master+reservation.replace(b(metadata),b(mutated)).replace(b(sha(metadata)),b(sha(mutated)))
 # Preserve true current valid positive, change only missing linked metadata key;
 # currentSQL expected to reject required identity, but initialcode may accept.
 db.query('BEGIN')
 try:db.query(query);passed=False;actual='ACCEPTED_INVALID_LINKED_METADATA'
 except Exception as ex:
  actual=str(ex);expected='canonical_crypto_nonce_purpose_binding'if field=='purpose'else'canonical_crypto_nonce_key_binding';passed=expected in actual
 finally:db.query('ROLLBACK')
 checks.append({'case':'independent-missing-linked-metadata-'+field,'passed':passed,'actualDiagnostic':actual})
'''
assert program.count(needle)==1;program=program.replace(needle,addition+needle)
ns={'__file__':str(p),'review_out':HERE};exec(compile(program,str(p),'exec'),ns)
r=json.loads((HERE/'crypto-registry-review.json').read_text());r.update(independentDatabase='review_crypto_nonce_34d',executedProgramSha256=hashlib.sha256(program.encode()).hexdigest(),originalProgramSha256=hashlib.sha256(original.encode()).hexdigest(),rootImplementationSha256=hashlib.sha256((ROOT/'scripts/generation_auth_crypto.py').read_bytes()).hexdigest())
(HERE/'crypto-registry-review.json').write_text(json.dumps(r,indent=2)+'\n')
