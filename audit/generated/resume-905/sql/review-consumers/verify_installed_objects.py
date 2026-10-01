"""Actual installed object inventory after independent canonical PG executions."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
rs=resource_index();checks=[]
for database,paths in [('archive_independent_sql_905',['database/generation-create-foundations.sql','database/generation-frozen-archive.sql','database/generation-create-read.sql']),('retry_independent_sql_905',['database/generation-create-foundations.sql','database/generation-locked-retry.sql','database/generation-retry-producer-child.sql'])]:
 def query(sql):
  r=subprocess.run(['/tmp/kcml-pg18/bin/psql','-X','-q','-h','/tmp/kcml-pg18-socket','-p55432','-d',database,'-At','-v','ON_ERROR_STOP=1'],input=sql,text=True,capture_output=True)
  if r.returncode:raise ValueError(r.stderr)
  return r.stdout.strip()
 for path in paths:
  text=rs[path]['raw'].decode()
  for kind,pattern in [('table',r'(?i)CREATE\s+TABLE\s+([a-z_0-9.]+)'),('function',r'(?i)CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+([a-z_0-9.]+)'),('role',r'(?i)CREATE\s+ROLE\s+([a-z_0-9]+)')]:
   for name in sorted(set(re.findall(pattern,text))):
    if kind=='table':present=query("SELECT to_regclass('"+name+"') IS NOT NULL")=='t'
    elif kind=='function':
     namespace,fn=name.split('.')if'.'in name else('public',name)
     present=query("SELECT count(*)>0 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='"+namespace+"' AND p.proname='"+fn+"'")=='t'
    else:present=query("SELECT count(*)>0 FROM pg_roles WHERE rolname='"+name+"'")=='t'
    checks.append(dict(database=database,path=path,kind=kind,name=name,present=present))
report=dict(sourceDocumentSha256=hashlib.sha256(SSOT.read_bytes()).hexdigest(),postgresVersion=query('SHOW server_version'),bindings={p:rs[p]['sha256']for p in sorted({c['path']for c in checks})},checks=checks,failed=sum(not c['present']for c in checks),scope='Actual pg_class/pg_proc/pg_roles object presence after exact canonical embedded SQL execution in independent own DBs. Installation-object proof only; no complete service-role security/context/dispatch or implementation acceptance.')
(OUT/'installed-canonical-objects.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(objects=len(checks),failed=report['failed'])));raise SystemExit(bool(report['failed']))
