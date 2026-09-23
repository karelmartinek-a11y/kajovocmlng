#!/usr/bin/env python3
"""KCML SSOT/2: offline parser, schema control and executable generation invariants.
Production adapters must obtain observations from the canonical writer; model
observations and caller-supplied receipts are never production authority.
Requires Python >=3.11, jsonschema >=4.23 and Node.js for RFC 8785 numbers.
"""
from __future__ import annotations
import argparse,base64,copy,hashlib,json,math,os,re,stat,subprocess,sys,zlib
from dataclasses import dataclass
from pathlib import Path
from functools import lru_cache
from typing import Any,Callable,Mapping
from datetime import datetime,timezone
import jsonschema
from referencing import Registry,Resource

MAX_JSON_BYTES=64*1024*1024
MAX_DEPTH=128
MAX_MEMBERS=1000000
MAX_SAFE=9007199254740991
MAX_COUNTER=9223372036854775807
BUNDLE_PATH='contracts/generation/generation-contracts.schema.json'

class ContractFailure(ValueError):
    def __init__(self,code:str,pointer:str,detail:str):
        self.code,self.pointer,self.detail=code,pointer,detail
        super().__init__(f'{code} {pointer}: {detail}')

def require(condition:bool,code:str,pointer:str,detail:str)->None:
    if not condition:raise ContractFailure(code,pointer,detail)

def raw_digest(value:bytes)->str:
    return 'sha256:'+hashlib.sha256(value).hexdigest()

def pointer_get(value:Any,pointer:str)->Any:
    if pointer=='':return value
    require(pointer.startswith('/'),'CONTRACT_PACK_REFERENCE_INVALID',pointer,'JSON Pointer must be absolute')
    for token in pointer[1:].split('/'):
        require(re.search(r'~(?![01])',token) is None,'CONTRACT_PACK_REFERENCE_INVALID',pointer,'Invalid pointer escape')
        token=token.replace('~1','/').replace('~0','~')
        if isinstance(value,dict):
            require(token in value,'CONTRACT_PACK_REFERENCE_INVALID',pointer,'Missing object member')
            value=value[token]
        elif isinstance(value,list):
            require(re.fullmatch(r'0|[1-9][0-9]*',token) is not None,'CONTRACT_PACK_REFERENCE_INVALID',pointer,'Invalid array index')
            idx=int(token)
            require(idx<len(value),'CONTRACT_PACK_REFERENCE_INVALID',pointer,'Array index out of range')
            value=value[idx]
        else:raise ContractFailure('CONTRACT_PACK_REFERENCE_INVALID',pointer,'Pointer crosses a scalar')
    return value

def strict_json(raw:bytes,byte_limit:int=MAX_JSON_BYTES,depth_limit:int=MAX_DEPTH)->Any:
    require(len(raw)<=byte_limit,'ARTIFACT_VALIDATION_FAILED','', 'Byte budget exceeded')
    require(not raw.startswith(b'\xef\xbb\xbf'),'ARTIFACT_VALIDATION_FAILED','', 'UTF-8 BOM forbidden')
    try:text=raw.decode('utf-8','strict')
    except UnicodeDecodeError as e:raise ContractFailure('ARTIFACT_VALIDATION_FAILED','', 'Invalid UTF-8') from e
    # A lexical bound is checked before allocating a deep parser tree.
    depth=0;quoted=False;escaped=False
    for char in text:
        if quoted:
            if escaped:escaped=False
            elif char=='\\':escaped=True
            elif char=='"':quoted=False
        elif char=='"':quoted=True
        elif char in '[{':
            depth+=1
            require(depth<=depth_limit,'ARTIFACT_VALIDATION_FAILED','', 'Depth budget exceeded')
        elif char in ']}':depth-=1
    members=0
    def pairs(items:list[tuple[str,Any]])->dict[str,Any]:
        nonlocal members
        out={}
        for key,value in items:
            require(key not in out,'ARTIFACT_VALIDATION_FAILED','/'+key,'Duplicate JSON member')
            members+=1
            require(members<=MAX_MEMBERS,'ARTIFACT_VALIDATION_FAILED','', 'Member budget exceeded')
            out[key]=value
        return out
    def reject_constant(value:str)->Any:
        raise ContractFailure('ARTIFACT_VALIDATION_FAILED','', 'Non-finite JSON constant: '+value)
    try:value=json.loads(text,object_pairs_hook=pairs,parse_constant=reject_constant)
    except (ValueError,RecursionError) as e:
        if isinstance(e,ContractFailure):raise
        raise ContractFailure('ARTIFACT_VALIDATION_FAILED','', 'Invalid JSON syntax') from e
    def check(v:Any,p:str='')->None:
        if isinstance(v,str):
            try:v.encode('utf-8','strict')
            except UnicodeEncodeError as e:raise ContractFailure('ARTIFACT_VALIDATION_FAILED',p,'Lone surrogate') from e
        elif isinstance(v,float):require(math.isfinite(v),'ARTIFACT_VALIDATION_FAILED',p,'Non-finite binary64 number')
        elif isinstance(v,int) and not isinstance(v,bool):
            require(-MAX_SAFE<=v<=MAX_SAFE,'ARTIFACT_VALIDATION_FAILED',p,'Integer outside safe JSON number range; use a declared decimal string')
        elif isinstance(v,list):
            require(len(v)<=MAX_MEMBERS,'ARTIFACT_VALIDATION_FAILED',p,'Array budget exceeded')
            for i,item in enumerate(v):check(item,p+'/'+str(i))
        elif isinstance(v,dict):
            for k,item in v.items():check(k,p);check(item,p+'/'+k.replace('~','~0').replace('/','~1'))
    check(value)
    return value

JCS_NODE=r'''const fs=require('node:fs');
function canonical(v){
 if(v===null||typeof v==='boolean'||typeof v==='string')return JSON.stringify(v);
 if(typeof v==='number'){if(!Number.isFinite(v))throw Error('Non-finite');return JSON.stringify(v);}
 if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';
 return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
}
const input=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(input.map(v=>canonical(v))));'''

@lru_cache(maxsize=8192)
def _jcs_cached(serialized:str)->bytes:
    try:p=subprocess.run(['node','-e',JCS_NODE],input='['+serialized+']',capture_output=True,text=True,timeout=20,check=False)
    except (OSError,subprocess.TimeoutExpired) as e:raise ContractFailure('CONTRACT_PACK_DRIFT','', 'Canonicalizer runtime unavailable') from e
    require(p.returncode==0,'CONTRACT_PACK_DRIFT','', 'Canonicalizer failed: '+p.stderr[:512])
    result=json.loads(p.stdout)
    return result[0].encode('utf-8')

def jcs(value:Any)->bytes:
    raw=json.dumps(value,ensure_ascii=True,separators=(',',':'),allow_nan=False)
    strict_json(raw.encode())
    def ordered(v:Any)->Any:
        if isinstance(v,float):raise ArithmeticError('binary64 path requires ECMAScript serialization')
        if isinstance(v,dict):return {k:ordered(v[k]) for k in sorted(v,key=lambda x:x.encode('utf-16-be'))}
        if isinstance(v,list):return [ordered(x) for x in v]
        return v
    try:return json.dumps(ordered(value),ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
    except ArithmeticError:return _jcs_cached(raw)

def semantic_digest(value:Any)->str:return raw_digest(jcs(value))

def counter(value:Any,pointer:str='')->int:
    require(type(value) is str and re.fullmatch(r'0|[1-9][0-9]{0,18}',value) is not None,'STATE_VERSION_CONFLICT',pointer,'Counter must be a canonical decimal string')
    n=int(value)
    require(n<=MAX_COUNTER,'STATE_VERSION_CONFLICT',pointer,'Counter exceeds PostgreSQL bigint')
    return n

def next_counter(value:str)->str:
    n=counter(value)
    require(n<MAX_COUNTER,'STATE_VERSION_CONFLICT','', 'Counter exhausted; never wrap')
    return str(n+1)

def safe_relpath(value:str)->str:
    require(isinstance(value,str) and 0<len(value)<=4096,'WORKSPACE_PATH_INVALID','', 'Invalid path length')
    require(re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*',value) is not None,'WORKSPACE_PATH_INVALID',value,'Not a canonical POSIX repository path')
    parts=value.split('/')
    require(all(p not in {'.','..'} and len(p.encode())<=255 for p in parts),'WORKSPACE_PATH_INVALID',value,'Invalid path segment')
    return value

def unique(values:list[Any],pointer:str)->None:
    require(len(values)==len(set(values)),'CONTRACT_PACK_REFERENCE_INVALID',pointer,'Duplicate identity')

def path_set(paths:list[str])->None:
    for path in paths:safe_relpath(path)
    folded=[p.casefold() for p in paths];unique(folded,'/paths')
    all_paths=set(folded)
    for path in folded:
        pieces=path.split('/')
        require(all('/'.join(pieces[:i]) not in all_paths for i in range(1,len(pieces))),'WORKSPACE_PATH_INVALID',path,'File/directory prefix collision')

def read_regular_at(root:Path,relative:str,max_bytes:int=MAX_JSON_BYTES)->bytes:
    """Open every component using directory descriptors; never follow a link."""
    safe_relpath(relative)
    root=root.absolute()
    fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for part in root.parts[1:]:
            nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=nxt
        root_dev=os.fstat(fd).st_dev
        parts=relative.split('/')
        for part in parts[:-1]:
            nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=nxt
            require(os.fstat(fd).st_dev==root_dev,'WORKSPACE_PATH_INVALID',relative,'Mount boundary not declared')
        f=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        try:
            before=os.fstat(f)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_dev==root_dev,'WORKSPACE_PATH_INVALID',relative,'File is not a single-link regular artifact')
            require(before.st_size<=max_bytes,'ARTIFACT_VALIDATION_FAILED',relative,'File budget exceeded')
            chunks=[];remaining=max_bytes+1
            while remaining:
                chunk=os.read(f,min(remaining,1024*1024))
                if not chunk:break
                chunks.append(chunk);remaining-=len(chunk)
            data=b''.join(chunks);after=os.fstat(f)
            require(len(data)<=max_bytes and (before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ctime_ns),'ARTIFACT_VALIDATION_FAILED',relative,'Concurrent file mutation or size overflow')
            return data
        finally:os.close(f)
    except OSError as e:raise ContractFailure('WORKSPACE_PATH_INVALID',relative,'Unsafe or missing filesystem entry: '+str(e)) from e
    finally:os.close(fd)

@dataclass(frozen=True)
class Embedded:
    path:str
    authority:str
    language:str
    body:bytes
    line:int

class Document:
    def __init__(self,path:Path):
        self.path=path;self.raw=path.read_bytes()
        require(len(self.raw)<=128*1024*1024,'ARTIFACT_VALIDATION_FAILED','', 'Document budget exceeded')
        self.text=self.raw.decode('utf-8','strict');self.assets={}
        lines=self.text.splitlines(keepends=True);i=0
        while i<len(lines):
            m=re.fullmatch(r'<!-- KCML-EMBEDDED path="([^"]+)" authority="([A-Z_]+)" -->\n?',lines[i])
            if not m:i+=1;continue
            name,authority=m.groups();safe_relpath(name)
            require(name not in self.assets,'CONTRACT_PACK_DRIFT',name,'Duplicate embedded path')
            require(i+1<len(lines),'CONTRACT_PACK_DRIFT',name,'Missing fence')
            f=re.fullmatch(r'(`{3,})([A-Za-z0-9_-]*)\s*\n?',lines[i+1])
            require(f is not None,'CONTRACT_PACK_DRIFT',name,'Invalid opening fence')
            fence,language=f.groups();start=i+2;j=start
            while j<len(lines) and lines[j].strip()!=fence:j+=1
            require(j+1<len(lines) and lines[j+1].strip()=='<!-- KCML-EMBEDDED-END -->','CONTRACT_PACK_DRIFT',name,'Unclosed embedded block')
            self.assets[name]=Embedded(name,authority,language,''.join(lines[start:j]).encode('utf-8'),i+1)
            i=j+2
        path_set(list(self.assets))
        self.schema=strict_json(self.assets[BUNDLE_PATH].body)
        self.schema_digest=raw_digest(self.assets[BUNDLE_PATH].body)
        self.resources={self.schema['$id']:self.schema}
        for asset in self.assets.values():
            if asset.authority=='NORMATIVE' and asset.language=='json':
                value=strict_json(asset.body)
                if isinstance(value,dict) and '$id' in value:
                    require(value['$id'] not in self.resources or value==self.resources[value['$id']],'CONTRACT_PACK_DRIFT',asset.path,'Schema identity collision')
                    self.resources[value['$id']]=value
        self.registry=Registry().with_resources((uri,Resource.from_contents(v)) for uri,v in self.resources.items())
        self.validator=jsonschema.Draft202012Validator(self.schema,registry=self.registry,format_checker=jsonschema.FormatChecker())
        self.catalog=self.load('contracts/generation/step-catalog.json')
        self.saga=self.load('contracts/generation/integration-step-catalog.json')
        self.kind_to_schema=self.load('contracts/generation/artifact-schema-map.json')
        self.record_to_schema=self.load('contracts/generation/domain-record-schema-map.json')
    def load(self,path:str)->Any:return strict_json(self.assets[path].body)
    def validate(self,definition:str,value:Any)->None:
        strict_json(json.dumps(value,ensure_ascii=True,allow_nan=False).encode())
        require(definition in self.schema['$defs'],'CONTRACT_PACK_REFERENCE_INVALID',definition,'Unknown schema definition')
        schema={'$schema':self.schema['$schema'],'$id':self.schema['$id']+':selection:'+definition,'$ref':self.schema['$id']+'#/$defs/'+definition}
        errors=sorted(jsonschema.Draft202012Validator(schema,registry=self.registry,format_checker=jsonschema.FormatChecker()).iter_errors(value),key=lambda e:str(list(e.absolute_path)))
        if errors:
            e=errors[0];p='/'.join(str(x) for x in e.absolute_path)
            raise ContractFailure('ARTIFACT_VALIDATION_FAILED','/'+p,e.message[:2000])
    def validate_address(self,address:dict[str,Any],value:Any)->None:
        self.validate('SchemaAddress',address)
        require(address['schemaId']==self.schema['$id'] and address['bundleDigest']==self.schema_digest,'CONTRACT_PACK_DRIFT','/schema','Unknown or stale schema resource')
        self.validate(address['definition'],value)
    def verify_manifest(self)->None:
        manifest=self.load('contracts/execution/embedded-manifest.json')
        seen=set()
        for entry in manifest['files']:
            name=entry['path'];require(name not in seen,'CONTRACT_PACK_DRIFT',name,'Duplicate manifest entry');seen.add(name)
            require(name in self.assets,'CONTRACT_PACK_REFERENCE_INVALID',name,'Missing embedded asset')
            asset=self.assets[name]
            require(raw_digest(asset.body)==entry['rawDigest'] and len(asset.body)==entry['sizeBytes'] and asset.authority==entry['authority'],'CONTRACT_PACK_DRIFT',name,'Embedded bytes differ')
        expected={p for p,a in self.assets.items() if a.authority=='NORMATIVE' and p!='contracts/execution/embedded-manifest.json'}
        require(seen==expected,'CONTRACT_PACK_DRIFT','/files','Manifest is not exact normative asset closure')

class ArtifactResolver:
    """A server-created inventory is required. Peer metadata alone is not a ledger."""
    def __init__(self,doc:Document,root:Path,trusted_inventory:Mapping[str,dict[str,Any]]):
        self.doc,self.root,self.inventory=doc,root,dict(trusted_inventory);self.active=set()
    def get(self,ref:dict[str,Any])->Any:
        self.doc.validate('ArtifactRef',ref)
        aid=ref['artifactId']
        require(aid in self.inventory and self.inventory[aid]==ref,'CONTRACT_PACK_REFERENCE_INVALID','/artifactId','Reference does not match trusted inventory')
        require(aid not in self.active,'CONTRACT_PACK_REFERENCE_INVALID','/artifactId','Cyclic artifact hydration')
        require(ref['path'] is not None,'CONTRACT_PACK_REFERENCE_INVALID','/path','Artifact has no materialized path in this resolver')
        raw=read_regular_at(self.root,ref['path'],min(MAX_JSON_BYTES,ref['sizeBytes']))
        require(len(raw)==ref['sizeBytes'] and raw_digest(raw)==ref['contentDigest'],'ARTIFACT_VALIDATION_FAILED','/contentDigest','Artifact bytes mismatch')
        if ref['kind'] not in self.doc.kind_to_schema:
            require(ref['kind'] in {'SOURCE','FILE_BYTES','PROCESS_STDOUT','PROCESS_STDERR','PROMPT_TEMPLATE','AGENT_INSTRUCTIONS','AGENTS_RUN_STATE','OPENAI_INSTRUCTIONS','JSON_SCHEMA_BUNDLE'},'CONTRACT_PACK_REFERENCE_INVALID','/kind','Unknown artifact kind')
            if ref['kind']=='JSON_SCHEMA_BUNDLE':
                value=strict_json(raw);jsonschema.Draft202012Validator.check_schema(value);validate_local_refs(value);return value
            return raw
        self.active.add(aid)
        try:
            value=strict_json(raw)
            require(ref['schema'] is not None,'CONTRACT_PACK_REFERENCE_INVALID','/schema','JSON artifact needs an exact schema')
            require(ref['schema']['definition']==self.doc.kind_to_schema[ref['kind']],'CONTRACT_PACK_REFERENCE_INVALID','/schema','Kind/schema mismatch')
            self.doc.validate_address(ref['schema'],value)
            if ref['schema']['definition']=='TypedDocument':self.typed(value['documentSchema'],value['document'])
            if ref['schema']['definition']=='TypedValue':
                self.typed(value['schema'],value['value'])
                require(semantic_digest(value['value'])==value['valueDigest'],'ARTIFACT_VALIDATION_FAILED','/valueDigest','Typed value digest differs')
            if ref['schema']['definition']=='EvidenceRecord':self.typed(value['observationSchema'],value['observations'])
            return value
        finally:self.active.remove(aid)
    def typed(self,reference:dict[str,Any],value:Any)->None:
        self.doc.validate('SchemaArtifact',reference)
        bundle=self.get(reference['bundle'])
        require(bundle.get('$id')==reference['schemaId'],'CONTRACT_PACK_DRIFT','/schemaId','Native schema identity mismatch')
        selected=pointer_get(bundle,reference['rootPointer'])
        require(semantic_digest(selected)==reference['nativeSchemaDigest'],'CONTRACT_PACK_DRIFT','/nativeSchemaDigest','Native definition differs')
        compiled=copy.deepcopy(bundle);compiled['$ref']='#'+reference['rootPointer']
        if reference['rootPointer']=='':compiled.pop('$ref',None)
        errors=list(jsonschema.Draft202012Validator(compiled,format_checker=jsonschema.FormatChecker()).iter_errors(value))
        require(not errors,'ARTIFACT_VALIDATION_FAILED','/value','Value violates declared native schema')
    def record(self,ref:dict[str,Any])->Any:
        self.doc.validate('ContractRecordRef',ref)
        require(ref['recordKind'] in self.doc.record_to_schema,'CONTRACT_PACK_REFERENCE_INVALID','/recordKind','Unregistered record kind')
        value=self.get(ref['artifact'])
        require(isinstance(value,dict),'CONTRACT_PACK_REFERENCE_INVALID','','Record body must be an object')
        self.doc.validate(self.doc.record_to_schema[ref['recordKind']],value)
        normalized=copy.deepcopy(value)
        if 'canonicalDigest' in normalized:normalized['canonicalDigest']=None
        require(semantic_digest(normalized)==ref['recordDigest'],'CONTRACT_PACK_DRIFT','/recordDigest','Record digest mismatch')
        require(ref['schema']==ref['artifact']['schema'],'CONTRACT_PACK_REFERENCE_INVALID','/schema','Record and artifact schema differ')
        return value

def validate_local_refs(schema:Any)->int:
    count=0
    def visit(value:Any)->None:
        nonlocal count
        if isinstance(value,dict):
            for key,item in value.items():
                if key in {'$ref','$dynamicRef'}:
                    require(isinstance(item,str) and item.startswith('#/'),'CONTRACT_PACK_REFERENCE_INVALID',str(item),'Offline local references only')
                    pointer_get(schema,item[1:]);count+=1
                else:visit(item)
        elif isinstance(value,list):
            for item in value:visit(item)
    visit(schema);return count

def evaluate(expr:dict[str,Any],context:Any,depth:int=0)->Any:
    require(depth<=64,'CONTRACT_PACK_REFERENCE_INVALID','','Expression depth exceeded')
    op=expr['op'];rec=lambda x:evaluate(x,context,depth+1)
    if op=='CONST':return copy.deepcopy(expr['value'])
    if op=='GET':return pointer_get(context,expr['pointer'])
    if op=='NOT':
        val=rec(expr['operand']);require(type(val) is bool,'CONTRACT_PACK_REFERENCE_INVALID','','NOT operand is not boolean');return not val
    if op in {'AND','OR'}:
        vals=[rec(x) for x in expr['operands']]
        require(all(type(x) is bool for x in vals),'CONTRACT_PACK_REFERENCE_INVALID','','Boolean operator received non-boolean')
        return all(vals) if op=='AND' else any(vals)
    if op=='ALL_UNIQUE':
        val=rec(expr['operand']);require(isinstance(val,list),'CONTRACT_PACK_REFERENCE_INVALID','','Expected array')
        vals=[jcs(x) for x in val];return len(vals)==len(set(vals))
    left,right=rec(expr['left']),rec(expr['right'])
    if op=='EQ':return jcs(left)==jcs(right)
    if op=='NE':return jcs(left)!=jcs(right)
    if op=='IN':
        require(isinstance(right,list),'CONTRACT_PACK_REFERENCE_INVALID','','IN right operand is not array');return jcs(left) in [jcs(v) for v in right]
    if op=='SET_EQ':
        require(isinstance(left,list) and isinstance(right,list),'CONTRACT_PACK_REFERENCE_INVALID','','SET_EQ needs arrays');return {jcs(x) for x in left}=={jcs(x) for x in right}
    if op=='COUNTER_LE':return counter(left)<=counter(right)
    raise ContractFailure('CONTRACT_PACK_REFERENCE_INVALID','/op','Unknown instruction')

def validate_plan(doc:Document,plan:dict[str,Any],paths:dict[str,Any])->list[str]:
    doc.validate('GenerationPlan',plan);doc.validate('PathPlan',paths)
    require(plan['planId']==paths['planId'] and plan['jobId']==paths['jobId'],'GENERATION_PLAN_INVALID','/pathPlan','Plan identity mismatch')
    require(plan['specificationDigest']==paths['sourceSpecificationDigest']==plan['scopeLock']['approvedSpecificationDigest'],'GENERATION_PLAN_INVALID','/specificationDigest','Specification mismatch')
    approved=set(plan['scopeLock']['approvedRequirementIds']);nodes={n['nodeId']:n for n in plan['nodes']}
    require(len(nodes)==len(plan['nodes']),'GENERATION_PLAN_INVALID','/nodes','Duplicate node')
    catalog={c['kind']:c for c in doc.catalog};roots={a['artifactId']:a for a in plan['rootArtifacts']}
    require(len(roots)==len(plan['rootArtifacts']),'GENERATION_PLAN_INVALID','/rootArtifacts','Duplicate root artifact')
    phases=['ANALYZING','IMPLEMENTING','INTEGRATING','VALIDATING','CML_CONFORMANCE','ACTIVATING']
    import heapq
    waiting={nid:set(n['dependencies']) for nid,n in nodes.items()};followers={nid:[] for nid in nodes}
    for nid,deps in waiting.items():
        require(len(deps)==len(nodes[nid]['dependencies']),'GENERATION_PLAN_INVALID','/dependencies','Duplicate dependency')
        for dep in deps:
            require(dep in nodes,'GENERATION_PLAN_INVALID','/dependencies','Dangling node '+dep);followers[dep].append(nid)
    ready=[nid for nid,deps in waiting.items() if not deps];heapq.heapify(ready);ordered=[]
    while ready:
        nid=heapq.heappop(ready);ordered.append(nid)
        for successor in followers[nid]:
            waiting[successor].remove(nid)
            if not waiting[successor]:heapq.heappush(ready,successor)
    require(len(ordered)==len(nodes),'GENERATION_PLAN_INVALID','/dependencies','Dependency cycle')
    for nid,n in nodes.items():
        c=catalog[n['kind']]
        require(n['phase']==c['phase'] and n['operationId']==c['canonicalOperationId'],'GENERATION_PLAN_INVALID','/nodes/'+nid,'Catalog mismatch')
        require(n['outputSchema']['definition']==c['outputDefinition'] and n['outputSchema']['schemaId']==doc.schema['$id'] and n['outputSchema']['bundleDigest']==doc.schema_digest,'GENERATION_PLAN_INVALID','/outputSchema','Wrong output schema')
        require(set(n['requirementIds'])<=approved,'GENERATION_PLAN_INVALID','/requirementIds','Scope expansion')
        for dep in n['dependencies']:
            require(phases.index(nodes[dep]['phase'])<=phases.index(n['phase']),'GENERATION_PLAN_INVALID','/dependencies','Backwards phase dependency')
        incoming={b['slot']:b['source'] for b in n['inputBindings']}
        require(len(incoming)==len(n['inputBindings']) and set(incoming)==set(c['inputSlots']),'GENERATION_PLAN_INVALID','/inputBindings','Missing, duplicate or excess input slot')
        for slot,source in incoming.items():
            kind=c['inputSlots'][slot]
            if source['origin']=='ROOT_ARTIFACT':
                a=source['artifact'];require(roots.get(a['artifactId'])==a and a['kind']==kind,'GENERATION_PLAN_INVALID','/inputBindings/'+slot,'Unregistered root or wrong kind')
            else:
                producer=source['producerNodeId'];require(producer in n['dependencies'],'GENERATION_PLAN_INVALID','/inputBindings/'+slot,'Data producer is not a direct dependency')
                pc=catalog[nodes[producer]['kind']]
                require(pc['outputSlots'].get(source['outputSlot'])==kind==source['expectedKind'],'GENERATION_PLAN_INVALID','/inputBindings/'+slot,'Output slot kind mismatch')
                if kind in doc.kind_to_schema:
                    require(source['expectedSchema'] is not None and source['expectedSchema']['definition']==doc.kind_to_schema[kind] and source['expectedSchema']['bundleDigest']==doc.schema_digest and source['expectedSchema']['schemaId']==doc.schema['$id'],'GENERATION_PLAN_INVALID','/inputBindings/'+slot,'Wrong input payload schema')
                else:
                    require(kind in doc.load('contracts/execution/raw-artifact-kinds.json') and source['expectedSchema'] is None,'GENERATION_PLAN_INVALID','/inputBindings/'+slot,'Raw artifact must use its native byte/parser contract')
    cov={row['requirementId']:row for row in plan['coverage']}
    require(len(cov)==len(plan['coverage']) and set(cov)==approved,'REQUIREMENT_TRACEABILITY_INCOMPLETE','/coverage','Coverage is not exactly approved scope')
    for rid,row in cov.items():
        for nid in row['producerNodeIds']+row['verificationNodeIds']:
            require(nid in nodes and rid in nodes[nid]['requirementIds'],'REQUIREMENT_TRACEABILITY_INCOMPLETE','/coverage/'+rid,'Broken bidirectional node coverage')
    for nid,n in nodes.items():
        for rid in n['requirementIds']:
            require(nid in cov[rid]['producerNodeIds']+cov[rid]['verificationNodeIds'],'REQUIREMENT_TRACEABILITY_INCOMPLETE','/nodes/'+nid,'Orphan node requirement relation')
    slotids=[s['slotId'] for s in paths['slots']];unique(slotids,'/slots')
    path_set([s['repositoryPath'] for s in paths['slots']]);slots={s['slotId']:s for s in paths['slots']}
    require(set(paths['symbolicTargetKeys'])==set(plan['scopeLock']['approvedTargetKeys']),'GENERATION_PLAN_INVALID','/symbolicTargetKeys','Target scope differs')
    for sid,s in slots.items():
        require(set(s['requirementIds'])<=approved,'REQUIREMENT_TRACEABILITY_INCOMPLETE','/slots/'+sid,'Slot expands scope')
        if s['ownerModule']!='$REPOSITORY_ROOT':
            safe_relpath(s['ownerModule'])
            require(s['repositoryPath'].startswith(s['ownerModule']+'/'),'WORKSPACE_PATH_INVALID','/slots/'+sid,'Path outside owner module')
        else:
            require('/' not in s['repositoryPath'],'WORKSPACE_PATH_INVALID','/slots/'+sid,'Root-owned slot must be a root file')
        for nid in s['allowedWriterNodeIds']:
            require(nid in nodes and sid in nodes[nid]['pathSlotIds'],'GENERATION_PLAN_INVALID','/slots/'+sid,'Missing bidirectional writer link')
        # Multiple writers of one slot must be totally ordered by dependencies.
        def ancestors(nid:str)->set[str]:
            result=set();pending=list(nodes[nid]['dependencies'])
            while pending:
                dep=pending.pop()
                if dep not in result:result.add(dep);pending.extend(nodes[dep]['dependencies'])
            return result
        writers=s['allowedWriterNodeIds']
        for i,a in enumerate(writers):
            for b in writers[i+1:]:require(a in ancestors(b) or b in ancestors(a),'GENERATION_PLAN_INVALID','/slots/'+sid,'Unordered concurrent writers')
    for nid,n in nodes.items():
        require(set(n['pathSlotIds'])<=set(slots),'GENERATION_PLAN_INVALID','/nodes/'+nid,'Unknown path slot')
        for sid in n['pathSlotIds']:require(nid in slots[sid]['allowedWriterNodeIds'],'GENERATION_PLAN_INVALID','/nodes/'+nid,'Writer not assigned')
    return ordered

def decode_file_bytes(value:dict[str,Any])->bytes:
    require(value.get('encoding')=='BASE64','ARTIFACT_VALIDATION_FAILED','','Unknown byte encoding')
    try:raw=base64.b64decode(value['data'],validate=True)
    except (ValueError,TypeError) as e:raise ContractFailure('ARTIFACT_VALIDATION_FAILED','/data','Invalid base64') from e
    require(base64.b64encode(raw).decode()==value['data'],'ARTIFACT_VALIDATION_FAILED','/data','Noncanonical base64 pad bits')
    require(len(raw)==value['sizeBytes'] and raw_digest(raw)==value['contentDigest'],'ARTIFACT_VALIDATION_FAILED','/contentDigest','Byte length/digest mismatch')
    return raw

def apply_patch_model(doc:Document,patch:dict[str,Any],paths:dict[str,Any],current:dict[str,Any],files:Mapping[str,bytes],resolve:Callable[[dict[str,Any]],bytes],executable:set[str]|None=None)->dict[str,bytes]:
    """Pure model of a transaction proposal. It does NOT publish files or commit DB."""
    doc.validate('WorkspacePatchSet',patch);doc.validate('PathPlan',paths)
    require(patch['base']==current,'STATE_VERSION_CONFLICT','/base','Stale workspace')
    require(patch['jobId']==paths['jobId'] and patch['pathPlanDigest']==semantic_digest(paths),'WORKSPACE_PATH_INVALID','/pathPlanDigest','Wrong path plan')
    require(tree_digest(files,executable)==current['treeDigest'],'ARTIFACT_VALIDATION_FAILED','/base/treeDigest','Actual base tree differs')
    slots={s['slotId']:s for s in paths['slots']};unique(list(slots),'/slots')
    require(len(slots)==len(paths['slots']),'WORKSPACE_PATH_INVALID','/slots','Duplicate slot')
    changed=[c['path'] for c in patch['changes']];path_set(changed)
    result=dict(files)
    for i,c in enumerate(patch['changes']):
        p='/changes/'+str(i);require(c['slotId'] in slots,'WORKSPACE_PATH_INVALID',p,'Unknown slot')
        slot=slots[c['slotId']]
        require(c['path']==slot['repositoryPath'] and patch['nodeId'] in slot['allowedWriterNodeIds'] and c['operation'] in slot['allowedOperations'],'WORKSPACE_PATH_INVALID',p,'Wrong path, writer or operation')
        require(set(c['requirementIds'])<=set(slot['requirementIds']),'REQUIREMENT_TRACEABILITY_INCOMPLETE',p,'Patch expands slot scope')
        old=files.get(c['path'])
        if c['operation']=='ADD':require(old is None,'STATE_VERSION_CONFLICT',p,'ADD target exists')
        else:require(old is not None and raw_digest(old)==c['expectedOldDigest'],'STATE_VERSION_CONFLICT',p,'Old bytes mismatch')
        if c['operation']=='DELETE':del result[c['path']]
        else:
            content=c['content'];data=decode_file_bytes(content) if 'encoding' in content else resolve(content)
            require(type(data) is bytes,'ARTIFACT_VALIDATION_FAILED',p,'Resolver did not return bytes')
            if slot['expectedSchema'] is not None:doc.validate_address(slot['expectedSchema'],strict_json(data))
            result[c['path']]=data
    path_set(list(result));return result

def tree_digest(files:Mapping[str,bytes],executable:set[str]|None=None)->str:
    executable=executable or set();path_set(list(files))
    require(executable<=set(files),'ARTIFACT_VALIDATION_FAILED','','Executable flag for absent file')
    return semantic_digest({'domain':'KCML-WORKSPACE-TREE/1','files':[{'path':p,'contentDigest':raw_digest(files[p]),'sizeBytes':len(files[p]),'executable':p in executable} for p in sorted(files)]})

def fresh_snapshot(expected:dict[str,Any],actual:dict[str,Any],db_now:str)->None:
    keys=['platformIncarnation','applicationDeploymentEpoch','jobStateVersion','phaseRunId','fencingToken','cancellationVersion','specificationDigest','planDigest','pathPlanDigest','sdkLockDigest','bindingSetRevision','activationEpoch','authorityLineageId','authorityLineageDigest','operationContextId','operationContextDigest','recoveryEpoch','phaseStateVersion','workspaceRevision','workspaceDigest','candidateDigest']
    for key in keys:require(expected.get(key)==actual.get(key) and key in actual,'CHECKPOINT_STALE','/snapshot/'+key,'Snapshot member is stale or missing')
    now=datetime.fromisoformat(db_now.replace('Z','+00:00'));deadline=datetime.fromisoformat(expected['deadlineAt'].replace('Z','+00:00'))
    require(now.tzinfo is not None and deadline.tzinfo is not None and now<deadline,'KCIP_DEADLINE_EXCEEDED','/deadlineAt','Deadline expired')
    require(not actual.get('cancelRequested',False) and actual.get('recoveryReady') is True,'PLATFORM_RECOVERY_IN_PROGRESS','/snapshot','Cancellation or recovery barrier')

def validate_step_output(doc:Document,step_input:dict[str,Any],output:dict[str,Any],trusted_commit:dict[str,Any],resolve:Callable[[dict[str,Any]],Any],required_check_ids:set[str])->None:
    doc.validate('StepInput',step_input);doc.validate('StepOutput',output)
    for key in ['jobId','nodeId','kind','logicalOperationId','attemptId','unitRevision','businessInputDigest']:
        require(output[key]==step_input[key],'GENERATION_PLAN_INVALID','/'+key,'Input/output identity differs')
    require(output['inputDigest']==semantic_digest(step_input),'ARTIFACT_VALIDATION_FAILED','/inputDigest','Output bound to another input')
    require(output['commit']==trusted_commit and trusted_commit['logicalOperationId']==output['logicalOperationId'],'STATE_VERSION_CONFLICT','/commit','Receipt is not the canonical commit')
    if output['status']=='SUCCEEDED':
        ids=[c['checkId'] for c in output['checks']]
        require(len(ids)==len(set(ids)) and set(ids)==required_check_ids and bool(ids),'ARTIFACT_VALIDATION_FAILED','/checks','Check set does not match trusted gate catalog')
        require(all(c['verdict']=='PASS' and not c['problems'] for c in output['checks']),'ARTIFACT_VALIDATION_FAILED','/checks','Success contains failed checks')
        for c in output['checks']:
            require(c['inputDigest']==output['inputDigest'],'ARTIFACT_VALIDATION_FAILED','/checks','Check binds another input')
            for a in c['evidence']:resolve(a)
        for a in output['outputs'].values():resolve(a)
        if output['executionMode']=='REUSED_UNCHANGED':resolve(output['reuseEvidence'])
    else:
        unknown=any(p['effectOutcome']=='UNKNOWN' for p in output['problems'])
        require(not unknown or output['status']=='BLOCKED','TERMINAL_CLOSURE_INCOMPLETE','/status','Unknown effect cannot be FAILED or CANCELLED')
        resolve(output['recoveryCheckpoint'])

def model_input_digest(command:dict[str,Any])->str:
    fields=['modelId','aggregateId','idempotencyKey','expectedState','expectedStateVersion','toState']
    return semantic_digest({k:command[k] for k in fields})

class ReferenceMachine:
    """Side-effect-free reference semantics; not a substitute for a PostgreSQL writer."""
    def __init__(self,model:dict[str,Any],state:dict[str,Any]):
        self.model=copy.deepcopy(model);self.state=copy.deepcopy(state);self.ledger={}
    def transition(self,command:dict[str,Any])->dict[str,Any]:
        before=copy.deepcopy(self.state);key=command['idempotencyKey']
        require(command['inputDigest']==model_input_digest(command),'IDEMPOTENCY_CONFLICT','/inputDigest','Business digest differs from canonical caller command')
        if key in self.ledger:
            saved=self.ledger[key]
            require(saved['inputDigest']==command['inputDigest'],'IDEMPOTENCY_CONFLICT','/idempotencyKey','Key reused for another immutable command')
            out=copy.deepcopy(saved['observation']);out['replayed']=True;return out
        require(command['modelId']==self.model['modelId']==before['modelId'] and command['aggregateId']==before['aggregateId'],'STATE_VERSION_CONFLICT','','Wrong aggregate/model')
        for ck,sk in [('expectedState','state'),('expectedStateVersion','stateVersion'),('expectedFence','fence'),('expectedIncarnation','incarnation'),('expectedCancellationVersion','cancellationVersion')]:
            require(command[ck]==before[sk],'STATE_VERSION_CONFLICT','/'+ck,'Stale command')
        matches=[e for e in self.model['edges'] if e['from']==before['state'] and e['to']==command['toState']]
        require(bool(matches),'STATE_VERSION_CONFLICT','/toState','Transition not declared')
        e=command['evidence'];to=command['toState']
        def edge_allowed(edge:dict[str,Any])->bool:
            ids=set(edge['guardIds'])
            if not e['scopeUnchanged'] and not ('FUNCTIONAL_CHANGE' in ids and e['functionalContractChanged']):return False
            predicates={
                'PRECONDITIONS':e['preconditionsComplete'],
                'DEPENDENCIES':e['dependenciesComplete'],
                'KNOWN_EFFECT':e['effectOutcome']!='UNKNOWN',
                'CLEANUP':e['cleanupComplete'],
                'CANCEL':e['cancelRequested'],
                'ROLLBACK':e['rollbackRequested'],
                'RESUME':e['resumeState']==to and not e['functionalContractChanged'],
                'FUNCTIONAL_CHANGE':e['functionalContractChanged'],
                'NO_NEW_EFFECT':e['effectOutcome']=='NOT_DISPATCHED',
                'INPUT_BARRIER':e['preconditionsComplete'] and e['dependenciesComplete']}
            require(ids<=set(predicates),'CONTRACT_PACK_REFERENCE_INVALID','/guardIds','Unknown model guard')
            return all(predicates[g] is True for g in ids)
        require(any(edge_allowed(edge) for edge in matches),'STATE_VERSION_CONFLICT','/evidence','No declared transition has satisfied guards')
        after=copy.deepcopy(before);after['state']=to;after['stateVersion']=next_counter(before['stateVersion']);after['eventSequence']=next_counter(before['eventSequence'])
        if to in self.model['terminalStates']:after['terminalOutcomeDigest']=command['inputDigest']
        self.state=after
        observation={'command':copy.deepcopy(command),'before':before,'after':copy.deepcopy(after),'accepted':True,'replayed':False,'decision':'COMMIT_MODEL_TRANSITION','possibleExternalDispatch':False}
        self.ledger[key]={'inputDigest':command['inputDigest'],'observation':copy.deepcopy(observation)}
        return observation

def recovery_action(facts:dict[str,Any])->str:
    # Same committed outcome is replayed before considering new execution identity.
    if facts['terminalCommitted']:return 'REPLAY_TERMINAL'
    if facts['effectOutcome']=='UNKNOWN':return 'MANUAL_REVIEW'
    if facts['possibleDispatch'] and not facts['outcomeReconciled']:return 'RECONCILE'
    if facts['compensationRequired']:return 'RUN_COMPENSATION'
    if not facts['cleanupComplete'] and facts['businessWorkTerminal']:return 'RUN_CLEANUP'
    if facts['cancelRequested'] and not facts['possibleDispatch']:return 'CANCEL_BEFORE_DISPATCH'
    if not facts['currentAuthority'] or not facts['checkpointCompatible']:return 'MANUAL_REVIEW'
    if facts['effectOutcome']=='CONFIRMED_NOT_APPLIED' and facts['retryAllowed']:return 'RETRY_SAME_OPERATION'
    return 'RESUME_FROM_CHECKPOINT'

def verify_saga(doc:Document,receipts:list[dict[str,Any]],job_id:str,saga_id:str,resolve:Callable[[dict[str,Any]],Any])->str|None:
    by={r['stepId']:r for r in receipts};require(len(by)==len(receipts),'GENERATION_PLAN_INVALID','/receipts','Duplicate integration step')
    known={s['stepId'] for s in doc.saga};require(set(by)<=known,'GENERATION_PLAN_INVALID','/receipts','Unknown integration step')
    for r in receipts:
        doc.validate('IntegrationStepReceipt',r)
        require(r['jobId']==job_id and r['sagaId']==saga_id,'GENERATION_PLAN_INVALID','/receipts','Another job/saga receipt')
        item=next(x for x in doc.saga if x['stepId']==r['stepId'])
        for dep in item['requiredPredecessorStepIds']:
            require(dep in by and by[dep]['state']=='SUCCEEDED','GENERATION_PLAN_INVALID','/receipts','Receipt exists after missing or unconfirmed predecessor')
    for s in doc.saga:
        r=by.get(s['stepId'])
        if r is None:return s['stepId']
        doc.validate('IntegrationStepReceipt',r)
        require(r['jobId']==job_id and r['sagaId']==saga_id,'GENERATION_PLAN_INVALID','/receipts','Another job/saga receipt')
        for dep in s['requiredPredecessorStepIds']:require(dep in by and by[dep]['state']=='SUCCEEDED','GENERATION_PLAN_INVALID','/receipts','Predecessor not confirmed')
        if r['state']!='SUCCEEDED':return s['stepId']
        require(r['result']['kind']==s['outputKind'],'CONTRACT_PACK_REFERENCE_INVALID','/result/kind','Wrong saga output kind')
        require(r['effectOutcome']!='UNKNOWN','TERMINAL_CLOSURE_INCOMPLETE','/effectOutcome','Unknown saga effect')
        resolve(r['result']);resolve(r['afterInventory'])
        for evidence in r['readBackEvidence']:resolve(evidence)
    return None

def closure(inventory:dict[str,Any])->bool:
    require(inventory['businessOutcome'] in {'SUCCEEDED','FAILED_KNOWN','CANCELLED_CONFIRMED'},'TERMINAL_CLOSURE_INCOMPLETE','/businessOutcome','Unsettled business outcome')
    for key in ['unknownEffects','pendingChildren','activeLeases','provisionalBindings','orphanRuntimes','unconfirmedPointers','pendingRequiredCleanup','uncommittedAudit','pendingAuthorityOutbox']:
        require(key in inventory and type(inventory[key]) is list and len(inventory[key])==0,'TERMINAL_CLOSURE_INCOMPLETE','/'+key,'Unclosed inventory')
    require(inventory.get('snapshotCurrent') is True,'CHECKPOINT_STALE','/snapshotCurrent','Closure inventory is stale')
    return True

def specialize_wire(doc:Document,definition:str,bindings:Mapping[str,dict[str,Any]])->dict[str,Any]:
    catalog=doc.load('contracts/execution/wire-specialization.json');spec=catalog[definition]
    require(set(bindings)=={x['slot'] for x in spec},'CONTRACT_PACK_REFERENCE_INVALID','/bindings','Wire specialization is not exact')
    out=copy.deepcopy(doc.schema);out['$ref']='#/$defs/'+definition
    for slot in spec:
        address=bindings[slot['slot']];doc.validate('SchemaAddress',address)
        require(address['schemaId']==doc.schema['$id'] and address['bundleDigest']==doc.schema_digest and address['definition'] in doc.schema['$defs'],'CONTRACT_PACK_DRIFT','/bindings','Unknown schema address')
        require(address['definition'] not in {'JsonValue',definition},'CONTRACT_PACK_REFERENCE_INVALID','/bindings','Unbound generic wire payload')
        obj=pointer_get(out,slot['schemaPointer'].rsplit('/',1)[0]);name=slot['schemaPointer'].rsplit('/',1)[1]
        obj[name]={'$ref':'#/$defs/'+address['definition']}
    jsonschema.Draft202012Validator.check_schema(out);return out

def compile_native_schema(raw:bytes,expected_digest:str,recipe:dict[str,Any])->dict[str,Any]:
    require(raw_digest(raw)==expected_digest,'CONTRACT_PACK_DRIFT','/nativeSchema','Unpinned SDK schema')
    schema=strict_json(raw);require(schema.get('$schema')=='https://json-schema.org/draft/2020-12/schema','CONTRACT_PACK_REFERENCE_INVALID','/$schema','Wrong native dialect')
    jsonschema.Draft202012Validator.check_schema(schema);validate_local_refs(schema)
    name=recipe['nativeDefinition'];require(name in schema.get('$defs',{}),'CONTRACT_PACK_REFERENCE_INVALID','/nativeDefinition','Native definition not exported')
    result=copy.deepcopy(schema);result.pop('$id',None);result['$ref']='#/$defs/'+name
    # Native extensibility and native null/absence semantics are preserved.
    return result

def check_catalogs(doc:Document)->dict[str,int]:
    jsonschema.Draft202012Validator.check_schema(doc.schema);refs=validate_local_refs(doc.schema)
    kinds=doc.schema['$defs']['NodeKind']['enum'];require({r['kind'] for r in doc.catalog}==set(kinds) and len(doc.catalog)==len(kinds),'CONTRACT_PACK_REFERENCE_INVALID','/stepCatalog','Incomplete node catalog')
    for record in doc.catalog:
        doc.validate('StepCatalogRecord',record)
        i=doc.schema['$defs'][record['inputDefinition']]['properties']['inputs']['properties']
        o=doc.schema['$defs'][record['outputDefinition']]['oneOf'][0]['properties']['outputs']['properties']
        require(set(i)==set(record['inputSlots']) and set(o)==set(record['outputSlots']),'CONTRACT_PACK_REFERENCE_INVALID',record['kind'],'Catalog/schema slots differ')
        for kind in list(record['inputSlots'].values())+list(record['outputSlots'].values()):require(kind in doc.kind_to_schema or kind in doc.load('contracts/execution/raw-artifact-kinds.json'),'CONTRACT_PACK_REFERENCE_INVALID',kind,'Unmapped artifact')
    require([x['stepId'] for x in doc.saga]==['S%02d'%i for i in range(1,15)],'CONTRACT_PACK_REFERENCE_INVALID','/saga','Wrong integration order')
    for i,r in enumerate(doc.saga):
        doc.validate('IntegrationCatalogRecord',r)
        require(all(p in {x['stepId'] for x in doc.saga[:i]} for p in r['requiredPredecessorStepIds']),'CONTRACT_PACK_REFERENCE_INVALID','/saga','Forward dependency')
        require(r['outputKind'] in doc.kind_to_schema,'CONTRACT_PACK_REFERENCE_INVALID','/saga','Unmapped saga output')
    for kind,name in {**doc.kind_to_schema,**doc.record_to_schema}.items():require(name in doc.schema['$defs'],'CONTRACT_PACK_REFERENCE_INVALID',kind,'Unresolved mapped definition')
    specialists=doc.load('contracts/execution/specialist-catalog.json')
    for record in specialists:
        doc.validate('SpecialistCatalogRecord',record)
        require(record['envelopeDefinition']==record['role']+'Proposal' and record['envelopeDefinition'] in doc.schema['$defs'] and record['proposalDefinition'] in doc.schema['$defs'],'CONTRACT_PACK_REFERENCE_INVALID','/specialists','Wrong specialist envelope')
    return {'definitions':len(doc.schema['$defs']),'localReferences':refs,'nodeKinds':len(doc.catalog),'integrationSteps':len(doc.saga),'specialists':len(specialists)}

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('ssot',type=Path);parser.add_argument('--check',action='store_true');parser.add_argument('--restore-source',type=Path);args=parser.parse_args()
    try:
        doc=Document(args.ssot);doc.verify_manifest();stats=check_catalogs(doc)
        if args.restore_source:
            source=doc.load('audit/source-integrity.json')
            require(type(source['sizeBytes']) is int and 0<=source['sizeBytes']<=128*1024*1024,'CONTRACT_PACK_DRIFT','','Source-integrity payload size invalid')
            decoder=zlib.decompressobj();raw=decoder.decompress(base64.b64decode(source['zlibBase64'],validate=True),source['sizeBytes']+1)
            require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,'CONTRACT_PACK_DRIFT','','Truncated, oversized or concatenated source-integrity payload')
            require(len(raw)==source['sizeBytes'] and raw_digest(raw)==source['rawDigest'],'CONTRACT_PACK_DRIFT','','Historical source hash mismatch')
            with args.restore_source.open('xb') as f:f.write(raw)
        print(json.dumps({'scope':'STATIC_EMBEDDED_CONTRACT_CHECK','status':'PASS','ssotRawDigest':raw_digest(doc.raw),**stats,'architectureReadiness':'NOT_EVALUATED_BY_THIS_COMMAND','applicationRuntimeTested':False},ensure_ascii=False,indent=2));return 0
    except (ContractFailure,OSError,KeyError,jsonschema.exceptions.SchemaError) as e:
        print(json.dumps({'scope':'STATIC_EMBEDDED_CONTRACT_CHECK','status':'FAIL','detail':str(e)},ensure_ascii=False),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())

