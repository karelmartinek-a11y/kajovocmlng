"""Author only evidenced locator and advisory-key SQL; no application generation."""
import argparse,hashlib,json
from ssot_sources import ROOT,SSOT,resources,resource_index
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
SQL=ROOT/'audit/generated/resume-5334/sql'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();text=SSOT.read_text();items=list(resources(text));rs=resource_index(items)
 path='database/explicit-entities.sql';old=rs[path]['raw'].decode();needle='logical_operation_id uuid NOT NULL REFERENCES domain_command(logical_operation_id) ON DELETE RESTRICT,';new='logical_operation_id uuid NOT NULL UNIQUE REFERENCES domain_command(logical_operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,'
 if old.count(needle)==1:replacement=old.replace(needle,new)
 elif old.count(new)==1:replacement=old
 else:raise ValueError('LOCATOR_EXACT_FK_DECLARATION_UNRESOLVED')
 updates={path:replacement.encode(),'database/postgres-advisory-key.sql':(SQL/'postgres-advisory-key-proposed.sql').read_bytes()}
 manifest=json.loads(rs['manifest.json']['raw'])
 for name,raw in updates.items():manifest['resources'][name]={'kind':'SQL','sizeBytes':len(raw),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest()}
 updates['manifest.json']=encoded(manifest,rs['manifest.json']['raw'])
 pending=[k for k,v in updates.items() if k not in rs or rs[k]['raw']!=v]
 if not a.check:SSOT.write_text(rewrite(text,items,updates),encoding='utf8',newline='\n')
 print(json.dumps({'status':'PASS' if not pending or not a.check else 'BLOCKED','pending':pending,'scope':'Exact49.4/51.12 locator uniqueness/deferredFK and51.8 digest→signedint4 projection; four operation helpers remainBLOCKED'}));return int(a.check and bool(pending))
if __name__=='__main__':raise SystemExit(main())
