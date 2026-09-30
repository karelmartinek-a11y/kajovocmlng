"""Materialize exact public transport, receipt/meta and case-specific errors."""
import argparse,hashlib,json
from ssot_sources import SSOT,resources,resource_index
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
from generation_http_contract import PATH,PAYLOAD,GEN,document,specialize

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    text=SSOT.read_text(encoding='utf8');items=list(resources(text));rs=resource_index(items)
    assert '#### 12.44.3 HTTP specializace' in text
    bundle=json.loads(rs[GEN]['raw']);payload=json.loads(rs[PAYLOAD]['raw'])
    updates={PATH:encoded(document(bundle,payload),rs[PATH]['raw'] if PATH in rs else b'{\n'),
             PAYLOAD:encoded(specialize(payload,bundle),rs[PAYLOAD]['raw'])}
    m=json.loads(rs['manifest.json']['raw'])
    for path,raw in updates.items():m['resources'][path]={'sizeBytes':len(raw),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest()}
    updates['manifest.json']=encoded(m,rs['manifest.json']['raw'])
    updates={p:b for p,b in updates.items() if p not in rs or b!=rs[p]['raw']}
    if args.check:print(json.dumps({'pending':list(updates)}));return int(bool(updates))
    if updates:SSOT.write_text(rewrite(text,items,updates),encoding='utf8',newline='\n')
    print(json.dumps({'changed':list(updates),'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest()}));return 0

if __name__=='__main__':raise SystemExit(main())
