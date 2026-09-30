from pathlib import Path
import sys,hashlib,json,copy
HERE=Path(__file__).parent;ROOT=HERE.parents[3];AUTHOR=ROOT/'audit/generated/resume-34d/retry-graph';sys.path.insert(0,str(AUTHOR));sys.path.insert(0,str(ROOT/'audit/generated/resume-34d/auth-crypto'))
p=AUTHOR/'verify_locked_retry.py';source=p.read_text().split('\nchecks=[]\n',1)[0]
source=source.replace("DB='retry_graph_34d'","DB='review_retry_34d'")
source=source.replace("SQL=(OUT/'locked-retry-ledger.sql').read_text()","OUT=review_out\nSQL=(author_out/'locked-retry-ledger.sql').read_text()")
ns={'__file__':str(p),'review_out':HERE,'author_out':AUTHOR};exec(compile(source,str(p),'exec'),ns)
from libpq_fixture import DB
conn=DB('review_retry_34d');conn.query('BEGIN');scan=json.loads(conn.query(ns['scan_sql'])[0][0]);rows=[]
args=(ns['INVENTORY'],'2026-09-30T00:00:00.000Z',ns['ib'],ns['plan'],ns['classifiers'])
result=ns['hydrate_locked_scan'](ns['repo'],scan,*args);rows.append({'case':'scan-hydrate-actualbytes-same-live-lockedtransaction','passed':result['contentDecision']['operationCount']==1 and conn.transaction_status()==2})
from generation_admission_contracts import ContractFailure
for name,change,expected in [('member-digest-drift',lambda s:s['rows'][0].__setitem__('evidenceBytes',s['rows'][0]['evidenceBytes']+'20'),'GENERATION_RETRY_SCAN_MEMBER_BYTES_MISMATCH'),('missing-current-state-bytes',lambda s:s['rows'][0].__setitem__('stateBytes',None),'GENERATION_RETRY_EFFECT_EVIDENCE_UNAVAILABLE'),('duplicate-physical-operation',lambda s:s['rows'].append(copy.deepcopy(s['rows'][0])),'GENERATION_RETRY_INVENTORY_DUPLICATE_OPERATION')]:
 s=copy.deepcopy(scan);change(s)
 try:ns['hydrate_locked_scan'](ns['repo'],s,*args);rows.append({'case':name,'passed':False,'accepted':True})
 except ContractFailure as e:rows.append({'case':name,'passed':e.code==expected,'expected':expected,'actual':e.code})
# Producer current singleton cannot point to an older retained projection at COMMIT.
v=json.loads(ns['repo'].records[ns['ids'](520)]['bytes']);v['jobId']=ns['job'];v['currentAttemptStateVersion']='1';raw=ns['canonical'](v)
conn.query('ROLLBACK');conn.close()
q=ns['run']('BEGIN;UPDATE kcml_retry_v1.operation SET source_bytes='+ns['b'](raw)+',source_digest='+ns['b'](hashlib.sha256(raw).digest())+';SET CONSTRAINTS ALL IMMEDIATE;ROLLBACK;')
rows.append({'case':'older-retained-currentprojection-cannot-commit','passed':q.returncode!=0 and 'RETRY_DEFERRED_CURRENT_JOIN_DRIFT'in q.stderr,'actual':q.stderr[-700:]})
report={'sourceDocumentSha256':hashlib.sha256(ns['entry']).hexdigest(),'canonicalFoundationSqlSha256':hashlib.sha256(ns['canonical_sql'].encode()).hexdigest(),'extensionSqlSha256':hashlib.sha256(ns['SQL'].encode()).hexdigest(),'executedPrefixSha256':hashlib.sha256(source.encode()).hexdigest(),'database':'review_retry_34d','postgresqlVersion':ns['run']('SHOW server_version;').stdout.strip(),'cases':rows,'scope':'OwnactualPGcanonicalfoundation+candidateledger; lockedscan→actualbytecontenthydration executesinsideone liveTX; positive-derivedcontentviolations+currentprojectionCOMMITdrift. Child persistence/wholeconsumer/allclassifiers not claimed.','wholeOperationCertified':False}
(HERE/'retry-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(rows),'failed':sum(not r['passed']for r in rows)}))
