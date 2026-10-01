"""Execute an original bounded fixture, isolate only DB identities and audit writes.
No source/hash replacement, altered mask, weakened negative or historical PASS.
"""
from pathlib import Path
import sys,json,hashlib,traceback,re,os
ROOT=Path('/workspace/kajovocmlng');HERE=Path(__file__).parent
sys.dont_write_bytecode=True
LABEL=sys.argv[1];OUT=Path(sys.argv[2]).resolve();OUT.mkdir(parents=True,exist_ok=True)
assert OUT.is_relative_to(HERE.resolve()),'OUTPUT_MUST_BE_OWNED'
SPEC=json.loads((HERE/'bounded_spec.json').read_text())[LABEL]
source_start=(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()
original_read=Path.read_text;original_write=Path.write_text;original_write_bytes=Path.write_bytes
# All original/nested fixture databases are rewritten consistently, never user DBs.
known=['archive_joined_905','archive_peer_key_fixed_905','auth_crypto_full_34d','archive_independent_sql_905','generation_independent_review_fixture','retry_preserved_stage_8cc','independent_preroot_archive_sql905','pending_transfer_34d','secret_publication_review_905','secret_owner_review_905','review_auth_chain_sql905']
DB_MAP={n:'cr8_'+LABEL.replace('-','_')+'_'+n for n in known}
DB_MAP={a:b[:63]for a,b in DB_MAP.items()};writes=[];reads=[]
def transform(raw):
 for old,new in DB_MAP.items():raw=raw.replace(old,new)
 return raw
def read_text(p,*args,**kwargs):
 emitted={w['originalPath']:w['ownedPath'] for w in writes}
 if str(p.resolve()) in emitted:return original_read(Path(emitted[str(p.resolve())]),*args,**kwargs)
 raw=original_read(p,*args,**kwargs)
 if p.suffix=='.py'and p.resolve().is_relative_to(ROOT):
  changed=transform(raw);reads.append({'path':str(p.resolve().relative_to(ROOT)),'originalSha256':hashlib.sha256(raw.encode()).hexdigest(),'executionSha256':hashlib.sha256(changed.encode()).hexdigest()});return changed
 return raw
def destination(p):
 p=p.resolve()
 if p.is_relative_to(OUT):return p
 if p.is_relative_to(ROOT):return OUT/'tree'/p.relative_to(ROOT)
 raise RuntimeError('FIXTURE_WRITE_OUTSIDE_OWNED_TREE:'+str(p))
def write_text(p,data,*args,**kwargs):
 target=destination(p);target.parent.mkdir(parents=True,exist_ok=True);writes.append({'originalPath':str(p),'ownedPath':str(target),'sha256':hashlib.sha256(data.encode()).hexdigest()});return original_write(target,data,*args,**kwargs)
def write_bytes(p,data,*args,**kwargs):
 target=destination(p);target.parent.mkdir(parents=True,exist_ok=True);writes.append({'originalPath':str(p),'ownedPath':str(target),'sha256':hashlib.sha256(data).hexdigest()});return original_write_bytes(target,data,*args,**kwargs)
Path.read_text=read_text;Path.write_text=write_text;Path.write_bytes=write_bytes
# Stop unknown database access before any original fixture can mutate it.
sys.path.insert(0,str(ROOT/'audit/generated/resume-34d/auth-crypto'))
import libpq_fixture,subprocess
original_db_init=libpq_fixture.DB.__init__;original_run=subprocess.run;original_popen=subprocess.Popen
connections=[]
def guard_database(name):
 if name!='postgres'and not name.startswith('cr8_'+LABEL.replace('-','_')+'_'):raise RuntimeError('UNISOLATED_FIXTURE_DATABASE:'+name)
 connections.append(name)
def db_init(self,name):guard_database(name);return original_db_init(self,name)
def subprocess_guard(argv):
 if isinstance(argv,(list,tuple))and argv and str(argv[0]).endswith('/psql'):
  if '-d'in argv:guard_database(str(argv[argv.index('-d')+1]))
  else:raise RuntimeError('PSQL_DATABASE_NOT_EXPLICIT')
def sub_run(argv,*a,**kw):subprocess_guard(argv);return original_run(argv,*a,**kw)
def sub_popen(argv,*a,**kw):subprocess_guard(argv);return original_popen(argv,*a,**kw)
libpq_fixture.DB.__init__=db_init;subprocess.run=sub_run;subprocess.Popen=sub_popen
failures=[]
try:
 for rel in SPEC['scripts']:
  p=ROOT/rel;program=read_text(p)
  # A child fixture retains its original __file__/input paths and proof algebra.
  # Only virtual audit writes and explicitly enumerated DB names change.
  try:exec(compile(program,str(p),'exec'),{'__file__':str(p),'__name__':'__bounded_fixture__'})
  except SystemExit as e:
   if e.code not in (None,0):raise
finally:
 Path.read_text=original_read;Path.write_text=original_write;Path.write_bytes=original_write_bytes
 libpq_fixture.DB.__init__=original_db_init;subprocess.run=original_run;subprocess.Popen=original_popen
 source_end=(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()
 manifest={'label':LABEL,'sourceDocumentSha256':hashlib.sha256(source_start).hexdigest(),'sourceUnchangedDuringRun':source_start==source_end,'originalScripts':SPEC['scripts'],'databaseIsolation':DB_MAP,'actualDatabaseConnections':sorted(set(connections)),'executedPythonReads':reads,'redirectedWrites':writes,'scope':'Original bounded fixture semantics; only isolated database names/audit output paths. No historical evidence source relabeling or whole-operation claim.'}
 (OUT/'execution-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert source_start==source_end,'SSOT_CHANGED_DURING_FIXTURE'
