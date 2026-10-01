"""Owned candidate ordered genuine auth→C→sorted E→H constructor.
Immutable kind ordinals/migration map remain review requirements; this code never
claims global §51.6 closure without the complete registered child lock plan.
"""
from native_auth_factory import *
from owner_api_ordered_auth import verify_owner_api_material,persist_verified_material
import uuid,hmac
class OrderedFactory(Factory):
 def __init__(self,name):
  super().__init__(name)
  self.db.query(Path(__file__).with_name('generation-ordered-context.sql').read_text())
 def build(self,body,job,op,snapshot,sequence=1,previous_hash=bytes(32),key='joined-native-key'):
  row,native,plain,token=self.native(body,key);kd=sha(key.encode());rd=bytes.fromhex(native['requestDigest'][7:]);desc=descriptor_bytes(OWNER,'sha256:'+kd.hex(),self.pinned)
  verified=verify_owner_api_material(self.db,token,rd,desc,self.ceiling)
  built=self._assemble(body,job,op,snapshot,row,native,plain,rd,kd,desc,verified.context_id,sequence,previous_hash,key)
  locator=built['parts'].pop('locator');self.db.query(locator[:-1]+' ON CONFLICT ON CONSTRAINT uq_idempotency_locator_scope DO NOTHING;')
  stored=self.db.query("SELECT logical_operation_id,encode(client_request_digest,'hex'),encode(frozen_revision_digest,'hex')FROM idempotency_locator WHERE operation_family='GENERATION'AND caller_authority_kind='OWNER_FULL'AND caller_stable_id="+lit(verified.owner_id)+"AND business_target_kind='CREATE_ROOT'AND business_target_id='generation_job'AND client_key_digest="+b(kd)+' FOR UPDATE')[0]
  if not hmac.compare_digest(bytes.fromhex(stored[1]),rd):raise ValueError('IDEMPOTENCY_CONFLICT')
  if stored[0]!=op:
   retained=self.db.query('SELECT logical_operation_id,state FROM domain_idempotency_record WHERE scope_digest='+b(bytes.fromhex(stored[2]))+'AND key_digest='+b(kd)+' FOR UPDATE')
   if len(retained)!=1 or retained[0][0]!=stored[0]:raise ValueError('GENERATION_RETAINED_IDEMPOTENCY_INCOMPLETE')
   return {'replay':True,'logicalOperationId':stored[0],'retainedState':retained[0][1],'verifiedOwnerId':verified.owner_id}
  self.db.query(built['parts'].pop('idempotency'))
  self.db.query('SELECT logical_operation_id FROM domain_idempotency_record WHERE scope_digest='+b(sha(desc))+'AND key_digest='+b(kd)+'FOR UPDATE')
  if self.db.query('SELECT id FROM owner_identity WHERE singleton_key=1 AND id='+lit(verified.owner_id)+' FOR UPDATE')!=[[verified.owner_id]]:raise ValueError('GENERATION_OWNER_IDENTITY_CHANGED')
  root=built['parts'].pop('root');roots=[job]+([body['parentJobId']]if body.get('parentJobId')else[])
  for id in sorted(set(roots),key=lambda v:uuid.UUID(v).bytes):
   if id==job:self.db.query(root)
   elif not self.db.query('SELECT id FROM generation_job WHERE id='+lit(id)+'FOR UPDATE'):raise ValueError('RETRY_SOURCE_JOB_UNAVAILABLE')
  persist_verified_material(self.db,verified,self.pinned['contractDigest'])
  hook=getattr(self,'late_acceptance_hook',None)
  if hook:hook(verified.context_id,op)
  # Domain command35 precedes actual source phase50 and effect state140/150.
  self.db.query(built['parts'].pop('command'));self.db.query(built['parts'].pop('typed-binding'))
  if body.get('kind')=='RETRY':self.db.query('SELECT phase_run_id FROM kcml_retry_v1.phase WHERE phase_run_id='+lit(body['generationBasis']['phaseRunId'])+'FOR UPDATE')
  self.db.query(built['parts'].pop('snapshot'))
  built['replay']=False
  return built
 def insert(self,built):
  # Work910 and auditI must remain last after archive/lineage children.
  for k in list(built['parts']):
   if k in ['nonce']:self.db.query(built['parts'].pop(k))
 def finish(self,built):
  for k in ['event','completion','finalize-idempotency','outbox','audit']:
   if k in built['parts']:self.db.query(built['parts'].pop(k))
