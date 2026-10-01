from pathlib import Path
import sys,json,hashlib
ROOT=Path('/workspace/kajovocmlng');HERE=Path(__file__).parent;AUTHOR=ROOT/'audit/generated/resume-8cc/key';sys.path.insert(0,str(AUTHOR))
program=(AUTHOR/'verify_manager_adapter.py').read_text().split('report={',1)[0]
program=program.replace('HERE=Path(__file__).parent;ROOT=HERE.parents[3]',"HERE=Path("+repr(str(AUTHOR))+");ROOT=Path('/workspace/kajovocmlng')")
ns={'__file__':str(AUTHOR/'verify_manager_adapter.py')};exec(compile(program,'independent-reproduction-manager-reference','exec'),ns)
assert all(c['passed']for c in ns['checks']),ns['checks']
r={'sourceDocumentSha256':hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'helperSha256':hashlib.sha256((AUTHOR/'systemd_key_authority.py').read_bytes()).hexdigest(),'referenceChecks':ns['checks'],'referencePass':len(ns['checks']),'providerStatus':'ENV_BLOCKED','scope':'Reproduced actual guarded parser/reference interface, explicitly patched manager and temporary key path; never actual provider attestation.'}
(HERE/'reproduced-manager-reference-proof.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'referencePASS':len(ns['checks']),'provider':'ENV_BLOCKED'}))
