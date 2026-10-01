"""Render effective illustrative UI references using the pinned Python audit environment.

Integrate as scripts/render_reference.py. Reference layout/interaction only;
no production implementation or exhaustive manual visual acceptance claim.
"""
import functools,hashlib,http.server,importlib.metadata,json,os,re,shutil,sys,threading
from pathlib import Path

SCRIPT=Path(__file__).resolve()
ROOT=next((parent for parent in SCRIPT.parents if (parent/'00_SSOT/KajovoCMLNG_SSOT.md').is_file() and (parent/'scripts/ssot_sources.py').is_file()),None)
if ROOT is None:raise SystemExit('REPOSITORY_ROOT_UNAVAILABLE')
sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index,resources

ALIASES={'process':'progress','dashboard':'ready','dashboard-empty':'empty','dashboard-stale':'stale','context-menu':'menu','object-detail':'detail','inputs-outputs':'inputs','live-communication':'live','failure':'error','human-wait':'waiting','multi-component':'multi','specification':'specification'}

def sha(raw):return hashlib.sha256(raw).hexdigest()

def run():
    # Parent integration uses canonical package destinations. For an isolated
    # review run set REFERENCE_OUTPUT_ROOT to the review directory explicitly.
    output_root=Path(os.environ.get('REFERENCE_OUTPUT_ROOT',str(ROOT))).resolve()
    output_root.mkdir(parents=True,exist_ok=True)
    report_path=output_root/'audit/visual-validation.json'
    report_path.parent.mkdir(parents=True,exist_ok=True)
    requirements=ROOT/'requirements-audit.txt'
    packages={}
    environment_problems=[]
    for line in requirements.read_text().splitlines():
        match=re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s]+)',line.strip())
        if not match:continue
        package,expected=match.groups()
        try:actual=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:actual=None
        packages[package]={'expected':expected,'actual':actual}
        if actual!=expected:environment_problems.append(package+' expected '+expected+', actual '+str(actual))
    chromium=os.environ.get('CHROMIUM_PATH')
    if not chromium or not Path(chromium).is_file():environment_problems.append('CHROMIUM_PATH must name an available browser executable')
    environment={'pythonExecutable':sys.executable,'pythonVersion':sys.version.split()[0],'auditRequirementsSha256':sha(requirements.read_bytes()),'packages':packages,'chromiumExecutable':chromium}
    if environment_problems:
        result={'status':'BLOCKED','diagnostic':'AUDIT_ENVIRONMENT_UNAVAILABLE','reasons':environment_problems,'environment':environment,'claims':__doc__,'runtimeBackendTested':False}
        report_path.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result));return 2
    from playwright.sync_api import sync_playwright
    original_source=SSOT.read_bytes();source_digest=sha(original_source)
    embedded=resource_index(resources(original_source.decode('utf8')))
    live_path='ui/contracts/live-experience.json'
    live=json.loads(embedded[live_path]['raw'])
    contract_files=['requirements-audit.txt','01_UI_CONTRACT/ui/contracts/live-experience.json','01_UI_CONTRACT/ui/contracts/ui-control-registry.json','01_UI_CONTRACT/closure/contracts/ui-action-resolution.json']
    contracts={name:sha((ROOT/name).read_bytes()) for name in contract_files}
    initial_support={name:sha((ROOT/name).read_bytes()) for name in ['scripts/ssot_sources.py','scripts/render_reference.mjs'] if (ROOT/name).is_file()}
    original_script=sha(SCRIPT.read_bytes())
    checks=[];renders=[];aliases=[];browser_errors=[];missing_local_assets=[];loaded={};loaded_lock=threading.Lock()
    def check(name,actual,expected=True):checks.append({'case':name,'passed':actual==expected,'actual':actual,'expected':expected})
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            # The local-only server records actual served bytes, rather than
            # merely hashing unrelated files after screenshots have been made.
            from urllib.parse import urlsplit,unquote
            relative=unquote(urlsplit(self.path).path).lstrip('/')
            target=(ROOT/relative).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                if relative!='favicon.ico':missing_local_assets.append(relative)
                self.send_error(404);return
            raw=target.read_bytes()
            with loaded_lock:loaded.setdefault(target.relative_to(ROOT).as_posix(),set()).add(sha(raw))
            self.send_response(200);self.send_header('Content-Type',self.guess_type(str(target)));self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    origin='http://127.0.0.1:'+str(server.server_port)
    browser_version=None;fatal=None
    try:
        with sync_playwright() as playwright:
            try:browser=playwright.chromium.launch(executable_path=chromium,headless=True)
            except Exception as error:
                fatal={'diagnostic':'BROWSER_ENVIRONMENT_UNAVAILABLE','reason':str(error)}
                browser=None
            if browser is not None:
                browser_version=browser.version
                try:
                    for viewport in live['viewports']:
                        width,height=map(int,viewport.split('x'))
                        for locale in ['cs','en']:
                            page=browser.new_page(viewport={'width':width,'height':height},reduced_motion='reduce')
                            page.set_default_timeout(5000)
                            page.on('pageerror',lambda error:browser_errors.append(str(error)))
                            def route(request):
                                url=request.request.url
                                if url.startswith(origin+'/') or url.startswith('data:'):request.continue_()
                                else:browser_errors.append('UNEXPECTED_EXTERNAL_REQUEST:'+url);request.abort()
                            page.route('**/*',route)
                            for view in live['views']:
                                view_id=view['id'];stem='dashboard' if view_id=='dashboard' else 'live-'+view_id
                                stem+=('-en' if locale=='en' else '')
                                relative='03_UI_REFERENCE/pages/'+stem+'.html'
                                response=page.goto(origin+'/'+relative,wait_until='load')
                                page.wait_for_selector('body[data-demo="true"][data-view="'+view_id+'"][data-state="'+view['state']+'"]')
                                page.wait_for_function("typeof explain==='function' && typeof openMenu==='function'")
                                page.evaluate('document.fonts.ready')
                                label=locale+'/'+viewport+'/'+view_id
                                check(label+'/http',response.status,200)
                                check(label+'/locale',page.locator('html').get_attribute('lang'),locale)
                                check(label+'/demo',page.locator('body').get_attribute('data-demo'),'true')
                                check(label+'/view',page.locator('body').get_attribute('data-view'),view_id)
                                check(label+'/state',page.locator('body').get_attribute('data-state'),view['state'])
                                # No fake marker: readiness is actual contract identity +
                                # loaded script + working modal/menu event handlers.
                                overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')
                                check(label+'/horizontal-overflow',overflow,False)
                                help_button=page.locator('.heading .toolbar button').last
                                help_button.click();check(label+'/help-modal',page.locator('dialog').evaluate('node=>node.open'))
                                check(label+'/help-text',bool(page.locator('dialog p').inner_text().strip()))
                                page.keyboard.press('Escape');check(label+'/dialog-escape',page.locator('dialog').evaluate('node=>node.open'),False)
                                check(label+'/help-focus-return',help_button.evaluate('node=>node===document.activeElement'))
                                if view_id in ['dashboard','context-menu']:
                                    graph=page.locator('.graph');graph.focus();page.keyboard.press('Shift+F10')
                                    check(label+'/keyboard-menu',page.locator('.sample-menu').evaluate("node=>node.classList.contains('open')"))
                                    check(label+'/menu-expanded',page.locator('[data-menu]').get_attribute('aria-expanded'),'true')
                                    check(label+'/first-menu-focus',page.locator('.sample-menu button').first.evaluate('node=>node===document.activeElement'))
                                    page.keyboard.press('ArrowDown');check(label+'/next-menu-focus',page.locator('.sample-menu button').nth(1).evaluate('node=>node===document.activeElement'))
                                    page.keyboard.press('Escape');check(label+'/menu-escape',page.locator('.sample-menu').evaluate("node=>node.classList.contains('open')"),False)
                                    check(label+'/menu-focus-return',graph.evaluate('node=>node===document.activeElement'))
                                    page.locator('[data-menu]').click();page.locator('.sample-menu button').first.click()
                                    check(label+'/visible-menu-dialog',page.locator('dialog').evaluate('node=>node.open'))
                                    page.keyboard.press('Escape');page.keyboard.press('Escape')
                                scenario=ALIASES.get(view_id,view_id)
                                directory=output_root/'04_UI_VIEWS'/('en/'+viewport if locale=='en' else viewport)
                                directory.mkdir(parents=True,exist_ok=True)
                                target=directory/('workspace-'+scenario+('-en' if locale=='en' else '')+'.png')
                                page.screenshot(path=str(target),full_page=True)
                                item={'viewId':view_id,'state':view['state'],'legacyScenario':scenario,'locale':locale,'viewport':viewport,'width':width,'height':height,'source':relative,'overflow':overflow,'screenshot':target.relative_to(output_root).as_posix(),'screenshotSha256':sha(target.read_bytes()),'visualInspection':'PENDING'}
                                renders.append(item)
                                if view_id=='dashboard':
                                    copied=directory/('dashboard-en.png' if locale=='en' else 'dashboard.png');shutil.copyfile(target,copied)
                                    aliases.append({'sourceRender':item['screenshot'],'copy':copied.relative_to(output_root).as_posix(),'sha256':sha(copied.read_bytes())})
                            page.close()
                except Exception as error:fatal={'diagnostic':'REFERENCE_PRESENTATION_CHECK_FAILED','reason':str(error)}
                finally:browser.close()
    finally:server.shutdown();server.server_close()
    check('no-browser-or-external-request-errors',browser_errors,[])
    check('no-missing-required-local-assets',missing_local_assets,[])
    check('ssot-source-unchanged',sha(SSOT.read_bytes()),source_digest)
    check('renderer-source-unchanged',sha(SCRIPT.read_bytes()),original_script)
    check('audit-and-ui-contract-inputs-unchanged',{name:sha((ROOT/name).read_bytes()) for name in contract_files},contracts)
    check('support-inputs-unchanged',{name:sha((ROOT/name).read_bytes()) for name in initial_support},initial_support)
    source_hashes={**contracts,**initial_support,SCRIPT.relative_to(ROOT).as_posix():original_script}
    for name,digests in sorted(loaded.items()):
        check('loaded-source-one-version/'+name,len(digests),1)
        first=sorted(digests)[0];source_hashes[name]=first
        check('loaded-source-current-bytes/'+name,sha((ROOT/name).read_bytes()),first)
    planned=len(live['views'])*len(live['viewports'])*2
    check('complete-declared-reference-universe',len(renders),planned)
    failures=[item for item in checks if not item['passed']]
    report={'sourceDocumentSha256':source_digest,'sourceHashes':source_hashes,'embeddedResourceSha256':{name:embedded[name]['sha256'] for name in [live_path,'ui/contracts/ui-control-registry.json','closure/contracts/ui-action-resolution.json']},'scriptSha256':original_script,'environment':{**environment,'browserVersion':browser_version,'browserExecutableSha256':sha(Path(chromium).read_bytes())},'status':'BLOCKED' if fatal and fatal['diagnostic']=='BROWSER_ENVIRONMENT_UNAVAILABLE' else 'FAIL' if failures or fatal else 'PASS','claims':__doc__,'scope':'Effective declared illustrative reference views; presentation DOM/layout/interactions, not backend or all UI action semantics','views':len(renders),'results':renders,'derivativeScreenshotAliases':aliases,'checks':checks,'checked':len(checks),'failed':len(failures)+(1 if fatal else 0),'failures':failures+([fatal] if fatal else []),'visualInspection':'PENDING_INDIVIDUAL_REVIEW','runtimeBackendTested':False,'implementationProductionAcceptance':'NOT_EVALUATED','coverage':{'effectiveViews':len(live['views']),'viewports':len(live['viewports']),'locales':['cs','en'],'plannedRenders':planned,'actualRenders':len(renders),'legacyAdministrativeViewsIncluded':False},'fontEvidence':'Browser/system fallback fonts; no claim of canonical font-package verification'}
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ['sourceDocumentSha256','status','views','checked','failed','coverage']}))
    return 0 if report['status']=='PASS' else 2 if report['status']=='BLOCKED' else 1

if __name__=='__main__':
    try:exit_code=run()
    except Exception as error:
        result={'status':'BLOCKED','diagnostic':'UNEXPECTED_RENDERER_TOOL_EXCEPTION','exceptionType':type(error).__name__,'reason':str(error),'runtimeBackendTested':False,'claims':__doc__}
        output_root=Path(os.environ.get('REFERENCE_OUTPUT_ROOT',str(ROOT))).resolve();report_path=output_root/'audit/visual-validation.json';report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result));exit_code=1
    raise SystemExit(exit_code)
