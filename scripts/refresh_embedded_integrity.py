"""Refresh current resource metadata; historical source digests remain provenance."""
import json,hashlib,re
from ssot_resources import SSOT,resources,capsule
text=SSOT.read_text();rs=list(resources(text));by={(r['family'],r['path']):r for r in rs};cap=capsule();changes=[]
# Inner manifests list current resource bytes, not obsolete hashes. Historical source snapshots
# keep their original digest and are not claimed to match the current full document.
for fam,path in [('KCML-R5-RESOURCE','r5-manifest.json'),('KCML-R7-RESOURCE','r7/manifest.json'),('KCML-R8-RESOURCE','r8/manifest.json')]:
 r=by[(fam,path)];d=json.loads(r['raw'])
 for item in d['resources']:
  key=(fam,item['path'])
  raw=by[key]['raw'] if key in by else cap.get(item['path'],'').encode() if item.get('storage')=='CAPSULE' else None
  if raw is not None:
   item['bytes']=len(raw);item['sha256']='sha256:'+hashlib.sha256(raw).hexdigest()
 r['raw']=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
for r in reversed(rs):
 a=r['attrs']
 if not a.get('sha256'):continue
 raw=r['raw'];sha=hashlib.sha256(raw).hexdigest()
 if sha==a['sha256'] and len(raw)==int(a['bytes']):continue
 start,end=r['span'];block=text[start:end]
 if r['path'].endswith('manifest.json') and r['family'] in ['KCML-R5-RESOURCE','KCML-R7-RESOURCE','KCML-R8-RESOURCE']:
  m=re.match(r'([^\n]+)\n(`{3,})([^\n]*)\n',block);head,fence,lang=m.groups()
  block=head+'\n'+fence+lang+'\n'+raw.decode()+'\n'+fence+'\n<!-- '+r['family']+'-END -->'
 block=re.sub(r' bytes="\d+"',f' bytes="{len(raw)}"',block,count=1)
 block=re.sub(r' sha256="[0-9a-f]+"',f' sha256="{sha}"',block,count=1)
 text=text[:start]+block+text[end:];changes.append(r['family']+':'+r['path'])
SSOT.write_text(text)
print(json.dumps({'updated':len(changes),'resources':changes}))
