"""Whole-tree structural verification and fail-closed semantic freeze gate.
Default checks source/schema/integrity. --freeze additionally rejects every unresolved
semantic finding. No audit status can be inferred from historical literal PASS fields.
"""
from pathlib import Path
import argparse,ast,csv,hashlib,json,re,subprocess,sys
from collections import defaultdict
from jsonschema import Draft202012Validator
from ssot_resources import ROOT,SSOT,resources,capsule
from verify_visual_contracts import verify as verify_visual

def strict_json(raw):
 def pairs(items):
  d={}
  for k,v in items:
   if k in d:raise ValueError('duplicate JSON key '+k)
   d[k]=v
  return d
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
def files():
 return sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(x in {'.git','.cache','__pycache__','node_modules'} for x in p.relative_to(ROOT).parts))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check_manifest():
 p=ROOT/'FILE_MANIFEST_SHA256';problems=[]
 if not p.exists():return ['missing FILE_MANIFEST_SHA256']
 listed={}
 for line in p.read_text().splitlines():
  digest,name=line.split('  ',1);listed[name]=digest
 actual={str(p.relative_to(ROOT)):sha(p) for p in files() if p.name!='FILE_MANIFEST_SHA256'}
 for n in sorted(set(listed)|set(actual)):
  if listed.get(n)!=actual.get(n):problems.append('file integrity: '+n)
 return problems

def audit():
 structural=[];findings=[];stats={};archival=[];entries=list(resources());by={(r['family'],r['path']):r for r in entries}
 check=lambda ok,msg:structural.append(msg) if not ok else None
 check(len(by)==len(entries),'duplicate embedded identity')
 for r in entries:
  a=r['attrs'];check(not a.get('sha256') or a['sha256']==r['sha256'],r['family']+':'+r['path']+' digest')
  check(not a.get('bytes') or int(a['bytes'])==len(r['raw']),r['family']+':'+r['path']+' byte length')
  if r['path'].endswith('.json'):
   try:strict_json(r['raw'])
   except Exception as e:structural.append(r['path']+': '+str(e))
  if r['path'].endswith('.py'):
   try:ast.parse(r['raw'].decode())
   except Exception as e:
    if a.get('authority')=='AUDIT_ONLY':archival.append({'resource':r['path'],'syntaxError':str(e),'authority':'AUDIT_ONLY','executed':False})
    else:structural.append(r['path']+': '+str(e))
 for p in files():
  if p.suffix=='.json':
   try:
    d=strict_json(p.read_bytes())
    if isinstance(d,dict) and '$schema' in d:Draft202012Validator.check_schema(d)
   except Exception as e:structural.append(str(p.relative_to(ROOT))+': '+str(e))
  if p.suffix=='.py':
   try:ast.parse(p.read_text())
   except Exception as e:structural.append(str(p.relative_to(ROOT))+': '+str(e))
 for family in ['UI','CLOSURE']:
  for r in entries:
   if r['family']=='KCML-'+family+'-RESOURCE':
    p=ROOT/'01_UI_CONTRACT'/r['path'];check(p.exists() and p.read_bytes()==r['raw'],'embedded/physical drift '+r['path'])
 cap=capsule();stats['embeddedResources']=len(entries);stats['capsuleResources']=len(cap);stats['repositoryFiles']=len(files())
 # Audit every route rather than trusting a declared count or additionalProperties flag.
 payload=json.loads(by[('KCML-R9-RESOURCE','contracts/payload-contracts.json')]['raw']);untyped=[]
 def has_opaque(value):
  if isinstance(value,dict):
   if 'canonicalJson' in value.get('properties',{}):return True
   return any(has_opaque(v) for v in value.values())
  return isinstance(value,list) and any(has_opaque(x) for x in value)
 for rec in payload['records']:
  if has_opaque(rec['requestSchema']):untyped.append(rec['routeId'])
 if untyped:findings.append({'id':'F-PAYLOAD','severity':'BLOCKER','count':len(untyped),'subject':'embedded R9 contracts/payload-contracts.json','finding':'Business payloads are requirementId/canonicalJson bags; closed envelopes do not type individual domain fields.','evidence':untyped,'requiredClosure':'Concrete domain input/output fields, constraints and positive/negative examples for each route; exact command/query profile bindings.'})
 errors=json.loads((ROOT/'01_UI_CONTRACT/ui/contracts/error-message-registry.json').read_text());incomplete=[r['error_code'] for r in errors['records'] if r['technical_condition']['predicateStatus']!='EXPLICIT' or r.get('presentationCompleteness')]
 if incomplete:findings.append({'id':'F-ERROR','severity':'BLOCKER','count':len(incomplete),'subject':'01_UI_CONTRACT/ui/contracts/error-message-registry.json','finding':'Inherited codes have class-level messages and unmaterialized domain predicates/retry bindings.','evidence':incomplete,'requiredClosure':'Review and define code-specific producer predicate, bilingual text and exact recovery binding; retain original semantics.'})
 text=SSOT.read_text();prose=text
 for r in reversed(entries):a,b=r['span'];prose=prose[:a]+'[RESOURCE]'+prose[b:]
 history=[(i,line[:220]) for i,line in enumerate(prose.splitlines(),1) if re.search(r'(?i)(předchozí verz|původn|opraven|doplněn|rozsah změn|výsledek revize|aktuální dodatek|stav po kapitola|nově přid|historick)',line)]
 if history:findings.append({'id':'F-PRVOPIS','severity':'BLOCKER','count':len(history),'subject':'00_SSOT/KajovoCMLNG_SSOT.md','finding':'Normative prose still contains provenance/precedence layers; lossless semantic consolidation is not complete.','evidence':history[:60],'requiredClosure':'Consolidate every overlapping norm, migrate historical explanation out of normative prose, prove no requirement lost with full traceability.'})
 # Schema IDs must be unambiguous under explicit resource identity; flag differing bodies.
 ids=defaultdict(list)
 for r in entries:
  if not r['path'].endswith('.json'):continue
  d=json.loads(r['raw'])
  if isinstance(d,dict) and '$id' in d:ids[d['$id']].append((r['family'],r['path'],hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()))
 conflicts={k:v for k,v in ids.items() if len({x[2] for x in v})>1}
 if conflicts:findings.append({'id':'F-SCHEMA-AUTHORITY','severity':'BLOCKER','count':len(conflicts),'subject':'embedded schema $id registry','finding':'The same schema identifier occurs with different schema bodies.','evidence':conflicts,'requiredClosure':'One canonical body per schema ID, explicit versioned replacement and all exact references updated.'})
 # Check the requested process-family universe exactly.
 families=json.loads(by[('KCML-R16-RESOURCE','r16/contracts/process-family-registry.json')]['raw']);visual=json.loads((ROOT/'01_UI_CONTRACT/ui/contracts/process-visual-registry.json').read_text())
 check({x['id'] for x in families['processFamilies']}=={x['process_family'] for x in visual['plans']},'process family coverage')
 vr=verify_visual();structural.extend(vr['failures']);stats.update({k:v for k,v in vr.items() if k not in ['failures','status']})
 results=[]
 for fam,path in [('R9','verify_r9.py'),('R10','r10/scripts/verify_r10.py'),('R16','r16/scripts/verify_r16.py'),('UI','ui/scripts/verify_ui.py'),('CLOSURE','closure/scripts/verify_final_closure.py'),('R17','r17/scripts/verify_r17.py')]:
  r=by[('KCML-'+fam+'-RESOURCE',path)];p=ROOT/'.cache/validators'/fam/Path(path).name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(r['raw']);run=subprocess.run([sys.executable,str(p),str(SSOT)],capture_output=True,text=True,timeout=180)
  results.append({'family':fam,'exitCode':run.returncode,'stdout':run.stdout.strip(),'stderr':run.stderr.strip()});check(run.returncode==0,'validator failed '+fam)
 visual_path=ROOT/'audit/visual-validation.json';check(visual_path.exists(),'missing visual validation')
 if visual_path.exists():
  v=json.loads(visual_path.read_text());check(v['status']=='PASS' and v['views']==48,'visual validation failed')
  for file,digest in v.get('sourceHashes',{}).items():check((ROOT/file).exists() and sha(ROOT/file)==digest,'render source drift '+file)

 return {'format':'KCML-FINAL-AUDIT/1','scope':'whole repository structure plus explicit semantic detectors; not a claim of manual line-by-line semantic certification','sourceBranch':'main','freezePerformed':False,'status':'BLOCKED' if structural or findings else 'READY_FOR_INDEPENDENT_AUDIT','structuralStatus':'FAIL' if structural else 'PASS','stats':stats,'legacyValidators':results,'structuralFailures':structural,'archivalSyntaxFindings':archival,'blockers':findings,'claims':{'FORENSICALLY_COMPLETE':not(structural or findings),'IMPLEMENTATION_READY':not(structural or findings),'VISUALLY_CLOSED':not(structural or findings),'CONTRACT_CLOSED':not(structural or findings),'FREEZE_READY':not(structural or findings)},'sourceDocumentSha256':sha(SSOT)}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--write-audit',action='store_true');p.add_argument('--freeze',action='store_true');p.add_argument('--skip-manifest',action='store_true');a=p.parse_args();r=audit()
 if a.write_audit:
  (ROOT/'audit/final-audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
  lines=['# Závěrečný audit SSOT','',f"Stav: **{r['status']}**. Strukturální kontroly: **{r['structuralStatus']}**. Freeze neproveden.",'','Rozsah: celý strom, vložené resources a kapsle, projekce UI, JSON/CSV, schémata, integrita a šest dílčích autoritativních validátorů. Automatické kontroly nejsou důkazem úplné ruční sémantické revize.','', '## Ověřené počty','']+[f'- {k}: {v}' for k,v in r['stats'].items()]+['','## Skutečné blockery','']
  for f in r['blockers']:lines += [f"### {f['id']}",'',f['finding'],'',f['requiredClosure'],'']
  lines+=['## Strukturální chyby','',json.dumps(r['structuralFailures'],ensure_ascii=False),'','Definitivní prvopis ani FREEZE READY se neprohlašuje. Přesné strojové důkazy a návratové kódy jsou v `final-audit.json`.']
  (ROOT/'audit/FINAL_AUDIT.md').write_text('\n'.join(lines)+'\n')
 integrity=[] if a.skip_manifest else check_manifest()
 print(json.dumps({'status':r['status'],'structuralStatus':r['structuralStatus'],'stats':r['stats'],'blockers':[(f['id'],f.get('count')) for f in r['blockers']],'failures':r['structuralFailures']+integrity},ensure_ascii=False))
 sys.exit(1 if r['structuralFailures'] or integrity or (a.freeze and r['blockers']) else 0)
