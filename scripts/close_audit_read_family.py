"""Publish reviewed Audit inspection masks, not unresolved event/error producers."""
import argparse,hashlib,importlib.util,json
from ssot_sources import ROOT,SSOT,resources,resource_index
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
BASE=ROOT/'audit/generated/closure-replan-84c/family-read/core-audit'
BEGIN='<!-- KCML-AUDIT-READ-FAMILY-V1-BEGIN -->';END='<!-- KCML-AUDIT-READ-FAMILY-V1-END -->'
def prepare(rs):
 spec=importlib.util.spec_from_file_location('core_audit_author',BASE/'author_core_audit.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);u=m.updates(rs)
 return {p:encoded(json.loads(raw),rs[p]['raw'] if p in rs else b'{\n') for p,raw in u.items()}
def normative(text):
 block=BEGIN+'\n'+(BASE/'CORE_AUDIT_NORMATIVE_SUPPLEMENT.md').read_text().rstrip()+'\n'+END
 if BEGIN in text:
  a=text.index(BEGIN);b=text.index(END,a)+len(END);return text[:a]+block+text[b:]
 return text+'\n\n'+block+'\n'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();text=SSOT.read_text();items=list(resources(text));rs=resource_index(items);u=prepare(rs)
 targets={ROOT/'01_UI_CONTRACT'/p:raw for p,raw in u.items()}
 pending=[p for p,raw in u.items()if p not in rs or rs[p]['raw']!=raw]+['projection:'+str(p.relative_to(ROOT))for p,raw in targets.items()if not p.is_file()or p.read_bytes()!=raw]
 norm=normative(text)==text
 if a.check:print(json.dumps({'status':'PASS'if not pending and norm else'BLOCKED','pending':pending,'normativeExact':norm}));return int(bool(pending)or not norm)
 SSOT.write_text(normative(rewrite(text,items,u)),encoding='utf8',newline='\n')
 for p,raw in targets.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 print(json.dumps({'published':list(u),'eventSchemasChanged':False,'wholeOperationsClosed':0}));return 0
if __name__=='__main__':raise SystemExit(main())
