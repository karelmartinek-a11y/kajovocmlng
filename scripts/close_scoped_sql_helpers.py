"""Publish reviewed scoped helper definitions; never activate arbitrary wrappers."""
import argparse,hashlib,json,re
from ssot_sources import ROOT,SSOT,resources,resource_index
from author_resource_updates import rewrite,block
from phase1_repair_contracts import encoded
BASE=ROOT/'audit/generated/closure-replan-84c/sql'
FILES={'database/operation-helper-owner-query.sql':('owner-query-helpers.sql','SQL'),'database/operation-helper-owner-query-install-acl.sql':('owner-query-install-acl.sql','SQL'),'contracts/sql-helper-call-sites.json':('operation-helper-callsite-registry.json','JSON')}
TEXT='''### 51.39 Scoped operation helper definitions and callsite closure

The four original database/operation-functions.sql helpers are defined by
`database/operation-helper-owner-query.sql` for ownerApiKey.read and
ownerApiKey.reveal only. They compare exact frozen operation/descriptor/static
plan bytes, then explicit physical projections; generic fieldUpdatePlan strings
or caller-declared validity are not interpreted. All other operations fail
closed with SQL_OPERATION_TYPED_HANDLER_UNRESOLVED. Dedicated reveal preserves
both verified OWNER_FULL channels per §§7.2,8.18. Private request-local context
binds the exact transaction/backend and CONSISTENT_READ repeatable-read/read-only
snapshot. A fixture-issued session or private context is not a deployed issuer.

Install the original wrappers, reviewed helper definitions and exact
`database/operation-helper-owner-query-install-acl.sql` revocations in the same
installation transaction. No PUBLIC execute or automatic runtime capability
grant is permitted. The exact trusted session/API gateway issuer, service role
and pool/reset lifecycle, audit attribution, canonical protected-key hydration
and public reveal consumer remain required before dispatch. Internal encrypted
hydration inputs are not the public response. Actual systemd evidence remains
blocked under §12.56, without blocking this bounded definition/PG reference.

`contracts/sql-helper-call-sites.json` enumerates all 262 original wrappers and
1048 required calls. Names present are not full helper/callsite closure: two
scoped reference implementations have no verified runtime dispatch; 260 typed
handlers remain unresolved. Literal/parser proof, actual bounded PostgreSQL
execution, complete callsite definitions and production acceptance are reported
separately. No operation is fully closed by this package.

'''
def prepare():
 text=SSOT.read_text();items=list(resources(text));rs=resource_index(items);updates={};kinds={}
 for path,(name,kind)in FILES.items():
  raw=(BASE/name).read_bytes()
  if kind=='JSON':
   doc=json.loads(raw);doc['helperDefinitionStatus']='SCOPED_DEFINITIONS_CANONICAL_NOT_FULL_CALLSITE_CLOSURE';raw=(json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode()
  updates[path]=raw;kinds[path]=kind
 manifest=json.loads(rs['manifest.json']['raw'])
 for path,raw in updates.items():manifest['resources'][path]={'kind':kinds[path],'sizeBytes':len(raw),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest()}
 updates['manifest.json']=encoded(manifest,rs['manifest.json']['raw']);return text,items,rs,updates,kinds

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();text,items,rs,updates,kinds=prepare();pending=[p for p,b in updates.items()if p not in rs or rs[p]['raw']!=b]
 if a.check:print(json.dumps({'status':'BLOCKED'if pending or text.count(TEXT)!=1 else 'PASS','pending':pending}));return int(bool(pending)or text.count(TEXT)!=1)
 existing={p:b for p,b in updates.items()if p in rs};text=rewrite(text,items,existing)
 for path,raw in updates.items():
  if path in rs:continue
  text+='\n\n'+block({'path':path,'family':'KCML-R9-RESOURCE','language':'sql'if kinds[path]=='SQL'else'json','declared':{'kind':kinds[path],'bytes':'0','sha256':'','encoding':'gzip+base64'}},raw)+'\n'
 old=re.search(r'^### 51\.39 Scoped operation helper definitions and callsite closure\n.*?(?=^### 51\.40 |^## 52\.)',text,re.M|re.S)
 if old:text=text[:old.start()]+TEXT+text[old.end():]
 else:
  m=re.search(r'^## 52\.',text,re.M)
  if not m:raise ValueError('SQL_SECTION_END_MISSING')
  text=text[:m.start()]+TEXT+text[m.start():]
 SSOT.write_text(text,encoding='utf8',newline='\n');print(json.dumps({'published':list(FILES),'dispatchVerified':0}));return 0
if __name__=='__main__':raise SystemExit(main())
