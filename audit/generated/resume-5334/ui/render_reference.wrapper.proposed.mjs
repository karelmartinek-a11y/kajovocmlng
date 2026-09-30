// Integrate as scripts/render_reference.mjs. Browser API belongs to the pinned
// Python audit environment; the unrelated Node Playwright package is not used.
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const python=process.env.AUDIT_PYTHON;
if(!python){
  console.error(JSON.stringify({status:'BLOCKED',diagnostic:'AUDIT_ENVIRONMENT_UNAVAILABLE',reason:'Set AUDIT_PYTHON to the interpreter prepared from requirements-audit.txt; no Node Playwright fallback is used.'}));
  process.exitCode=2;
}else{
  const script=fileURLToPath(new URL('./render_reference.py',import.meta.url));
  const result=spawnSync(python,[script,...process.argv.slice(2)],{stdio:'inherit',env:process.env,shell:false});
  if(result.error){console.error(JSON.stringify({status:'BLOCKED',diagnostic:'AUDIT_ENVIRONMENT_UNAVAILABLE',reason:String(result.error)}));process.exitCode=2;}
  else process.exitCode=result.status ?? 2;
}
