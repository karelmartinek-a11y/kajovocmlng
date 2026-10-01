"""Bounded design reference model; not canonical runtime/auth/PG evidence."""
from pathlib import Path
import json,hashlib,hmac,uuid,copy,secrets,threading,re,sys
sys.path.insert(0,"/workspace/kajovocmlng/scripts")
from create_completion_contracts import canonical_digest,semantic_result
from datetime import datetime,timedelta,timezone
from dataclasses import dataclass
from jsonschema import Draft202012Validator,FormatChecker
OUT=Path(__file__).parent;PACK=json.loads((OUT/'operation-mask-delta.json').read_text());OPS={x['operationId']:x for x in PACK['operations']}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def digest(v):return 'sha256:'+hashlib.sha256(v if isinstance(v,bytes)else canonical(v)).hexdigest()
def uid():return str(uuid.uuid4())
def stamp(v):return v.isoformat(timespec='milliseconds').replace('+00:00','Z')
def parse(v):return datetime.fromisoformat(v.replace('Z','+00:00'))
class Violation(ValueError):pass
@dataclass(frozen=True)
class Context:
 issuer:object;owner_id:str;channel:str;current_id:str|None;credential_version:int
class Store:
 def __init__(self):
  self.owner_id=uid();self.owner_epoch=2;self.owner_version=0;self.owner_sequence=0;self.now=datetime(2026,10,1,tzinfo=timezone.utc);self.issuer=object();self.api=secrets.token_bytes(32);self.api_hash=hashlib.sha256(self.api).digest();self.credential_version=1;self.rows={};self.session_tokens={};self.csrf={};self.events=[];self.outbox=[];self.audit=[];self.commands={};self.cursors={};self.responses={};self.lock=threading.RLock()
  # These are fixture values of a proposed versioned policy, not normative caps.
  self.policy={'policyId':'SYNTHETIC_POLICY_ONLY','version':'1','readDefaultPageSize':'2','reauthMaxAgeSeconds':'600'};self.policy_digest=digest(self.policy)
 def add(self,*,revoked=False,expired=False,epoch=None):
  sid=uid();token=secrets.token_bytes(32);self.session_tokens[sid]=hashlib.sha256(token).digest();self.csrf[sid]=secrets.token_bytes(32);created=self.now-timedelta(hours=1)
  self.rows[sid]={'id':sid,'createdAt':stamp(created),'lastSeenAt':stamp(self.now-timedelta(minutes=1)),'expiresAt':stamp(self.now-timedelta(seconds=1)if expired else self.now+timedelta(hours=1)),'revokedAt':stamp(self.now-timedelta(minutes=1))if revoked else None,'reauthenticatedAt':stamp(self.now-timedelta(minutes=1)),'sessionEpoch':str(self.owner_epoch if epoch is None else epoch),'stateVersion':'0','deviceMetadata':{'userAgent':'Synthetic exact  α\tUA','ipAddress':'192.0.2.17'},'ownerIdentityId':self.owner_id,'lookupDigest':digest(token),'sessionHash':'SYNTHETIC_NOT_CANONICAL_SESSION_HASH','mfaVerifiedAt':stamp(created)}
  return sid,token
 def authenticate(self,credential,channel):
  if channel=='OWNER_API_KEY':
   if not hmac.compare_digest(hashlib.sha256(credential).digest(),self.api_hash):raise Violation('UNAUTHENTICATED')
   return Context(self.issuer,self.owner_id,channel,None,self.credential_version)
  if channel!='OWNER_SESSION':raise Violation('UNAUTHENTICATED')
  matches=[sid for sid,v in self.session_tokens.items()if hmac.compare_digest(hashlib.sha256(credential).digest(),v)]
  if len(matches)!=1:raise Violation('UNAUTHENTICATED')
  sid=matches[0];row=self.rows[sid]
  if row['ownerIdentityId']!=self.owner_id or row['revokedAt']is not None or parse(row['expiresAt'])<=self.now or int(row['sessionEpoch'])!=self.owner_epoch or row['mfaVerifiedAt']is None:raise Violation('UNAUTHENTICATED')
  return Context(self.issuer,self.owner_id,channel,sid,self.credential_version)
 def require(self,ctx):
  if ctx.issuer is not self.issuer or ctx.owner_id!=self.owner_id or ctx.credential_version!=self.credential_version:raise Violation('UNAUTHENTICATED')
  if ctx.current_id:
   row=self.rows[ctx.current_id]
   if row['revokedAt']is not None or parse(row['expiresAt'])<=self.now or int(row['sessionEpoch'])!=self.owner_epoch:raise Violation('UNAUTHENTICATED')
 def public(self,row,ctx):return {k:copy.deepcopy(v)for k,v in row.items()if k in PACK['sessionPublicSchema']['properties'] and k!='current'}|{'current':row['id']==ctx.current_id}
 def response(self,oid,output,logical=None):
  row=OPS[oid];logical=logical or uid();v={'routeId':row['requestSchema']['properties']['routeId']['const'],'operationId':oid,'logicalOperationId':logical or uid(),'correlationId':logical or uid(),'status':'SUCCEEDED','terminal':True,'output':output,'error':None};v['resultDigest']=canonical_digest(semantic_result(v));Draft202012Validator(row['responseSchema'],format_checker=FormatChecker()).validate(v);raw=canonical(v);self.responses[v['logicalOperationId']]=raw;return v
 def listing(self,ctx,query):
  with self.lock:
   self.require(ctx)
   if query['cursor']is not None:
    saved=self.cursors.get(query['cursor'])
    if not saved or saved['ownerId']!=ctx.owner_id:raise Violation('CURSOR_INVALID')
    if saved['channel']!=ctx.channel or saved['currentId']!=ctx.current_id or query['limit']not in(None,str(saved['limit'])):raise Violation('CURSOR_QUERY_MISMATCH')
    rows=copy.deepcopy(saved['rows']);offset=saved['offset'];limit=saved['limit'];observed=saved['observedAt']
   else:
    limit=int(query['limit']or self.policy['readDefaultPageSize']);offset=0;observed=stamp(self.now);rows=[self.public(v,ctx)for _,v in sorted(self.rows.items())if v['ownerIdentityId']==ctx.owner_id]
   chosen=rows[offset:offset+limit];nextid=None
   if offset+limit<len(rows):
    nextid=uid();self.cursors[nextid]={'ownerId':ctx.owner_id,'channel':ctx.channel,'currentId':ctx.current_id,'rows':rows,'offset':offset+limit,'limit':limit,'observedAt':observed,'policyDigest':self.policy_digest}
   return self.response('owner.session.list',{'sessions':chosen,'observedAt':observed,'accessChannel':ctx.channel,'nextCursor':nextid,'ownerStateVersion':str(self.owner_version),'ownerSessionEpoch':str(self.owner_epoch)})
 def revoke(self,ctx,sid,expected,key,csrf=None,failpoint=None):
  with self.lock:
   self.require(ctx)
   if ctx.channel=='OWNER_SESSION':
    if not isinstance(csrf,bytes)or not hmac.compare_digest(csrf,self.csrf[ctx.current_id]):raise Violation('CSRF_INVALID')
    if parse(self.rows[ctx.current_id]['reauthenticatedAt'])<self.now-timedelta(seconds=int(self.policy['reauthMaxAgeSeconds'])):raise Violation('REAUTHENTICATION_REQUIRED')
   request={'operationId':'owner.session.revoke','sessionId':sid,'expectedStateVersion':expected};scope=(ctx.owner_id,'owner.session.revoke',sid,key);dg=digest(request)
   if scope in self.commands:
    old=self.commands[scope]
    if old['requestDigest']!=dg:raise Violation('IDEMPOTENCY_CONFLICT')
    return copy.deepcopy(old['response'])
   row=self.rows.get(sid)
   if row is None or row['ownerIdentityId']!=ctx.owner_id:raise Violation('SESSION_NOT_FOUND')
   if row['revokedAt']is not None:raise Violation('SESSION_ALREADY_REVOKED')
   if parse(row['expiresAt'])<=self.now:raise Violation('SESSION_EXPIRED')
   if int(row['sessionEpoch'])!=self.owner_epoch:raise Violation('SESSION_EPOCH_INVALIDATED')
   if row['stateVersion']!=expected:raise Violation('STATE_VERSION_CONFLICT')
   backup=copy.deepcopy((self.rows,self.events,self.outbox,self.audit,self.commands,self.responses,self.owner_version,self.owner_sequence));logical=uid()
   try:
    row['stateVersion']=str(int(row['stateVersion'])+1);row['revokedAt']=stamp(self.now);self.owner_version+=1;self.owner_sequence+=1
    payload={'sessionId':sid,'revokedAt':row['revokedAt'],'stateVersion':row['stateVersion'],'ownerStateVersion':str(self.owner_version)};ev=uid();event={'routeId':'route.0019','operationId':'owner.session.revoke','logicalOperationId':logical,'correlationId':logical,'sequence':str(self.owner_sequence),'eventType':'owner.session.revoked','payload':payload,'payloadDigest':digest(payload)}
    Draft202012Validator(OPS['owner.session.revoke']['eventSchema'],format_checker=FormatChecker()).validate(event)
    self.events.append(event);self.outbox.append({'eventId':ev,'logicalOperationId':logical,'payloadDigest':event['payloadDigest']});self.audit.append({'eventId':ev,'afterDigest':event['payloadDigest'],'sessionId':sid});response=self.response('owner.session.revoke',payload|{'current':sid==ctx.current_id},logical);self.commands[scope]={'requestDigest':dg,'response':response}
    if failpoint=='AFTER_OUTBOX':raise Violation('SYNTHETIC_ROLLBACK_CUTPOINT')
    return copy.deepcopy(response)
   except Exception:self.rows,self.events,self.outbox,self.audit,self.commands,self.responses,self.owner_version,self.owner_sequence=backup;raise
 def hydrate(self,response):
  row=OPS[response['operationId']];Draft202012Validator(row['responseSchema'],format_checker=FormatChecker()).validate(response)
  if canonical_digest(semantic_result(response))!=response['resultDigest']:raise Violation('RESULT_DIGEST_MISMATCH')
  if self.responses.get(response['logicalOperationId'])!=canonical(response):raise Violation('SERVER_RECEIPT_BYTES_MISMATCH')
  if response['operationId']=='owner.session.list':
   ids=[x['id']for x in response['output']['sessions']]
   if ids!=sorted(set(ids)):raise Violation('SESSION_LIST_ORDER_OR_DUPLICATE')
  return copy.deepcopy(response['output'])
def decode(oid,method,path,query,headers,body=b''):
 row=OPS[oid];mut=oid.endswith('revoke');params={}
 if method!=row['transport']['method']:raise Violation('HTTP_METHOD_MISMATCH')
 if mut:
  prefix='/owner/sessions/'
  if not path.startswith(prefix)or not re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',path[len(prefix):]):raise Violation('HTTP_PATH_INVALID')
  params={'id':path[len(prefix):]}
 elif path!='/owner/sessions':raise Violation('HTTP_PATH_INVALID')
 if body:raise Violation('HTTP_BODY_NOT_ALLOWED')
 names=[x[0]for x in query]
 if len(set(names))!=len(names):raise Violation('HTTP_QUERY_DUPLICATE')
 if any(n not in ([]if mut else ['cursor','limit'])for n in names):raise Violation('HTTP_QUERY_UNKNOWN')
 hs={}
 for name,value in headers:
  n=name.lower()
  if n in hs:raise Violation('HTTP_HEADER_DUPLICATE')
  hs[n]=value
 guards={k:None for k in row['requestSchema']['properties']['guards']['properties']}
 if mut:
  if 'if-match'not in hs:raise Violation('HTTP_IF_MATCH_REQUIRED')
  if not re.fullmatch(r'"(?:0|[1-9][0-9]*)"',hs['if-match']):raise Violation('HTTP_IF_MATCH_INVALID')
  guards['expectedStateVersion']=hs['if-match'][1:-1]
  if not hs.get('idempotency-key'):raise Violation('HTTP_IDEMPOTENCY_KEY_REQUIRED')
  guards['idempotencyKey']=hs['idempotency-key']
 native={'routeId':row['requestSchema']['properties']['routeId']['const'],'operationId':oid,'pathParameters':params,'query':[]if mut else {'cursor':dict(query).get('cursor'),'limit':dict(query).get('limit')},'body':None,'guards':guards};guards['clientRequestDigest']=digest({k:v for k,v in native.items()if k!='guards'}|{'expectedStateVersion':guards['expectedStateVersion']});Draft202012Validator(row['requestSchema'],format_checker=FormatChecker()).validate(native);return native
