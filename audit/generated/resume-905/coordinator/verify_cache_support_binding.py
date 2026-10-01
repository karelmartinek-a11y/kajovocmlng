"""Reproduce old cache blindness to an actually consumed independent fixture script."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from run_ssot_repair_design_checks import evidence_inputs_hash
old=subprocess.check_output(['git','show','32a63a9e3447bd4ed9a7dc4638cadc113071a8b7:scripts/run_ssot_repair_design_checks.py'],cwd=ROOT,text=True)
ns={'__name__':'historical_cache_probe','__file__':str(ROOT/'scripts/run_ssot_repair_design_checks.py')};exec(compile(old,'historical-pushed-runner','exec'),ns)
p=ROOT/'audit/generated/resume-905/sql/review-consumers/archive/verify_archive.py';original=p.read_bytes();name='verify_producer_archive_handoffs.py'
before_old=ns['evidence_inputs_hash'](name);before_new=evidence_inputs_hash(name)
try:
 p.write_bytes(original+b'\n# Synthetic isolated cache-binding mutation; not an execution claim.\n')
 after_old=ns['evidence_inputs_hash'](name);after_new=evidence_inputs_hash(name)
 report={'sourceDocumentSha256':hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest(),'historicalRunnerCommit':'32a63a9e3447bd4ed9a7dc4638cadc113071a8b7','consumedPath':p.relative_to(ROOT).as_posix(),'oldFailure':{'result':'DEFECT_REPRODUCED','before':before_old,'after':after_old,'hashIncorrectlyUnchanged':before_old==after_old},'repair':{'before':before_new,'after':after_new,'changedConsumedCodeInvalidatesCache':before_new!=after_new},'status':'PASS'if before_old==after_old and before_new!=after_new else'BLOCKED','wholeOperationClosed':False}
finally:p.write_bytes(original)
report['inputRestoredExactly']=p.read_bytes()==original
(Path(__file__).parent/'cache-support-binding-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'oldDefectReproduced':report['oldFailure']['hashIncorrectlyUnchanged'],'inputRestoredExactly':report['inputRestoredExactly']}));sys.exit(report['status']!='PASS')
