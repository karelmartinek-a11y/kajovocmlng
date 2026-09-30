"""Reproduce prior root code byte-for-byte using a complete valid metadata witness."""
from pathlib import Path
import sys,hashlib,json,importlib.util,copy
from datetime import datetime,timezone
HERE=Path(__file__).parent;ROOT=HERE.parents[4];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'audit/generated/resume-34d/secrets-browser'))
from ssot_sources import SSOT
from secret_profile_reference import SCHEMA,compiled_schema_bytes,schema_digest,canonical_value_digest,validate
from synthetic_profile_fixtures import fixtures,consumer
from jsonschema import Draft202012Validator,FormatChecker
artifact=HERE/'secret_profile_import_pre_fix.py';expected=json.loads((HERE/'secret-native-prior-two-counterexamples.json').read_text())['rootImplementationDigests']['secret_profile_import.py']
assert hashlib.sha256(artifact.read_bytes()).hexdigest()==expected,'HISTORICAL_ROOT_BYTES_DO_NOT_MATCH_PRIOR_EXECUTION_HASH'
s=importlib.util.spec_from_file_location('exact_historical_root_import',artifact);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p='TOTP_BASE32_V1';raw=json.dumps(fixtures[p]).encode();candidate={'type':'TOTP_SEED','representation':'PROFILE_JSON_V1','profileId':p,'bytes':raw};metadata={'secretId':'00000000-0000-4000-8000-000000000001','versionId':'00000000-0000-4000-8000-000000000002','type':'TOTP_SEED','representation':'PROFILE_JSON_V1','profileId':p,'schemaId':SCHEMA['$id']+'#/$defs/'+p,'schemaDigest':schema_digest(p),'plaintextByteLength':len(raw),'valueDigest':'sha256:'+hashlib.sha256(raw).hexdigest(),'canonicalValueDigest':canonical_value_digest(candidate),'payloadFormat':'EXACT_SECRET_BYTES_V1'}
validate('StoredVersionMetadata',metadata)
e={k:metadata[k]for k in ['secretId','versionId','type']};c=consumer(p)
for row in c['profiles']:row['schemaDigest']=schema_digest(row['profileId'])
now=datetime(2026,9,30,tzinfo=timezone.utc);baseline=m.load_use_profile(raw,metadata,e,c,now);rows=[{'case':'full-native-metadata-baseline-valid-under-effective-mask','passed':baseline['status']=='REFERENCE_PREFLIGHT_PASSED'}]
for case,key,value in [('wrong-advertised-schema-id','schemaId','urn:kcml:wrong'),('wrong-profile-type-with-same-selected-type','type','PRIVATE_KEY')]:
 wrong=copy.deepcopy(metadata);wrong[key]=value;selected=dict(e)
 if key=='type':selected['type']=value;wrong['canonicalValueDigest']=canonical_value_digest({**candidate,'type':value})
 compiled=json.loads(compiled_schema_bytes('StoredVersionMetadata'));assert not Draft202012Validator(compiled,format_checker=FormatChecker()).is_valid(wrong),'MUTANT_MUST_BREAK_SPECIFIC_NATIVE_METADATA_BINDING'
 result=m.load_use_profile(raw,wrong,selected,c,now);rows.append({'case':case,'acceptedByExactPreFixRoot':result['status']=='REFERENCE_PREFLIGHT_PASSED'})
report={'sourceDocumentSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'historicalRootModuleSHA256':expected,'reconstructedArtifactExactRecordedHashVerified':True,'scope':'Original seven-field initial reference witness was incomplete under fullStoredVersionMetadata; this independent reexecution uses full11field positive validatedunderactualnative mask andexactoldrootmodule bytes, thenone specificbindingviolation. Historical accepted defects only, notcurrentPASS.','cases':rows,'currentCorrectedEvidence':'secret-native-review.json','wholeSecretOperationClosed':False}
(HERE/'secret-native-full-metadata-historical-reproduction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'historicalFullPositive':rows[0]['passed'],'reproducedAcceptedDefects':sum(r.get('acceptedByExactPreFixRoot',False)for r in rows)}))
