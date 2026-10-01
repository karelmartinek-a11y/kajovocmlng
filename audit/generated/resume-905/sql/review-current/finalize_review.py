"""Bind independently reproduced fixture outputs to exact current consumed bytes."""
from pathlib import Path
import sys,hashlib,json
ROOT=Path('/workspace/kajovocmlng');HERE=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
rs=resource_index();source=hashlib.sha256(SSOT.read_bytes()).hexdigest();assert source=='4ac6fe00df084e910a90093485b12172866be73db94f66b6815200556c35be06'
proofs={}
for name in ['authenticated-chain-review.json','crypto-registry-review.json','retry-review.json','preroot-initial-review.json']:
 r=json.loads((HERE/name).read_text());assert r['sourceDocumentSha256']==source
 if name.startswith('authenticated'):assert r['failed']==0 and r['checked']==14
 elif name.startswith('crypto'):assert r['failed']==0 and r['checked']==13 and r['proposalRegistrySha256']==rs['database/canonical-crypto-registry.sql']['sha256']
 elif name.startswith('retry'):assert all(c['passed']for c in r['cases'])and r['extensionSqlSha256']==rs['database/generation-locked-retry.sql']['sha256']
 else:assert r['cases'][0]['accepted']and all(not c['accepted']and'GENERATION_PREROOT_NATIVE_OUTCOME_INVALID'in c['diagnostic']for c in r['cases'][1:])and r['extensionSqlSha256']==rs['database/generation-create-preroot.sql']['sha256']
 proofs[name]={'sha256':hashlib.sha256((HERE/name).read_bytes()).hexdigest(),'checked':r.get('checked',len(r.get('cases',[]))),'status':'PASS'}
record=dict(sourceDocumentSha256=source,proofs=proofs,consumedResourceSha256={p:rs[p]['sha256']for p in ['database/generation-create-foundations.sql','database/generation-create-authentication.sql','database/generation-create-read.sql','database/generation-create-preroot.sql','database/generation-locked-retry.sql','database/canonical-crypto-registry.sql']},rootHelpers={p:hashlib.sha256((ROOT/'scripts'/p).read_bytes()).hexdigest()for p in ['generation_auth_crypto.py','generation_auth_acceptance.py','generation_read_hydration.py','generation_create_consumer.py','generation_locked_retry.py']},limits=['14-check retained auth/read fixture executes real synthetic OWNER API verifier and actual canonical AES opening; key bytes isolated synthetic, not systemd encrypted credential source. It uses bounded current-schema reader, not complete frozen archive/kind policy pipeline.','13-check global nonce registry executes exact embedded SQL; uniqueness/immutable registry only, no complete physical protected-row producer identity/systemd authority.','5-check locked-scan reproduction uses root generation_locked_retry and exact embedded SQL; child persistence covered separately by33 producer-child tests, full49.8 remains OPEN.','4-check pre-root response negatives use synthetic server acceptance and opaque snapshot; exact finite native error rejection, not auth/crypto/complete pending-decision producer.'],wholeOperationClosed=False,implementationProductionAcceptance='NOT_EVALUATED')
(HERE/'current-review-source-bindings.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(proofs))
