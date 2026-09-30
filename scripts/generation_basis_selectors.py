"""Exact closed own-kind immutable selectors; no repository trust is inferred."""
import copy
from create_operation_contracts import UID,DIGEST,obj
closed=obj

def selector_schema():
 approval={'approvedRevisionId':UID,'expectedSpecificationDigest':DIGEST,'authorityId':UID,'expectedAuthorityDigest':DIGEST}
 return {'oneOf':[
  closed({'basisKind':{'const':'UPDATE_TARGET_REVISION'},'snapshotId':UID,'expectedDigest':DIGEST}),
  closed({'basisKind':{'const':'RETRY_FAILED_TECHNICAL_PART'},'phaseRunId':UID,'expectedDigest':DIGEST,
          'planId':UID,'expectedPlanDigest':DIGEST,**approval}),
  closed({'basisKind':{'const':'REPAIR_MONITORING_EVIDENCE'},'monitoringArtifactId':UID,'expectedDigest':DIGEST,
          'snapshotId':UID,'expectedTargetDigest':DIGEST,**approval})]}

def apply(body):
 result=copy.deepcopy(body)
 result["properties"]["generationBasis"]=selector_schema()
 for kind,basis in [("UPDATE","UPDATE_TARGET_REVISION"),("RETRY","RETRY_FAILED_TECHNICAL_PART"),("REPAIR","REPAIR_MONITORING_EVIDENCE")]:
  result["allOf"].append({"if":{"required":["kind"],"properties":{"kind":{"const":kind}}},"then":{"required":["generationBasis"]+(["parentJobId"] if kind=="RETRY" else ["targetObjectId","targetKind"]),"properties":{"generationBasis":{"properties":{"basisKind":{"const":basis}}}}}})
 result["allOf"].append({"if":{"required":["kind"],"properties":{"kind":{"enum":["UPDATE","RETRY","REPAIR"]}}},"else":{"not":{"required":["generationBasis"]}}})
 return result
