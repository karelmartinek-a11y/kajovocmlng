"""Capture official npm metadata for exact UI dependency selection; no package scripts."""
import concurrent.futures
import hashlib
import json
import urllib.request
import urllib.parse
from ssot_sources import ROOT

PACKAGES = {
 'react': '18.3.1', 'react-dom': '18.3.1', 'vite': '6.3.5',
 '@xyflow/react': '12.8.5', '@radix-ui/react-context-menu': '2.2.16',
 '@radix-ui/react-dialog': '1.1.15', '@radix-ui/react-tooltip': '1.2.8',
 '@radix-ui/react-popover': '1.1.15', '@tanstack/react-table': '8.21.3',
 'papaparse': '5.5.3', 'exceljs': '4.4.0', 'pdfjs-dist': '5.4.149',
 '@dnd-kit/core': '6.3.1', '@dnd-kit/sortable': '10.0.0'}


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
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: results = list(pool.map(probe,PACKAGES.items()))
    out = ROOT/'audit/generated/ui-package-evidence.json'; out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'packages':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([(r['name'],r['status']) for r in results]))
