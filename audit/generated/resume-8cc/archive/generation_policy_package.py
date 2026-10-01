"""Installer-owned source package; static digest dispatch, no eval/latest fallback."""
import json,hashlib,copy,re
from pathlib import Path
from create_operation_contracts import strict_json,ContractFailure
from generation_frozen_schema_compiler import compile_frozen
from generation_admission_contracts import Repository
import generation_own_kind_policy_v1 as own_kind
from ssot_sources import SSOT
ROOT=SSOT.parents[1];HERE=Path(__file__).parent
PACKAGE_ID='urn:kcml:generation:kind-policy-package:1'
DEPENDENCIES=['generation_admission_contracts.py','create_operation_contracts.py','follow_up_contracts.py','create_completion_contracts.py','generation_frozen_schema_compiler.py','generation_create_consumer.py','generation_frozen_archive.py','generation_native_graph.py','generation_basis_consumer.py','generation_retry_inventory.py','generation_locked_retry.py','generation_request_policy_v1.py','ssot_sources.py']
def digest(raw):return 'sha256:'+hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def fail(code):raise ContractFailure(code,'')
def known_sources():
 return {'urn:kcml:policy-source:'+n:(ROOT/'scripts'/n).read_bytes()for n in DEPENDENCIES}|{'urn:kcml:policy-source:generation_own_kind_policy_v1.py':(HERE/'generation_own_kind_policy_v1.py').read_bytes(),'urn:kcml:policy-source:generation_policy_package.py':Path(__file__).read_bytes()}
TRUSTED_SOURCES=known_sources()
def build_package(rs,request_schema_bytes,request_policy_bytes,authority_bytes):
 """Trusted deployment author consumes exact normative resources and real sources.
 Not called from public request/model data; SQL installer role owns acceptance.
 """
 blobs={}
 def add(kind,id,raw):
  blobs[(kind,id,digest(raw))]=raw
  return {'kind':kind,'id':id,'digest':digest(raw)}
 members=[add('SCHEMA',json.loads(request_schema_bytes)['$id'],request_schema_bytes)]
 members +=[add('DOMAIN_POLICY',json.loads(request_policy_bytes)['policyId'],request_policy_bytes),add('AUTHORITY','SSOT#12.51-55',authority_bytes)]
 for path in ['contracts/generation/generation-contracts.schema.json','contracts/generation/admission-basis.schema.json','contracts/generation/retry-inventory.schema.json']:
  raw=rs[path]['raw'];members.append(add('SCHEMA',json.loads(raw)['$id'],raw))
 for path in ['contracts/generation/artifact-schema-map.json','contracts/generation/domain-record-schema-map.json','contracts/execution/raw-artifact-kinds.json']:
  members.append(add('AUTHORITY',path,rs[path]['raw']))
 sources=known_sources()
 for id,raw in sources.items():members.append(add('POLICY_IMPLEMENTATION',id,raw))
 main='urn:kcml:policy-source:generation_own_kind_policy_v1.py'
 entry={'handlerId':own_kind.REVISION,'implementationId':main,'implementationDigest':digest(sources[main]),'dependencyDigests':sorted(digest(v)for k,v in sources.items()if k!=main),'supportedKinds':['UPDATE','RETRY','REPAIR']}
 package={'packageId':PACKAGE_ID,'version':1,'members':sorted(members,key=lambda x:(x['kind'],x['id'],x['digest'])),'entrypoints':[entry],
 'requestSchema':{'schemaId':json.loads(request_schema_bytes)['$id'],'bundleDigest':digest(request_schema_bytes),'definition':None},
 'requestPolicy':{'policyId':json.loads(request_policy_bytes)['policyId'],'policyDigest':digest(request_policy_bytes)}}
 return canonical(package),blobs

def load_package(raw,expected_digest,archived):
 if not isinstance(raw,bytes)or digest(raw)!=expected_digest:fail('GENERATION_POLICY_PACKAGE_DIGEST_MISMATCH')
 p=strict_json(raw)
 if not isinstance(p,dict)or set(p)!={'packageId','version','members','entrypoints','requestSchema','requestPolicy'}or p['packageId']!=PACKAGE_ID or type(p['version'])is not int or p['version']!=1:fail('GENERATION_POLICY_PACKAGE_INVALID')
 if not isinstance(p['members'],list) or not p['members'] or not isinstance(p['entrypoints'],list):fail('GENERATION_POLICY_PACKAGE_INVALID')
 if len(p['entrypoints'])!=1:fail('GENERATION_POLICY_PACKAGE_INVALID')
 e=p['entrypoints'][0]
 if not isinstance(e,dict)or set(e)!={'handlerId','implementationId','implementationDigest','dependencyDigests','supportedKinds'}or any(not isinstance(e[k],str)for k in ['handlerId','implementationId','implementationDigest'])or not isinstance(e['dependencyDigests'],list)or any(not isinstance(d,str)or re.fullmatch(r'sha256:[0-9a-f]{64}',d)is None for d in e['dependencyDigests'])or e['supportedKinds']!=['UPDATE','RETRY','REPAIR']:fail('GENERATION_POLICY_PACKAGE_INVALID')
 for key,fields in [('requestSchema',{'schemaId','bundleDigest','definition'}),('requestPolicy',{'policyId','policyDigest'})]:
  if not isinstance(p[key],dict)or set(p[key])!=fields:fail('GENERATION_POLICY_PACKAGE_INVALID')
  for field,value in p[key].items():
   if field=='definition':
    if value is not None:fail('GENERATION_POLICY_PACKAGE_INVALID')
   elif not isinstance(value,str)or not value or ('Digest'in field and re.fullmatch(r'sha256:[0-9a-f]{64}',value)is None):fail('GENERATION_POLICY_PACKAGE_INVALID')
 seen=set();bundles={};schemas={};authorities={};code={}
 for m in p['members']:
  if not isinstance(m,dict)or set(m)!={'kind','id','digest'}or any(not isinstance(m[k],str) for k in ['kind','id','digest'])or m['kind']not in ['SCHEMA','DOMAIN_POLICY','AUTHORITY','POLICY_IMPLEMENTATION']or re.fullmatch(r'sha256:[0-9a-f]{64}',m['digest'])is None or(m['kind'],m['id'])in seen:fail('GENERATION_POLICY_PACKAGE_MEMBER_DUPLICATE')
  seen.add((m['kind'],m['id']));actual=archived.get((m['kind'],m['id'],m['digest']))
  if not isinstance(actual,bytes):fail('GENERATION_POLICY_PACKAGE_MEMBER_UNAVAILABLE')
  if digest(actual)!=m['digest']:fail('GENERATION_POLICY_PACKAGE_MEMBER_DIGEST_MISMATCH')
  bundles[m['digest']]=actual
  if m['kind']=='SCHEMA':
   schema=strict_json(actual)
   if not isinstance(schema,dict)or schema.get('$id')!=m['id']:fail('GENERATION_POLICY_PACKAGE_SCHEMA_IDENTITY_MISMATCH')
   schemas[m['digest']]=actual
  elif m['kind']=='AUTHORITY':authorities[m['id']]=actual
  elif m['kind']=='POLICY_IMPLEMENTATION':code[m['id']]=actual
 return p,schemas,authorities,code

def dispatch_own_kind(raw,expected_digest,archived,body,records,owner,target_heads=None):
 p,schemas,authority,code=load_package(raw,expected_digest,archived)
 entries=[e for e in p['entrypoints']if e.get('handlerId')==own_kind.REVISION]
 if len(entries)!=1:fail('GENERATION_POLICY_IMPLEMENTATION_UNSUPPORTED')
 entry=entries[0];known=TRUSTED_SOURCES;main='urn:kcml:policy-source:generation_own_kind_policy_v1.py'
 if entry['implementationId']!=main or entry['implementationDigest']!=digest(known[main]) or code.get(main)!=known[main]:fail('GENERATION_POLICY_IMPLEMENTATION_UNAVAILABLE')
 expected_deps=sorted(digest(raw)for id,raw in known.items()if id!=main)
 if entry['dependencyDigests']!=expected_deps or any(code.get(id)!=raw for id,raw in known.items()):fail('GENERATION_POLICY_DEPENDENCY_REVISION_UNAVAILABLE')
 if body.get('kind','CREATE')not in entry['supportedKinds']:fail('GENERATION_POLICY_KIND_UNSUPPORTED')
 for required in ['contracts/generation/artifact-schema-map.json','contracts/generation/domain-record-schema-map.json','contracts/execution/raw-artifact-kinds.json']:
  if required not in authority:fail('GENERATION_POLICY_AUTHORITY_MEMBER_UNAVAILABLE')
 # Build a single selected historical closure, not Repository.from_current_ssot.
 repo=Repository(copy.deepcopy(records),schemas,strict_json(authority['contracts/generation/artifact-schema-map.json']),owner,target_heads)
 from generation_frozen_archive import compile_archived_request
 binding={'schemaId':p['requestSchema']['schemaId'],'schemaDigest':p['requestSchema']['bundleDigest'],'policyId':p['requestPolicy']['policyId'],'policyDigest':p['requestPolicy']['policyDigest'],'dependencies':[]}
 all_bundles={d:raw for (kind,id,d),raw in archived.items()}
 validator=compile_archived_request(binding,all_bundles,policy_implementations={digest(raw):raw for raw in code.values()})
 return own_kind.evaluate(body,repo,validator)
