"""Current continuation overlay after explicit runner/register; no own-result commit hash."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=ROOT/'audit/SSOT_REPAIR_CHECKPOINT.json';c=json.loads(p.read_text());source=sha(ROOT/'00_SSOT/KajovoCMLNG_SSOT.md');assert c['currentSourceDocumentSha256']==source
 previous=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 c['continuationInput'].update(lastVerifiedCommittedBlock=previous,currentBlock='SECRET_EFFECTIVE_IMPORT_AND_STORED_METADATA_BOUNDED',sourceSha256=source)
 proofs={}
 for label,path in [('native','coordinator/secret-profile-native-tests.json'),('independent','review/secret-current/secret-native-review.json'),('PostgreSQL','failure-sql/secret-profile-current/postgres-tests.json'),('Chromium','secrets-browser/partition-current/partition-cookie-tests.json')]:
  file=ROOT/'audit/generated/resume-34d'/path;q=json.loads(file.read_text());assert q.get('sourceDocumentSha256',q.get('sourceSha256',q.get('inputSsotSha256')))==source and q['failed']==0
  proofs[label]={'path':file.relative_to(ROOT).as_posix(),'sha256':sha(file),'sourceSha256':source,'checked':q['checked'],'failed':0,'scope':'Exact bounded proof only; whole operation and production acceptance excluded'}
 c['secretCurrentIntegration']={'normative':['§8.12','§8.13'],'effectiveMasks':['contracts/secrets/import.schema.json','contracts/secrets/profile-handoffs.schema.json'],'approvedLimitedProfiles':10,'fullBrowserProfile':'NOT_ACTIVATED','wholeOperationClosed':False,'proofs':proofs,'actualDefectsReproducedAndFixed':['Stored schemaId mismatch accepted','Stored type/profile mismatch accepted'],'createDiagnosticMapping':'Only35 current import/parser/registry diagnostics; load/use failures never called create-input errors','mandatoryRemaining':['Actual trusted registry review/context/command producer and locked root acceptance','Canonical systemd key/global nonce/typed protected rows','Atomic command/root/event/outbox/audit/locator and reserved OWNER credential joins','Real consumer target/activation/broker and complete read/UI','Full13.15 bridge/encrypted bundle/CAS/account and all serializer/key/generator variants']}
 c['secretVariants'].update(effective='CURRENT_ROUTE_PROFILE_IMPORT_EFFECTIVE_BOUNDED_STORAGE_USE',status='LIMITED_PROFILE_MASKS_EFFECTIVE_WHOLE_OPERATION_OPEN',concreteFormatApproval='TEN_LIMITED_NAMES_APPROVED_NOT_UNIVERSAL_TYPES',currentSourceReviewEvidence=proofs['independent']['path'])
 c['secretVariants']['semanticProposalCases']='HISTORICAL18/42 proposal cases; current precise native and independent proofs are in secretCurrentIntegration, not format approval'
 c['secretVariants']['productApproval']['effectiveActivation']='EXACT_LIMITED_IMPORT_EFFECTIVE_FULL_AUTHENTICATED_ACTIVATION_OPEN'
 if 'secrets-browser' not in c['auxiliaryReviews']['integrated']:c['auxiliaryReviews']['integrated'].append('secrets-browser')
 c['auxiliaryReviews']['preparedNotYetEffective']=[]
 c['nextBlock']={'id':'GENERATION_LOCKED_RETRY_PRODUCER_TO_CHILD_AND_CANONICAL_KEY_SOURCE','scope':'Complete full49.8 phase-ledger producer/completeness/fencing under source gate and hold scan transaction through child frozen-lineage/root commit. In parallel resolve actual systemd credential fixture availability and canonical key/global nonce protected-row authority. Continue trusted Secret registry/context/command/root/event/outbox/audit joins. No bool-valid inputs or mock key authority substitutes.','inputs':['audit/SSOT_CREATE_OPERATION_OBLIGATIONS.md','audit/generated/resume-34d/retry-graph/INTEGRATION.md','contracts/generation/create-chain-handoffs.json','contracts/secrets/import-storage-use.json'],'generationWholeOperation':'OPEN','secretWholeOperation':'OPEN'}
 c['metricsBeforeAfter']['after']['provenanceDetectorHits']=c['currentResults']['provenanceDetectorHits']
 c['metricsBeforeAfter']['interpretation']='Two new required checks extend coverage46→48; broad overlapping inventory unchanged. Provenance lexical additions come from new source wording, not established defects or detector changes. Zero whole closed operations, no percent.'
 c['remaining']=c['generationMandatoryRemaining']+c['secretCurrentIntegration']['mandatoryRemaining']+['242references/1500genericboundaries/500genericroutes/152eventapplicability; all remaining whole domain families','Four generic SQL helpers/262call-site plans;258legacyerrorpredicates and '+str(c['currentResults']['provenanceDetectorHits'])+'lexicalprovenancehits require semantic review','Browser/MCP/agents/OpenAI/monitoring and all13 P00–P12 handoffs']
 c['evidenceInvalidation']['visual']='Exact consumed UI/schema/file/requirements/render bytes verified unchanged; reused current96 renders, no rerender in Secret block. Manual PENDING/runtime NOT_EVALUATED.'
 c['draftPR'].update(status='FORBIDDEN',title='Repair SSOT authenticated create chains and exact Secret import handoffs',body='audit/SSOT_REPAIR_DRAFT_PR.md',currentAttemptEvidence='audit/generated/resume-34d/coordinator/draft-pr-attempt.json',bypassAttempted=False)
 c['continuationInput']['lastVerifiedCommittedBlockSSOTSha256']='8e9f915fa95e7f1524992ec8677306a4133422f007b06abfff7c0861256abfdf'
 resume=json.loads((ROOT/'audit/generated/resume-34d/coordinator/runner-resume-proof.json').read_text());assert resume['sourceSha256']==source
 c['runnerResumeVerification'].update(cacheReuse=resume['reused'],commandsExecuted=resume['commandsExecuted'],proof='audit/generated/resume-34d/coordinator/runner-resume-proof.json')
 c['integrationDiagnostics']={'historicalFailedRunner':'audit/generated/resume-34d/coordinator/secret-integration-diagnostics/initial-48-commands.json','repaired':['Audit native Secret candidate bytes omitted from JSON witness export','Norm8.11 old RAW text replaced by owned exact PROFILE addendum; original42 Secrets policy checks pass','PEM labels removed from35-code CREATE-stage diagnostic whitelist'],'currentExceptionsOrTimeouts':[]}
 breakdown_path=ROOT/'audit/generated/resume-34d/coordinator/generic-boundary-breakdown.json'
 if breakdown_path.exists():
  breakdown=json.loads(breakdown_path.read_text());assert breakdown['sourceSha256']==source
  c['metricsBeforeAfter']['before']['genericBoundariesByRole']=breakdown['before'];c['metricsBeforeAfter']['after']['genericBoundariesByRole']=breakdown['after'];c['metricsBeforeAfter']['boundaryEvidence']=breakdown_path.relative_to(ROOT).as_posix()
 c['finalPackaging']={'receipt':'audit/generated/integrity-receipt.json','verification':'Verify after all evidence/checkpoint writes; packaging-only readiness remains BLOCKED','ownCommitShaIncluded':False}
 c['status']='PARTIAL';c['SSOT_CONTRACT_READY']='BLOCKED';c['IMPLEMENTATION_PRODUCTION_ACCEPTANCE']='NOT_EVALUATED'
 p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'source':source,'priorCommittedBlock':previous,'status':'PARTIAL'}))
if __name__=='__main__':main()
