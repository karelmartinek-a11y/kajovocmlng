"""Independent exact supplementation/alias compatibility review.

Preserved-policy execution relocates only its hardcoded output expression. The
actual script stays untouched; original/executed bytes are both recorded.
"""
import sys,subprocess,json,hashlib,os,re,copy
from pathlib import Path
ROOT=Path('/workspace/kajovocmlng');O=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resources,resource_index
from author_resource_updates import rewrite
ENTRY=SSOT.read_bytes();RS=resource_index(resources(ENTRY.decode()));cases=[]
MASK='contracts/operation-contracts.json';BASE='verify_preserved_policy.py';GEN='verify_generation_operation_masks.py'
runner="""import sys;from pathlib import Path;sys.path.insert(0,sys.argv[4]);import ssot_sources;ssot_sources.SSOT=Path(sys.argv[1]);script=Path(sys.argv[2]);out=Path(sys.argv[3]);code=script.read_text();needle=\"ROOT/'audit/generated/preserved-policy.json'\";assert code.count(needle)==1;code=code.replace(needle,repr(str(out)),1).replace('('+repr(str(out))+').write_text','Path('+repr(str(out))+').write_text',1);exec(compile(code,str(script),'exec'),{'__name__':'__main__','__file__':str(script)})"""
def policy(id,text,expected_pass,expected_section=None):
 source=O/(id+'.md');source.write_text(text);out=O/(id+'.json')
 p=subprocess.run([sys.executable,'-c',runner,str(source),str(ROOT/'scripts'/BASE),str(out),str(ROOT/'scripts')],cwd=ROOT,text=True,capture_output=True,timeout=120)
 (O/(id+'.log')).write_text(p.stdout+p.stderr)
 r=json.loads(out.read_text())if out.is_file()else{};failures=[x['section']for x in r.get('checks',[])if x['status']=='FAIL']
 good=p.returncode==0 if expected_pass else p.returncode!=0 and bool(failures) and (expected_section is None or expected_section in failures)
 cases.append({'id':id,'passed':good,'exit':p.returncode,'failedSections':failures,'mutantSourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scriptOriginalSha256':hashlib.sha256((ROOT/'scripts'/BASE).read_bytes()).hexdigest(),'instrumentation':'ONE REPORT DESTINATION RELOCATION ONLY; actual source/policy logic unchanged'});source.unlink();print(id,good,p.stdout.strip())
policy('policy-current',ENTRY.decode(),True)
text=ENTRY.decode();m=re.search(r'^## 8\.[^\n]*\n',text,re.M);assert m;policy('policy-original-unrelated-content-change',text[:m.end()]+'INDEPENDENT_UNAUTHORIZED_POLICY_MUTATION\n'+text[m.end():],False)
from close_secret_retention_contract import TEXT
assert text.count(TEXT)==1;policy('policy-supplement-byte-change',text.replace(TEXT,TEXT.replace('Secret','UnauthorizedSecret',1),1),False,'8.17')
policy('policy-supplement-duplicate',text+'\n'+TEXT,False,'8.17')
# One positive actual full native verifier; further source mutants are sufficient
# to prove exact set rejection, not a new project-wide audit.
run="""import sys;from pathlib import Path;sys.path.insert(0,sys.argv[3]);import ssot_sources;ssot_sources.SSOT=Path(sys.argv[1]);import verify_generation_operation_masks as m;raise SystemExit(m.main())"""
def masks(id,text,expected_case=None,expected_text=None):
 source=O/(id+'.md');source.write_text(text);out=O/'mask-reports'/id;out.mkdir(parents=True,exist_ok=True)
 p=subprocess.run([sys.executable,'-c',run,str(source),'unused',str(ROOT/'scripts')],cwd=ROOT,text=True,capture_output=True,env={**os.environ,'KCML_AUDIT_OUTPUT':str(out)},timeout=180)
 (O/(id+'.log')).write_text(p.stdout+p.stderr);reports=list(out.glob('*.json'));r=json.loads(reports[0].read_text())if reports else{}
 bad=[x['case']for x in r.get('checks',[])if not x['passed']]
 good=p.returncode==0 if expected_case is None and expected_text is None else p.returncode!=0 and ((expected_case in bad)if expected_case else expected_text in p.stdout+p.stderr)
 cases.append({'id':id,'passed':good,'exit':p.returncode,'failedCases':bad,'diagnostic':(p.stdout+p.stderr)[-1300:],'mutantSourceSha256':hashlib.sha256(source.read_bytes()).hexdigest()});source.unlink();print(id,good)
masks('native-masks-current',text)
original=json.loads(RS[MASK]['raw']);doc=copy.deepcopy(original);doc['$defs']['independent.unrelated.injected']={'type':'object'}
masks('native-unrelated-definition-still-rejected',rewrite(text,list(resources(text)),{MASK:(json.dumps(doc)+'\n').encode()}),'exact-source-derived-variant-set')
doc=copy.deepcopy(original);doc['$defs']['owner.session.list:response']['additionalProperties']=True
masks('native-owner-definition-not-blanket-allowed',rewrite(text,list(resources(text)),{MASK:(json.dumps(doc)+'\n').encode()}),'exact-source-derived-variant-set')
doc=copy.deepcopy(original);doc['$defs']['mcp.resources.read:command']['allOf'][1]['properties']['method']['const']='resources/write'
masks('native-read-alias-method-substitution',rewrite(text,list(resources(text)),{MASK:(json.dumps(doc)+'\n').encode()}),expected_text='ALIAS_IDENTITY_CONFLICT:mcp.resources.read:command')
report={'sourceSha256':hashlib.sha256(ENTRY).hexdigest(),'sourceUnchanged':SSOT.read_bytes()==ENTRY,'checked':len(cases),'failed':sum(not x['passed']for x in cases),'cases':cases,'consumedResources':{k:RS[k]['sha256']for k in [MASK,'contracts/owner-session-family.json','contracts/mcp/native-2026-07-28.schema.json','contracts/mcp-native-schema-artifact.json']},'scriptsSha256':{k:hashlib.sha256((ROOT/'scripts'/k).read_bytes()).hexdigest()for k in [BASE,GEN]},'externalAliasPackageSha256':hashlib.sha256((ROOT/'audit/generated/closure-replan-84c/references/native-read-reference-patch.json').read_bytes()).hexdigest(),'wholeOperationsClosed':0,'runtimeAcceptance':'NOT_EVALUATED'}
(O/'policy-mask-review.json').write_text(json.dumps(report,indent=2)+'\n');print('policy/mask checks',len(cases),'failed',report['failed']);raise SystemExit(bool(report['failed']))
