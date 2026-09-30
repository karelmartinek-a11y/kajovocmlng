"""Explicit Chromium CDP cookie member adapter; no browser profile/authority fallback."""
import base64,math,struct,time
class CookieRejected(ValueError):pass
def reject(code):raise CookieRejected(code)
def ieee(v):return {'encoding':'IEEE754_BINARY64_BIG_ENDIAN_BASE64','base64':base64.b64encode(struct.pack('>d',v)).decode()}
def seconds(v):
 try:raw=base64.b64decode(v['base64'],validate=True);n=struct.unpack('>d',raw)[0]
 except (ValueError,KeyError,TypeError,struct.error):reject('BROWSER_COOKIE_EXPIRY_ENCODING_INVALID')
 if not math.isfinite(n):reject('BROWSER_COOKIE_EXPIRY_ENCODING_INVALID')
 return n

def from_cdp(native):
 if native.get('partitionKeyOpaque'):reject('BROWSER_COOKIE_OPAQUE_PARTITION_UNSUPPORTED')
 partition=native.get('partitionKey')
 if partition is not None and (not isinstance(partition,dict)or set(partition)!={'topLevelSite','hasCrossSiteAncestor'}):reject('BROWSER_COOKIE_PARTITION_CAPABILITY_UNSUPPORTED')
 return {'name':native['name'],'value':native['value'],'domain':native['domain'],'hostOnly':not native['domain'].startswith('.'),'path':native['path'],'secure':native['secure'],'httpOnly':native['httpOnly'],'sameSite':native.get('sameSite','UNSPECIFIED'),'expiry':{'kind':'SESSION'}if native['session']else{'kind':'ABSOLUTE','unixSeconds':ieee(native['expires'])},'partition':{'kind':'UNPARTITIONED'}if partition is None else{'kind':'TOP_LEVEL_SITE',**partition}}

def native_params(cookie):
 # Only validated Cookie mask inputs reach this transport adapter.
 out={k:cookie[k]for k in ['name','value','domain','path','secure','httpOnly']}
 if cookie['sameSite']!='UNSPECIFIED':out['sameSite']=cookie['sameSite']
 if cookie['hostOnly']!=(not cookie['domain'].startswith('.')):reject('BROWSER_COOKIE_HOST_SCOPE_MISMATCH')
 if cookie['expiry']['kind']=='ABSOLUTE':
  n=seconds(cookie['expiry']['unixSeconds'])
  if n<=time.time():reject('BROWSER_COOKIE_EXPIRED_BEFORE_RESTORE')
  out['expires']=n
 if cookie['partition']['kind']=='TOP_LEVEL_SITE':
  if not cookie['secure']:reject('BROWSER_COOKIE_PARTITION_SECURE_REQUIRED')
  out['partitionKey']={k:cookie['partition'][k]for k in ['topLevelSite','hasCrossSiteAncestor']}
 return out

def identity(cookie):
 p=cookie['partition']
 return (cookie['name'],cookie['domain'],cookie['hostOnly'],cookie['path'],p['kind'],p.get('topLevelSite'),p.get('hasCrossSiteAncestor'))

def capture(cdp):return [from_cdp(c)for c in cdp.send('Network.getAllCookies')['cookies']]

def restore_empty_context(cdp,cookies):
 # Caller creates a fresh isolated context under the authenticated restore plan.
 # On mismatch it must close that context; source bundle is never rewritten.
 if cdp.send('Network.getAllCookies')['cookies']:reject('BROWSER_COOKIE_RESTORE_CONTEXT_NOT_FRESH')
 keys=[identity(c)for c in cookies]
 if len(keys)!=len(set(keys)):reject('BROWSER_COOKIE_DUPLICATE_PARTITION_IDENTITY')
 params=[native_params(c)for c in cookies]
 try:cdp.send('Network.setCookies',{'cookies':params})
 except __import__('playwright.sync_api',fromlist=['Error']).Error:reject('BROWSER_COOKIE_ENGINE_INPUT_REJECTED')
 restored=capture(cdp)
 actual={identity(c):c for c in restored}
 if len(actual)!=len(cookies)or any(actual.get(identity(c))!=c for c in cookies):reject('BROWSER_COOKIE_ENGINE_VALUE_OR_PARTITION_MISMATCH')
 return restored
