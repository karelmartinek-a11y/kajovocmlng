from pathlib import Path
import hashlib,json
from playwright.sync_api import sync_playwright
HERE=Path(__file__).parent;ROOT=HERE.parents[3];AUTHOR=ROOT/'audit/generated/resume-34d/secrets-browser';codec=(AUTHOR/'browser_clone.js').read_text();cases=[]
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=b.new_page();page.evaluate(codec);version=b.version
 for label,expr in [('dense-array','[null,undefined,3]'),('sparse-array','(()=>{let a=new Array(3);a[2]=3;return a})()'),('array-own-property','(()=>{let a=[1];a.syntheticExtra="retained";return a})()')]:
  r=page.evaluate('async()=>{const original='+expr+';const native=structuredClone(original),graph=await KCMLClone.encode(original),hydrated=KCMLClone.decode(graph);return{nativeOwnKeys:Object.keys(native),hydratedOwnKeys:Object.keys(hydrated),nativeLength:native.length,hydratedLength:hydrated.length,equal:Object.keys(native).join(",")===Object.keys(hydrated).join(",")&&native.length===hydrated.length,graph}}')
  cases.append({'case':label,'exactNativeCloneSemanticsPreserved':r['equal'],'nativeOwnKeys':r['nativeOwnKeys'],'hydratedOwnKeys':r['hydratedOwnKeys']})
 r=page.evaluate('async()=>{const buffer=new Uint8Array(500000).buffer;try{const graph=await KCMLClone.encode(buffer),value=KCMLClone.decode(graph);return {accepted:true,length:value.byteLength,encodedLength:graph.nodes[0].base64.length}}catch(e){return{accepted:false,diagnostic:e.name+": "+e.message}}}')
 cases.append({'case':'required-transport-sized-500k-buffer','exactNativeCloneSemanticsPreserved':r.get('accepted')and r.get('length')==500000,**r})
 b.close()
report={'sourceDocumentSha256':hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'codecSha256':hashlib.sha256(codec.encode()).hexdigest(),'browserVersion':version,'cases':cases,'scope':'ActualisolatedChromium native structuredClone versus authoredcodec forarray hole/ownproperty preservation; syntheticnonsensitive values, no fullbrowserpostconditionclaim','wholeOperationCertified':False}
(HERE/'browser-codec-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(cases))
