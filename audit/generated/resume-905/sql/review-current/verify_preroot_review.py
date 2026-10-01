from pathlib import Path
import hashlib,json
HERE=Path(__file__).parent;ROOT=Path('/workspace/kajovocmlng');AUTHOR=ROOT/'audit/generated/resume-34d/failure-sql'
p=AUTHOR/'verify_failure_before_root.py';source=p.read_text().split('\nchecks=[]\n',1)[0]
source=source.replace("'failure_sql_34d'","'review_preroot_sql905'").replace('CREATE DATABASE failure_sql_34d','CREATE DATABASE review_preroot_sql905')
ns={'__file__':str(p)};exec(compile(source,str(p),'exec'),ns)
base=ns['parts']();run=ns['run'];checks=[]
def case(name,parts):
 q=run('BEGIN;'+''.join(parts.values())+'SET CONSTRAINTS ALL IMMEDIATE;ROLLBACK;')
 checks.append({'case':name,'accepted':q.returncode==0,'diagnostic':q.stderr[-1200:]})
case('actual-native-valid-retained-error-positive',base)
# Baseline only proves currentSQL accepts author fixture. Adversarial native
# mask violations are evaluated independently against actual createcompletion.
import sys;sys.path.insert(0,str(ROOT/'scripts'))
from create_completion_contracts import ERRORS
definition='def parts'+source.split('def parts',1)[1]
for name,mutation in [('unknown-native-error-code', "error['stableCode']='UNKNOWN_REVIEW_CODE'"),('wrong-native-error-classification',"error['classification']='BOGUS'"),('extra-sensitive-error-field',"error['secretValue']='SYNTHETIC_REVIEW_VALUE'")]:
 program=definition.replace(" response=copy.deepcopy(ns['response']);",' '+mutation+"\n response=copy.deepcopy(ns['response']);")
 program=program.replace(" assert Draft202012Validator(ns['row']['responseSchema'],format_checker=FormatChecker()).is_valid(response),'INVALID_POSITIVE_NATIVE_RESPONSE'"," assert not Draft202012Validator(ns['row']['responseSchema'],format_checker=FormatChecker()).is_valid(response),'MUTANT_MUST_BREAK_EXACT_NATIVE_MASK'")
 fork=ns.copy();exec(compile(program,'positive-derived-error-mutation','exec'),fork);case(name,fork['parts']())
report={'sourceDocumentSha256':hashlib.sha256(ns['SSOT'].read_bytes()).hexdigest(),'canonicalSqlSha256':hashlib.sha256(ns['canonical']).hexdigest(),'extensionSqlSha256':hashlib.sha256(ns['extension']).hexdigest(),'executedAuthorPrefixSha256':hashlib.sha256(source.encode()).hexdigest(),'database':'review_preroot_sql905','postgresqlVersion':run('SHOW server_version;').stdout.strip(),'cases':checks,'scope':'Author-native-error validity checked independently againsteffectivefinitecatalog beforeclaimingpositive-derivedfailurenegatives','wholeOperationCertified':False}
(HERE/'preroot-initial-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(checks))
