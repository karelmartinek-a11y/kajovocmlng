"""Repair JSON-quoted SQL arguments only in the exact generated wrapper grammar."""
import argparse
import json
import re
from ssot_sources import SSOT, resources, resource_index
from author_resource_updates import rewrite
PATH='database/operation-functions.sql'
CALLS={'kcml_assert_operation_descriptor_v1','kcml_assert_recovery_and_incarnation_v1',
       'kcml_lock_exact_root_plan_v1','kcml_apply_exact_domain_plan_v1'}
TOKEN=re.compile(r'"(?:[^"\\]|\\.)*"')

def repair(raw):
    text=raw.decode('utf8')
    lines=[]
    for line in text.splitlines(keepends=True):
        match=re.match(r'\s*(?:PERFORM|RETURN) (\w+)\(',line)
        if match and match[1] in CALLS:
            # Existing SQL single-quoted literals are already repaired. Mixing
            # syntaxes is rejected rather than guessing across escaped quotes.
            if "'" not in line:
                line=TOKEN.sub(lambda m:"'"+json.loads(m[0]).replace("'","''")+"'",line)
        lines.append(line)
    return ''.join(lines).encode('utf8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    text=SSOT.read_text(encoding='utf8');items=list(resources(text));rs=resource_index(items)
    old=rs[PATH]['raw'];new=repair(old)
    if args.check:
        print(json.dumps({'status':'PASS' if old==new else 'BLOCKED','resource':PATH,'repairRequired':old!=new}))
        return int(old!=new)
    if new!=old:SSOT.write_text(rewrite(text,items,{PATH:new}),encoding='utf8',newline='\n')
    print(json.dumps({'resource':PATH,'changed':old!=new}))
    return 0
if __name__=='__main__':raise SystemExit(main())
