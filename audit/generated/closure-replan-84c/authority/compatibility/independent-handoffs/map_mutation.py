from pathlib import Path
import sys,json,os,importlib,hashlib
ROOT=Path('/workspace/kajovocmlng');OWN=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT
m=importlib.import_module('verify_producer_archive_handoffs');mapfile=ROOT/m.PROOF_MAPPING;out=OWN/'malformed-map-after-import';os.environ['KCML_AUDIT_OUTPUT']=str(out)
oldtext=Path.read_text;oldbytes=Path.read_bytes
Path.read_text=lambda self,*a,**kw:'[]'if self==mapfile else oldtext(self,*a,**kw)
Path.read_bytes=lambda self:b'[]'if self==mapfile else oldbytes(self)
try:code=m.main()
finally:Path.read_text=oldtext;Path.read_bytes=oldbytes
q=json.loads((out/'producer-archive-chain-tests.json').read_text());matched=next(e for e in q['evidence']if e['path']==m.PROOF_MAPPING);assert matched['sha256']==hashlib.sha256(b'[]').hexdigest()
(OWN/'mapping-toctou-review.json').write_text(json.dumps({'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'actualExit':code,'actualStatus':q['status'],'actualMapDigestRecorded':matched['sha256'],'malformedMapShape':'[]','failedInvariant':code==0,'scope':'Valid current map at import; independently substituted actual mapping reads thereafter in this process only, no shared mutation. A digest is not a shape/coverage check.'},indent=2)+'\n');print(code,q['status'])
