"""Additive authoring proposal; no canonical mutation or runtime implementation."""
import copy
REASON='RESULT_RETAINED_AS_TOMBSTONE'
def retained_error_reason(schema):
 result=copy.deepcopy(schema)
 def visit(node):
  if isinstance(node,dict):
   p=node.get('properties',{})
   if node.get('additionalProperties')is False and {'stableCode','classification','retryDirective','message','detailsDigest'}<=set(p):
    p['machineReason']={'type':'string','const':REASON}
    node.setdefault('allOf',[]).append({'if':{'required':['machineReason']},'then':{'properties':{'stableCode':{'const':'IDEMPOTENCY_CONFLICT'},'classification':{'const':'CONFLICT'},'retryDirective':{'const':'DO_NOT_RETRY'}}}})
   for v in list(node.values()):visit(v)
  elif isinstance(node,list):
   for v in node:visit(v)
 visit(result)
 return result
