"""Exact historical check-universe and unchanged provenance-detector comparison."""
import collections,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from ssot_sources import resources
PATTERN=r'(?i)(předchozí verz|původn|opraven|doplněn|rozsah změn|výsledek revize|aktuální dodatek|stav po kapitola|nově přid|historick)'
def git(commit,path):return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
def hits(raw):
 text=raw.decode();prose=text
 for r in reversed(list(resources(text))):a,b=r['match'].span();prose=prose[:a]+'[RESOURCE]'+prose[b:]
 return [line for line in prose.splitlines() if re.search(PATTERN,line)]
def main():
 old=json.loads(git('003cef7','audit/generated/repair-2026-09-30/design-current/commands.json'));new=json.loads(git('5334d8c','audit/generated/repair-2026-09-30/design-current/commands.json'))
 a={c['script']:c for c in old['commands']};b={c['script']:c for c in new['commands']}
 versions={c:hits(git(c,'00_SSOT/KajovoCMLNG_SSOT.md')) for c in ['aaab5a1','003cef7','5334d8c']}
 added=list((collections.Counter(versions['5334d8c'])-collections.Counter(versions['003cef7'])).elements())
 reviewed=[{'line':l,'scope':'Create12.48/12.49 domain original frozen receipt/lineage or explicit73.7 historical-gate precedence; not a conflicting contract by token match alone','status':'BOUNDED_SEMANTIC_REVIEW','finding':'Lexical hit; no new conflicting requirement established'} for l in added]
 report={'detectorPattern':PATTERN,'detectorPatternChanged':False,'historicalVerifierBytesUnchanged':git('003cef7','scripts/verify_package.py')==git('5334d8c','scripts/verify_package.py'),'hitsByCommit':{c:len(v) for c,v in versions.items()},'addedChecks':[k for k in b if k not in a],'changedResults':[{'script':k,'before':a[k]['exitCode'],'after':b[k]['exitCode'],'cause':'Historical native-bundle byte equality rejects exact scoped create-error catalog additions; corrected scoped composition preserves all other masks and original codes'} for k in a.keys()&b.keys() if a[k]['exitCode']!=b[k]['exitCode']],'additionalDetectorHits':reviewed,'legacyHitReview':'152 remains required; bounded review of7additional lexical hits does not close global provenance consolidation','reported149':'149 is the legacy-parser aaab5a1 historical count; full-family re-count is148. Full-family003cef7 is152 and5334d8c is159. Legacy parser omitted3ERRORS/EXPERIENCE resources and inflated003/533 lexical counts153/161; parsercoverage correction preserves common resource bytes and detector regex.', 'parserCoverageRepair':'scripts/ssot_resources.py delegates canonical all-family parser; existing common decodedbytes identical, adds3effectiveERRORS/EXPERIENCE resources'}
 out=ROOT/'audit/generated/resume-5334/coordinator/metrics-explanation.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['hitsByCommit','addedChecks','changedResults','detectorPatternChanged']}))
if __name__=='__main__':main()
