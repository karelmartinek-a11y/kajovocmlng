"""Current twelve reference views: isolated Chromium presentation checks only."""
import functools,hashlib,http.server,json,threading,sys,importlib.metadata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
from playwright.sync_api import sync_playwright
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 rs=resource_index();live=json.loads(rs['ui/contracts/live-experience.json']['raw']);source_sha=hashlib.sha256(SSOT.read_bytes()).hexdigest();checks=[];renders=[];consumed=set();browser_errors=[]
 def check(name,actual,expected=True):checks.append({'case':name,'passed':actual==expected,'actual':actual,'expected':expected})
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();origin='http://127.0.0.1:'+str(server.server_port)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True);version=browser.version
   for viewport in live['viewports']:
    w,h=map(int,viewport.split('x'))
    for locale in ['cs','en']:
     page=browser.new_page(viewport={'width':w,'height':h},reduced_motion='reduce');page.set_default_timeout(5000)
     page.on('pageerror',lambda error:browser_errors.append(str(error)))
     def route(request):
      url=request.request.url
      if url.startswith(origin):
       rel=url[len(origin)+1:].split('?')[0];consumed.add(rel);request.continue_()
      elif url.startswith('data:'):request.continue_()
      else:browser_errors.append('UNEXPECTED_EXTERNAL_REQUEST:'+url);request.abort()
     page.route('**/*',route)
     for view in live['views']:
      vid=view['id'];stem='dashboard' if vid=='dashboard' else 'live-'+vid;stem+=('-en' if locale=='en' else '')
      relative='03_UI_REFERENCE/pages/'+stem+'.html';response=page.goto(origin+'/'+relative,wait_until='load');page.evaluate('document.fonts.ready');prefix=locale+'/'+viewport+'/'+vid
      check(prefix+'/http',response.status,200)
      check(prefix+'/current-view',page.locator('body').get_attribute('data-view'),vid);check(prefix+'/current-state',page.locator('body').get_attribute('data-state'),view['state']);check(prefix+'/demo-label',page.locator('body').get_attribute('data-demo'),'true')
      check(prefix+'/live-script-loaded',page.evaluate("typeof explain === 'function' && typeof openMenu === 'function'"))
      check(prefix+'/not-historical-data-ready',page.locator('[data-ready="true"]').count(),0)
      overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth');check(prefix+'/horizontal-overflow',overflow,False)
      button=page.locator('.heading .toolbar button').last;button.click();check(prefix+'/help-dialog',page.locator('dialog').evaluate('(el)=>el.open'));check(prefix+'/demo-explanation-present',bool(page.locator('dialog p').inner_text().strip()));page.keyboard.press('Escape');check(prefix+'/dialog-escape',page.locator('dialog').evaluate('(el)=>el.open'),False);check(prefix+'/dialog-focus-restored',button.evaluate('(el)=>document.activeElement===el'))
      if vid in ['dashboard','context-menu']:
       graph=page.locator('.graph');graph.focus();page.keyboard.press('Shift+F10');check(prefix+'/keyboard-menu',page.locator('.sample-menu').evaluate("el=>el.classList.contains('open')"));check(prefix+'/menu-expanded',page.locator('[data-menu]').get_attribute('aria-expanded'),'true');first=page.locator('.sample-menu button').first;check(prefix+'/menu-first-focus',first.evaluate('(el)=>document.activeElement===el'));page.keyboard.press('ArrowDown');check(prefix+'/menu-next-focus',page.locator('.sample-menu button').nth(1).evaluate('(el)=>document.activeElement===el'));page.keyboard.press('Escape');check(prefix+'/menu-escape',page.locator('.sample-menu').evaluate("el=>el.classList.contains('open')"),False);check(prefix+'/menu-focus-return',graph.evaluate('(el)=>document.activeElement===el'))
       page.locator('[data-menu]').click();page.locator('.sample-menu button').first.click();check(prefix+'/visible-menu-dialog',page.locator('dialog').evaluate('(el)=>el.open'));page.keyboard.press('Escape');page.keyboard.press('Escape')
      target=OUT/'renders'/locale/viewport/(vid+'.png');target.parent.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(target),full_page=True);renders.append({'view':vid,'locale':locale,'viewport':viewport,'source':relative,'screenshot':target.relative_to(ROOT).as_posix(),'visualInspection':'PENDING','runtimeBackendTested':False})
     page.close()
   browser.close()
 finally:server.shutdown();server.server_close()
 check('no-browser-or-external-request-errors',browser_errors,[]);check('input-source-unchanged',hashlib.sha256(SSOT.read_bytes()).hexdigest(),source_sha)
 consumed.update(['scripts/render_reference.mjs','01_UI_CONTRACT/ui/contracts/live-experience.json','01_UI_CONTRACT/ui/contracts/ui-control-registry.json','01_UI_CONTRACT/closure/contracts/ui-action-resolution.json'])
 hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(consumed) if (ROOT/p).is_file()}
 report={'sourceDocumentSha256':source_sha,'sourceHashes':hashes,'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':__doc__,'browser':'Chromium '+version,'executable':'/usr/bin/chromium','playwright':importlib.metadata.version('playwright'),'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL','checks':checks,'checked':len(checks),'failed':sum(not c['passed'] for c in checks),'renders':renders,'visualInspection':'PENDING_INDIVIDUAL_REVIEW','backendAcceptance':'NOT_EVALUATED','coverage':{'referenceViews':len(live['views']),'viewports':len(live['viewports']),'locales':2,'renderCount':len(renders),'legacyAdministrativeViewsIncluded':False}}
 (OUT/'current-reference-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['sourceDocumentSha256','status','checked','failed','coverage']}))
 return int(bool(report['failed']))
if __name__=='__main__':raise SystemExit(main())
