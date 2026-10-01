from pathlib import Path
import json,hashlib
ROOT=Path('/workspace/kajovocmlng');O=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=sha(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md');live=json.loads((O/'live-render/audit/visual-validation.json').read_text());dom=json.loads((O/'secret-dom-renders.json').read_text());mismatch=[]
for path,d in live['sourceHashes'].items():
 if not(ROOT/path).is_file()or sha(ROOT/path)!=d:mismatch.append(path)
for path,d in dom['servedInputDigests'].items():
 if len(d)!=1 or sha(ROOT/path)!=d[0]:mismatch.append(path)
assert not mismatch,mismatch
assert source==live['sourceDocumentSha256']==dom['sourceDocumentSha256'],'SOURCE_CHANGED'
assert sha(O/'secrets.html')==sha(ROOT/'03_UI_REFERENCE/pages/secrets.html')
for result in dom['renders']:
 p=O/result['path'];assert sha(p)==result['sha256'];field=p.parent/'root-status-field.png';result['statusFieldScreenshot']={'path':str(field.relative_to(O)),'sha256':sha(field)}
(O/'secret-dom-renders.json').write_text(json.dumps(dom,indent=2)+'\n')
old=json.loads((ROOT/'audit/generated/reference-package-renders.json').read_text());unchanged=[x for x in old['checks']if x['source']!='03_UI_REFERENCE/pages/secrets.html']
receipt={'status':'PASS_ACTUAL_CURRENT_SELECTED_INPUTS','currentSourceSha256':source,'executionSourceSha256':live['sourceDocumentSha256'],'liveActualRenders':96,'liveChecks':live['checked'],'secretActualRenders':4,'secretDOMChecks':dom['checked'],'sourceInputsByteEqualCanonical':True,'canonicalSecretPageActuallyServed':dom['servedCanonicalRepository'],'reports':['live-render/audit/visual-validation.json','secret-dom-renders.json'],'oldAdminRemaining':{'status':'HISTORICAL_UNBOUND','count':len(unchanged),'originalExecutionSourceSha256':old['sourceDocumentSha256'],'originalReportSha256':sha(ROOT/'audit/generated/reference-package-renders.json'),'newExecution':False,'reason':'Old admin package report does not bind each served HTML/asset digest; do not promote124 historical renders to current PASS.'},'manualAcceptance':'PENDING_FULL_VISUAL_UNIVERSE','implementationAcceptance':'NOT_EVALUATED','wholeUIClosed':False}
(O/'current-input-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
manual={'status':'LIMITED_REFERENCE_SEMANTICS_REVIEW','scope':'Four actual Secret readonly status field crops plus desktop root/detail framing; not all live/admin visual acceptance','reviewedFiles':[{'path':r['statusFieldScreenshot']['path'],'sha256':r['statusFieldScreenshot']['sha256']}for r in dom['renders']],'findings':['Stav is readable and bounded without clipping at four declared viewports','Root INACTIVE and selected immutable v1 CREATED are visibly distinguished','Readonly server-derived status field has no editable control; root status not permission','No Secret plaintext fixture visible; original value field remains bullets'],'independentRootReview':'Coordinator reproduced selected-row/stateVersion183 identity counterexample before fix; final candidate reviewed and copied byteexact','fullManualGate':'PENDING','backendAcceptance':'NOT_EVALUATED'}
(O/'manual-scoped-review.json').write_text(json.dumps(manual,indent=2)+'\n')
print('current96live +4Secret proof;124historical unbound preserved')
