"""Read canonical embedded sources without executing or changing them."""
from pathlib import Path, PurePosixPath
import hashlib
import re
import base64
import gzip
import bisect

ROOT = Path(__file__).resolve().parents[1]
SSOT = ROOT / '00_SSOT/KajovoCMLNG_SSOT.md'
PATTERN = re.compile(
    r'^<!-- (?P<family>KCML-(?:EMBEDDED|[A-Z0-9]+-RESOURCE)) '
    r'path="(?P<path>[^"]+)"(?P<attrs>[^\n]*)-->\n'
    r'(?P<fence>`{3,})(?P<language>[^\n`]*)\n(?P<body>.*?)^(?P=fence)\n'
    r'<!-- (?P=family)-END[^\n]*-->$', re.M | re.S)


def resources(text=None):
    text = SSOT.read_text(encoding='utf-8') if text is None else text
    newlines = [m.start() for m in re.finditer('\n', text)]
    for match in PATTERN.finditer(text):
        item = match.groupdict()
        item['declared'] = dict(re.findall(r'(\w+)="([^"]*)"', item['attrs']))
        raw = item.pop('body').encode('utf-8')
        if item['declared'].get('encoding') == 'gzip+base64':
            raw = gzip.decompress(base64.b64decode(b''.join(raw.split()), validate=True))
        # Older envelopes add one presentation newline outside the declared resource.
        elif 'sha256' in item['declared'] and raw.endswith(b'\n\n'):
            if hashlib.sha256(raw[:-1]).hexdigest() == item['declared']['sha256']:
                raw = raw[:-1]
        item['raw'] = raw
        item['line'] = bisect.bisect_left(newlines, match.start()) + 1
        item['sha256'] = hashlib.sha256(raw).hexdigest()
        item['match'] = match
        yield item


def safe_path(root, name):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or ':' in name or '\\' in name:
        raise ValueError('Unsafe embedded path: ' + name)
    result = root.joinpath(*p.parts).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError('Path escapes extraction root: ' + name)
    return result


def load_resource(name, family=None):
    found = [r for r in resources() if r['path'] == name and (family is None or r['family'] == family)]
    if not found or len({r['sha256'] for r in found}) != 1:
        raise ValueError((name, 'ambiguous or missing resource', len(found)))
    return found[0]


def resource_index(items=None):
    """Deduplicate identical projections; never resolve a conflict by source order."""
    result={}
    for item in resources() if items is None else items:
        prior=result.get(item['path'])
        if prior and prior['sha256'] != item['sha256']:
            raise ValueError('SSOT_NORMATIVE_CONFLICT:'+item['path'])
        result.setdefault(item['path'],item)
    return result


def replace_resource(name, value, family=None):
    """Authoring helper: replace one canonical JSON resource and its envelope digest."""
    import json
    text = SSOT.read_text(encoding='utf-8')
    found = [r for r in resources(text) if r['path']==name and (family is None or r['family']==family)]
    if len(found)!=1: raise ValueError('Missing or ambiguous canonical resource: '+name)
    r=found[0]; raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    block=(f'<!-- {r["family"]} path="{name}" kind="JSON" bytes="{len(raw)}" '
           f'sha256="{hashlib.sha256(raw).hexdigest()}" encoding="plain" -->\n'
           '```json\n'+raw.decode()+'```\n'+f'<!-- {r["family"]}-END -->')
    m=r['match']; SSOT.write_text(text[:m.start()]+block+text[m.end():],encoding='utf-8',newline='\n')
