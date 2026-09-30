"""Actual Chromium partitioned-cookie capture/fresh restore, synthetic local fixtures."""
import copy,hashlib,json,sys,time,math,os,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
D=Path(__file__).resolve().parent
R=next(p for p in D.parents if (p/'00_SSOT/KajovoCMLNG_SSOT.md').is_file())
sys.path.insert(0,str(R/'scripts'))
from ssot_resources import get
from jsonschema import Draft202012Validator,FormatChecker
MASK_PATH='contracts/secrets/profile-handoffs.schema.json'
mask_raw=get('KCML-R9-RESOURCE',MASK_PATH)
SCHEMA=json.loads(mask_raw);_cookie_defs=SCHEMA['$defs']
assert _cookie_defs['Cookie']['properties']['sameSite']['enum'].count('UNSPECIFIED')==1, 'CURRENT_NORMATIVE_COOKIE_MASK_MISSING_OR_DUPLICATED_UNSPECIFIED'
def validate(name,value):
 Draft202012Validator({'$schema':SCHEMA['$schema'],'$defs':_cookie_defs,'$ref':'#/$defs/'+name},format_checker=FormatChecker()).validate(value)
from partition_cookie_adapter import *
D=Path(__file__).resolve().parent;D.joinpath('partition-cookie-member.schema.json').write_text(json.dumps({'$schema':SCHEMA['$schema'],'$defs':_cookie_defs,'$ref':'#/$defs/Cookie'},indent=2)+'\n');source=R/'00_SSOT/KajovoCMLNG_SSOT.md';input_hash=hashlib.sha256(source.read_bytes()).hexdigest();checks=[]
def check(id_,v):checks.append({'id':id_,'passed':bool(v)})
def no(id_,fn,code):
 try:fn();checks.append({'id':id_,'passed':False,'actual':'ACCEPTED','expectedCode':code})
 except CookieRejected as e:checks.append({'id':id_,'passed':str(e)==code,'actualCode':str(e),'expectedCode':code})
with sync_playwright()as pw:
 browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH')or shutil.which('chromium'),headless=True,args=['--no-sandbox']);version=browser.version
 contexts=[]
 def fresh():
  c=browser.new_context();contexts.append(c);p=c.new_page();return c.new_cdp_session(p)
 source_cdp=fresh()
 # Same name/domain/path/site differs solely by ancestor bit; an adapter
 # dropping that bit collapses the actual browser cookie identities.
 expiry=float(math.floor(time.time())+86400)+.125
 source_cdp.send('Network.setCookies',{'cookies':[{'name':'SYNTHETIC','value':'exact_false_%2B','domain':'example.invalid','path':'/','secure':True,'httpOnly':True,'sameSite':'None','expires':expiry,'partitionKey':{'topLevelSite':'https://top.invalid','hasCrossSiteAncestor':False}},{'name':'SYNTHETIC','value':'exact_true','domain':'example.invalid','path':'/','secure':True,'httpOnly':False,'sameSite':'None','partitionKey':{'topLevelSite':'https://top.invalid','hasCrossSiteAncestor':True}},{'name':'SYNTHETIC','value':'other_site','domain':'example.invalid','path':'/','secure':True,'httpOnly':True,'sameSite':'Strict','partitionKey':{'topLevelSite':'https://other.invalid','hasCrossSiteAncestor':False}},{'name':'UNPARTITIONED','value':'exact_no_partition','domain':'.example.invalid','path':'/scope','secure':True,'httpOnly':True,'sameSite':'Lax'},{'name':'UNSPECIFIED','value':'native_unspecified_samesite','domain':'example.invalid','path':'/','secure':True,'httpOnly':True}]})
 captured=capture(source_cdp)
 for c in captured:validate('Cookie',c)
 check('actual-capture-five-closed-profile-cookie-masks',len(captured)==5)
 keys={identity(c)for c in captured};check('same-site-cookie-ancestor-bits-not-collapsed',len(keys)==5)
 check('exact-fractional-expiry-binary64',any(c['expiry']['kind']=='ABSOLUTE'and seconds(c['expiry']['unixSeconds'])==expiry for c in captured))
 check('native-unspecified-samesite-not-guessed-as-lax',next(c for c in captured if c['name']=='UNSPECIFIED')['sameSite']=='UNSPECIFIED')
 dst=fresh();check('actual-fresh-context-exact-partition-value-expiry-unspecified-restore',restore_empty_context(dst,captured)==capture(dst))
 no('nonfresh-context-specific-rejection',lambda:restore_empty_context(dst,captured),'BROWSER_COOKIE_RESTORE_CONTEXT_NOT_FRESH')
 bad=copy.deepcopy(captured);bad.append(copy.deepcopy(bad[0]));no('duplicate-native-partition-identity',lambda:restore_empty_context(fresh(),bad),'BROWSER_COOKIE_DUPLICATE_PARTITION_IDENTITY')
 bad=copy.deepcopy(captured);bad[0]['hostOnly']=not bad[0]['hostOnly'];no('host-only-domain-incoherence',lambda:restore_empty_context(fresh(),bad),'BROWSER_COOKIE_HOST_SCOPE_MISMATCH')
 bad=copy.deepcopy(captured);next(c for c in bad if c['partition']['kind']=='TOP_LEVEL_SITE')['partition']['topLevelSite']='https://sub.top.invalid'
 # Browser maps this origin to schemeful site https://top.invalid. Never accept
 # the resulting mismatch or silently normalize the imported protected value.
 no('engine-schemeful-site-normalization-rejected-exactly',lambda:restore_empty_context(fresh(),bad),'BROWSER_COOKIE_ENGINE_VALUE_OR_PARTITION_MISMATCH')
 bad=copy.deepcopy(captured);next(c for c in bad if c['partition']['kind']=='TOP_LEVEL_SITE')['secure']=False
 no('partitioned-cookie-secure-required',lambda:restore_empty_context(fresh(),bad),'BROWSER_COOKIE_PARTITION_SECURE_REQUIRED')
 bad=copy.deepcopy(captured);bad[0]['expiry']={'kind':'ABSOLUTE','unixSeconds':ieee(1)}
 no('expired-cookie-not-partial-auth-success',lambda:restore_empty_context(fresh(),bad),'BROWSER_COOKIE_EXPIRED_BEFORE_RESTORE')
 bad=copy.deepcopy(captured);bad[0]['value']=' INVALID LEADING SPACE '
 no('invalid-native-cookie-encoding-specific-engine-error',lambda:restore_empty_context(fresh(),bad),'BROWSER_COOKIE_ENGINE_INPUT_REJECTED')
 opaque=source_cdp.send('Network.getAllCookies')['cookies'][0].copy();opaque['partitionKeyOpaque']=True
 no('opaque-partition-no-silent-fallback',lambda:from_cdp(opaque),'BROWSER_COOKIE_OPAQUE_PARTITION_UNSUPPORTED')
 check('source-context-cookie-snapshot-not-mutated-by-failed-restores',capture(source_cdp)==captured)
 for c in contexts:c.close()
 browser.close()
report={'inputSsotSha256':input_hash,'inputSourceUnchangedDuringFixture':hashlib.sha256(source.read_bytes()).hexdigest()==input_hash,'authority':['00_SSOT/KajovoCMLNG_SSOT.md §13.15 cookies including partition/partition-key metadata','§13.15 fresh context restore before navigation; no partially authenticated fallback','§8.4 exact immutable protected bytes; §72.21 NO_SILENT_NORMALIZATION'],'browserVersion':version,'checked':len(checks),'failed':sum(not c['passed']for c in checks),'checks':checks,'supportSha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in [D/'verify_partition_cookie.py',D/'partition_cookie_adapter.py',D/'cookie-mask-patch.json',D/'partition-cookie-member.schema.json',R/'scripts/ssot_resources.py',R/'scripts/ssot_sources.py']},'canonicalResource':MASK_PATH,'canonicalResourceSha256':hashlib.sha256(mask_raw).hexdigest(),'maskSource':'ACTUAL_CANONICAL_EMBEDDED_BYTES_NO_PROPOSAL_PATCH','sensitiveValuesInReport':False,'scope':'REAL_CHROMIUM_PARTITION_COOKIE_MEMBER_CAPTURE_RESTORE','excluded':['Full required browser capture transaction/barrier/encryption/epoch-CAS','Real provider account/tenant marker','Client-certificate/OWNER Device Bridge','Whole profile activation'],'fullProfileActivation':'NOT_ACTIVATED'}
(D/'partition-cookie-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checked':report['checked'],'failed':report['failed']}));
for c in checks:
 if not c['passed']:print(json.dumps(c))
raise SystemExit(bool(report['failed']))
