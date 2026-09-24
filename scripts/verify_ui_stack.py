"""Capture official npm metadata for exact UI dependency selection; no package scripts."""
import concurrent.futures
import hashlib
import json
import re
import urllib.request
import urllib.parse
from ssot_sources import ROOT, resource_index

# Exact releases selected by the embedded live-experience SSOT contract.
PACKAGES = {
 'react': '18.3.1', 'react-dom': '18.3.1', 'vite': '6.3.5',
 '@xyflow/react': '12.8.5', '@radix-ui/react-context-menu': '2.2.16',
 '@radix-ui/react-dialog': '1.1.15', '@radix-ui/react-tooltip': '1.2.8',
 '@radix-ui/react-popover': '1.1.15', '@tanstack/react-table': '8.21.3',
 'papaparse': '5.5.3', 'exceljs': '4.4.0', 'pdfjs-dist': '5.4.149',
 '@dnd-kit/core': '6.3.1', '@dnd-kit/sortable': '10.0.0'}

SSOT_VERSION_TEXT = {
 'react': 'React', 'react-dom': 'React', 'vite': 'Vite',
 '@xyflow/react': '@xyflow/react',
 '@radix-ui/react-context-menu': 'Radix ContextMenu',
 '@radix-ui/react-dialog': 'Dialog', '@radix-ui/react-tooltip': 'Tooltip',
 '@radix-ui/react-popover': 'Popover', '@tanstack/react-table': 'TanStack React Table',
 'papaparse': 'PapaParse', 'exceljs': 'ExcelJS', 'pdfjs-dist': 'PDF.js',
 '@dnd-kit/core': '@dnd-kit/core', '@dnd-kit/sortable': '@dnd-kit/sortable',
 'typescript': 'TypeScript',
}


def verify_contract_alignment():
    resources = resource_index()
    experience = json.loads(resources['ui/contracts/live-experience.json']['raw'])
    normative_text = ' '.join(str(value) for value in experience['stack'].values())
    contract_path = ROOT/'01_UI_CONTRACT/ui/contracts/ui-stack-contract.json'
    contract = json.loads(contract_path.read_text(encoding='utf-8'))
    expected = {**PACKAGES, 'typescript': '6.0.3'}
    problems = []
    for name, version in expected.items():
        if contract.get('packageVersions', {}).get(name) != version:
            problems.append(f'physical stack contract disagrees for {name}')
        label = SSOT_VERSION_TEXT[name]
        if not re.search(re.escape(label)+r'\s+'+re.escape(version)+r'(?![0-9.])', normative_text, re.I):
            problems.append(f'embedded SSOT does not support {name} {version}')
    if problems:
        raise ValueError('UI_STACK_CONTRACT_DRIFT:'+ '; '.join(problems))


def probe(item):
    name, version = item
    url = 'https://registry.npmjs.org/' + urllib.parse.quote(name, safe='') + '/' + version
    try:
        with urllib.request.urlopen(url, timeout=30) as response: raw = response.read()
        j = json.loads(raw)
        return {'name':name, 'version':version, 'status':'PASS', 'url':url,
            'metadataSha256':hashlib.sha256(raw).hexdigest(), 'license':j.get('license'),
            'engines':j.get('engines',{}), 'peerDependencies':j.get('peerDependencies',{}),
            'repository':j.get('repository'), 'dist':j.get('dist'),
            'limitation':'Registry evidence is not a browser integration or Ubuntu build test.'}
    except Exception as exc:
        return {'name':name,'version':version,'url':url,'status':'BLOCKED','reason':str(exc)}


if __name__ == '__main__':
    verify_contract_alignment()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: results = list(pool.map(probe,PACKAGES.items()))
    out = ROOT/'audit/generated/ui-package-evidence.json'; out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'packages':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([(r['name'],r['status']) for r in results]))
