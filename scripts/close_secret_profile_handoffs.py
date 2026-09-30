"""Publish explicit limited Secret import profiles and bounded storage contracts."""
import hashlib,json,re
from ssot_sources import ROOT,SSOT,resource_index,resources
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
BASE=ROOT/'audit/generated/resume-34d/secrets-browser'
def authored_secret_norm():
 return (BASE/'norm-8.12.md').read_text()+'\n\n### 8.13 Exact browser cookie preservation\n\nFull mandatory browser capture podle §13.15 zachovává skutečnou absenci SameSite jako explicitní UNSPECIFIED; restore tento atribut neposílá. Nesmí ji tiše zaměnit za Lax. Partition identity zahrnuje přesný topLevelSite a hasCrossSiteAncestor; chybějící člen, normalizace site, jiná partition nebo sloučení s unpartitioned cookie jsou konkrétní chyby. Limited cookie/localStorage masky tím nejsou změněny. Actual Chromium member fixtures neuzavírají celý browser bundle, bridge, CAS ani account postconditions; full profile zůstává NOT_ACTIVATED do všech povinných důkazů.\n\n'

def main():
 text=SSOT.read_text();items=list(resources(text));rs=resource_index(items)
 full=json.loads((BASE/'secret-profile-handoffs.schema.json').read_text());full['$defs']['Cookie']['properties']['sameSite']['enum'].append('UNSPECIFIED')
 active=json.loads((BASE/'secret-active-import.schema.json').read_text());active['$id']='urn:kcml:secret-active-import:1';active['$defs']['Cookie']=full['$defs']['Cookie']
 for document in [full,active]:
  body=document['$defs']['SecretCreateBody'];body['properties']['type']['type']='string'
  for condition in body.get('allOf',[]):
   v=condition.get('if',{}).get('properties',{}).get('value')
   if v is not None:v['type']='object'
 doc={'version':'SECRET_PROFILE_IMPORT_STORAGE_USE_V1','authority':['SSOT8.12','SSOT8.13','SSOT25.6','SSOT49.22.1','SSOT51.20','SSOT13.15'], 'limitedProfileNamesApproved':True,'schemas':'contracts/secrets/profile-handoffs.schema.json','currentImport':'contracts/secrets/import.schema.json','physicalRoots':'database/secret-profile-roots.sql','decoder':'scripts/secret_profile_import.py','valueRepresentation':['RAW_UTF8','RAW_BINARY','PROFILE_JSON_V1'],'originalBytes':'Exact original value.profile UTF8 span; RAW exact UTF8 or strict decoded BASE64','idempotency':'Profile request digest binds semantic body plus original import-byte digest; never collapse distinct immutable values','registryAuthority':'Trusted locked server reader resolves current normative source and independent review receipt. No client flag/source digest grants authority.','legacyRaw':'Retain exact immutable own type/bytes; explicit new version for conversion; OWNER reveal unchanged','fullBrowserProfile':'NOT_ACTIVATED_MANDATORY_REMAINING_FIXTURES','wholeOperationClosed':False,'mandatoryRemaining':['Trusted registry review receipt/context/command/root/event/outbox/audit/locator producer joins','Actual systemd crypto source and shared nonce protected-row joins','Activation/broker exact target and consumer admission','Complete13.15 browser state bridge/bundle CAS/account and all key/generator variants','Entire secret operation error/persistence/recovery/read/UI semantics'],'IMPLEMENTATION_PRODUCTION_ACCEPTANCE':'NOT_EVALUATED'}
 updates={
  'contracts/secrets/profile-handoffs.schema.json':(json.dumps(full,ensure_ascii=False,indent=2)+'\n').encode(),
  'contracts/secrets/import.schema.json':(json.dumps(active,ensure_ascii=False,indent=2)+'\n').encode(),
  'contracts/secrets/import-storage-use.json':(json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode(),
  'database/secret-profile-roots.sql':(BASE/'secret-profile-roots.sql').read_bytes()}
 manifest=json.loads(rs['manifest.json']['raw'])
 for path,raw in updates.items():manifest['resources'][path]={'kind':'SQL' if path.endswith('.sql')else'JSON','sizeBytes':len(raw),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest()}
 manifest['resourceCount']=len(manifest['resources']);updates['manifest.json']=encoded(manifest,rs['manifest.json']['raw'])
 text=rewrite(text,items,updates);text=text.replace('KCML-R9-RESOURCE path="database/secret-profile-roots.sql" kind="JSON"','KCML-R9-RESOURCE path="database/secret-profile-roots.sql" kind="SQL"')
 norm=authored_secret_norm()
 m=re.search(r'^### 8\.12 .*?(?=^### 8\.(?!13\b)|^## 9\.)',text,re.M|re.S)
 if m:text=text[:m.start()]+norm+text[m.end():]
 else:
  m=re.search(r'^## 9\.',text,re.M);assert m;text=text[:m.start()]+norm+text[m.start():]
 SSOT.write_text(text,encoding='utf8',newline='\n')
 for path,raw in updates.items():
  if path=='manifest.json':continue
  p=ROOT/'01_UI_CONTRACT'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 print(json.dumps({'authored':list(updates),'wholeOperationsClosed':0}))
if __name__=='__main__':main()
