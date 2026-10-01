from pathlib import Path
import sys,re,json,hashlib
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resource_index,SSOT
from verify_operation_sql_literals import expressions,literal_arguments
r=resource_index()['database/operation-functions.sql'];raw=r['raw'].decode();rows=[]
family={'ownerApiKey.read','ownerApiKey.reveal'}
for m in re.finditer(r'-- ([\w.]+) / (sha256:[a-f0-9]+)\nCREATE OR REPLACE FUNCTION (\w+)\(.*?END \$\$;',raw,re.S):
 op,digest,fn=m.group(1,2,3);calls=list(map(literal_arguments,expressions(m.group(0).encode())))
 assert len(calls)==4
 rows.append({'id':'SQL.WRAPPER.'+op,'operationId':op,'wrapperFunction':'public.'+fn,'descriptorDigest':digest,'sourcePointer':'database/operation-functions.sql:line'+str(raw[:m.start()].count('\n')+1),'required':True,'definitionApplicability':'SCOPED_REFERENCE_IMPLEMENTED'if op in family else'UNIMPLEMENTED','dispatchStatus':'BLOCKED','blockerIds':['SQL.OWNER_QUERY.TRUSTED_ISSUER','SQL.OWNER_QUERY.RUNTIME_CAPABILITY','SQL.OWNER_QUERY.AUDIT_HYDRATION']if op in family else['SQL.TYPED_HANDLER.'+op],'calls':[{'id':'SQL.CALL.'+op+'.'+name,'helper':'public.'+name,'literalArguments':args,'required':True,'executionStatus':'SCOPED_REFERENCE_PASS'if op in family else'NOT_IMPLEMENTED','dispatchStatus':'BLOCKED'}for name,args in calls]})
assert len(rows)==262 and sum(len(x['calls'])for x in rows)==1048
j={'schemaVersion':1,'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'sourceResourceSha256':hashlib.sha256(r['raw']).hexdigest(),'scope':'Complete required callsite universe of this exact embedded operation-functions.sql; not complete SSOT operation universe','overallStatus':'BLOCKED','literalStatus':'PASS','helperDefinitionStatus':'PROPOSED_SCOPED_DEFINITIONS_PRESENT_NOT_CANONICAL','wrapperCount':262,'requiredCallsiteCount':1048,'referenceImplementedWrappers':2,'unimplementedWrappers':260,'dispatchVerifiedWrappers':0,'wholeOperationsClosed':0,'wrappers':rows}
(OUT/'operation-helper-callsite-registry.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
f=OUT/'owner-query-family.json';j=json.loads(f.read_text());j['sourceResourceSha256']=hashlib.sha256(r['raw']).hexdigest();f.write_text(json.dumps(j,indent=2)+'\n')
print(json.dumps({'wrappers':len(rows),'calls':1048,'dispatchVerified':0}))
