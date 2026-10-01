"""Reuse historical bounded evidence only when every declared consumed input remains exact.
Execution identity is preserved. New producer modules are outside this prior scope.
"""
import hashlib,re,subprocess
from ssot_sources import ROOT,SSOT,resource_index,resources
PIN='905555e47f3547516439a699e262df62cbbec229'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def section(text,n):
 m=re.search(r'^#{2,3} '+re.escape(n)+r'(?:\.| )[^\n]*\n',text,re.M)
 if not m:raise ValueError('AUTHORITY_SECTION_MISSING:'+n)
 level=m.group().count('#');end=re.search(r'^#{2,'+str(level)+r'} ',text[m.end():],re.M)
 return text[m.start():m.end()+end.start() if end else len(text)]
def secret_scope_current(q):
 source=q.get('sourceDocumentSha256',q.get('sourceSha256',q.get('inputSsotSha256')))
 if source==digest(SSOT.read_bytes()):return True
 old=subprocess.check_output(['git','show',PIN+':00_SSOT/KajovoCMLNG_SSOT.md'],cwd=ROOT)
 if source!=digest(old):return False
 before=old.decode();after=SSOT.read_text()
 from close_producer_archive_handoffs import SECRET_NORM
 if after.count(SECRET_NORM)!=1:return False
 after=after.replace(SECRET_NORM,'')
 # These exact additive reviewed paragraphs change root presentation/handoffs,
 # not the prior isolated import parsers/schema/cookie fixture consumed scope.
 from secret_root_status_authority import ROOT_STATUS_NORM,decision_approved
 from close_retry_authority_handoffs import SECRET_NORM as OWNER_VALUE_READ_NORM
 from close_secret_effective_handoffs import NORM as DERIVED_STATUS_NORM
 if not decision_approved():return False
 for norm in [ROOT_STATUS_NORM,OWNER_VALUE_READ_NORM,DERIVED_STATUS_NORM]:
  if after.count(norm)!=1:return False
  after=after.replace(norm,'',1)

 # Prior fixture authority: entire Secrets chapter plus browser continuity and UI.
 if any(section(before,n)!=section(after,n)for n in ['8','13.15','72.21']):return False
 rs=resource_index();previous=resource_index(resources(before))
 declared=q.get('sourceResourceSha256',q.get('canonicalResourceSha256',{}))
 if isinstance(declared,str):declared={q['canonicalResource']:declared}
 required={'contracts/secrets/profile-handoffs.schema.json'}
 if not required<=set(declared):return False
 for name,d in declared.items():
  if name not in rs or name not in previous or rs[name]['sha256']!=d or previous[name]['sha256']!=d:return False
 supports={**{str(ROOT/'scripts'/n):d for n,d in q.get('rootImplementationDigests',{}).items()},**q.get('supportSha256',{})}
 if not supports:return False
 for name,d in supports.items():
  p=ROOT/name
  if not p.is_file()or digest(p.read_bytes())!=d:return False
 return q.get('failed')==0
