"""Structural inventory only, never semantic completion."""
import hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent;s=json.loads((D/'secret-profile-handoffs.schema.json').read_text());fields=[]
for name,v in s['$defs'].items():
 def walk(x,p):
  if isinstance(x,dict):
   for key,value in x.get('properties',{}).items():
    fields.append({'definition':name,'pointer':p+'/properties/'+key,'field':key,'required':key in x.get('required',[]),'schema':value,'authority':'§8.2/8.3/8.4/8.7/8.8/8.11/25.6/72.21; browser members §13.15; concrete technical naming requires normative integration','origin':'OWNER_IMPORT'if name not in ['StoredVersionMetadata','ConsumerDeclaration','ConsumerProfileSupport','KeyAlgorithmPolicy']else'SERVER_PINNED_INTERNAL','sensitive':'value bytes or metadata; never automatic receipt echo'})
   for key,value in x.items():
    if key!='properties':walk(value,p+'/'+key)
  elif isinstance(x,list):
   for i,value in enumerate(x):walk(value,p+'/'+str(i))
 walk(v,'#/$defs/'+name)
(D/'field-register.json').write_text(json.dumps({'sourceSha256':s['x-sourceSha256'],'schemaSha256':hashlib.sha256((D/'secret-profile-handoffs.schema.json').read_bytes()).hexdigest(),'status':'STRUCTURAL_FIELD_INVENTORY_NOT_SEMANTIC_COMPLETION','fields':fields},indent=2)+'\n')
print(len(fields))
