"""Recheck pending Secret proposals; schema acceptance never activates a format."""
import hashlib,json,sys
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from create_operation_contracts import strict_json

def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 path=ROOT/'audit/generated/create-review-authority/secret-variant-proposals.json';raw=path.read_bytes();proposal=strict_json(raw)
 assert proposal['effective'] is False and proposal['status']=='PENDING_OWNER_FORMAT_REVIEW'
 source=(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()
 excerpts=[]
 for name,digest in proposal['sourceExcerptSHA256'].items():
  excerpt=(path.parent/name).read_bytes();assert sha(excerpt)==digest
  excerpts.append({'path':(path.parent/name).relative_to(ROOT).as_posix(),'sha256':digest,'exactBytesPresentInCurrentSSOT':excerpt in source})
 checks=[]
 for contract in proposal['contracts']:
  assert contract['status']=='PENDING_OWNER_FORMAT_REVIEW' and contract['effectiveContract'] is False
  schema=contract['schema'];Draft202012Validator.check_schema(schema)
  validator=Draft202012Validator(schema,format_checker=FormatChecker())
  positives={c['id'].rsplit('-',1)[0]:c['value'] for c in contract['syntheticCases'] if c['expected']=='SCHEMA_ACCEPT'}
  def leaves(errors):
   return [leaf for e in errors for leaf in ([e]+leaves(e.context))]
  for case in contract['syntheticCases']:
   errors=list(validator.iter_errors(case['value']));expected=case['expected']=='SCHEMA_ACCEPT'
   if not expected:
    positive=positives[case['id'].rsplit('-',1)[0]];assert validator.is_valid(positive)
    changed=[k for k in set(positive)|set(case['value']) if k not in positive or k not in case['value'] or positive[k]!=case['value'][k]]
    assert len(changed)==1,'Negative is not a single violation of its valid witness'
    field=changed[0]
    keyword='required' if field not in case['value'] else 'additionalProperties' if field not in positive else 'type' if case['value'][field] is None else 'const'
    exact=[e for e in leaves(errors) if e.validator==keyword and (e.json_path=='$' if keyword in ['required','additionalProperties'] else e.json_path=='$.'+field)]
    assert exact,case['id']+' rejected by an unrelated diagnostic'
   checks.append({'id':case['id'],'passed':(not errors)==expected,'expected':case['expected'],'scope':'SYNTHETIC_PROPOSAL_SCHEMA_ONLY','diagnostics':[{'keyword':e.validator,'pointer':e.json_path} for e in errors]})
 assert len(checks)==60 and all(c['passed'] for c in checks)
 report={'status':'PENDING_OWNER_FORMAT_REVIEW','sourceDocumentSha256':sha(source),'proposalSha256':sha(raw),'verifierSha256':sha(Path(__file__).read_bytes()),'jsonschemaVersion':__import__('importlib.metadata',fromlist=['version']).version('jsonschema'),'formatPrincipleApproved':True,'concreteFormatsApproved':False,'types':9,'variants':10,'proposalSchemaChecks':60,'failed':0,'checks':checks,'authorityExcerptByteRevalidation':excerpts,'semanticProposalCases':'NOT_EXECUTED_BY_THIS_STRUCTURAL_VERIFIER; independent42case proof in audit/generated/resume-5334/coordinator/secret-semantic-tests.json must be source/proposal/helper-bound separately','wholeSecretOperationVerified':False,'implementationAcceptance':'NOT_EVALUATED','limits':'Concrete encodings, fields, ranges and consumer semantics are new proposals; schema checks are not crypto/browser/OAuth parser or runtime proof.'}
 assert all(e['exactBytesPresentInCurrentSSOT'] for e in excerpts),'Historical authoritative excerpt changed: review before relying on proposal'
 out=ROOT/'audit/generated/create-review-authority/secret-proposals-current-review.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['status','sourceDocumentSha256','types','variants','proposalSchemaChecks','failed']}))
if __name__=='__main__':main()
