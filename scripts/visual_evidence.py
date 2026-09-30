"""Validate consumed-source reference evidence; never claim manual/UI semantic closure."""
import hashlib,json
from ssot_sources import ROOT,resource_index,safe_path

def verify_reference(report):
 issues=[]
 def check(ok,message):
  if not ok:issues.append(message)
 def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
 live=json.loads(resource_index()['ui/contracts/live-experience.json']['raw'])
 expected={(view['id'],locale,viewport) for view in live['views'] for locale in ['cs','en'] for viewport in live['viewports']}
 rows=report.get('results',[])
 observed=[(r.get('viewId'),r.get('locale'),r.get('viewport')) for r in rows]
 check(report.get('status')=='PASS' and report.get('failed')==0,'reference renderer not successful')
 check(report.get('views')==len(expected)==len(rows),'reference count differs from effective view/locale/viewport contract')
 check(len(observed)==len(set(observed)) and set(observed)==expected,'incomplete/duplicate reference render universe')
 check(report.get('scriptSha256')==sha(ROOT/'scripts/render_reference.py'),'reference renderer changed')
 check(report.get('environment',{}).get('auditRequirementsSha256')==sha(ROOT/'requirements-audit.txt'),'reference audit requirements changed')
 bindings=report.get('sourceHashes',{})
 check(bool(bindings),'reference source bindings missing')
 for path,digest in bindings.items():
  p=safe_path(ROOT,path);check(p.is_file() and sha(p)==digest,'render source drift '+path)
 for path,digest in report.get('embeddedResourceSha256',{}).items():check(resource_index()[path]['sha256']==digest,'embedded render contract drift '+path)
 check(set(report.get('embeddedResourceSha256',{}))=={'ui/contracts/live-experience.json','ui/contracts/ui-control-registry.json','closure/contracts/ui-action-resolution.json'},'missing embedded render contract bindings')
 for row in rows:
  p=safe_path(ROOT,row['screenshot']);check(p.is_file() and sha(p)==row.get('screenshotSha256'),'screenshot drift '+row['screenshot'])
 for row in report.get('derivativeScreenshotAliases',[]):
  path=row.get('path') or row.get('destination') or row.get('screenshot');digest=row.get('sha256') or row.get('screenshotSha256')
  if path and digest:
   p=safe_path(ROOT,path);check(p.is_file() and sha(p)==digest,'derived screenshot drift '+path)
 return issues
