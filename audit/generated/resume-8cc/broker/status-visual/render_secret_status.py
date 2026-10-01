from pathlib import Path
import functools,http.server,threading,json,hashlib,os
from urllib.parse import urlsplit,unquote
from playwright.sync_api import sync_playwright
O=Path(__file__).parent;ROOT=Path(os.environ.get('SECRET_REFERENCE_ROOT',str(O/'snapshot')));served={};checks=[];renders=[];external=[]
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  relative=unquote(urlsplit(self.path).path).lstrip('/');p=(ROOT/relative).resolve()
  if not p.is_relative_to(ROOT.resolve()) or not p.is_file():self.send_error(404);return
  raw=p.read_bytes();served.setdefault(relative,set()).add(hashlib.sha256(raw).hexdigest());self.send_response(200);self.send_header('Content-Type',self.guess_type(str(p)));self.end_headers();self.wfile.write(raw)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)));t=threading.Thread(target=server.serve_forever,daemon=True);t.start();origin='http://127.0.0.1:'+str(server.server_port)
def check(name,value):checks.append({'id':name,'status':'PASS'if value else'FAIL'})
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ['CHROMIUM_PATH'],headless=True)
 for viewport in ['390x844','768x1024','1366x768','1920x1080']:
  w,h=map(int,viewport.split('x'));page=browser.new_page(viewport={'width':w,'height':h},reduced_motion='reduce')
  def route(r):
   if r.request.url.startswith(origin+'/')or r.request.url.startswith('data:'):r.continue_()
   else:external.append(r.request.url);r.abort()
  page.route('**/*',route);page.goto(origin+'/03_UI_REFERENCE/pages/secrets.html',wait_until='networkidle')
  field=page.locator('[data-field="secret.status"]');root=field.locator('[data-record-status]');detail=page.locator('.cardhead').filter(has_text='Secret detail')
  check(viewport+'/exact-Stav-field',field.locator('label').inner_text()=='Stav');check(viewport+'/root-INACTIVE',root.inner_text()=='INACTIVE');check(viewport+'/server-readonly-projection',root.get_attribute('data-source')=='SERVER_PROJECTION'and root.get_attribute('data-readonly')=='true'and field.locator('input,textarea,select,[contenteditable="true"]').count()==0)
  selected=page.locator('tr[data-selected-root="true"]');head=page.locator('.statusrow')
  check(viewport+'/exact-selected-root-state-feed',all(x.get_attribute('data-secret-id')==root.get_attribute('data-secret-id')and x.get_attribute('data-record-state-version')==root.get_attribute('data-record-state-version')=='183' for x in [selected,head,detail]))
  check(viewport+'/CREATED-selected-version-not-active-pointer',detail.get_attribute('data-active-version-id')=='null'and root.get_attribute('data-active-version-id')=='null'and detail.locator('[data-version-lifecycle]').get_attribute('data-version-lifecycle')=='CREATED')
  check(viewport+'/selected-version-separated',detail.inner_text().endswith('vybraná v1 · CREATED'))
  detail.locator('.badge').evaluate("e=>e.textContent='vybraná v1 · ACTIVE'");check(viewport+'/no-lifecycle-inference',root.inner_text()=='INACTIVE');detail.locator('.badge').evaluate("e=>e.textContent='vybraná v1 · CREATED'")
  rows=page.locator('table.data tbody .status').all_inner_texts();check(viewport+'/root-table-vocabulary',set(rows)<=set(['INACTIVE','ACTIVE','DELETED']))
  value=page.locator('.field').filter(has=page.locator('label',has_text='Hodnota')).locator('.textarea').inner_text();check(viewport+'/no-plaintext-value-fixture',bool(value)and set(value)=={'•'})
  check(viewport+'/no-horizontal-overflow',not page.evaluate('document.documentElement.scrollWidth>innerWidth'))
  dest=O/'renders'/viewport/'secrets.png';dest.parent.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(dest),full_page=True);field.screenshot(path=str(dest.parent/'root-status-field.png'));renders.append({'viewport':viewport,'path':str(dest.relative_to(O)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'visualInspection':'PENDING'});page.close()
 version=browser.version;browser.close()
server.shutdown();server.server_close();t.join();check('only-local-assets',not external)
report={'sourceDocumentSha256':hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'servedInputDigests':{k:list(v)for k,v in served.items()},'candidateReferenceOnly':True,'servedCanonicalRepository':ROOT==Path('/workspace/kajovocmlng'),'checked':len(checks),'failed':sum(x['status']=='FAIL'for x in checks),'checks':checks,'renders':renders,'browserVersion':version,'noBackendRuntime':True,'manualReview':'PENDING','wholeUIClosed':False}
(O/'secret-dom-renders.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checks),'checks',report['failed'],'failures')
if report['failed']:raise SystemExit(1)
