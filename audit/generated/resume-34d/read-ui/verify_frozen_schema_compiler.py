import sys,json,subprocess,hashlib,copy
from pathlib import Path
from frozen_schema_compiler import *
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resources,resource_index
from create_operation_contracts import ContractFailure
oldsource=subprocess.run(['git','show','d362487999bd795d4723c2a930e93fc7aa8aa295:00_SSOT/KajovoCMLNG_SSOT.md'],cwd=ROOT,capture_output=True,check=True).stdout
oldrs=resource_index(resources(oldsource.decode()));newrs=resource_index()
def body(rs):return next(row['requestSchema']['properties']['body']for row in json.loads(rs['contracts/payload-contracts.json']['raw'])['records']if row['operationId']=='generation.job.create')
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
old=canonical(body(oldrs));new=canonical(body(newrs));oldaddress={'schemaId':body(oldrs)['$id'],'bundleDigest':sha(old),'definition':None};newaddress={'schemaId':body(newrs)['$id'],'bundleDigest':sha(new),'definition':None};bundles={sha(old):old,sha(new):new};checks=[]
def positive(name,f):f();checks.append({'id':name,'passed':True})
def negative(name,code,f):
 try:f()
 except ContractFailure as e:assert e.code==code,(name,code,e.code);checks.append({'id':name,'passed':True,'expectedDiagnostic':code,'actualDiagnostic':e.code});return
 raise AssertionError(name+' accepted')
assert old!=new and oldaddress['schemaId']==newaddress['schemaId']
legacy={'intent':'Synthetic unchanged UPDATE intent','kind':'UPDATE','targetKind':'PLATFORM_COMPONENT','targetObjectId':'00000000-0000-4000-8000-000000000001'}
positive('actual-historical-request-schema-accepts-own-valid-witness',lambda:compile_frozen(oldaddress,bundles)(legacy))
negative('current-body-must-not-be-substituted-for-archive','FROZEN_SCHEMA_CONTENT_INVALID',lambda:compile_frozen(newaddress,bundles)(legacy))
positive('same-id-archives-remain-independently-resolvable',lambda:compile_frozen(oldaddress,bundles)(legacy))
negative('wrong-declared-bundle-digest','FROZEN_SCHEMA_BUNDLE_DIGEST_MISMATCH',lambda:compile_frozen(oldaddress,{sha(old):new}))
negative('missing-archive-does-not-use-current','FROZEN_SCHEMA_BUNDLE_UNAVAILABLE',lambda:compile_frozen(oldaddress,{sha(new):new}))
negative('wrong-schema-id','FROZEN_SCHEMA_ID_MISMATCH',lambda:compile_frozen({**oldaddress,'schemaId':'urn:wrong'},bundles))
negative('same-closure-alias-conflict','FROZEN_SCHEMA_DEPENDENCY_ALIAS_CONFLICT',lambda:compile_frozen(oldaddress,bundles,dependencies=[{'schemaId':newaddress['schemaId'],'bundleDigest':newaddress['bundleDigest']}]))
negative('undeclared-definition','FROZEN_SCHEMA_DEFINITION_UNRESOLVED',lambda:compile_frozen({**oldaddress,'definition':'MISSING'},bundles))
for name,patch in [('unknown-property',{'unknown':1}),('null-kind',{'kind':None}),('wrong-kind',{'kind':'AUTOGUESS'})]:
 negative(name,'FROZEN_SCHEMA_CONTENT_INVALID',lambda patch=patch:compile_frozen(oldaddress,bundles)({**legacy,**patch}))
report={'status':'PASS','checked':len(checks),'failed':0,'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'historicalSourceCommit':'d362487999bd795d4723c2a930e93fc7aa8aa295','historicalSourceSha256':hashlib.sha256(oldsource).hexdigest(),'historicalSchemaAddress':oldaddress,'currentSchemaAddress':newaddress,'checks':checks,'supportSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in [HERE/'frozen_schema_compiler.py',Path(__file__)]},'scope':'Actual historical/current masks independently resolved despite same$id. Structural archive compilation only; archived domain-policy consumer/producer and durable registry availability NOT proven','wholeOperationClosed':False}
(HERE/'frozen-schema-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checks),'PASS')
