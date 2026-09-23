import { createRequire } from 'node:module';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
const require=createRequire(import.meta.url);
const root=path.resolve(path.dirname(new URL(import.meta.url).pathname),'..');
const moduleRoot=process.env.PLAYWRIGHT_MODULE || (process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ? path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright') : 'playwright');
const {chromium}=require(moduleRoot);
const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{})});
let server;
let origin=process.env.REFERENCE_ORIGIN;
if(!origin){
 server=http.createServer(async(req,res)=>{try{let p=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://local').pathname));if(!p.startsWith(root+path.sep))throw Error('path');let data=await readFile(p);res.setHeader('Content-Type',({'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png'})[path.extname(p)]||'application/octet-stream');res.end(data)}catch(e){res.statusCode=404;res.end('Not found')}});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));origin='http://127.0.0.1:'+server.address().port;
}
const failures=[],results=[];
for(const [width,height] of [[390,844],[768,1024],[1366,768],[1920,1080]]){
 const page=await browser.newPage({viewport:{width,height},reducedMotion:'reduce'});
 page.on('pageerror',e=>failures.push(String(e)));
 for(const state of ['ready','progress','menu','detail','inputs','live','error','waiting','multi','stale','empty','specification']){
  const url=`${origin}/03_UI_REFERENCE/pages/${state==='specification'?'generation':'dashboard'}.html?state=${state}`;
  await page.goto(url);await page.waitForSelector('[data-ready="true"]');
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  if(overflow)failures.push(`horizontal overflow ${width} ${state}`);
  const dest=path.join(root,'04_UI_VIEWS',`${width}x${height}`,`workspace-${state}.png`);await mkdir(path.dirname(dest),{recursive:true});
  await page.screenshot({path:dest,fullPage:true});
  if(state==='ready')await page.screenshot({path:path.join(root,'04_UI_VIEWS',`${width}x${height}`,'dashboard.png'),fullPage:true});
  if(state==='specification')await page.screenshot({path:path.join(root,'04_UI_VIEWS',`${width}x${height}`,'generation.png'),fullPage:true});
  results.push({width,height,state,overflow,screenshot:path.relative(root,dest)});
 }
 // Meaningful reference interactions: menu, keyboard, typed tab, no fabricated backend mutation.
 await page.goto(`${origin}/03_UI_REFERENCE/pages/dashboard.html?state=ready`);await page.waitForSelector('[data-ready="true"]');
 await page.locator('#object-actions').click();await page.locator('#object-menu button').first().click();
 if(!await page.locator('dialog[open]').count())failures.push(`action binding dialog absent ${width}`);
 await page.keyboard.press('Escape');
 await page.locator('[data-tab="outputs"]').click();
 if(!await page.locator('#tab-body').innerText().then(s=>s.includes('Výstup')))failures.push(`output tab ${width}`);
 await page.close();
}
await browser.close();
if(server)await new Promise(resolve=>server.close(resolve));
await mkdir(path.join(root,'audit'),{recursive:true});
const sourceHashes={};for(const file of ['03_UI_REFERENCE/pages/dashboard.html','03_UI_REFERENCE/pages/generation.html','03_UI_REFERENCE/assets/workspace.css','03_UI_REFERENCE/assets/workspace.js','01_UI_CONTRACT/ui/contracts/ui-control-registry.json','01_UI_CONTRACT/closure/contracts/ui-action-resolution.json'])sourceHashes[file]=createHash('sha256').update(await readFile(path.join(root,file))).digest('hex');
await writeFile(path.join(root,'audit','visual-validation.json'),JSON.stringify({sourceHashes,status:failures.length?'FAIL':'PASS',browser:'Playwright Chromium reference renderer',claims:'Reference layout and interaction only; no production backend execution claimed',views:results.length,results,failures},null,2)+'\n');
console.log(JSON.stringify({views:results.length,failures}));if(failures.length)process.exitCode=1;
