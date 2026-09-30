"""Current authoritative SQL syntax and exact locator/advisory design checks."""
import hashlib,json,os,struct,subprocess
from pathlib import Path
import pglast
from ssot_sources import ROOT,SSOT,resource_index

def constraints(sql):
 ast=json.loads(pglast.parser.parse_sql_json(sql));table=next(s['stmt']['CreateStmt'] for s in ast['stmts'] if s['stmt'].get('CreateStmt',{}).get('relation',{}).get('relname')=='idempotency_locator');column=next(e['ColumnDef'] for e in table['tableElts'] if e.get('ColumnDef',{}).get('colname')=='logical_operation_id');return [x['Constraint'] for x in column['constraints']]
def unique(cs):return any(c['contype']=='CONSTR_UNIQUE' for c in cs)
def deferred(cs):
 i=next((i for i,c in enumerate(cs) if c['contype']=='CONSTR_FOREIGN'),None)
 if i is None:return False
 attrs={c['contype'] for c in cs[i+1:]};return (cs[i].get('deferrable') or 'CONSTR_ATTR_DEFERRABLE' in attrs) and (cs[i].get('initdeferred') or 'CONSTR_ATTR_DEFERRED' in attrs)
def main():
 source=SSOT.read_bytes();rs=resource_index();sql=rs['database/explicit-entities.sql']['raw'].decode();advisory=rs['database/postgres-advisory-key.sql']['raw'].decode();checks=[]
 def check(id_,passed):checks.append({'id':id_,'passed':bool(passed)})
 cs=constraints(sql);check('locator.unique',unique(cs));check('locator.deferredFK',deferred(cs));check('locator.preservedFKtarget',next(c for c in cs if c['contype']=='CONSTR_FOREIGN')['pktable']['relname']=='domain_command')
 for id_,mutant,test in [('missing-unique',sql.replace('logical_operation_id uuid NOT NULL UNIQUE REFERENCES','logical_operation_id uuid NOT NULL REFERENCES'),unique),('nondeferred-fk',sql.replace(' DEFERRABLE INITIALLY DEFERRED',''),deferred)]:check('negative/'+id_,not test(constraints(mutant)))
 pglast.parse_sql(advisory);pglast.parse_plpgsql(advisory);check('advisory.sql+plpgsqlSyntax',True)
 heads=['00000000','00000001','00000100','00010000','01000000','7fffffff','80000000','80000001','ffffffff'];raws=[bytes.fromhex(h)+bytes(range(4,32)) for h in heads];vectors=[{'digestHex':r.hex(),'expected':struct.unpack('>i',r[:4])[0]} for r in raws]
 js='const rows=JSON.parse(process.argv[1]);process.stdout.write(JSON.stringify(rows.map(r=>Buffer.from(r.digestHex,"hex").readInt32BE(0))));';actual=json.loads(subprocess.check_output(['node','-e',js,json.dumps(vectors)]))
 for v,a in zip(vectors,actual):check('advisory/'+v['digestHex'][:8],a==v['expected'])
 def reference(raw):
  if not isinstance(raw,bytes) or len(raw)!=32:raise ValueError('ADVISORY_KEY_REQUIRES_SHA256_DIGEST')
  return struct.unpack('>i',raw[:4])[0]
 for id_,v in [('null',None),('short',raws[0][:-1])]:
  try:reference(v);rejected=False
  except ValueError as e:rejected=str(e)=='ADVISORY_KEY_REQUIRES_SHA256_DIGEST'
  check('negative/advisory-'+id_,rejected)
 check('negative/littleEndian',any(int.from_bytes(r[:4],'little',signed=True)!=v['expected'] for r,v in zip(raws,vectors)))
 check('negative/unsignedOverflow',any(int.from_bytes(r[:4],'big',signed=False)!=v['expected'] for r,v in zip(raws,vectors)))
 if SSOT.read_bytes()!=source:raise RuntimeError('SSOT_INPUT_CHANGED')
 report={'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'requirementsSha256':hashlib.sha256((ROOT/'requirements-audit.txt').read_bytes()).hexdigest(),'nodeVersion':subprocess.check_output(['node','--version']).decode().strip(),'sourceDocumentSha256':hashlib.sha256(source).hexdigest(),'resources':{p:rs[p]['sha256'] for p in ['database/explicit-entities.sql','database/postgres-advisory-key.sql']},'pglastVersion':pglast.__version__,'checked':len(checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,'vectors':vectors,'scope':'PostgreSQL17 syntax and independent design vectors; actual PostgreSQL18.6 SQL execution NOT_RUN','missingOperationHelpers':'BLOCKED','implementationAcceptance':'NOT_EVALUATED'}
 out=ROOT/os.environ.get('KCML_AUDIT_OUTPUT','audit/generated/resume-5334/coordinator');out.mkdir(parents=True,exist_ok=True);(out/'create-storage-invariants.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['sourceDocumentSha256','checked','failed']}));return int(bool(report['failed']))
if __name__=='__main__':raise SystemExit(main())
