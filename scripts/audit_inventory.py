"""Reproducible structural audit; semantic/visual completion is never inferred."""
import ast
import csv
import hashlib
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
import base64
import lzma
import zlib
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from PIL import Image
from jsonschema import Draft202012Validator
from ssot_sources import ROOT, SSOT, resources

EXCLUDED = {'.git': 'Git object database, not package content', '.cache': 'Reproducible temporary tool output',
            '__pycache__': 'Python bytecode', 'node_modules': 'Installed dependencies'}


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        self.links.extend(v for k, v in attrs if k in ('src', 'href') and v)


def validate_content(path, raw):
    suffix = Path(path).suffix.lower(); checks = []; issues = []
    if suffix == '.png':
        with Image.open(io.BytesIO(raw)) as im:
            size = list(im.size); im.verify()
        return ['PNG_DECODE', 'dimensions=' + str(size)], []
    text = raw.decode('utf-8'); checks.append('UTF8')
    if suffix == '.json':
        value = json.loads(text); checks.append('JSON_PARSE')
        if isinstance(value, dict) and value.get('$schema') == 'https://json-schema.org/draft/2020-12/schema':
            Draft202012Validator.check_schema(value); checks.append('JSON_SCHEMA_META')
    elif suffix == '.py':
        ast.parse(text, filename=str(path)); checks.append('PYTHON_SYNTAX')
    elif suffix == '.csv':
        rows = list(csv.reader(io.StringIO(text))); checks.append('CSV_PARSE')
        if rows and any(len(r) != len(rows[0]) for r in rows): issues.append('CSV_RAGGED_ROWS')
    elif suffix == '.svg':
        ET.fromstring(text); checks.append('XML_PARSE')
    elif suffix == '.html':
        parser = Links(); parser.feed(text); checks.append('HTML_PARSE')
        for link in parser.links:
            if link.startswith(('#', 'http:', 'https:', 'data:', 'mailto:', 'javascript:')): continue
            target = (ROOT / path).parent / link.split('#')[0].split('?')[0]
            if not target.exists(): issues.append('MISSING_LINK:' + link)
    return checks, issues


def build():
    report = {'format': 'KCML-AUDIT-INVENTORY/1', 'excluded': EXCLUDED, 'files': [], 'embedded': [], 'capsules': [],
              'scope': 'All package files and direct embedded resources. Structural results do not imply semantic or visual closure.'}
    archive_index=ROOT/'audit/provenance/INDEX.json'
    archived={r['archivePath']:r for r in json.loads(archive_index.read_text(encoding='utf-8'))['records']} if archive_index.exists() else {}
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or any(x in EXCLUDED for x in p.relative_to(ROOT).parts): continue
        rel = p.relative_to(ROOT).as_posix()
        # Reports/manifests have a self-reference-free integrity check in verify_package.py.
        if rel.startswith('audit/generated/') or rel == 'FILE_MANIFEST_SHA256.json': continue
        raw = p.read_bytes()
        try: checks, issues = validate_content(rel, raw)
        except Exception as exc: checks, issues = [], [type(exc).__name__ + ':' + str(exc)]
        historical=rel in archived
        if historical and hashlib.sha256(raw).hexdigest()!=archived[rel]['actualSha256']:issues.append('ARCHIVED_BYTES_CHANGED')
        report['files'].append({'path': rel, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'purpose': 'canonical specification' if p == SSOT else 'package source or projection',
            'checks': checks, 'issues': issues, 'structuralStatus': 'FAIL' if issues else 'PASS',
            'authority':'HISTORICAL_EVIDENCE_ONLY' if historical else 'PACKAGE_SOURCE_OR_PROJECTION',
            'semanticStatus': 'NOT_EVALUATED', 'visualStatus': 'NOT_EVALUATED' if p.suffix in ('.png','.html','.svg') else 'NOT_APPLICABLE'})
    seen = set()
    for r in resources():
        key = (r['family'], r['path']); errors = []
        if key in seen: errors.append('DUPLICATE_RESOURCE')
        seen.add(key)
        for field, actual in [('bytes', str(len(r['raw']))), ('sha256', r['sha256'])]:
            if field in r['declared'] and r['declared'][field] != actual: errors.append('RESOURCE_' + field.upper() + '_MISMATCH')
        try: checks, issues = validate_content(r['path'], r['raw']); errors.extend(issues)
        except Exception as exc: checks = []; errors.append(type(exc).__name__ + ':' + str(exc))
        report['embedded'].append({'family': r['family'], 'path': r['path'], 'line': r['line'],
            'sha256': r['sha256'], 'bytes': len(r['raw']), 'checks': checks, 'issues': errors,
            'structuralStatus': 'FAIL' if errors else 'PASS', 'semanticStatus': 'NOT_EVALUATED'})
        if r['path'].endswith('.json'):
            try: value=json.loads(r['raw'])
            except ValueError: continue
            if isinstance(value,dict) and value.get('format')=='KCML-UTF8-RESOURCE-MAP-XZ/1':
                capsule_errors=[]
                try:
                    compressed=base64.b64decode(''.join(value['dataSegments']),validate=True)
                    decoded=lzma.decompress(compressed)
                    for prefix,blob in [('compressed',compressed),('decoded',decoded)]:
                        if len(blob)!=value[prefix+'Bytes']:capsule_errors.append(prefix+'_BYTES_MISMATCH')
                        if 'sha256:'+hashlib.sha256(blob).hexdigest()!=value[prefix+'Sha256']:capsule_errors.append(prefix+'_HASH_MISMATCH')
                    nested=json.loads(decoded)
                    if set(nested)!=set(value['resourcePaths']):capsule_errors.append('PATH_SET_MISMATCH')
                    for name,content in nested.items():
                        raw=content.encode('utf-8')
                        try:checks,issues=validate_content(name,raw)
                        except Exception as exc:checks=[];issues=[str(exc)]
                        report['capsules'].append({'container':r['family']+'/'+r['path'],'path':name,'bytes':len(raw),
                            'sha256':hashlib.sha256(raw).hexdigest(),'checks':checks,'issues':issues,
                            'structuralStatus':'FAIL' if issues or capsule_errors else 'PASS','semanticStatus':'NOT_EVALUATED'})
                    if capsule_errors:report['embedded'][-1]['issues'].extend(capsule_errors);report['embedded'][-1]['structuralStatus']='FAIL'
                except Exception as exc:
                    report['embedded'][-1]['issues'].append('CAPSULE_DECODE:'+str(exc));report['embedded'][-1]['structuralStatus']='FAIL'
    report['summary'] = {'files': len(report['files']), 'directEmbeddedResources': len(report['embedded']),
        'decodedCapsuleFiles':len(report['capsules']),
        'structuralFailures': sum(x['structuralStatus']=='FAIL' and (x.get('authority')!='HISTORICAL_EVIDENCE_ONLY' or 'ARCHIVED_BYTES_CHANGED' in x['issues']) for x in report['files']+report['embedded']+report['capsules']),
        'historicalFailuresPreserved':sum(x['structuralStatus']=='FAIL' and x.get('authority')=='HISTORICAL_EVIDENCE_ONLY' for x in report['files']),
        'families': dict(Counter(x['family'] for x in report['embedded']))}
    return report


if __name__ == '__main__':
    output = ROOT / 'audit/generated/inventory.json'; output.parent.mkdir(parents=True, exist_ok=True)
    report = build(); output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report['summary']))
    sys.exit(bool(report['summary']['structuralFailures']))
