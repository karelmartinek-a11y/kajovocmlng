"""Synthetic semantic evidence, values never appear in the report."""
import base64,copy,hashlib,importlib.metadata,json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from profile_reference import *
checks=[]
def positive(name,fn):
 try:
  result=fn()
  if result is False:raise AssertionError('POSITIVE_PREDICATE_FALSE')
  checks.append({'id':name,'passed':True})
 except Exception as e:checks.append({'id':name,'passed':False,'code':getattr(e,'code',None),'pointer':getattr(e,'pointer',None),'unexpectedException':type(e).__name__})
def negative(name,fn,code,pointer=None):
 try:fn();checks.append({'id':name,'passed':False,'actual':'ACCEPTED','expectedCode':code})
 except Rejected as e:checks.append({'id':name,'passed':e.code==code and(pointer is None or e.pointer==pointer),'actualCode':e.code,'expectedCode':code,'pointer':e.pointer})
 except Exception as e:checks.append({'id':name,'passed':False,'unexpectedException':type(e).__name__})
p=json.loads((D/'synthetic-fixture-proposals.json').read_text())
fixtures={}
for c in p['contracts']:
 for s in c['schema']['oneOf']:
  profile=s['properties']['variant']['const'];fixtures[profile]=next(copy.deepcopy(v['value'])for v in c['syntheticCases']if v['expected']=='SCHEMA_ACCEPT'and v['value']['variant']==profile)
floatv=lambda v:{'encoding':'IEEE754_BINARY64_BIG_ENDIAN_BASE64','base64':base64.b64encode(struct.pack('>d',v)).decode()}
key=serialization.load_pem_private_key(fixtures['PKCS8_PEM_PRIVATE_KEY_V1']['pem'].encode(),None)
der=base64.b64encode(key.private_bytes(serialization.Encoding.DER,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())).decode()
graph={'serializer':'ECMASCRIPT_AUTH_CLONE_GRAPH_V1','rootNodeId':'obj','nodes':[{'id':'obj','kind':'OBJECT','entries':[{'name':'self','valueNodeId':'obj'},{'name':'token','valueNodeId':'text'},{'name':'bytes','valueNodeId':'buf'}]},{'id':'text','kind':'STRING','value':' SYNTHETIC \u00e9\n'},{'id':'buf','kind':'ARRAY_BUFFER','base64':'AAEC/w=='}]}
full={'variant':'BROWSER_AUTH_STATE_GRAPH_V1','cookies':[{'name':'synthetic','value':' Exact +% \n','domain':'example.invalid','hostOnly':True,'path':'/','secure':True,'httpOnly':True,'sameSite':'None','expiry':{'kind':'ABSOLUTE','unixSeconds':floatv(1900000000.125)},'partition':{'kind':'TOP_LEVEL_SITE','topLevelSite':'https://top.example.invalid','hasCrossSiteAncestor':True}}],'origins':[{'origin':'https://example.invalid','localStorage':[{'name':'exact','value':' v\n'}],'indexedDB':[{'name':'auth','version':1,'objectStores':[{'name':'tokens','keyPath':None,'autoIncrement':False,'nextGeneratedKey':None,'indexes':[],'records':[{'key':{'kind':'STRING','value':'key'},'value':graph}]}]}]}],'pages':[{'pageKey':'login','origin':'https://example.invalid','sessionStorage':[{'name':'session','value':' exact '}]}],'permissions':[{'origin':'https://example.invalid','permission':'geolocation','state':'granted'}],'clientCertificateBindings':[{'kind':'OWNER_DEVICE_BRIDGE','origin':'https://example.invalid','bridgeBindingId':'b832b1c4-a1d7-4cc2-af57-c9a848cf733a','bridgeBindingRevision':'1'}],'virtualAuthenticators':[{'authenticatorKey':'automation','protocol':'ctap2','transport':'usb','hasResidentKey':True,'hasUserVerification':True,'automaticPresenceSimulation':True,'isUserVerified':True,'credentials':[{'kind':'VIRTUAL_AUTOMATION_ACCOUNT','credentialIdBase64':'AQID','rpId':'example.invalid','userHandleBase64':'AQ==','privateKeyPkcs8DerBase64':der,'signCount':0,'isResidentCredential':True,'backupEligible':False,'backupState':False}]}]}
fixtures[full['variant']]=full
now=datetime(2026,9,30,tzinfo=timezone.utc)
def consumer(profile):
 return {'consumerId':'SYNTHETIC_ADAPTER','consumerRevision':'1','purposeKind':'REFERENCE_TEST','profiles':[{'secretType':INVENTORY[profile]['secretType'],'profileId':profile,'schemaDigest':schema_digest(profile)}],'allowedOrigins':['https://example.invalid'],'cookieHosts':['example.invalid'],'tokenEndpoint':'https://oauth.example.invalid/token','database':'syntheticdb','keyAlgorithms':['RSA','EC','ED25519','ED448'],'browserMembers':['COOKIES','PARTITIONED_COOKIES','LOCAL_STORAGE','INDEXED_DB','SESSION_STORAGE','PERMISSIONS','CLIENT_CERTIFICATE_BINDINGS','VIRTUAL_WEBAUTHN'],'serializerIds':['ECMASCRIPT_AUTH_CLONE_GRAPH_V1','BROWSER_AUTH_STATE_GRAPH_V1','BROWSER_COOKIE_LOCAL_STORAGE_V1','HTTP_COOKIE_JAR_V1'],'engineBuild':'SYNTHETIC_REFERENCE_ONLY','keyAlgorithmPolicies':[{'algorithm':'RSA','minimumModulusBits':1024,'publicExponents':[65537]},{'algorithm':'EC','namedCurves':['secp256r1','secp384r1','secp521r1']},{'algorithm':'ED25519'},{'algorithm':'ED448'}],'totpPolicies':[{'algorithm':'SHA1','digits':6,'minimumSeedBytes':1,'minimumPeriodSeconds':1,'maximumPeriodSeconds':1000},{'algorithm':'SHA256','digits':8,'minimumSeedBytes':1,'minimumPeriodSeconds':1,'maximumPeriodSeconds':1000}],'oauthClientId':fixtures['OAUTH_CLIENT_SECRET_V1']['clientId'],'authorizedOAuthScopes':list(set(fixtures['OAUTH_CLIENT_SECRET_V1'].get('scopes',[])+fixtures['OAUTH_BEARER_TOKEN_SET_V1'].get('scopes',[])))}
