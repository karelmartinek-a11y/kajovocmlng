from pathlib import Path
import sys,json,re,hashlib
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
rs=resource_index();raw=rs['database/operation-functions.sql']['raw'].decode();selected=[]
for op in ['ownerApiKey.read','ownerApiKey.reveal']:
 start=raw.index('-- '+op+' /');end=raw.index('END $$;',start)+len('END $$;');fn=raw[start:end];name=re.search(r'FUNCTION (\w+)',fn)[1];dg=re.search(r'/ (sha256:\w+)',fn)[1]
 selected.append({'operationId':op,'functionName':name,'descriptorDigest':dg,'sourceSql':fn})
(OUT/'owner-query-original-wrappers.sql').write_text('\n\n'.join(x['sourceSql']for x in selected)+'\n')
(OUT/'owner-query-family.json').write_text(json.dumps({'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'sourceResourceSha256':rs['database/operation-functions.sql']['sha256'],'family':selected},indent=2)+'\n')
