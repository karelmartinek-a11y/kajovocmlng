// Integration proposal: replace historical workspace-state renderer with effective live reference views.
import {createRequire} from 'node:module';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import {createHash} from 'node:crypto';
const require=createRequire(import.meta.url);
// When integrated this file lives in scripts/render_reference.mjs.
const root=path.resolve(path.dirname(new URL(import.meta.url).pathname),'..');
const moduleRoot=process.env.PLAYWRIGHT_MODULE||(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'):'playwright');
const {chromium}=require(moduleRoot);
const contractPath='01_UI_CONTRACT/ui/contracts/live-experience.json';
const live=JSON.parse(await readFile(path.join(root,contractPath),'utf8'));
const initialSource=await readFile(path.join(root,'00_SSOT/KajovoCMLNG_SSOT.md'));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const consumed=new Set([contractPath,'01_UI_CONTRACT/ui/contracts/ui-control-registry.json','01_UI_CONTRACT/closure/contracts/ui-action-resolution.json']);
const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{})});
let server;
let origin=process.env.REFERENCE_ORIGIN;
if(!origin){
 server=http.createServer(async(req,res)=>{try{const p=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://local').pathname));if(!p.startsWith(root+path.sep))throw Error('path');const data=await readFile(p);consumed.add(path.relative(root,p));res.setHeader('Content-Type',({'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png'})[path.extname(p)]||'application/octet-stream');res.end(data)}catch(error){res.statusCode=404;res.end('Not found')}});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));origin='http://127.0.0.1:'+server.address().port;
}
const alias={process:'progress',dashboard:'ready','dashboard-empty':'empty','dashboard-stale':'stale','context-menu':'menu','object-detail':'detail','inputs-outputs':'inputs','live-communication':'live',failure:'error','human-wait':'waiting','multi-component':'multi',specification:'specification'};
const failures=[],results=[];
try{
 for(const viewport of live.viewports){
  const [width,height]=viewport.split('x').map(Number);
  const page=await browser.newPage({viewport:{width,height},reducedMotion:'reduce'});page.setDefaultTimeout(5000);
  page.on('pageerror',error=>failures.push(String(error)));
  for(const view of live.views){
   const stem=view.id==='dashboard'?'dashboard':'live-'+view.id;
   const source=`03_UI_REFERENCE/pages/${stem}.html`;
   const response=await page.goto(`${origin}/${source}`,{waitUntil:'load'});
   if(response?.status()!==200)throw Error(`reference missing: ${source}`);
   // Static live.js references carry their explicit view/state/demo identity.
   // No historical query-state or synthetic data-ready injection is permitted.
   await page.waitForSelector(`body[data-demo="true"][data-view="${view.id}"][data-state="${view.state}"]`);
   await page.waitForFunction(()=>typeof explain==='function'&&typeof openMenu==='function');
   await page.evaluate(()=>document.fonts.ready);
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
   if(overflow)failures.push(`horizontal overflow ${viewport} ${view.id}`);
   const help=page.locator('.heading .toolbar button').last();await help.click();
   if(!await page.locator('dialog').evaluate(node=>node.open))failures.push(`help interaction ${viewport} ${view.id}`);
   await page.keyboard.press('Escape');
   const destination=path.join(root,'04_UI_VIEWS',viewport,`workspace-${alias[view.id]||view.id}.png`);await mkdir(path.dirname(destination),{recursive:true});await page.screenshot({path:destination,fullPage:true});
   // generation.png belongs to the administrative page renderer; do not replace
   // it with the distinct live specification panel.
   if(view.id==='dashboard')await page.screenshot({path:path.join(root,'04_UI_VIEWS',viewport,'dashboard.png'),fullPage:true});
   results.push({width,height,viewId:view.id,state:view.state,legacyScenario:alias[view.id]||null,source,overflow,screenshot:path.relative(root,destination),visualInspection:'PENDING'});
  }
  await page.goto(`${origin}/03_UI_REFERENCE/pages/dashboard.html`,{waitUntil:'load'});await page.waitForFunction(()=>typeof openMenu==='function');
  await page.locator('.graph').focus();await page.keyboard.press('Shift+F10');
  if(!await page.locator('.sample-menu').evaluate(node=>node.classList.contains('open')))failures.push(`keyboard menu ${viewport}`);
  await page.keyboard.press('ArrowDown');await page.keyboard.press('Escape');
  await page.locator('[data-menu]').click();await page.locator('.sample-menu button').first().click();
  if(!await page.locator('dialog').evaluate(node=>node.open))failures.push(`menu dialog ${viewport}`);
  await page.keyboard.press('Escape');await page.close();
 }
}finally{await browser.close();if(server)await new Promise(resolve=>server.close(resolve));}
if(sha(await readFile(path.join(root,'00_SSOT/KajovoCMLNG_SSOT.md')))!==sha(initialSource))failures.push('SOURCE_CHANGED_DURING_RENDER');
const sourceHashes={};for(const file of consumed)sourceHashes[file]=sha(await readFile(path.join(root,file)));
await writeFile(path.join(root,'audit','visual-validation.json'),JSON.stringify({sourceDocumentSha256:sha(initialSource),sourceHashes,status:failures.length?'FAIL':'PASS',browser:'Playwright Chromium current live reference renderer',claims:'Current illustrative reference presentation and interactions only; no backend, full UI action semantic closure, or production acceptance',views:results.length,results,failures},null,2)+'\n');
console.log(JSON.stringify({views:results.length,failures}));if(failures.length)process.exitCode=1;
