"""Isolated exact-version compile probe. No application or production calls."""
import json
import subprocess
import sys
from ssot_sources import ROOT
from verify_ui_stack import PACKAGES

def run():
    work=ROOT/'.cache/ui-stack';work.mkdir(parents=True,exist_ok=True)
    deps={**PACKAGES,'typescript':'6.0.3','@types/node':'24.10.12','@types/react':'18.3.18','@types/react-dom':'18.3.5','@types/papaparse':'5.3.16'}
    (work/'package.json').write_text(json.dumps({'name':'kcml-ui-contract-probe','version':'0.0.0','private':True,'type':'module','dependencies':deps},indent=2)+'\n',encoding='utf-8')
    (work/'probe.tsx').write_text('''import { createRoot } from 'react-dom/client';
import { ReactFlow, MiniMap, Controls, Background, type Node, type Edge } from '@xyflow/react';
import * as ContextMenu from '@radix-ui/react-context-menu';
import * as Dialog from '@radix-ui/react-dialog';
import * as Tooltip from '@radix-ui/react-tooltip';
import * as Popover from '@radix-ui/react-popover';
import { DndContext, KeyboardSensor, TouchSensor } from '@dnd-kit/core';
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { useReactTable, getCoreRowModel } from '@tanstack/react-table';
import Papa from 'papaparse';
import ExcelJS from 'exceljs';
import { getDocument } from 'pdfjs-dist';
const nodes: Node[] = [{id:'a',position:{x:0,y:0},data:{label:'Demo'}}];
const edges: Edge[] = [];
export function Probe() {
  const table=useReactTable({data:[{id:'a'}],columns:[{accessorKey:'id'}],getCoreRowModel:getCoreRowModel()});
  return <DndContext><ContextMenu.Root><ContextMenu.Trigger><ReactFlow nodes={nodes} edges={edges} fitView><Controls/><MiniMap/><Background/></ReactFlow></ContextMenu.Trigger><ContextMenu.Portal><ContextMenu.Content><ContextMenu.Item>Detail</ContextMenu.Item></ContextMenu.Content></ContextMenu.Portal></ContextMenu.Root><Dialog.Root><Dialog.Trigger>Open</Dialog.Trigger><Dialog.Portal><Dialog.Content><Dialog.Title>Object</Dialog.Title><Dialog.Description>Demo</Dialog.Description></Dialog.Content></Dialog.Portal></Dialog.Root><Tooltip.Provider><Tooltip.Root><Tooltip.Trigger>Help</Tooltip.Trigger><Tooltip.Content>Explanation</Tooltip.Content></Tooltip.Root></Tooltip.Provider><Popover.Root><Popover.Trigger>Touch help</Popover.Trigger><Popover.Content>Explanation</Popover.Content></Popover.Root></DndContext>;
}
void [createRoot,KeyboardSensor,TouchSensor,sortableKeyboardCoordinates,Papa.parse,new ExcelJS.Workbook(),getDocument];
''',encoding='utf-8')
    (work/'tsconfig.json').write_text(json.dumps({'compilerOptions':{'target':'ES2022','module':'ESNext','moduleResolution':'Bundler','jsx':'react-jsx','strict':True,'noEmit':True,'skipLibCheck':False,'esModuleInterop':True,'types':['node','react','react-dom'],'lib':['ES2022','DOM']},'include':['probe.tsx']}),encoding='utf-8')
    commands=[['npm.cmd' if sys.platform=='win32' else 'npm','install','--ignore-scripts','--no-audit','--no-fund'],['node','node_modules/typescript/bin/tsc','--project','tsconfig.json']]
    results=[]
    for cmd in commands:
        result=subprocess.run(cmd,cwd=work,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300)
        results.append({'command':cmd,'exitCode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'status':'PASS' if result.returncode==0 else 'FAIL'})
        if result.returncode:break
    report={'scope':'Isolated local compile probe, not product implementation or target Ubuntu validation. Package lifecycle scripts disabled.',
            'node':subprocess.check_output(['node','--version'],text=True).strip(),'packages':deps,'checks':results}
    out=ROOT/'audit/generated/ui-stack-probe.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([(r['command'][0],r['status']) for r in results]))
    return any(r['exitCode'] for r in results)

if __name__=='__main__':sys.exit(run())
