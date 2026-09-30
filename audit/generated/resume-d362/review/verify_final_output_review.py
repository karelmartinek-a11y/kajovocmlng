from pathlib import Path
import sys,json,copy,hashlib
HERE=Path(__file__).parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from generation_follow_up_fixtures import factory
from generation_admission_contracts import validate_declared_final_output,canonical,digest,ContractFailure
U=lambda n:'99999999-9999-4999-8999-'+str(n).zfill(12)
def make():return factory('PUBLISHED_FINAL_OUTPUT','synthetic-owner',U(1),U(2),U(3),U(4),U(5))
cases=[]
def test(name,fn,expected):
 try:fn();actual='ACCEPTED'
 except ContractFailure as e:actual=e.code
 except Exception as e:actual=type(e).__name__
 cases.append({'id':name,'expected':expected,'actual':actual,'passed':actual==expected})
body,server,_=make();test('declared-native-final-positive',lambda:validate_declared_final_output(body,server['generationBasisRepository'],server['finalOutputDeclarations']),'ACCEPTED')
test('published-bytes-without-server-final-slot',lambda:validate_declared_final_output(body,server['generationBasisRepository'],{}),'GENERATION_FINAL_OUTPUT_DECLARATION_UNAVAILABLE')
body,server,_=make();repo=server['generationBasisRepository'];decl=server['finalOutputDeclarations'][(U(1),U(4))];r=repo.records[U(3)];spec=json.loads(r['bytes']);spec['resultContract']['recordId']='OtherSyntheticResultIdentity';r['bytes']=canonical(spec);r['contentDigest']=digest(r['bytes']);decl['sourceSpecificationDigest']=r['contentDigest']
test('actual-result-id-versus-spec-record-id',lambda:validate_declared_final_output(body,repo,server['finalOutputDeclarations']),'GENERATION_FINAL_RESULT_CONTRACT_IDENTITY_MISMATCH')
def altered_schema(schema):
 body,server,_=make();repo=server['generationBasisRepository'];decl=server['finalOutputDeclarations'][(U(1),U(4))]
 sr=repo.records[U(3)];spec=json.loads(sr['bytes']);rr=repo.records[decl['resultContractArtifactId']];result=json.loads(rr['bytes']);br=repo.records[result['outputSchema']['bundle']['artifactId']]
 raw=canonical(schema);br['bytes']=raw;br['contentDigest']=digest(raw);br['artifactRef']['contentDigest']=digest(raw);br['artifactRef']['sizeBytes']=len(raw)
 result['outputSchema'].update(schemaId=schema['$id'],rootPointer='',nativeSchemaDigest=digest(raw));result['outputSchema']['bundle']=copy.deepcopy(br['artifactRef'])
 rr['bytes']=canonical(result);rr['contentDigest']=digest(rr['bytes']);rr['artifactRef']['contentDigest']=rr['contentDigest'];rr['artifactRef']['sizeBytes']=len(rr['bytes'])
 spec['resultContract']['artifact']=copy.deepcopy(rr['artifactRef']);spec['resultContract']['recordDigest']=rr['contentDigest'];sr['bytes']=canonical(spec);sr['contentDigest']=digest(sr['bytes']);decl['sourceSpecificationDigest']=sr['contentDigest'];decl['resultContractDigest']=rr['contentDigest']
 return body,server,repo
body,server,repo=altered_schema({'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:synthetic:actual-final-output','type':'string'})
test('native-valid-output-wrong-declared-consumer-mask',lambda:validate_declared_final_output(body,repo,server['finalOutputDeclarations']),'GENERATION_FINAL_OUTPUT_CONSUMER_SCHEMA_INVALID')
body,server,repo=altered_schema({'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:kcml:synthetic:actual-final-output','type':'INTEGER'})
test('invalid-source-output-schema-structured-rejection',lambda:validate_declared_final_output(body,repo,server['finalOutputDeclarations']),'GENERATION_FINAL_OUTPUT_SCHEMA_INVALID')
report={'scope':'Independent actual native final-slot/content/consumer-mask mutations; no SQL publication-role/closure predicate execution claim.','cases':cases,'checks':len(cases),'failed':sum(not c['passed']for c in cases),'helperSha256':hashlib.sha256((ROOT/'scripts/generation_admission_contracts.py').read_bytes()).hexdigest()}
(HERE/'final-output-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(cases),'failed':report['failed']}))
