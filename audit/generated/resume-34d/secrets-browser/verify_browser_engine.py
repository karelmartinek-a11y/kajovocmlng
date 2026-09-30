"""Actual isolated Chromium fixtures; no external account or Device Bridge authority."""
import base64,hashlib,http.server,json,threading,copy
from pathlib import Path
from playwright.sync_api import sync_playwright
from cryptography.hazmat.primitives import serialization,hashes
from cryptography.hazmat.primitives.asymmetric import ec
from profile_reference import validate,clone,Rejected
D=Path(__file__).resolve().parent;checks=[]
def check(id_,value):checks.append({'id':id_,'passed':bool(value)})
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  raw=b'<!doctype html><title>Isolated synthetic account fixture</title>'
  self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(raw)
 def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();origin='http://localhost:'+str(server.server_port)
codec=(D/'browser_clone.js').read_text()
try:
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  version=browser.version;c=browser.new_context();p=c.new_page();p.goto(origin);p.evaluate(codec)
  check('native-500000-byte-binary-below-transport-ceiling-no-stack-failure',p.evaluate("async()=>{const b=new Uint8Array(500000);b[499999]=255;const g=await KCMLClone.encode(b.buffer);const restored=new Uint8Array(KCMLClone.decode(g));return restored.length===500000&&restored[499999]===255&&g.nodes[0].base64.length<1048576}"))
  graph=p.evaluate("""async()=>{const b=new Uint8Array([0,1,2,255]).buffer,o={exact:' é\\n',n:-0,nan:NaN,big:12345678901234567890n,date:new Date(1735689600123),regex:/test/gi,blob:new Blob([' exact '],{type:'text/plain'}),file:new File([' f\\n'],'synthetic.txt',{type:'text/plain',lastModified:123}),view:new Uint16Array(b,0,2)};o.self=o;o.map=new Map([[o,'same object'],['primitive',b]]);o.set=new Set([o,NaN,-0]);return KCMLClone.encode(o)}""")
  validate('CloneGraph',graph);clone(graph,'/fixture');check('native-engine-graph-valid-closed-mask',True)
  sparse=p.evaluate("async()=>{const a=[];a[2]='exact';a.syntheticExtra='kept';return KCMLClone.encode(a)}")
  validate('CloneGraph',sparse);clone(sparse,'/fixture')
  check('native-sparse-array-and-extra-properties-preserved',p.evaluate("g=>{const a=KCMLClone.decode(g);return a.length===3&&Object.keys(a).join(',')==='2,syntheticExtra'&&a.syntheticExtra==='kept'&&!(0 in a)&&!(1 in a)}",sparse))
  got=p.evaluate("""async g=>{const o=KCMLClone.decode(g);return {self:o.self===o,negzero:Object.is(o.n,-0),nan:Number.isNaN(o.nan),big:o.big===12345678901234567890n,date:o.date.getTime()===1735689600123,map:o.map.get(o)==='same object',set:o.set.has(o)&&o.set.has(NaN),shared:o.map.get('primitive')===o.view.buffer,bytes:Array.from(new Uint8Array(o.view.buffer)).join(',')==='0,1,2,255',exact:o.exact===' é\\n',blob:await o.blob.text()===' exact ',file:await o.file.text()===' f\\n',regex:o.regex.source==='test'&&o.regex.flags==='gi'}}""",graph)
  for key,value in got.items():check('native-engine-clone-'+key,value)
  bad=copy.deepcopy(graph);next(n for n in bad['nodes']if n['kind']=='TYPED_ARRAY')['byteLength']=999
  try:clone(bad,'/fixture');check('invalid-buffer-range-rejected-exactly',False)
  except Rejected as e:check('invalid-buffer-range-rejected-exactly',e.code=='BROWSER_STATE_TYPED_ARRAY_RANGE_INVALID')
  check('unknown-engine-object-no-json-fallback',p.evaluate("""async()=>{try{await KCMLClone.encode(new URL('https://example.invalid'));return false}catch(e){return e.message==='BROWSER_STATE_SERIALIZER_UNSUPPORTED'}}"""))
  # Actual IDB object store/index definitions and exact clone value persistence.
  p.evaluate("""async g=>{await new Promise((resolve,reject)=>{let r=indexedDB.open('syntheticAuth',1);r.onupgradeneeded=()=>{const s=r.result.createObjectStore('tokens',{keyPath:'id',autoIncrement:true});s.createIndex('account','account',{unique:true})};r.onerror=()=>reject(r.error);r.onsuccess=()=>{const db=r.result,tx=db.transaction('tokens','readwrite');tx.objectStore('tokens').put({id:40,account:'SYNTHETIC',value:KCMLClone.decode(g)});tx.oncomplete=()=>{db.close();resolve()};tx.onerror=()=>reject(tx.error)}})}""",graph)
  capture=p.evaluate("""async()=>{const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('syntheticAuth');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)});const tx=db.transaction('tokens','readonly'),s=tx.objectStore('tokens');const rows=await new Promise((resolve,reject)=>{const r=s.getAll();r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)});const metadata={keyPath:s.keyPath,autoIncrement:s.autoIncrement,index:{name:s.index('account').name,keyPath:s.index('account').keyPath,unique:s.index('account').unique,multiEntry:s.index('account').multiEntry},graph:await KCMLClone.encode(rows[0])};db.close();return metadata}""")
  check('idb-native-store-and-unique-index-captured',capture['keyPath']=='id'and capture['autoIncrement']and capture['index']=={'name':'account','keyPath':'account','unique':True,'multiEntry':False})
  nextkey=p.evaluate("""async()=>{const db=await new Promise(resolve=>{const r=indexedDB.open('syntheticAuth');r.onsuccess=()=>resolve(r.result)});return await new Promise((resolve,reject)=>{const tx=db.transaction('tokens','readwrite');let key;const r=tx.objectStore('tokens').add({account:'TEMPORARY_GENERATOR_PROBE'});r.onsuccess=()=>{key=r.result;tx.abort()};tx.onabort=()=>{db.close();resolve(key)};r.onerror=()=>reject(r.error)})}""")
  check('idb-generator-probe-aborted-without-persisted-mutation',nextkey==41)
  p.evaluate("""()=>{localStorage.setItem('exact',' v\\n');sessionStorage.setItem('session',' exact ')}""")
  c.add_cookies([{'name':'synthetic','value':'EXACT%2B','url':origin,'httpOnly':True,'sameSite':'Lax'}]);cookies=c.cookies();check('native-cookie-captured-exact-value',cookies[0]['value']=='EXACT%2B')
  c.grant_permissions(['geolocation'],origin=origin);check('native-origin-permission-granted',p.evaluate("async()=> (await navigator.permissions.query({name:'geolocation'})).state")=='granted')
  fresh=browser.new_context();fresh.add_cookies(cookies);fresh.grant_permissions(['geolocation'],origin=origin)
  fresh.add_init_script("if(location.origin==="+json.dumps(origin)+"){localStorage.setItem('exact',' v\\n');sessionStorage.setItem('session',' exact ');globalThis.preBootstrapSession=sessionStorage.getItem('session')}")
  q=fresh.new_page();q.goto(origin);q.evaluate(codec)
  check('fresh-context-session-installed-before-bootstrap',q.evaluate("()=>preBootstrapSession===' exact '&&localStorage.getItem('exact')===' v\\n'"))
  check('fresh-context-cookie-and-permission',fresh.cookies()[0]['value']=='EXACT%2B'and q.evaluate("async()=> (await navigator.permissions.query({name:'geolocation'})).state")=='granted')
  q.evaluate("""async g=>{await new Promise((resolve,reject)=>{const r=indexedDB.open('syntheticAuth',1);r.onupgradeneeded=()=>{let s=r.result.createObjectStore('tokens',{keyPath:'id',autoIncrement:true});s.createIndex('account','account',{unique:true})};r.onerror=()=>reject(r.error);r.onsuccess=()=>{const db=r.result,tx=db.transaction('tokens','readwrite');tx.objectStore('tokens').put(KCMLClone.decode(g));tx.oncomplete=()=>{db.close();resolve()};tx.onerror=()=>reject(tx.error)}})}""",capture['graph'])
  result=q.evaluate("""async()=>{const db=await new Promise(resolve=>{const r=indexedDB.open('syntheticAuth');r.onsuccess=()=>resolve(r.result)});const tx=db.transaction('tokens','readwrite'),s=tx.objectStore('tokens');const key=await new Promise(resolve=>{const r=s.add({account:'SECOND'});r.onsuccess=()=>resolve(r.result)});const v=await new Promise(resolve=>{const r=s.get(40);r.onsuccess=()=>resolve(r.result)});db.close();return {key,cycle:v.value.self===v.value,exact:v.value.exact===' é\\n'}}""")
  check('idb-native-restore-graph-and-generator',result=={'key':41,'cycle':True,'exact':True})
  unique=q.evaluate("""async()=>{const db=await new Promise(resolve=>{const r=indexedDB.open('syntheticAuth');r.onsuccess=()=>resolve(r.result)});return await new Promise(resolve=>{const tx=db.transaction('tokens','readwrite'),r=tx.objectStore('tokens').add({account:'SYNTHETIC'});r.onerror=()=>{resolve(r.error.name==='ConstraintError');db.close()};r.onsuccess=()=>{resolve(false);db.close()}})}""")
  check('actual-idb-unique-index-specific-negative',unique)
  # Actual virtual automation authenticator signs; independent Python verifies
  # signature, challenge/origin and RP binding. No real platform passkey export.
  private=ec.generate_private_key(ec.SECP256R1());der=private.private_bytes(serialization.Encoding.DER,serialization.PrivateFormat.PKCS8,serialization.NoEncryption());credential=b'SYNTHETIC_AUTOMATION_CREDENTIAL';challenge=b'SYNTHETIC_CHALLENGE_32_BYTES_EXACT'
  session=fresh.new_cdp_session(q);session.send('WebAuthn.enable');aid=session.send('WebAuthn.addVirtualAuthenticator',{'options':{'protocol':'ctap2','transport':'usb','hasResidentKey':True,'hasUserVerification':True,'isUserVerified':True,'automaticPresenceSimulation':True}})['authenticatorId']
  session.send('WebAuthn.addCredential',{'authenticatorId':aid,'credential':{'credentialId':base64.b64encode(credential).decode(),'isResidentCredential':False,'rpId':'localhost','privateKey':base64.b64encode(der).decode(),'userHandle':base64.b64encode(b'SYNTHETIC').decode(),'signCount':0}})
  assertion=q.evaluate("""async arg=>{const bytes=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0)),b64=b=>btoa(String.fromCharCode(...new Uint8Array(b)));const c=await navigator.credentials.get({publicKey:{challenge:bytes(arg.challenge),rpId:'localhost',allowCredentials:[{type:'public-key',id:bytes(arg.id)}],userVerification:'required',timeout:5000}});return {auth:b64(c.response.authenticatorData),client:b64(c.response.clientDataJSON),signature:b64(c.response.signature)}}""",{'challenge':base64.b64encode(challenge).decode(),'id':base64.b64encode(credential).decode()})
  auth=base64.b64decode(assertion['auth']);client=base64.b64decode(assertion['client']);signature=base64.b64decode(assertion['signature']);private.public_key().verify(signature,auth+hashlib.sha256(client).digest(),ec.ECDSA(hashes.SHA256()));cd=json.loads(client)
  check('virtual-webauthn-real-assertion-signature-rp-origin-challenge',auth[:32]==hashlib.sha256(b'localhost').digest()and cd['origin']==origin and base64.urlsafe_b64decode(cd['challenge']+'='*((-len(cd['challenge']))%4))==challenge and auth[32]&5==5)
  try:private.public_key().verify(signature,auth+hashlib.sha256(client+b'X').digest(),ec.ECDSA(hashes.SHA256()));check('virtual-webauthn-tampered-signed-client-data',False)
  except __import__('cryptography.exceptions',fromlist=['InvalidSignature']).InvalidSignature:check('virtual-webauthn-tampered-signed-client-data',True)
  c.close();fresh.close();browser.close()
finally:server.shutdown()
report={'input':json.loads((D/'input-source.json').read_text()),'browserVersion':version,'checked':len(checks),'failed':sum(not x['passed']for x in checks),'checks':checks,'supportSha256':{n:hashlib.sha256((D/n).read_bytes()).hexdigest()for n in ['verify_browser_engine.py','browser_clone.js','profile_reference.py','secret-profile-handoffs.schema.json']},'sensitiveValuesInReport':False,'mandatoryUnverified':['Exact OWNER Device Bridge certificate binding resolution','Encrypted immutable bundle signing/storage/epoch-CAS integration','Partitioned-cookie exact context capture/restore fixture','Authenticated external account/tenant adapter postcondition','All indexedDB key/value variants and exhausted key generator'],'activation':'FULL_PROFILE_NOT_ACTIVATED','runtimeAcceptance':'NOT_EVALUATED'}
(D/'browser-engine-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checked':report['checked'],'failed':report['failed']}));raise SystemExit(bool(report['failed']))
