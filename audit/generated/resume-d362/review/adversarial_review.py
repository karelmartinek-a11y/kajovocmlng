from pathlib import Path
import sys,json,copy,hashlib,importlib.util
ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'audit/generated/resume-d362'
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
state=module('state_review',BASE/'sql-lifecycle/state_reference.py')
consumer=module('consumer_review',BASE/'consumers/generation_consumer_reference.py')
findings=[]
ob={'runId':'run-1','releaseSha':'a'*40,'planDigest':'b'*64,'cleanup':['clean-1'],'effects':['effect-1'],'checks':['check-1']}
inv={k:ob[k] for k in ['runId','releaseSha','planDigest']}
inv.update(cleanup=[{'id':'clean-1','outcome':'COMPLETE','evidenceDigest':'c'*64}],effects=[{'id':'effect-1','outcome':'KNOWN','evidenceDigest':'d'*64}],checks=[{'id':'check-1','outcome':'TERMINAL','evidenceDigest':'e'*64}],orphans=[],manualResolutionIds=[])
def record(name,fn,expected_limitation):
 try:
  value=fn();findings.append({'id':name,'result':'ACCEPTED','value':value,'interpretation':expected_limitation})
 except Exception as exc:
  findings.append({'id':name,'result':'REJECTED','exception':type(exc).__name__,'reason':str(exc),'interpretation':expected_limitation})
record('invented-evidence-hashes-and-finalization-boolean',lambda:state.cancellation_projection(ob,inv,state.digest(inv),True),'Digest shape and boolean do not prove durable closure/fence. Projection only, not proof of full cancellation closure.')
m=copy.deepcopy(inv);m['checks'][0]['evidenceDigest']='0'*64
record('unknown-evidence-bytes-still-terminal',lambda:state.cancellation_projection(ob,m,state.digest(m),True),'No evidence repository resolver exists; syntactically valid arbitrary digest remains accepted.')
m=copy.deepcopy(inv);m['cleanup'][0]['id']=17;ob_bad=copy.deepcopy(ob);ob_bad['cleanup']=[17]
record('malformed-authoritative-obligation-id',lambda:state.cancellation_projection(ob_bad,m,state.digest(m),True),'Reference must type its trusted inputs, or state explicit prevalidated-input prerequisite.')
record('falsey-finalization-string',lambda:state.cancellation_projection(ob,inv,state.digest(inv),'false'),'Truthy string must not mean committed terminalization; bool input currently unvalidated.')
record('unknown-ui-outcome-classification',lambda:consumer.retry_action('BOGUS','BOGUS','same','same'),'UI reducer accepts undefined classification/status rather than structured contract rejection.')
record('unknown-with-accepted-status',lambda:consumer.retry_action('ACCEPTED','UNKNOWN','same','same'),'Outcome coherence must be checked upstream or explicitly in reducer; current branch trusts string hints.')
report={'sourceHead':'d362487999bd795d4723c2a930e93fc7aa8aa295','scope':'Independent adversarial model inputs. No runtime or PostgreSQL acceptance. Findings intentionally expose current accepted counterexamples.','findings':findings,'consumedSha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE/'sql-lifecycle/state_reference.py',BASE/'consumers/generation_consumer_reference.py']}}
(BASE/'review/adversarial-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'counterexamples':len(findings),'accepted':sum(f['result']=='ACCEPTED' for f in findings)}))
