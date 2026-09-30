"""Server-only pinned descriptor authoring from actual authoritative resource bytes."""
from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resources,resource_index,SSOT
from create_operation_contracts import strict_json,ContractFailure
from jsonschema import Draft202012Validator,FormatChecker
FIELDS=['callerAuthorityKind','clientKeyDigest','operationContractId','operationContractRevision','stableBusinessTargetKey','stableCallerObjectId','stableCallerRevisionId']
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')
def schema():
 return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:generation-create-frozen-descriptor:1','type':'object','additionalProperties':False,'properties':{'callerAuthorityKind':{'const':'OWNER_FULL'},'clientKeyDigest':{'type':'string','pattern':'^sha256:[0-9a-f]{64}$(?![\\s\\S])'},'operationContractId':{'const':'generation.job.create'},'operationContractRevision':{'type':'string','minLength':1},'stableBusinessTargetKey':{'const':'CREATE_ROOT:generation_job'},'stableCallerObjectId':{'type':'string','format':'uuid'},'stableCallerRevisionId':{'type':'null'}},'required':FIELDS}
def pin():
 frozen=resource_index(resources(SSOT.read_bytes().decode('utf8')));opres=frozen['contracts/operation-contracts.json'];rr=frozen['contracts/payload-contracts.json'];sr=frozen['contracts/create-operation-design.schema.json']
 op=next(r for r in strict_json(opres['raw'])['records'] if r['operationId']=='generation.job.create')
 route=next(r for r in strict_json(rr['raw'])['records'] if r['operationId']=='generation.job.create')
 domain=route['requestSchema']['properties']['body']
 revision={'operationRecord':op,'routeRecord':route,'domainSchema':domain}
 return {'operationId':op['operationId'],'operationRevision':op['operationRevision'],'operationRecordBytes':canonical(op),'routeRecordBytes':canonical(route),'domainSchemaBytes':canonical(domain),'contractRevisionBytes':canonical(revision),'operationResourceDigest':bytes.fromhex(opres['sha256']),'routeResourceDigest':bytes.fromhex(rr['sha256']),'schemaResourceDigest':bytes.fromhex(sr['sha256']),'contractDigest':hashlib.sha256(canonical(revision)).digest(),'domainSchemaDigest':hashlib.sha256(canonical(domain)).digest()}
def descriptor(owner,client_key_digest,pinned=None):
 p=pin() if pinned is None else pinned
 d={'callerAuthorityKind':'OWNER_FULL','clientKeyDigest':client_key_digest,'operationContractId':p['operationId'],'operationContractRevision':p['operationRevision'],'stableBusinessTargetKey':'CREATE_ROOT:generation_job','stableCallerObjectId':owner,'stableCallerRevisionId':None}
 Draft202012Validator(schema(),format_checker=FormatChecker()).validate(d);return canonical(d)
def validate(raw,pinned,owner):
 d=strict_json(raw);Draft202012Validator(schema(),format_checker=FormatChecker()).validate(d)
 if raw!=canonical(d):raise ContractFailure('GENERATION_DESCRIPTOR_NOT_CANONICAL')
 if d['operationContractRevision']!=pinned['operationRevision'] or d['stableCallerObjectId']!=owner:raise ContractFailure('GENERATION_DESCRIPTOR_PIN_BINDING_MISMATCH')
 return d
if __name__=='__main__':
 h=Path(__file__).resolve().parent;h.joinpath('generation-execution-descriptor.schema.json').write_text(json.dumps(schema(),indent=2)+'\n')
 p=pin();h.joinpath('generation-contract-pin-manifest.json').write_text(json.dumps({k:(v.hex() if isinstance(v,bytes) and k.endswith('Digest') else {'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)} if isinstance(v,bytes) else v) for k,v in p.items()},indent=2)+'\n')


def pin_insert_sql(epoch=7,pin_id='70000000-0000-4000-8000-000000000001',pinned=None):
 p=pin() if pinned is None else pinned;values=[pin_id,str(epoch),p['operationId'],p['operationRevision']]+[p[x] for x in ['operationRecordBytes','routeRecordBytes','domainSchemaBytes','contractRevisionBytes','operationResourceDigest','routeResourceDigest','schemaResourceDigest','contractDigest','domainSchemaDigest']]
 quoted=[str(epoch) if i==1 else "decode('"+v.hex()+"','hex')" if isinstance(v,bytes) else "'"+v.replace("'","''")+"'" for i,v in enumerate(values)]
 return 'INSERT INTO generation_create_contract_pin VALUES('+','.join(quoted)+');'
