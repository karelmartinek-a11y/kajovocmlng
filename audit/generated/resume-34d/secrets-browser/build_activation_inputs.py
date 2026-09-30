"""Materialize coordinator inputs only; never edits canonical SSOT/projections."""
import copy,json,hashlib
from pathlib import Path
from secret_import_adapter import active_import_document,APPROVED_PROFILES
from profile_reference import SCHEMA,compiled_schema_bytes,schema_digest
D=Path(__file__).resolve().parent
active=active_import_document()
(D/'secret-active-import.schema.json').write_text(json.dumps(active,indent=2)+'\n')
registry=[]
for profile in APPROVED_PROFILES:
 raw=compiled_schema_bytes(profile)
 registry.append({'profileId':profile,'secretType':next(v['secretType']for v in SCHEMA['x-profileInventory']if v['profileId']==profile),'schemaId':SCHEMA['$id']+'#/$defs/'+profile,'schemaDigest':schema_digest(profile),'schemaBytesFile':'compiled-profile-schemas/'+profile+'.json','activation':'REQUIRES_CURRENT_NORMATIVE_SOURCE_AND_REAL_REVIEW_RECEIPT'})
 dest=D/'compiled-profile-schemas'/f'{profile}.json';dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
(D/'activation-inputs.json').write_text(json.dumps({'input':json.loads((D/'input-source.json').read_text()),'profiles':registry,'fullBrowserRequiredProfile':{'profileId':'BROWSER_AUTH_STATE_GRAPH_V1','activation':'NOT_ACTIVATED','obligationsFile':'browser-engine-tests.json'},'digestCircularity':'compiled schema bytes contain definitions only; normative source digest is stored outside its own SSOT source and supplied by verified server deployment registry','wholeSecretCreate':'OPEN'},indent=2)+'\n')
print(json.dumps({'limitedProfiles':len(registry),'wholeOperation':'OPEN'}))
