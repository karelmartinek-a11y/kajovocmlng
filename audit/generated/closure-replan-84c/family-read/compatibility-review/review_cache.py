"""Static binding and isolated consumed-byte hash mutations; no design-suite run."""
import ast,json,hashlib,sys,subprocess,copy
from pathlib import Path
ROOT=Path('/workspace/kajovocmlng');O=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
import run_ssot_repair_design_checks as m
source=(ROOT/'scripts/run_ssot_repair_design_checks.py').read_text();tree=ast.parse(source)
old=subprocess.check_output(['git','show','HEAD:scripts/run_ssot_repair_design_checks.py'],cwd=ROOT).decode()
def literal_checks(text):
 for n in ast.parse(text).body:
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name)and t.id=='CHECKS'for t in n.targets):return ast.literal_eval(n.value)
before=literal_checks(old);after=literal_checks(source);assert before==after and len(after)==49
main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
a=next(i for i,n in enumerate(main.body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='support'for t in n.targets));b=next(i for i,n in enumerate(main.body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='support_hash'for t in n.targets))
fragment=ast.Module(body=main.body[a:b+1],type_ignores=[]);code=compile(fragment,'actual-runner-support-binding-fragment','exec')
fixture=O/'cache-fixture';fixture.mkdir(parents=True,exist_ok=True)
for p in m.EXTERNAL_SUPPORT_PATHS:
 f=fixture/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('Independent fixture provider bytes')
def support():
 ns={'ROOT':fixture,'hashlib':hashlib,'EXTERNAL_SUPPORT_PATHS':m.EXTERNAL_SUPPORT_PATHS};exec(code,ns);return ns['support_hash']
base=support();cases=[{'id':'exact49mandatorychecksunchanged','passed':True}]
for p in m.EXTERNAL_SUPPORT_PATHS:
 f=fixture/p;original=f.read_bytes();f.write_bytes(original+b' mutation');cases.append({'id':'external-provider-byte-change/'+p,'passed':support()!=base});f.write_bytes(original)
# Actual evidence_inputs_hash() function with isolated copies of its filesystem
# dependencies: support code and nested subreport mutations are independently bound.
original_root=m.ROOT;original_inputs=copy.deepcopy(m.EVIDENCE_INPUTS)
try:
 m.ROOT=fixture
 name='verify_generation_chain_handoffs.py';rp=fixture/'report.json';sp=fixture/'external-helper.py';sub=fixture/'subproof.json';sp.write_text('positive helper');sub.write_text('{"checked":1}')
 rp.write_text(json.dumps({'supportSha256':{'external-helper.py':hashlib.sha256(sp.read_bytes()).hexdigest()},'reportsSha256':{'subproof.json':hashlib.sha256(sub.read_bytes()).hexdigest()}}));m.EVIDENCE_INPUTS[name]=['report.json']
 first=m.evidence_inputs_hash(name);sp.write_text('changed helper');cases.append({'id':'gen-dynamic-actual-support-byte-change','passed':m.evidence_inputs_hash(name)!=first});sp.write_text('positive helper')
 sub.write_text('{"checked":2}');cases.append({'id':'gen-dynamic-subproof-byte-change','passed':m.evidence_inputs_hash(name)!=first});sub.write_text('{"checked":1}');sp.unlink();cases.append({'id':'gen-dynamic-missing-helper-invalidates','passed':m.evidence_inputs_hash(name)!=first})
finally:m.ROOT=original_root;m.EVIDENCE_INPUTS=original_inputs
# Inspect actual validator input declarations. Removed old Secret report names
# are historical replacements; live nested subproofs remain declared dynamically.
from verify_generation_chain_handoffs import PROOF
assert PROOF in original_inputs['verify_generation_chain_handoffs.py'];cases.append({'id':'actual-generation-validator-proof-path-bound','passed':True})
required={'audit/generated/closure-replan-84c/family-read/core-audit/author_core_audit.py','audit/generated/closure-replan-84c/family-read/core-audit/authorable-core-delta.json','audit/generated/closure-replan-84c/family-read/core-audit/CORE_AUDIT_NORMATIVE_SUPPLEMENT.md','audit/generated/closure-replan-84c/references/author_native_read_refs.py','audit/generated/closure-replan-84c/references/native-read-reference-patch.json'}
cases.append({'id':'exact-five-external-author-dependencies','passed':set(m.EXTERNAL_SUPPORT_PATHS)==required})
report={'sourceSha256':hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'scriptSha256':hashlib.sha256(source.encode()).hexdigest(),'beforeMandatoryChecks':len(before),'afterMandatoryChecks':len(after),'checked':len(cases),'failed':sum(not x['passed']for x in cases),'cases':cases,'executed':'Actual support-hash AST fragment + actual evidence_inputs_hash function against own isolated provider/report bytes; no full design suite','actualExternalInputs':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() if (ROOT/p).is_file()else'MISSING'for p in m.EXTERNAL_SUPPORT_PATHS}}
(O/'cache-review.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'cache binding checks; failed',report['failed']);raise SystemExit(bool(report['failed']))
