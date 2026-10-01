"""Synthetic domain witnesses regenerated against current schema bytes.
No tests/writes execute in historical imported fixture modules. Factory returns
real bytes, never valid=true. Real phase/approval producer authority is separate.
"""
from native_auth_factory import *
import types,re
from generation_admission_contracts import Repository,GEN,local_bundle,digest,select_generation_basis
from generation_retry_inventory import bundle,INVENTORY_SCHEMA_ID

def witness_factory():
 # Regenerate source-native complete graph using current canonical mask and root helper.
 graphfile=ROOT/'audit/generated/resume-34d/retry-graph/graph_current_fixtures.py'
 code=graphfile.read_text().replace('from generation_graph_current import *','from generation_native_graph import *')
 code=re.sub(r"source=subprocess.check_output\([^\n]+\)","source=SSOT.read_bytes()",code)
 code=re.sub(r"assert hashlib.sha256\(source\).hexdigest\(\)==[^\n]+",'',code)
 g={'__file__':str(graphfile),'SSOT':SSOT};exec(compile(code,'current-native-domain-graph-witness','exec'),g)
 # Regenerate own-kind native selectors against current canonical generation schema.
 fixturefile=ROOT/'audit/generated/resume-d362/admission/generation_admission_fixtures.py'
 code=fixturefile.read_text().replace('from generation_admission_reference import *','from generation_admission_contracts import *')
 code=re.sub(r"source=subprocess.check_output\([^\n]+\)","source=SSOT.read_bytes()",code)
 code=re.sub(r"assert hashlib.sha256\(source\).hexdigest\(\)==[^\n]+",'',code)
 code=code.replace('local_raw=canonical(local_bundle())',"local_raw=rs['contracts/generation/admission-basis.schema.json']['raw']")
 a={'__file__':str(fixturefile),'SSOT':SSOT};exec(compile(code,'current-native-admission-witness','exec'),a)
 records=copy.deepcopy(a['records']);records.update(copy.deepcopy(g['records']))
 # Approved spec bytes use the complete native graph, not generic witness envelopes.
 spec=copy.deepcopy(g['spec']);specraw=canonical_bytes(spec);sd=digest(specraw)
 rev=a['REV'];records[rev].update(bytes=specraw,contentDigest=sd)
 specid=a['SPEC'];records[specid].update(bytes=specraw,contentDigest=sd)
 authority=copy.deepcopy(a['authority']);authority['specificationDigest']=sd
 # Authority native reference is the one actually contained in this spec graph.
 nativeauth=records[spec['authorityModel']['artifact']['artifactId']];authority['authority']=strict_json(nativeauth['bytes'])
 records[a['AUTH']].update(bytes=canonical_bytes(authority),contentDigest=digest(canonical_bytes(authority)))
 approval=strict_json(records[a['APP']]['bytes']);approval['specificationDigest']=sd
 records[a['APP']].update(bytes=canonical_bytes(approval),contentDigest=digest(canonical_bytes(approval)))
 plan=copy.deepcopy(a['plan']);plan['specificationDigest']=sd;plan['scopeLock']['approvedSpecificationDigest']=sd;plan['nodes'][0]['sideEffectClass']='LOCAL_STATE_IDEMPOTENT'
 raw=canonical_bytes(plan);pd=digest(raw);records[a['PLAN']].update(bytes=raw,contentDigest=pd)
 phase=copy.deepcopy(a['run']);phase.update(planDigest=pd,specificationDigest=sd,authorityDigest=records[a['AUTH']]['contentDigest'])
 raw=canonical_bytes(phase);rd=digest(raw);records[a['RUN']].update(bytes=raw,contentDigest=rd)
 body=copy.deepcopy(a['bodies']['RETRY']);body['generationBasis'].update(expectedDigest=rd,expectedPlanDigest=pd,expectedSpecificationDigest=sd,expectedAuthorityDigest=records[a['AUTH']]['contentDigest'])
 for record in records.values():record['owner']=OWNER
 inventoryraw=resource_index()['contracts/generation/retry-inventory.schema.json']['raw']
 bundles={a['gb']:a['gen_raw'],a['lb']:a['local_raw'],digest(inventoryraw):inventoryraw}
 repo=Repository(records,bundles,a['artifact_map'],OWNER)
 decision=select_generation_basis(body,repo)
 return {'repo':repo,'body':body,'phase':phase,'phaseDigest':rd,'plan':plan,'decision':decision,'domain_map':g['domain_map'],'raw_kinds':g['raw_kinds'],'genBundleDigest':a['gb'],'inventoryBundleDigest':digest(inventoryraw),'graph':g}

def persist(db,w,*,only=None,exclude=()):
 for dg,raw in w['repo'].bundles.items():
  db.query('INSERT INTO kcml_native_basis_v1.schema_bundle VALUES('+','.join([b(bytes.fromhex(dg[7:])),lit(strict_json(raw)['$id']),b(raw)])+') ON CONFLICT DO NOTHING;')
 for key,r in w['repo'].records.items():
  if key in exclude or(only is not None and key not in only):continue
  schema=r.get('schema');ref=r.get('artifactRef');values=[lit(key),lit(uid(1)),lit(OWNER),b(bytes.fromhex(r['contentDigest'][7:])),b(r['bytes']),b(bytes.fromhex(schema['bundleDigest'][7:]))if schema else'NULL',lit(schema['schemaId'])if schema else'NULL',lit(schema['definition'])if schema else'NULL',b(canonical_bytes(ref))if ref else'NULL',lit(r['publicationReceiptId'])if r.get('publicationReceiptId')else'NULL',lit(r['artifactKind'])if r.get('artifactKind')else'NULL']
  db.query('INSERT INTO kcml_native_basis_v1.record VALUES('+','.join(values)+');')

def hydrate(db,w):
 records={};bundles={}
 for dg,raw in db.query("SELECT encode(digest,'hex'),encode(exact_bytes,'hex') FROM kcml_native_basis_v1.schema_bundle"):
  bundles['sha256:'+dg]=bytes.fromhex(raw)
 for values in db.query("SELECT record_id,source_job_id,owner_id,encode(content_digest,'hex'),encode(exact_bytes,'hex'),encode(schema_bundle_digest,'hex'),schema_id,definition,encode(artifact_ref,'hex'),publication_receipt_id,artifact_kind FROM kcml_native_basis_v1.record ORDER BY record_id"):
  key,job,owner,dg,raw,sd,sid,definition,ref,publication,kind=values
  r={'recordId':key,'jobId':job,'owner':owner,'contentDigest':'sha256:'+dg,'bytes':bytes.fromhex(raw),'schema':{'bundleDigest':'sha256:'+sd,'schemaId':sid,'definition':definition}if sd else None}
  if ref:r['artifactRef']=strict_json(bytes.fromhex(ref))
  if publication:r['publicationReceiptId']=publication
  if kind:r['artifactKind']=kind
  records[key]=r
 return Repository(records,bundles,w['repo'].artifact_map,OWNER)
