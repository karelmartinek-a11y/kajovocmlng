from pathlib import Path
import sys,json,copy,hashlib
OUT=Path(__file__).parent;sys.path.insert(0,str(OUT))
from family_reference import *
from jsonschema import Draft202012Validator,FormatChecker
checks=[]
def case(i,v,details):checks.append({'id':i,'status':'PASS'if v else'FAIL','details':details})
s=Store();a,_=s.add();b,_=s.add();c,_=s.add();api=s.authenticate(s.api,'OWNER_API_KEY');first=s.listing(api,{'cursor':None,'limit':'1'});cursor=first['output']['nextCursor'];assert cursor
s.revoke(api,b,'0','independent-synthetic-revoke');later=s.listing(api,{'cursor':cursor,'limit':None})
case('frozen-cursor-owner-head-stays-in-same-snapshot',later['output']['ownerStateVersion']==first['output']['ownerStateVersion'],{'firstHead':first['output']['ownerStateVersion'],'laterHead':later['output']['ownerStateVersion'],'sameObservedAt':later['output']['observedAt']==first['output']['observedAt']})
receipt=next(iter(s.commands.values()))['response'];event=copy.deepcopy(s.events[-1]);v=Draft202012Validator(OPS['owner.session.revoke']['eventSchema'],format_checker=FormatChecker());v.validate(event);event['sequence']='0';accepted=v.is_valid(event);case('committed-event-zero-sequence-rejects',not accepted,{'accepted':accepted,'positiveSequence':s.events[-1]['sequence']})
response=copy.deepcopy(receipt);response.update(status='FAILED',output=None,error={'stableCode':'DEPENDENCY_UNAVAILABLE','classification':'DEPENDENCY','retryDirective':'RETRY_SAME_OPERATION','message':'Synthetic dependency wait','detailsDigest':None});v=Draft202012Validator(OPS['owner.session.revoke']['responseSchema'],format_checker=FormatChecker());accepted=v.is_valid(response);case('retryable-failure-cannot-be-terminal',not accepted,{'acceptedTerminalTrue':accepted})
# Digest byte spellings must be exact; correct JSON schema decoding is not hashing.
r=copy.deepcopy(receipt);r['resultDigest']+='\n';accepted=v.is_valid(r);case('result-digest-trailing-newline-rejects',not accepted,{'accepted':accepted})
# A cursor UUID must obey the same lowercase rule as path UUID.
q=decode('owner.session.list','GET','/owner/sessions',[('cursor','abcdef12-3456-4789-8abc-abcdef123456')],[]);x=copy.deepcopy(q);x['query']['cursor']+='\n';validator=Draft202012Validator(OPS['owner.session.list']['requestSchema'],format_checker=FormatChecker());case('cursor-newline-rejects',not validator.is_valid(x),{})
# Bounded positive independent source/model checks.
case('read-only-list-does-not-emit-mutation-event',len(s.events)==1,{})
case('selected-revoke-does-not-increment-global-session-epoch',s.owner_epoch==2,{})
case('selected-revoke-preserves-other-session',s.rows[a]['revokedAt']is None and s.rows[c]['revokedAt']is None,{})
report={'sourceSha256':PACK['sourceSha256'],'packageSha256':hashlib.sha256((OUT/'operation-mask-delta.json').read_bytes()).hexdigest(),'checked':len(checks),'failed':sum(x['status']=='FAIL'for x in checks),'checks':checks,'scope':'Independent semantic counterexamples from valid reference witnesses; no PG/auth deployment/runtime assertion','wholeOperationClosed':False}
(OUT/'independent-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checked':len(checks),'failed':report['failed']}))
