"""Bind bounded integrated chain proofs; whole operations stay OPEN."""
import hashlib,json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=sha(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md');path=ROOT/'audit/SSOT_COMPLETION_REGISTER.json';r=json.loads(path.read_text());assert r['sourceDocumentSha256']==source
 base='audit/generated/resume-34d/'
 entries=[
 ('owner-api-locked-material','auth-crypto/auth-crypto-proof.json','§7.2/51.20: actual bearer bytes, exact request/descriptor/epoch receipt and credential lock; OWNER session and effective gateway policy remain OPEN','database/generation-create-authentication.sql'),
 ('independent-authenticated-read-chain','review/authenticated-chain-review.json','Actual API→protected input→canonical atomic root/event/outbox/audit→read→native consumer; only CREATE fixture, not all kinds or full runtime','contracts/generation/create-chain-handoffs.json'),
 ('global-crypto-registry','review/crypto-registry-review.json','Actual canonical global nonce/key-fingerprint registry; missing metadata SQL NULL counterexamples specifically rejected; actual systemd key producer/typed ciphertext joins remain OPEN','database/canonical-crypto-registry.sql'),
 ('accepted-before-root-retention','failure-sql/failure-before-root-proof.json','Exact accepted pending/failure/unknown/cancel retained command outcomes, atomic audit/locator/idempotency and negative tests; actual decision producers remain OPEN','database/generation-create-preroot.sql'),
 ('pending-protected-transfer','failure-sql/pending-transfer-proof.json','Pending→same prospective root/context/snapshot success and unchanged earlier outcome; exact cipher transfer/version negatives; actual auth/crypto decision wiring separate','database/generation-create-preroot.sql'),
 ('current-read-storage','read-ui/read-chain-proof.json','Exact 39-column internal SQL read and actual byte receipt/event/input consumer; frozen policy archive/full public children/UI remain OPEN','database/generation-create-read.sql'),
 ('locked-retry-projection','retry-graph/locked-retry-tests.json','Actual source phase gate/current-state/evidence scan and concurrent phantom negatives; complete49.8 producer/child commit remains OPEN','database/generation-locked-retry.sql')]
 from sys import path as imports
 imports.insert(0,str(ROOT/'scripts'));from ssot_sources import resource_index
 rs=resource_index()
 r['obligations']=[o for o in r['obligations'] if not o['id'].startswith('generation-chain-bounded:')]
 for name,proof,scope,resource in entries:
  p=ROOT/(base+proof);q=json.loads(p.read_text());proofsource=q.get('sourceDocumentSha256',q.get('sourceSha256'));valid=proofsource==source and q.get('failed',0)==0 and all(c.get('passed',True) for c in q.get('checks',[]))
  r['obligations'].append({'id':'generation-chain-bounded:'+name,'area':'generation','scope':scope,'authoritativeSources':[{'pointer':resource,'ssotSha256':source,'resourceSha256':rs[resource]['sha256']},{'pointer':'00_SSOT/KajovoCMLNG_SSOT.md#section.12.54','ssotSha256':source}],'dependencies':['operation:generation.job.create:persistence-hydration'],'state':'VERIFIED' if valid else 'BLOCKED','verificationLevel':'ACTUAL_PREGEN_BOUNDED_FIXTURE','blocker':None if valid else {'type':'TECHNICAL','reason':'Missing/stale/failed integrated current source proof'},'repair':'scripts/close_generation_chain_handoffs.py','evidence':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'sourceSha256':proofsource}],'sourceBinding':{'ssotSha256':source},'reviewer':'independent_review_34d','implementationAcceptance':'NOT_EVALUATED'})
 r['coverage'].update(states=dict(Counter(o['state'] for o in r['obligations'])),levels=dict(Counter(o['verificationLevel'] for o in r['obligations'])),totalRegisteredObligations=len(r['obligations']),wholeOperationsSemanticallyVerified=0)
 r['gates']={'SSOT_CONTRACT_READY':'BLOCKED','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r['coverage']))
if __name__=='__main__':main()
