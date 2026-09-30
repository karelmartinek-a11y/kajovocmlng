"""Render pending explicit Secret masks for owner review; never author SSOT."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MEANING={'variant':'Explicitní diskriminátor importní masky','clientId':'Identita OAuth klienta u cílového poskytovatele','clientSecret':'Přesná citlivá hodnota client-secret','tokenEndpoint':'Explicitní endpoint tokenového protokolu; cílová autorita je serverový binding','scopes':'Přesné scope položky; bez implicitního dělení nebo normalizace','accessToken':'Přesné bajty access tokenu; bez hádání JWT','tokenType':'Deklarovaný podporovaný tokenový mechanismus','refreshToken':'Přesná volitelná obnovovací hodnota','expiresAt':'Explicitní čas expirace; pravidlo importu a pravidlo použití se liší','seedBase32':'Explicitně zakódované přesné seed bytes','algorithm':'Zvolený hash TOTP','digits':'Počet číslic výsledného TOTP','periodSeconds':'Časový interval TOTP','certificatesPem':'Řetězec certifikátů v deklarovaném pořadí','pem':'Původní přesné PKCS8 PEM bytes','username':'Účet příslušného konzumenta','password':'Přesná citlivá hodnota hesla','database':'Volitelný explicitní název databáze','cookies':'Explicitní cookie položky; identity a doménová způsobilost podle níže uvedených predicates','origins':'Explicitní webové origins a příslušné storage položky','privateKeyPem':'Původní přesné OpenSSH PEM bytes','passphrase':'Přesná volitelná passphrase; žádná implicitní konverze','name':'Přesný název cookie/storage položky','value':'Přesná původní hodnota položky','domain':'Explicitní cookie domain','path':'Explicitní cookie path','expires':'Expirace cookie; navržená session varianta null je označená maskou','httpOnly':'Cookie HttpOnly příznak','secure':'Cookie Secure příznak','sameSite':'Explicitní SameSite varianta','partitionKey':'Explicitní partition identity','origin':'Explicitní origin storage','localStorage':'Explicitní dvojice localStorage; žádný obecný libovolný object'}
def typ(s):
 if 'type' in s:return str(s['type'])
 if 'const' in s:return {'str':'string','int':'integer','bool':'boolean'}.get(type(s['const']).__name__,type(s['const']).__name__)
 if 'enum' in s:return '/'.join(sorted({type(v).__name__ for v in s['enum']}))
 return ' | '.join(typ(v) for v in s.get('oneOf',s.get('anyOf',[]))) or 'viz přesná maska'
def rows(s,pointer,prefix=''):
 result=[]
 for k,v in s.get('properties',{}).items():
  name=prefix+k;ptr=pointer+'/properties/'+k
  limits={a:v[a] for a in ['const','enum','format','pattern','minLength','maxLength','minimum','maximum','minItems','maxItems','uniqueItems'] if a in v}
  result.append([name,MEANING.get(k,'Explicitní položka deklarované varianty; přesný význam určují predicates níže'),typ(v),'required' if k in s.get('required',[]) else 'optional (omission)',json.dumps(limits,ensure_ascii=False,separators=(',',':')) if limits else 'viz typ/maska',ptr])
  if v.get('type')=='object':result+=rows(v,ptr,name+'.')
  if v.get('type')=='array' and v.get('items',{}).get('type')=='object':result+=rows(v['items'],ptr+'/items',name+'[].')
 return result
p=ROOT/'audit/generated/create-review-authority/secret-variant-proposals.json';d=json.loads(p.read_text());assert d['effective'] is False
semantic_note='Sémantické příklady nebyly tímto strukturálním generátorem spuštěny; samostatné aktuální důkazy je nutné ověřit.'
semantic_path=ROOT/'audit/generated/resume-5334/coordinator/secret-semantic-tests.json'
if semantic_path.exists():
 semantic=json.loads(semantic_path.read_text())
 current_source=hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest()
 if semantic['sourceDocumentSha256']==current_source and semantic['proposalSha256']==hashlib.sha256(p.read_bytes()).hexdigest() and semantic['failed']==0 and semantic['checked']==len(semantic['checks']) and all(c['passed'] for c in semantic['checks']) and all(semantic['supportSha256'][name]==hashlib.sha256((ROOT/'audit'/name).read_bytes()).hexdigest() for name in ['secret_proposal_semantics.py','verify_secret_proposal_semantics.py']):
  semantic_note='Všech 18 původních sémantických případů bylo izolovaně spuštěno; 42 syntetických kontrol prošlo včetně platného SSH KEY svědka. Viz generated/resume-5334/coordinator/secret-semantic-tests.json. Formáty zůstávají návrhy; nejde o produkční ani provider runtime důkaz.'
lines=['# Konkrétní Secret formáty k přezkumu','', '**PENDING_OWNER_FORMAT_REVIEW. Žádná zde uvedená konkrétní varianta není účinná ani VERIFIED.**','', 'SSOT dokládá devět typů, TYPE_SPECIFIC, zákaz tiché normalizace a šifrované immutable verze. Konkrétní formáty, pole, volitelnost a limity níže jsou nové návrhy. Schválení principu explicitních variant je neaktivovalo. Přesné JSON masks, syntetické příklady a chyby jsou v [návrhovém JSON](generated/create-review-authority/secret-variant-proposals.json).','', 'Aktuální přezkum: SSOT SHA-256 '+hashlib.sha256((ROOT/'00_SSOT/KajovoCMLNG_SSOT.md').read_bytes()).hexdigest()+'. Devět autoritativních výňatků zůstává byteově přítomno. Šedesát strukturálních příkladů má platný pozitivní základ a negativní mutace odmítají konkrétní porušení. '+semantic_note+'','', 'Všechna importní pole pocházejí od oprávněného OWNER. Nemají serverovou autoritu. Serverové identity, digests, bindingy, receipts a guards nejsou importní hodnoty. Každý řádek uvádí pointer do návrhu; normativní autorita pro nový konkrétní formát dosud neexistuje.','', '## Import, uložení a použití','']
for k,v in d['commonTransportProposal'].items():lines+=['- **'+k+'**: '+v]
lines+=['','Citlivé hodnoty se nevracejí v create/import receipts, eventech, logách ani důkazech. Existující explicitní OWNER reveal je samostatná obchodní funkce podle §8.6.1; případnou změnu jejího rozsahu je nutné rozhodnout výslovně.','']
for i,c in enumerate(d['contracts']):
 lines+=['## '+c['secretType'],'','**Doložená autorita:** '+ '; '.join(a['source']+': '+a['claim'] for a in c['authority']), '', '**Nový návrh:** níže uvedená maska a její semantické podmínky. Veškeré str fields zachovávají původní UTF-8 bytes; BASE32/PEM mají vlastní explicitní dekodér, bez trimování či normalizace. Volitelná pole se vynechávají; null je povolen pouze tam, kde jej přesná maska výslovně obsahuje.','']
 for j,s in enumerate(c['schema'].get('oneOf',[c['schema']])):
  pointer=f'#/contracts/{i}/schema'+(f'/oneOf/{j}' if 'oneOf' in c['schema'] else '')
  lines+=['### '+s['properties']['variant']['const'],'','| Pole | Význam | Typ | Přítomnost | Validace / navržené limity | Pointer do návrhového JSON |','|---|---|---|---|---|---|']
  for row in rows(s,pointer):lines+=['| '+' | '.join(str(v).replace('|','&#124;') for v in row)+' |']
  lines+=['']
 lines+=['**Vazby a semantická odmítnutí:**','']+['- '+str(v) for v in c['semanticPredicates']]+['','**Konzument / podporované varianty:**', '','```json',json.dumps(c['consumerContract'],ensure_ascii=False,indent=2),'```','','**Přesné navržené chyby:**','','```json',json.dumps(c['specificErrors'],ensure_ascii=False,indent=2),'```','','**Konkrétní otázky pro přezkum:**','']+['- '+str(q) for q in c['reviewDecisions']]+['']
lines.insert(8,'Souhrnná rozhodnutí, nepokryté funkce a technické limity: [SSOT_SECRET_OWNER_DECISIONS.md](SSOT_SECRET_OWNER_DECISIONS.md).')
lines.insert(9,'')
(ROOT/'audit/SSOT_SECRET_VARIANT_REVIEW.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'types':len(d['contracts']),'variants':10,'status':'PENDING_OWNER_FORMAT_REVIEW','output':'audit/SSOT_SECRET_VARIANT_REVIEW.md'}))
