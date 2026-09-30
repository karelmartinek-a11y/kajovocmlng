from pathlib import Path
import os,sys,hashlib,json,subprocess
HERE=Path(__file__).parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import SSOT,resource_index
script=ROOT/'scripts/verify_generation_physical_handoff.py';original=script.read_text();program=original.replace("database='generation_canonical_design_fixture'","database='generation_independent_canonical_review_fixture'")
assert program!=original
os.environ['KCML_AUDIT_OUTPUT']='audit/generated/resume-d362/review/canonical_handoff'
ns={'__file__':str(script),'__name__':'independent_canonical_handoff_review'};exec(compile(program,str(script),'exec'),ns);exitcode=ns['main']()
reportpath=HERE/'canonical_handoff/generation-physical-tests.json';report=json.loads(reportpath.read_text());rs=resource_index();sql=rs['database/generation-create-foundations.sql']['raw'];installed=(HERE/'combined-foundations.sql').read_bytes();assert installed==sql,'INDEPENDENT_INSTALLED_BYTES_DIFFER_CANONICAL'
report.update({'independentAdaptation':'Original current root verifier executed unchanged except disposable database name and supported KCML_AUDIT_OUTPUT destination. No shared files modified.','independentDatabase':'generation_independent_canonical_review_fixture','rootVerifierSHA256':hashlib.sha256(original.encode()).hexdigest(),'executedVerifierSHA256':hashlib.sha256(program.encode()).hexdigest(),'independentlyComparedInstalledBytesSHA256':hashlib.sha256(installed).hexdigest(),'installationByteEqualityVerified':True})
reportpath.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'canonicalIndependentChecked':report['checked'],'failed':report['failed'],'status':report['status'],'exactEmbeddedSQL':True}))
raise SystemExit(exitcode)
