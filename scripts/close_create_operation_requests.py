"""Author exact create requests without modifying their still-open response/events."""
import argparse,hashlib,json,re
from ssot_sources import ROOT,SSOT,resources,resource_index
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
from create_operation_contracts import PATH,PAYLOAD,schema,specialize

GEN_TEXT='''### 12.47 Create request admission

`generation.job.create` přijímá přes `POST /generation/jobs` přesnou masku
`urn:kcml:create-operation-design:1#/$defs/GenerationJobCreateBody`.
`intent` je povinný nenullový neprázdný OWNER záměr (§12.2, §72.11); jeho
původní UTF-8 text se nemění. Volitelné `kind` používá enum §12.3 a při
vynechání znamená `CREATE`. `targetKind` je technické pojmenování výrobců
§12.1, nikoli jiný produktový rozsah. UPDATE vyžaduje exact existující
`targetObjectId` a `targetKind`; server resolveuje jejich typ a aktuální
revision. `parentJobId` odkazuje na parent/source job podle §25.11; server
ověřuje vztah k původnímu jobu. CREATE může mířit na registered placeholder
bez předchozí release podle §49.18, nejde o klientské vytvoření identity. `requestedModel` je OWNER výběr OpenAI modelu,
ne capability snapshot vytvořený klientem.

`sources` jsou explicitní TEXT, FILE, IMAGE, URL, API_DOC, CREDENTIAL_REF
nebo OBJECT_REF podle §12.2 a §25.11. FILE/IMAGE/API_DOC obsahují pouze
`artifactId`: server načte persistovaný artefakt, ověří jeho identitu, skutečné
bytes/content digest a media type a teprve potom provede hydration/parser.
Klient nenahrává `ArtifactRef` jako trusted receipt. Volitelné `credential`
je přesná hodnota dedikovaného OWNER pole gen.credential (§72.11/§8.6);
server vyžaduje bounded ephemeral policy a serverový Secret-use context
svázaný s novým jobem před použitím. Absence ověřené policy je BLOCKED.
CREDENTIAL_REF obsahuje
stable name a vyžaduje serverový Secret-use context; přímý credential v OWNER
textu zůstává dovolen podle §8.6.1. URI zdroje podléhají server navigation
policy; reference objektů serverově resolveují actual owner/identity/revision.
Initial request a všechny vstupy se persistují před následným modelovým
zpracováním. Nový root vzniká ve stavu DISCUSSING podle §49.15; tento stav,
OWNER context, ID, authority, digest, phase a timestamps nesmí dodat klient.

Obě create operace používají UTF-8 JSON body, `Content-Type: application/json`
a povinný `Idempotency-Key` (§25.16). Nemají path parametry ani query.
Duplikované JSON klíče na jakékoliv hloubce, nevalidní UTF-8/JSON, nonfinite
numbers, neznámé query, neznámá pole a duplicitní doménové reference se
odmítají před admission. HTTP proxy/authentication headers zůstávají
transportními vstupy kanonické authentication service; nejsou business pole
ani způsob, jak klient deklaruje trusted authority. Create root nemá starou
CAS verzi; If-Match nebo klientské identity nového rootu nejsou create guard.
R9 guards zachovávají idempotency key, deadline a volitelný client digest hint;
root snapshot guards jsou null. Client digest se nikdy nepřevezme bez
serverového přepočtu. Native body je přesně dekódovaný domain body, žádný
schemaId/slot/values/canonicalJson adapter.

Idempotency scope je exact OWNER + operation + key; serverový request digest
váže canonical operationId a domain body. Tentýž key/digest replayuje původní
receipt či failure, jiný digest je konflikt. UNKNOWN outcome vyžaduje lookup
nebo reconciliation původní operace; nesmí vytvořit další root ani být
prohlášen za známý failure. Persistence/admission/queue/outbox mají hranice
§49 a §51. Request schema samo nedokazuje executable SQL nebo runtime closure.

'''
SECRET_TEXT='''### 8.11 Secret create request admission

`secret.create` přes `POST /secrets` používá přesnou masku
`urn:kcml:create-operation-design:1#/$defs/SecretCreateBody`. Povinné nenullové
vstupy jsou `stableName`, `displayName`, `type` a `value` podle §72.21.
Enum `type` je přesně §8.2. Stable name je unique včetně soft-deleted položek,
neprovádí se implicitní změna case, trim ani recyklace (§25.6). Volitelné
metadata `description`, `purposeKind`, `targetObjectId`, `tags`, `group`,
`url`, `username`, `notes`, `expiration` pocházejí z §8.3 a §72.21. Omission
není null; nullable hodnoty tato create maska nepoužívá. Rotation policy a
exact bindings nejsou novými volnými create JSON bags: spravují se přes
kanonické metadata/rotation/binding operace; vytvoření secretu samo nedává
consumerovi binding ani runtime authority.

`value` je konkrétní přenos plaintext bytes nové verze: pro GENERIC_BINARY
má `encoding=BASE64` a `base64`; pro ostatní typy má `encoding=UTF8` a `text`.
BASE64 se strict dekóduje a musí znovu vytvořit stejné canonical BASE64.
UTF-8 text se převádí na bytes beze změny case, whitespace nebo Unicode
normalizace; není to JSON schovaný ve stringu místo domain metadata. Obsah
secretu je skutečná důvěrná hodnota, kterou lze podle §8.6.1 dále přímo
používat. Případný JSON obsah hodnoty se nesmí automaticky přepsat na jinou
hodnotu. Type-specific content validation vyžaduje current explicitní
serverovou policy daného typu (§72.21); missing/unverified policy znamená
BLOCKED před persistencí, nikoli automatické přijetí libovolného certifikátu,
OAuth token setu nebo browser session state.

Server odvozuje secret ID/version number, authenticated encryption metadata,
fingerprint/value digest, timestamps, state version, activation epoch a audit.
Klient je nepředává. Atomická tvorba recordu a první immutable verze musí
respektovat §25.6; tento request neprohlašuje první verzi automaticky ACTIVE.
Aktivace a invalidace mají vlastní kontrakt §49.22.1/§51.14. Reserved
KCML_OWNER_API_KEY a deployment PASS nepřebírají obecné create jako náhradu
své singleton/deployment authority. OPENAI_API_KEY a ostatní business secrets
zůstávají v kanonickém Password Manageru. Reveal/copy/log/chat/commit/export
pravidla §8.6.1 se touto maskou neomezují.

Transport, duplicate JSON handling, server digest a idempotency/reconciliation
jsou shodné s §12.47. Response, typed error applicability, event envelope,
actual DB helpers a plná persist/hydration/consumer předávka vyžadují samostatné
důkazy; request closure není potvrzením celé secret operace.

'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    text=SSOT.read_text(encoding='utf8');items=list(resources(text));rs=resource_index(items)
    design=(json.dumps(schema(),ensure_ascii=False,indent=2)+'\n').encode()
    payload=encoded(specialize(json.loads(rs[PAYLOAD]['raw'])),rs[PAYLOAD]['raw'])
    manifest=json.loads(rs['manifest.json']['raw'])
    for name,raw in [(PATH,design),(PAYLOAD,payload)]:
        entry=manifest['resources'].setdefault(name,{'kind':'JSON'})
        entry.update(sizeBytes=len(raw),sha256='sha256:'+hashlib.sha256(raw).hexdigest())
    ui_path='closure/contracts/ui-action-resolution.json'
    ui=json.loads(rs[ui_path]['raw'])
    for binding in ui['bindings']:
        if binding.get('canonicalOperationId')=='generation.job.create':
            binding['argumentProfile']['requestContractRef']='urn:kcml:create-operation-design:1#/$defs/GenerationJobCreateBody'
            binding['argumentProfile']['fieldMappings']={'intent':'gen.intent OWNER text','sources':'gen.url -> URL source when present','credential':'gen.credential exact OWNER value when present'}
            if binding['actionId']=='component.generate':
                binding['argumentProfile']['targetContextMapping']='selected component -> server-resolved targetObjectId/targetKind; sourceContext is presentation context, not a native body field'
        if binding.get('canonicalOperationId')=='secret.create':
            binding['argumentProfile']['requestContractRef']='urn:kcml:create-operation-design:1#/$defs/SecretCreateBody'
            binding['argumentProfile']['fieldMappings']={k:'secret.'+k for k in ['stableName','displayName','type','description','url','username','notes','expiration']}
            binding['argumentProfile']['fieldMappings']['value']='secret.value -> exact UTF8 bytes or BASE64 binary bytes according to type; no normalization'
    ui_raw=(json.dumps(ui,ensure_ascii=False,indent=2)+'\n').encode()
    updates={PATH:design,PAYLOAD:payload,ui_path:ui_raw,'manifest.json':encoded(manifest,rs['manifest.json']['raw'])}
    pending=[k for k,v in updates.items() if k not in rs or rs[k]['raw']!=v]
    if args.check:
        print(json.dumps({'status':'BLOCKED' if pending else 'PASS','pending':pending}));return int(bool(pending))
    text=rewrite(text,items,updates)
    if '### 8.11 Secret create request admission' not in text:text=text.replace('## 9. Externí systémy, API a webhooks',SECRET_TEXT+'## 9. Externí systémy, API a webhooks',1)
    if '### 12.47 Create request admission' not in text:
        match=re.search(r'^## 13\.',text,re.M)
        if not match:raise ValueError('GENERATION_SECTION_END_NOT_FOUND')
        text=text[:match.start()]+GEN_TEXT+text[match.start():]
    SSOT.write_text(text,encoding='utf8',newline='\n')
    (ROOT/'01_UI_CONTRACT'/ui_path).write_bytes(ui_raw)
    print(json.dumps({'requestOperations':list(specialize.__globals__['OPERATIONS']),'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest()}))
    return 0
if __name__=='__main__':raise SystemExit(main())
