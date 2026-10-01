import sys,json,hashlib
from pathlib import Path
from urllib.parse import urlencode
ROOT=Path('/workspace/kajovocmlng');O=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(O))
from history_read_reference import decode_profiled_read
from ssot_sources import SSOT,resource_index
cases=[]
def ok(label):cases.append({'id':label,'status':'PASS'})
def reject(label,query):
 try:decode_profiled_read('route.0451',{},urlencode(query,doseq=True).encode(),b'');raise AssertionError(label+' accepted')
 except ValueError as e:assert str(e)=='HISTORY_QUERY_INVALID';ok(label)
exp={'queryProfile':'EXPERIENCE_HISTORY_V1','fromInclusive':'2026-10-01T00:00:00Z','toExclusive':'2026-10-02T00:00:00Z','timezone':'Europe/Prague','limit':'500'}
old={'queryProfile':'HISTORY_QUERY_V1','from':'2026-10-01T00:00:00Z','to':'2026-10-02T00:00:00Z','recordKinds':['RUN','EVENT'],'direction':'ANY','result':'ANY','sort':'TIME_DESC','limit':'200'}
assert decode_profiled_read('route.0451',{},urlencode(exp).encode(),b'')['filters']['limit']==500;ok('experience-explicit-profile-preserves-source500')
assert decode_profiled_read('route.0451',{},urlencode(old,doseq=True).encode(),b'')['filters']['limit']==200;ok('distinct-history-explicit-profile-preserves-source200-and-sort-kinds')
for label,q in [('history-over200',{**old,'limit':'201'}),('experience-over500',{**exp,'limit':'501'}),('no-format-guess',{k:v for k,v in exp.items()if k!='queryProfile'}),('wrong-variant',{**exp,'queryProfile':'AUTO'}),('history-missing-required-sort',{k:v for k,v in old.items()if k!='sort'}),('history-duplicate-kind',{**old,'recordKinds':['RUN','RUN']}),('experience-refuses-other-profile-fields',{**exp,'recordKinds':'RUN'}),('history-refuses-other-profile-fields',{**old,'fromInclusive':exp['fromInclusive']})]:reject(label,q)
reject('duplicate-format-selector',list(exp.items())+[('queryProfile','HISTORY_QUERY_V1')])
r=resource_index();report={'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'exactConsumedSchemaDigest':r['ui/contracts/live-experience.json']['sha256'],'checked':len(cases),'failed':0,'cases':cases,'activation':'NOT_ACTIVATED_TECHNICAL_PROPOSAL','producerExecutionProof':False,'scope':'explicit source-profile parser coexistence only, not native runtime/route consumer authority','wholeOperationClosed':False}
(O/'profile-binding-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'profile parser checks PASS; notactivated')
