"""Integrate reviewed bounded RETRY SQL; leave unproved authorities explicit."""
import hashlib,json,re
from ssot_sources import ROOT,SSOT,resources,resource_index
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
BASE=ROOT/'audit/generated/resume-8cc'
SQL={
 'database/generation-effect-ledger-producer.sql':'ledger/order-repair-v2/side-effect-producer.sql',
 'database/generation-trusted-policy-publisher.sql':'archive/late-ticket/generation-trusted-policy-publisher.sql',
 'database/generation-ordered-context.sql':'native/generation-ordered-context.sql',
 'database/generation-ordered-retry-child.sql':'native/generation-ordered-child.sql',
 'database/generation-native-lineage.sql':'native/generation-native-lineage.sql',
 'database/generation-native-source-parent.sql':'native/physical-parent/native-source-parent.sql',
}
NORM='''### 12.57 Ordered authenticated native RETRY reference handoff

Under §§12.51.2,49.8–49.9,51.6–51.7, the reference admission transaction authenticates the actual OWNER credential under held platform/deployment/credential heads, reserves canonical C0/C1 idempotency claims before OWNER E10, the current reserved Secret E20 root and sorted source/new-child E90 roots, and persists authentication/context children only afterwards. `database/generation-ordered-context.sql` retains exact canonical context/descriptor/current-authority validation, uses only explicitly public-qualified trusted types/relations and pg_catalog search path, and adds no late lower-class acquisition. Temporary caller relations cannot supply trusted heads. An in-memory verifier result is backend/transaction-bound, private and one-use; it is not a caller authorized flag. The actual current credential Secret/version identities are pinned under B and validated against the held E20 reserved API_KEY root, active pointer/lifecycle/type/fingerprint and derived ACTIVE status before fresh acceptance or replay returns; DELETED with an old ACTIVE version cannot authorize either. Credential genesis, complete historical reference retention and full ingress usage/transport authority remain separately mandatory.

`database/generation-ordered-retry-child.sql` permits uncommitted preallocated child root insertion at its sorted E90 position. Exact deferred parent and same-transaction scan/command/completion closure require rollback if eligibility, complete ledger or lineage fails; no partial child can commit. Source phase scan remains held through immutable child lineage, archived policy, root/command/receipt/event/outbox/audit and locator commit. Both raw UUID root orders must be exercised. No blanket terminal source guard is introduced; FOLLOW_UP §§12.49–12.50 and own UPDATE/REPAIR discussion/execution separation stay effective.

`database/generation-effect-ledger-producer.sql` defines the bounded immutable intent/attempt, canonical dispatch outbox, raw evidence sequence, server-owned frozen classifier, fenced checkpoint and continuation producer. Actual PostgreSQL read-back bytes feed the classifier. Prepared checkpoints are constructed from typed server projections and precede higher H140/H150 inserts. Dedicated G evidence allocator precedes UUID-sorted attempt/state/evidence H150 acquisitions, including implicit FK locks; exact same-byte evidence replay consumes no sequence and changed replay rejects. Deferred projection equality, exact FKs, root/phase fences, cancellation/deadline/concurrency and rollback guards remain required. This closes the independently reproduced checkpoint/evidence order defects; it does not certify every audit/UNKNOWN/reconciliation/compensation/manual outcome, source authority or remaining lock acquisition.

`database/generation-native-lineage.sql` and `database/generation-native-source-parent.sql` bind exact immutable native schema/records to the source job and child lineage to the new child. Schema copies are scoped by source job and digest; cross-source schema substitution rejects. Explicit non-null generated parent columns and stable IDs retain exact bytes and record identity. Fresh migration blocks on populated unscoped tables instead of guessing historical ownership. The separate source publisher locks OWNER then source root before ordered schema/record writes. The frozen archived package is used for historical masks/policy dispatch; missing or substituted actual bytes reject, never fall back to current policy or execute archived Python.

`database/generation-trusted-policy-publisher.sql` supplies the narrow installer-owned archived packages and late-H same-transaction acceptance ticket. A private trigger records actual receipt insertion transaction, so old receipts cannot mint fresh tickets. Ticket publication validates the exact persisted acceptance/context/snapshot/command package without reacquiring lower heads. Trusted deployment/source/budget/binding/approval producers and complete package-kind coverage remain mandatory. Public/model callers cannot create installer or ticket authority.

The installation and lock-identity contract is `contracts/generation/ordered-native-retry-handoffs.json`. Explicit new child ordinals are migration identities, never inferred from table name/OID. Remaining missing physical parent mappings, capability grants, global key/nonce production and all-kind/error/recovery consumers are BLOCKED before whole-operation readiness; bounded reference transaction tests do not discharge them. Actual encrypted systemd credential materialization/invocation remains ENVIRONMENT BLOCKED in this workspace. Fixture credentials/keys, PostgreSQL CAS targets and stored receipt rows are not that mechanism. No generated application or production acceptance is asserted.

'''
def main():
 text=SSOT.read_text();items=list(resources(text));rs=resource_index(items)
 (ROOT/'scripts/owner_api_credential_root_auth.py').write_bytes((BASE/'native/credential-root/owner_api_credential_root_auth.py').read_bytes())
 updates={n:(BASE/p).read_bytes()for n,p in SQL.items()}
 # Keep approved original key/read additions; do not run a historical author
 # which would replace this reviewed late-ticket producer with its pre-C form.
 from close_retry_authority_handoffs import GENERATION_NORM
 paragraphs=GENERATION_NORM.strip().split('\n\n')
 key_norm=paragraphs[0]+'\n\n'+paragraphs[3]+'\n\n'
 match=re.search(r'^### 12.56 .*?(?=^### |^## )',text,re.M|re.S)
 if match:text=text[:match.start()]+key_norm+text[match.end():]
 manifest_path='contracts/generation/ordered-native-retry-handoffs.json'
 ledger=json.loads((BASE/'ledger/order-repair-v2/lock-kind-migration.json').read_text()) if (BASE/'ledger/order-repair-v2/lock-kind-migration.json').exists() else json.loads((BASE/'ledger/order-repair/lock-kind-migration.json').read_text())
 doc={'contractId':'GENERATION_ORDERED_NATIVE_RETRY_HANDOFFS_V1','authority':['SSOT12.57','SSOT49.8','SSOT49.9','SSOT51.6','SSOT51.7'],'installationDependencies':[*json.loads(rs['contracts/generation/producer-archive-handoffs.json']['raw'])['generationInstallationOrder'],*SQL],
  'canonicalSqlSha256':{n:hashlib.sha256(b).hexdigest()for n,b in updates.items()},'ledgerLockIdentityMigration':ledger,
  'sourceNativeChildren':[{'relation':'kcml_native_basis_v1.schema_bundle','ordinal':154,'parent':'source_job_id','stableId':'digest','physicalParent':'primary_parent_uuid'},{'relation':'kcml_native_basis_v1.record','ordinal':155,'parent':'source_job_id','stableId':'record_id UTF8 C bytes','physicalParent':'primary_parent_uuid'},{'relation':'kcml_native_basis_v1.child_lineage','ordinal':153,'parent':'child_job_id','stableId':'child_job_id UUID bytes','physicalParent':'primary_parent_uuid'}],
  'remainingLockIdentityAndProducerGates':['GEN.RETRY.LOCK.AUTH_RECEIPT_CONTEXT_PHYSICAL_PARENT','GEN.RETRY.LOCK.SNAPSHOT_SCAN_NONCE_ARCHIVE_EVENT_COMPLETION_PHYSICAL_PARENT','GEN.RETRY.LOCK.ALL_IMPLICIT_FK_ACQUISITIONS','GEN.RETRY.PRODUCER.ALL_AUDIT_UNKNOWN_RECONCILIATION_OUTCOMES','GENERATION.AUTH.CREDENTIAL_GENESIS_AND_HISTORICAL_REFERENCE','GENERATION.SOURCE.TRUSTED_APPROVAL_BINDING_BUDGET','GENERATION.ARCHIVE.INSTALLER_KIND_COVERAGE','SQL.HELPERS.CONCRETE_CALL_SITES','SHARED.CRYPTO.SYSTEMD_SOURCE','SHARED.CRYPTO.GLOBAL_NONCE'],
  'scope':'Bounded exact reference producer/admission/child/hydration design; all listed gates stay OPEN/BLOCKED before complete operation readiness','wholeOperationClosed':False,'SSOT_CONTRACT_READY':'BLOCKED','IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 doc['installationDependencies']=list(dict.fromkeys(doc['installationDependencies']))
 updates[manifest_path]=(json.dumps(doc,indent=2)+'\n').encode()
 for name,key in [('contracts/generation/create-chain-handoffs.json','sqlInstallationOrder'),('contracts/generation/producer-archive-handoffs.json','generationInstallationOrder')]:
  d=json.loads(rs[name]['raw']);order=d[key]
  for module in SQL:
   if module not in order:order.append(module)
  d['orderedNativeRetryContract']=manifest_path
  updates[name]=encoded(d,rs[name]['raw'])
 manifest=json.loads(rs['manifest.json']['raw'])
 for name,raw in updates.items():manifest['resources'][name]={'kind':'SQL'if name.endswith('.sql')else'JSON','sizeBytes':len(raw),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest()}
 manifest['resourceCount']=len(manifest['resources']);updates['manifest.json']=encoded(manifest,rs['manifest.json']['raw'])
 text=rewrite(text,items,updates)
 for name in SQL:text=text.replace('KCML-R9-RESOURCE path="'+name+'" kind="JSON"','KCML-R9-RESOURCE path="'+name+'" kind="SQL"')
 m=re.search(r'^### 12.57 .*?(?=^### |^## )',text,re.M|re.S)
 if m:text=text[:m.start()]+NORM+text[m.end():]
 else:
  end=re.search(r'^## 13\.',text,re.M);assert end;text=text[:end.start()]+NORM+text[end.start():]
 SSOT.write_text(text,encoding='utf8',newline='\n')
 for name,raw in updates.items():
  if name=='manifest.json':continue
  p=ROOT/'01_UI_CONTRACT'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 print(json.dumps({'authored':list(updates),'wholeOperationsClosed':0}))
if __name__=='__main__':main()
