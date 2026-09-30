"""Bound current Secret import/metadata and mandatory fixture leaves, never a whole-operation certificate."""
import hashlib,json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=sha(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md');path=ROOT/'audit/SSOT_COMPLETION_REGISTER.json';r=json.loads(path.read_text());assert r['sourceDocumentSha256']==source
 entries=[('native-import-stored-metadata','coordinator/secret-profile-native-tests.json','Actual current HTTP profile import/exact original byte request digest and stored type/schema/digest checks; auth/registry/context synthetic, whole Secret still OPEN','contracts/secrets/import.schema.json'),('independent-native-load','review/secret-current/secret-native-review.json','Independent reproduction of two accepted metadata mismatches, repaired exact schema/type rejection plus legacy RAW null bindings and byte preservation; no real broker','contracts/secrets/profile-handoffs.schema.json'),('canonical-storage-fixture','failure-sql/secret-profile-current/postgres-tests.json','Actual canonical SQL PostgreSQL18.6 roots/immutable version/type FK and37 bounded checks; crypto fixture not systemd and command/event/outbox/audit joins OPEN','database/secret-profile-roots.sql'),('partitioned-cookie-member','secrets-browser/partition-current/partition-cookie-tests.json','Actual Chromium14 member capture/restore tests preserving partition identity and absent SameSite; full13.15 bundle/bridge/CAS/account profile NOT_ACTIVATED','contracts/secrets/profile-handoffs.schema.json')]
 import sys;sys.path.insert(0,str(ROOT/'scripts'));from ssot_sources import resource_index
 rs=resource_index();r['obligations']=[o for o in r['obligations']if not o['id'].startswith('secret-handoff-bounded:')]
 for name,proof,scope,resource in entries:
  p=ROOT/'audit/generated/resume-34d'/proof;q=json.loads(p.read_text());ps=q.get('sourceDocumentSha256',q.get('sourceSha256',q.get('inputSsotSha256')));valid=ps==source and q.get('failed')==0
  r['obligations'].append({'id':'secret-handoff-bounded:'+name,'area':'secrets','scope':scope,'authoritativeSources':[{'pointer':resource,'ssotSha256':source,'resourceSha256':rs[resource]['sha256']},{'pointer':'00_SSOT/KajovoCMLNG_SSOT.md#section.8.12','ssotSha256':source}],'dependencies':['operation:secret.create:persistence-hydration'],'state':'VERIFIED'if valid else'BLOCKED','verificationLevel':'ACTUAL_PREGEN_BOUNDED_FIXTURE','blocker':None if valid else{'type':'TECHNICAL','reason':'Missing/stale/failed current proof'},'repair':'scripts/close_secret_profile_handoffs.py','evidence':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'sourceSha256':ps}],'sourceBinding':{'ssotSha256':source},'reviewer':'independent_review_34d','implementationAcceptance':'NOT_EVALUATED'})
 r['coverage'].update(states=dict(Counter(o['state']for o in r['obligations'])),levels=dict(Counter(o['verificationLevel']for o in r['obligations'])),totalRegisteredObligations=len(r['obligations']),wholeOperationsSemanticallyVerified=0)
 r['gates']={'SSOT_CONTRACT_READY':'BLOCKED','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r['coverage']))
if __name__=='__main__':main()
