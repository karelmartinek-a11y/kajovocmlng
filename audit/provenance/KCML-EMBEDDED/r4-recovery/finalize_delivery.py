from __future__ import annotations
import base64,copy,gzip,hashlib,importlib.util,json,pathlib,re,subprocess,sys,traceback
ROOT=pathlib.Path('/mnt/data');W=ROOT/'kcml_final_work';SOURCE=ROOT/'KájovoCML_SSOT_REGISTRY_R3_PRUBEZNE(1).md';stage=ROOT/'KájovoCML_SSOT_REGISTRY_R4_OVERENE.md';OUT=ROOT/'KájovoCML_SSOT_REGISTRY_R4.md'

def block(path,obj,authority='AUDIT_ONLY',language='json'):
 body=json.dumps(obj,ensure_ascii=False,indent=2)+'\n' if language=='json' else obj
 fence='`'*(max([len(m.group()) for m in re.finditer(r'`+',body)]+[2])+1)
 return '\n<!-- KCML-EMBEDDED path="'+path+'" authority="'+authority+'" -->\n'+fence+language+'\n'+body.rstrip('\n')+'\n'+fence+'\n<!-- KCML-EMBEDDED-END -->\n'

if not stage.exists():
 source=SOURCE.read_text('utf-8')
 failures=[]
 for p in sorted(W.glob('*.log')):
  failures.append({'path':p.name,'output':p.read_text('utf-8',errors='replace')[-16000:]})
 source+='\n\n## 59. Skutecny vysledek obnovy a materializace\n\nARCHITECTURE_READINESS = BLOCKED\n\nObnova navazujicich artefaktu nebo jejich kontrola selhala. Tento stav nenahrazuje nesplnene kontrakty tvrzenim PASS. Puvodni rozsah i text zustavaji zachovany.\n'
 source+=block('r4/audit/execution-failures.json',{'status':'BLOCKED','failures':failures})
 for p in (W/'recover.py',W/'run_recovered.py',W/'close_pack.py',W/'validate_single_md.py'):
  if p.exists():source+=block('r4/audit-tools/'+p.name,p.read_text('utf-8'),'AUDIT_ONLY','python')
 OUT.write_text(source,encoding='utf-8')
 (W/'delivery-final.json').write_text(json.dumps({'path':str(OUT),'status':'BLOCKED','reason':'RECOVERY_OR_CLOSURE_SCRIPT_FAILED','bytes':OUT.stat().st_size,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()},indent=2)+'\n')
 raise SystemExit(0)

text=stage.read_text('utf-8')
spec=importlib.util.spec_from_file_location('kcml_single_md_validator',W/'validate_single_md.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
runreport={};negative=[]
try:
 blocks=v.load_blocks(text);runreport=v.verify(blocks)
 # These tests require the intended failure code, not merely a non-zero baseline status.
 manifest=v.load_json(blocks['r4/active-manifest.json']['bytes'])
 if manifest['records']:
  changed=copy.deepcopy(blocks);row=manifest['records'][0];old=changed[row['embeddedPath']]['bytes'];changed[row['embeddedPath']]['bytes']=(b'X' if old[:1]!=b'X' else b'Y')+old[1:]
  rr=v.verify(changed);want='file-sha256/'+row['logicalPath'];negative.append({'caseId':'TAMPERED_ARTIFACT_BYTES','expectedFailure':want,'passed':any(c['checkId']==want and c['status']=='FAIL' for c in rr['checks'])})
 def replace_registry(b,f,rows):
  b['r4/registries/'+f+'.json']['bytes']=json.dumps({'family':f,'records':rows},ensure_ascii=False).encode()
  m=v.load_json(b['r4/active-manifest.json']['bytes'])
  for entry in m['registries']:
   if entry['kind']==f:entry['recordCount']=len(rows);entry['digest']=v.digest(v.canonical(rows))
  m['registrySetDigest']=v.digest(v.canonical(m['registries']));b['r4/active-manifest.json']['bytes']=json.dumps(m,ensure_ascii=False).encode()
 for entry in manifest['registries']:
  f=entry['kind'];rows=v.load_json(blocks['r4/'+entry['dataRef']]['bytes'])['records']
  if not rows:continue
  changed=copy.deepcopy(blocks);newrows=copy.deepcopy(rows);newrows.append(copy.deepcopy(rows[0]));replace_registry(changed,f,newrows)
  rr=v.verify(changed);prefix='unique-id/'+f+'/';negative.append({'caseId':'DUPLICATE_ID_WITH_RECOMPUTED_DIGESTS','expectedFailurePrefix':prefix,'passed':any(c['checkId'].startswith(prefix) and c['status']=='FAIL' for c in rr['checks'])})
  changed=copy.deepcopy(blocks);replace_registry(changed,f,[]);rr=v.verify(changed);want='registry-count/'+f;negative.append({'caseId':'EMPTY_REGISTRY_WITH_RECOMPUTED_DIGESTS','expectedFailure':want,'passed':any(c['checkId']==want and c['status']=='FAIL' for c in rr['checks'])})
  break
 changed=copy.deepcopy(blocks);ar=v.load_json(changed['r4/source-integrity/input.json']['bytes']);ar['sha256']='0'*64;changed['r4/source-integrity/input.json']['bytes']=json.dumps(ar).encode();rr=v.verify(changed);negative.append({'caseId':'SOURCE_INTEGRITY_DIGEST_MISMATCH','expectedFailure':'source-sha256','passed':any(c['checkId']=='source-sha256' and c['status']=='FAIL' for c in rr['checks'])})
 try:
  v.load_blocks('<!-- KCML-EMBEDDED path="../outside.json" authority="NORMATIVE" -->\n```json\n{}\n```\n<!-- KCML-EMBEDDED-END -->\n');path_rejected=False
 except ValueError:path_rejected=True
 negative.append({'caseId':'PATH_TRAVERSAL','passed':path_rejected})
except Exception as e:
 runreport={'status':'FAIL','error':type(e).__name__+': '+str(e),'traceback':traceback.format_exc(),'architectureReadinessNotInferred':True}

text+='\n\n## 60. Overeni vyjmute primo z tohoto jednoho MD\n\n'
text+='Vlozeny kontrolni skript je samostatny: zdrojem dat je pouze tento Markdown, nikoli soubory v puvodnim pracovnim adresari. Jeho kontrola integrity, JSON schemat a referenci nenahrazuje chybejici semanticke uzavreni architektury. Negativni testy vyzaduji zachyceni konkretni vlozene vady; nestaci obecne selhani kvuli jine chybe.\n\n'
text+='Nasledujici prikaz spusti kontrolu bez vytvareni repozitare, bez pristupu k siti a bez volani placeneho API:\n\n'
bootstrap='''python3 - KájovoCML_SSOT_REGISTRY_R4.md <<'PY'
import pathlib,re,sys
p=pathlib.Path(sys.argv[1]); text=p.read_text(encoding="utf-8")
marker='<!-- KCML-EMBEDDED path="r4/scripts/validate_single_md.py" authority="NORMATIVE" -->'
start=text.index(marker)+len(marker)
m=re.match(r"\\s*\\n(`{3,})python\\n",text[start:])
if m is None:raise SystemExit("Missing exact validator block")
a=start+m.end();end=re.search(r"^"+re.escape(m.group(1))+r"\\s*$",text[a:],re.M)
if end is None:raise SystemExit("Unclosed validator block")
code=text[a:a+end.start()]
sys.argv=["validate_single_md.py",str(p)]
exec(compile(code,"embedded:validate_single_md.py","exec"),{"__name__":"__main__"})

