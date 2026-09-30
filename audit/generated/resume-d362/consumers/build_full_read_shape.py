"""Read-only composition of reviewed candidate physical root into wire shape.

Unresolved lifecycle/authority joins stay explicit, not hidden by JSON types.
"""
import json,re,hashlib
from pathlib import Path
from generation_consumer_reference import *
OUT=Path(__file__).parent
sqlpath=OUT.parent/'persistence/generation-root-proposed.sql'
sql=sqlpath.read_text().split('CREATE TABLE generation_job (',1)[1].split('\n);',1)[0]
def camel(s):
 a=s.split('_');return a[0]+''.join(x.title() for x in a[1:])
props={};mapping=[]
for line in sql.splitlines():
 m=re.match(r'  ([a-z_]+) (uuid|text|bigint|bytea|timestamptz) (.*)',line)
 if not m:continue
 col,typ,rest=m.groups();name=camel(col)
 if col=='id':name='jobId'
 if col=='aggregate_event_sequence':name='eventSequence'
 s={'uuid':UID,'text':{'type':'string'},'bigint':COUNTER,'bytea':DIGEST,'timestamptz':TIME}[typ]
 if col=='kind':s={'enum':['CREATE','UPDATE','FOLLOW_UP','RETRY','REPAIR']}
 if col=='state':s={'enum':STATES}
 if col=='target_kind':
  from create_operation_contracts import TARGETS
  s={'enum':TARGETS}
 isnull='NOT NULL' not in rest and 'PRIMARY KEY' not in rest
 props[name]=nullable(s) if isnull else copy.deepcopy(s)
 mapping.append({'wireField':name,'physicalColumn':'generation_job.'+col,'physicalType':typ,'nullAllowed':isnull,'wireRepresentation':{'uuid':'canonical UUID','text':'exact text (unresolved own dictionary where stated)','bigint':'canonical nonnegative decimal string, signed bigint maximum','bytea':'sha256:<lowercase64hex>','timestamptz':'RFC3339 timestamp'}[typ],'authority':'SSOT §25.11 generation_job corresponding field; candidate physical root reviewed independently'})
result=obj(props)
result['$id']='urn:kcml:design:generation-job-root-read:review-v1'
result['$comment']='Review-only complete root-row shape. Does not resolve currentPhase/access-channel/error dictionaries, external FKs or complete child hydration; do not mark whole read VERIFIED.'
report={'inputCommit':'d362487999bd795d4723c2a930e93fc7aa8aa295','physicalProposalSHA256':hashlib.sha256(sqlpath.read_bytes()).hexdigest(),'schema':result,'fieldMappings':mapping,'unresolved':['currentPhase own token/state map','initiatingAccessChannel own dictionary and authenticated context provenance','errorCode exact applicability dictionary','Same-job current/approved spec/authority/capability/plan/phase/checkpoint joins','Exact targetKind→actual canonical root identity binding','Public projection authority/minimal exposure for initiating context/leases','Child byte hydration and producer schema pin lineage','Full response error/transport/event applicability masks'],'activationStatus':'REVIEW_ONLY_NOT_NORMATIVE'}
(OUT/'generation-full-root-read.proposed.json').write_text(json.dumps(report,indent=2)+'\n')
print(len(props),'root wire fields inventoried; unresolved dictionaries/joins retained')
