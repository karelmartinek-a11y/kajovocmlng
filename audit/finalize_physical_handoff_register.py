"""Current canonical PG proof joins a bounded obligation, not a whole operation."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index
from run_ssot_repair_design_checks import evidence_inputs_hash
from collections import Counter
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=sha(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md');p=ROOT/'audit/SSOT_COMPLETION_REGISTER.json';r=json.loads(p.read_text());assert r['sourceDocumentSha256']==source
 proof=ROOT/'audit/generated/repair-2026-09-30/design-current/verify_generation_physical_handoff/generation-physical-tests.json';q=json.loads(proof.read_text());assert q['sourceDocumentSha256']==source and q['status']=='PASS'and q['failed']==0
 assert 'PostgreSQL 18.6 'in q['postgresqlVersion'];assert q['canonicalSqlSha256']==resource_index()['database/generation-create-foundations.sql']['sha256']
 for file,h in q['supportSha256'].items():assert sha(ROOT/file)==h,file
 runner=json.loads((ROOT/'audit/generated/repair-2026-09-30/design-current/commands.json').read_text());check=next(x for x in runner['commands']if x['script']=='scripts/verify_generation_physical_handoff.py');assert check['exitCode']==0 and check['evidenceInputsSha256']==evidence_inputs_hash('verify_generation_physical_handoff.py')
 r['obligations']=[o for o in r['obligations']if o['id']!='generation-physical-design:canonical-joined-roots']
 r['obligations'].append({'id':'generation-physical-design:canonical-joined-roots','area':'generation','scope':'Actual canonical embedded DDL in isolated PG18.6: own roots/pin/context/scoped-command/atomic successful commit, exact locator tuple and retained delivery/outcome/audit; synthetic opaque auth/cipher is not authentication/crypto proof','authoritativeSources':[{'pointer':'00_SSOT/KajovoCMLNG_SSOT.md#section.12.52','ssotSha256':source},{'pointer':'database/generation-create-foundations.sql','ssotSha256':source,'resourceSha256':q['canonicalSqlSha256']}],'dependencies':['operation:generation.job.create:persistence-hydration'],'state':'VERIFIED','verificationLevel':'ACTUAL_PREGEN_POSTGRESQL_BOUNDED_FIXTURE','blocker':None,'repair':'scripts/close_generation_physical_handoff.py','evidence':[{'path':proof.relative_to(ROOT).as_posix(),'sha256':sha(proof),'sourceSha256':source}],'sourceBinding':{'ssotSha256':source},'implementationAcceptance':'NOT_EVALUATED'})
 r['coverage'].update(states=dict(Counter(o['state']for o in r['obligations'])),levels=dict(Counter(o['verificationLevel']for o in r['obligations'])),totalRegisteredObligations=len(r['obligations']),verifiedCanonicalPostgreSQLBoundedObligations=1,wholeOperationsSemanticallyVerified=0)
 p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r['coverage']))
if __name__=='__main__':main()
