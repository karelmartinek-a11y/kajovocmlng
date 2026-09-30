# Konkrétní Secret formáty k přezkumu

**PENDING_OWNER_FORMAT_REVIEW. Žádná zde uvedená konkrétní varianta není účinná ani VERIFIED.**

SSOT dokládá devět typů, TYPE_SPECIFIC, zákaz tiché normalizace a šifrované immutable verze. Konkrétní formáty, pole, volitelnost a limity níže jsou nové návrhy. Schválení principu explicitních variant je neaktivovalo. Přesné JSON masks, syntetické příklady a chyby jsou v [návrhovém JSON](generated/create-review-authority/secret-variant-proposals.json).

Aktuální přezkum: SSOT SHA-256 22256baa17729b7577ca4e2498b74b7dfc2b3e6bab57f3b88c338a059557a0ee. Devět autoritativních výňatků zůstává byteově přítomno. Šedesát strukturálních příkladů má platný pozitivní základ a negativní mutace odmítají konkrétní porušení. Všech 18 původních sémantických případů bylo izolovaně spuštěno; 42 syntetických kontrol prošlo včetně platného SSH KEY svědka. Viz generated/resume-5334/coordinator/secret-semantic-tests.json. Formáty zůstávají návrhy; nejde o produkční ani provider runtime důkaz.

Souhrnná rozhodnutí, nepokryté funkce a technické limity: [SSOT_SECRET_OWNER_DECISIONS.md](SSOT_SECRET_OWNER_DECISIONS.md).

Všechna importní pole pocházejí od oprávněného OWNER. Nemají serverovou autoritu. Serverové identity, digests, bindingy, receipts a guards nejsou importní hodnoty. Každý řádek uvádí pointer do návrhu; normativní autorita pro nový konkrétní formát dosud neexistuje.

## Import, uložení a použití

- **native**: Closed JSON object with explicit type + value.variant; no values/slots/canonicalJson, no sniffing format
- **import**: Decode outer HTTP JSON strictly; unknownfields/duplicates reject; explicit sourceformat discriminator only; existing UTF8wrapper masks require ownerapproved future replacement, never accept JSONhiddenintext by sniffing
- **persistence**: Store original exact value bytes encrypted; structured import can retain original input JSONbytes and separately typed validated view. Canonical digest computation never replaces persisted bytes. Versionimmutable; no plaintext response/event/log/audit echo. ServerID/version/ciphermetadata/digests are not importfields
- **load**: Decrypt internally, select pinnedschema+variant, validate stored variant/hydration; missingparser/incompatibleconsumer BLOCKED; never auto fallback
- **consumers**: Exact consumer contract declares supported variants. Explicit transformation creates new version through authorized operation rather than mutating storedbytes
- **errorDisclosure**: Specific stable code + fieldpointer only; no rejected secretvalue or parser exception text echo
- **existingPolicyConflict**: Original §8.6.1 permits OWNERreveal/copy/log/chat/commit/export; current prohibition targets create/import responses/events/log/audit evidence and syntheticexamples. Do not silently delete legitimate explicit OWNER reveal operation; coordinator must record exact new instruction scope/precedence.

Citlivé hodnoty se nevracejí v create/import receipts, eventech, logách ani důkazech. Existující explicitní OWNER reveal je samostatná obchodní funkce podle §8.6.1; případnou změnu jejího rozsahu je nutné rozhodnout výslovně.

## OAUTH_CLIENT

**Doložená autorita:** SSOT §8.2: Type exists; SSOT §72.21 secret.value: TYPE_SPECIFIC + NO_SILENT_NORMALIZATION required; SSOT §8.4 /25.6: Encrypted immutable version, server cipher/digest metadata

**Nový návrh:** níže uvedená maska a její semantické podmínky. Veškeré str fields zachovávají původní UTF-8 bytes; BASE32/PEM mají vlastní explicitní dekodér, bez trimování či normalizace. Volitelná pole se vynechávají; null je povolen pouze tam, kde jej přesná maska výslovně obsahuje.

### OAUTH_CLIENT_SECRET_V1

| Pole | Význam | Typ | Přítomnost | Validace / navržené limity | Pointer do návrhového JSON |
|---|---|---|---|---|---|
| variant | Explicitní diskriminátor importní masky | string | required | {"const":"OAUTH_CLIENT_SECRET_V1"} | #/contracts/0/schema/oneOf/0/properties/variant |
| clientId | Identita OAuth klienta u cílového poskytovatele | string | required | {"minLength":1,"maxLength":4096} | #/contracts/0/schema/oneOf/0/properties/clientId |
| clientSecret | Přesná citlivá hodnota client-secret | string | required | {"minLength":1,"maxLength":1048576} | #/contracts/0/schema/oneOf/0/properties/clientSecret |
| tokenEndpoint | Explicitní endpoint tokenového protokolu; cílová autorita je serverový binding | string | required | {"format":"uri","pattern":"^https://"} | #/contracts/0/schema/oneOf/0/properties/tokenEndpoint |
| scopes | Přesné scope položky; bez implicitního dělení nebo normalizace | array | optional (omission) | {"maxItems":4096,"uniqueItems":true} | #/contracts/0/schema/oneOf/0/properties/scopes |

**Vazby a semantická odmítnutí:**

- clientId/clientSecret exact nonempty UTF8; preserve whitespace
- tokenEndpoint absolute HTTPS with no userinfo or fragment; origin bound by server exact auth target
- scopes unique exact strings; do not split whitespace or infer grant type

**Konzument / podporované varianty:**

```json
"Exact OAuth adapter must declare OAUTH_CLIENT_SECRET_V1 and its supported grant contract; no fallback from another variant"
```

**Přesné navržené chyby:**

```json
[
  "OAUTH_CLIENT_FIELD_INVALID",
  "OAUTH_TOKEN_ENDPOINT_INVALID",
  "OAUTH_SCOPE_DUPLICATE",
  "SECRET_VARIANT_UNSUPPORTED"
]
```

**Konkrétní otázky pro přezkum:**

- Is token endpoint mandatory within Secret value or wholly external binding?
- Approve this client-secret variant; public-client and private_key_jwt are deliberately absent

## OAUTH_TOKEN_SET

**Doložená autorita:** SSOT §8.2: Type exists; SSOT §72.21 secret.value: TYPE_SPECIFIC + NO_SILENT_NORMALIZATION required; SSOT §8.4 /25.6: Encrypted immutable version, server cipher/digest metadata

**Nový návrh:** níže uvedená maska a její semantické podmínky. Veškeré str fields zachovávají původní UTF-8 bytes; BASE32/PEM mají vlastní explicitní dekodér, bez trimování či normalizace. Volitelná pole se vynechávají; null je povolen pouze tam, kde jej přesná maska výslovně obsahuje.

### OAUTH_BEARER_TOKEN_SET_V1

| Pole | Význam | Typ | Přítomnost | Validace / navržené limity | Pointer do návrhového JSON |
|---|---|---|---|---|---|
| variant | Explicitní diskriminátor importní masky | string | required | {"const":"OAUTH_BEARER_TOKEN_SET_V1"} | #/contracts/1/schema/oneOf/0/properties/variant |
| accessToken | Přesné bajty access tokenu; bez hádání JWT | string | required | {"minLength":1,"maxLength":1048576} | #/contracts/1/schema/oneOf/0/properties/accessToken |
| tokenType | Deklarovaný podporovaný tokenový mechanismus | string | required | {"const":"Bearer"} | #/contracts/1/schema/oneOf/0/properties/tokenType |
| refreshToken | Přesná volitelná obnovovací hodnota | string | optional (omission) | {"minLength":1,"maxLength":1048576} | #/contracts/1/schema/oneOf/0/properties/refreshToken |
| expiresAt | Explicitní čas expirace; pravidlo importu a pravidlo použití se liší | string | optional (omission) | {"format":"date-time"} | #/contracts/1/schema/oneOf/0/properties/expiresAt |
| scopes | Přesné scope položky; bez implicitního dělení nebo normalizace | array | optional (omission) | {"maxItems":4096,"uniqueItems":true} | #/contracts/1/schema/oneOf/0/properties/scopes |

**Vazby a semantická odmítnutí:**

- Tokens exact UTF8 bytes, no sniffing JWT/decode or recoding
- expiresAt explicit absolute time; expired imported value may be stored as candidate but not used without consumer expiry rule
- Refresh permitted only when exact adapter declares refresh procedure; secret create performs no provider call

**Konzument / podporované varianty:**

```json
"OAuth adapter consumes explicit token-set fields; renewal writes new immutable version via own rotation authority"
```

**Přesné navržené chyby:**

```json
[
  "OAUTH_TOKEN_TYPE_INVALID",
  "OAUTH_TOKEN_FIELD_EMPTY",
  "OAUTH_TOKEN_EXPIRY_INVALID",
  "SECRET_VARIANT_UNSUPPORTED",
  "OAUTH_SCOPE_DUPLICATE"
]
```

**Konkrétní otázky pro přezkum:**

- Approve Bearer-only initial variant; MAC/DPoP not implied
- Approve candidate-import expiry handling separately from runtime-use rejection

## TOTP_SEED

**Doložená autorita:** SSOT §8.2: Type exists; SSOT §72.21 secret.value: TYPE_SPECIFIC + NO_SILENT_NORMALIZATION required; SSOT §8.4 /25.6: Encrypted immutable version, server cipher/digest metadata

**Nový návrh:** níže uvedená maska a její semantické podmínky. Veškeré str fields zachovávají původní UTF-8 bytes; BASE32/PEM mají vlastní explicitní dekodér, bez trimování či normalizace. Volitelná pole se vynechávají; null je povolen pouze tam, kde jej přesná maska výslovně obsahuje.

### TOTP_BASE32_V1

| Pole | Význam | Typ | Přítomnost | Validace / navržené limity | Pointer do návrhového JSON |
|---|---|---|---|---|---|
| variant | Explicitní diskriminátor importní masky | string | required | {"const":"TOTP_BASE32_V1"} | #/contracts/2/schema/oneOf/0/properties/variant |
| seedBase32 | Explicitně zakódované přesné seed bytes | string | required | {"pattern":"^[A-Z2-7]+$","minLength":16,"maxLength":1024} | #/contracts/2/schema/oneOf/0/properties/seedBase32 |
| algorithm | Zvolený hash TOTP | str | required | {"enum":["SHA1","SHA256","SHA512"]} | #/contracts/2/schema/oneOf/0/properties/algorithm |
| digits | Počet číslic výsledného TOTP | int | required | {"enum":[6,8]} | #/contracts/2/schema/oneOf/0/properties/digits |
| periodSeconds | Časový interval TOTP | integer | required | {"minimum":1,"maximum":300} | #/contracts/2/schema/oneOf/0/properties/periodSeconds |

**Vazby a semantická odmítnutí:**

- Strict unpadded uppercase RFC4648 Base32; decode/reencode equality including trailing padbits; no whitespace/case normalization
- Decoded seed length >=10 bytes (proposed security minimum)
- Generator uses current selected immutable version, declared algorithm/digits/period and server boundedclockskew

**Konzument / podporované varianty:**

```json
"TOTP generator/QR exporter explicitly declare TOTP_BASE32_V1; QR serialization is separate typed output not implicit input detection"
```

**Přesné navržené chyby:**

```json
[
  "TOTP_BASE32_INVALID",
  "TOTP_SEED_LENGTH_INVALID",
  "TOTP_ALGORITHM_UNSUPPORTED",
  "TOTP_PARAMETERS_INVALID"
]
```

**Konkrétní otázky pro přezkum:**

- Approve Base32-only import instead of hex/otpauth URI
- Approve seed min10bytes, algorithm list, digits and period bound (not existing SSOT constants)

## CERTIFICATE

**Doložená autorita:** SSOT §8.2: Type exists; SSOT §72.21 secret.value: TYPE_SPECIFIC + NO_SILENT_NORMALIZATION required; SSOT §8.4 /25.6: Encrypted immutable version, server cipher/digest metadata

**Nový návrh:** níže uvedená maska a její semantické podmínky. Veškeré str fields zachovávají původní UTF-8 bytes; BASE32/PEM mají vlastní explicitní dekodér, bez trimování či normalizace. Volitelná pole se vynechávají; null je povolen pouze tam, kde jej přesná maska výslovně obsahuje.

### X509_PEM_CHAIN_V1

| Pole | Význam | Typ | Přítomnost | Validace / navržené limity | Pointer do návrhového JSON |
|---|---|---|---|---|---|
| variant | Explicitní diskriminátor importní masky | string | required | {"const":"X509_PEM_CHAIN_V1"} | #/contracts/3/schema/oneOf/0/properties/variant |
| certificatesPem | Řetězec certifikátů v deklarovaném pořadí | array | required | {"minItems":1,"maxItems":32,"uniqueItems":true} | #/contracts/3/schema/oneOf/0/properties/certificatesPem |

**Vazby a semantická odmítnutí:**

- Each item contains exactly one PEM CERTIFICATE block with valid DER X.509; reject extra key/unknown blocks/trailing nonwhitespace
- Leaf-first chain: adjacent subject/issuer and signatures valid; duplicates rejected by DER fingerprint, not PEM spelling
- No implicit trust installation or claim of valid target hostname/time/CA; exact consumer validates trust/usage at use

**Konzument / podporované varianty:**

```json
"TLS/certificate adapter declares X509_PEM_CHAIN_V1 and explicit chain/trust/hostname constraints; server metadata not derived from caller assertions"
```

**Přesné navržené chyby:**

```json
[
  "CERTIFICATE_PEM_INVALID",
  "CERTIFICATE_CHAIN_INVALID",
  "CERTIFICATE_DUPLICATE",
  "SECRET_VARIANT_UNSUPPORTED"
]
```

**Konkrétní otázky pro přezkum:**

- Approve PEM-chain vs DER singlecert variants
- Approve bounded32chain and leaf-first order; imported selfsigned allowed as candidate but not auto trusted

## PRIVATE_KEY

**Doložená autorita:** SSOT §8.2: Type exists; SSOT §72.21 secret.value: TYPE_SPECIFIC + NO_SILENT_NORMALIZATION required; SSOT §8.4 /25.6: Encrypted immutable version, server cipher/digest metadata

**Nový návrh:** níže uvedená maska a její semantické podmínky. Veškeré str fields zachovávají původní UTF-8 bytes; BASE32/PEM mají vlastní explicitní dekodér, bez trimování či normalizace. Volitelná pole se vynechávají; null je povolen pouze tam, kde jej přesná maska výslovně obsahuje.

### PKCS8_PEM_PRIVATE_KEY_V1

| Pole | Význam | Typ | Přítomnost | Validace / navržené limity | Pointer do návrhového JSON |
|---|---|---|---|---|---|
| variant | Explicitní diskriminátor importní masky | string | required | {"const":"PKCS8_PEM_PRIVATE_KEY_V1"} | #/contracts/4/schema/oneOf/0/properties/variant |
| pem | Původní přesné PKCS8 PEM bytes | string | required | {"minLength":1,"maxLength":1048576} | #/contracts/4/schema/oneOf/0/properties/pem |

**Vazby a semantická odmítnutí:**

- Exactly one unencrypted PRIVATE KEY PEM PKCS8 block; complete cryptographic parse, no extra block
- Algorithm allowed only by exact consumer key contract; parser support alone does not authorize algorithm
- No implicit password decryption, certificate matching or key conversion; preserve original PEM UTF8 bytes

**Konzument / podporované varianty:**

```json
"Consumer declares PKCS8_PEM_PRIVATE_KEY_V1 plus compatible algorithm/size policy; hardware nonexportable keys use separate bridge authority"
```

**Přesné navržené chyby:**

```json
[
  "PRIVATE_KEY_PEM_INVALID",
  "PRIVATE_KEY_ENCRYPTION_UNSUPPORTED",
  "PRIVATE_KEY_ALGORITHM_UNSUPPORTED"
]
```

**Konkrétní otázky pro přezkum:**

- Approve unencrypted PKCS8 vs encryptedPKCS8/OpenSSH/PKCS1 import variants
- Approve keeping algorithm policy in exact consumer rather than global RSA-only rule

## DATABASE_CREDENTIAL

**Doložená autorita:** SSOT §8.2: Type exists; SSOT §72.21 secret.value: TYPE_SPECIFIC + NO_SILENT_NORMALIZATION required; SSOT §8.4 /25.6: Encrypted immutable version, server cipher/digest metadata

**Nový návrh:** níže uvedená maska a její semantické podmínky. Veškeré str fields zachovávají původní UTF-8 bytes; BASE32/PEM mají vlastní explicitní dekodér, bez trimování či normalizace. Volitelná pole se vynechávají; null je povolen pouze tam, kde jej přesná maska výslovně obsahuje.

### DATABASE_USER_PASSWORD_V1

| Pole | Význam | Typ | Přítomnost | Validace / navržené limity | Pointer do návrhového JSON |
|---|---|---|---|---|---|
| variant | Explicitní diskriminátor importní masky | string | required | {"const":"DATABASE_USER_PASSWORD_V1"} | #/contracts/5/schema/oneOf/0/properties/variant |
| username | Účet příslušného konzumenta | string | required | {"minLength":1,"maxLength":4096} | #/contracts/5/schema/oneOf/0/properties/username |
| password | Přesná citlivá hodnota hesla | string | required | {"minLength":1,"maxLength":1048576} | #/contracts/5/schema/oneOf/0/properties/password |
| database | Volitelný explicitní název databáze | string | optional (omission) | {"minLength":1,"maxLength":4096} | #/contracts/5/schema/oneOf/0/properties/database |

**Vazby a semantická odmítnutí:**

- Exact username/password UTF8 bytes without normalization
- Endpoint/vendor/TLS/network guard remains in exact target binding; no credentials embedded in URI
- Consumer rejects absent database if its explicit connection contract requires it; import itself performs no login

**Konzument / podporované varianty:**

```json
"Exact DB connector declares DATABASE_USER_PASSWORD_V1, binds host/port/database and TLS separately; alternative service-account/token/DSN formats need separate variants"
```

**Přesné navržené chyby:**

```json
[
  "DATABASE_CREDENTIAL_FIELD_INVALID",
  "DATABASE_CREDENTIAL_TARGET_MISMATCH",
  "SECRET_VARIANT_UNSUPPORTED"
]
```

**Konkrétní otázky pro přezkum:**

- Approve minimaluser/password and optional database value shape
- Approve target endpoint remains bindingmetadata instead of secretvalue

## COOKIE_JAR

**Doložená autorita:** SSOT §8.2: Type exists; SSOT §72.21 secret.value: TYPE_SPECIFIC + NO_SILENT_NORMALIZATION required; SSOT §8.4 /25.6: Encrypted immutable version, server cipher/digest metadata; SSOT §13.15: Exact serializer and cookie/origin state semantics plus verifiedaccount condition; concrete proposedvariant is restricted member subset

**Nový návrh:** níže uvedená maska a její semantické podmínky. Veškeré str fields zachovávají původní UTF-8 bytes; BASE32/PEM mají vlastní explicitní dekodér, bez trimování či normalizace. Volitelná pole se vynechávají; null je povolen pouze tam, kde jej přesná maska výslovně obsahuje.

### HTTP_COOKIE_JAR_V1

| Pole | Význam | Typ | Přítomnost | Validace / navržené limity | Pointer do návrhového JSON |
|---|---|---|---|---|---|
| variant | Explicitní diskriminátor importní masky | string | required | {"const":"HTTP_COOKIE_JAR_V1"} | #/contracts/6/schema/oneOf/0/properties/variant |
| cookies | Explicitní cookie položky; identity a doménová způsobilost podle níže uvedených predicates | array | required | {"maxItems":4096,"uniqueItems":true} | #/contracts/6/schema/oneOf/0/properties/cookies |
| cookies[].name | Přesný název cookie/storage položky | string | required | {"minLength":1,"maxLength":4096} | #/contracts/6/schema/oneOf/0/properties/cookies/items/properties/name |
| cookies[].value | Přesná původní hodnota položky | string | required | {"maxLength":1048576} | #/contracts/6/schema/oneOf/0/properties/cookies/items/properties/value |
| cookies[].domain | Explicitní cookie domain | string | required | {"minLength":1,"maxLength":4096} | #/contracts/6/schema/oneOf/0/properties/cookies/items/properties/domain |
| cookies[].path | Explicitní cookie path | string | required | {"pattern":"^/"} | #/contracts/6/schema/oneOf/0/properties/cookies/items/properties/path |
| cookies[].secure | Cookie Secure příznak | boolean | required | viz typ/maska | #/contracts/6/schema/oneOf/0/properties/cookies/items/properties/secure |
| cookies[].httpOnly | Cookie HttpOnly příznak | boolean | required | viz typ/maska | #/contracts/6/schema/oneOf/0/properties/cookies/items/properties/httpOnly |
| cookies[].sameSite | Explicitní SameSite varianta | str | required | {"enum":["Strict","Lax","None"]} | #/contracts/6/schema/oneOf/0/properties/cookies/items/properties/sameSite |
| cookies[].expires | Expirace cookie; navržená session varianta null je označená maskou | null &#124; integer | required | viz typ/maska | #/contracts/6/schema/oneOf/0/properties/cookies/items/properties/expires |

**Vazby a semantická odmítnutí:**

- Cookie key(name,domain,path) unique; reject exactdom duplicate even if value differs
- Domain syntax valid and actual allowedtarget scope separately verified; path absolute
- SameSite None requires secure=true; session expires=null, otherwise Unixsecondsinteger
- Cookie value exact; no URLdecode/trim, no opaque extra partition metadata fallback

**Konzument / podporované varianty:**

```json
"Browser serializer must declare HTTP_COOKIE_JAR_V1 and unpartitioned-cookie support; partitionedcookies rejected pending explicit additional variant"
```

**Přesné navržené chyby:**

```json
[
  "COOKIE_DUPLICATE",
  "COOKIE_DOMAIN_INVALID",
  "COOKIE_SAMESITE_SECURE_REQUIRED",
  "COOKIE_SCOPE_MISMATCH",
  "SECRET_VARIANT_UNSUPPORTED"
]
```

**Konkrétní otázky pro přezkum:**

- Approve unpartitioned cookie variant; partitioned/browserengine additions require declared variant
- Approve sessionexpiry null and epochsecond expiration schema

## SESSION_STATE

**Doložená autorita:** SSOT §8.2: Type exists; SSOT §72.21 secret.value: TYPE_SPECIFIC + NO_SILENT_NORMALIZATION required; SSOT §8.4 /25.6: Encrypted immutable version, server cipher/digest metadata; SSOT §13.15: Exact serializer and cookie/origin state semantics plus verifiedaccount condition; concrete proposedvariant is restricted member subset

**Nový návrh:** níže uvedená maska a její semantické podmínky. Veškeré str fields zachovávají původní UTF-8 bytes; BASE32/PEM mají vlastní explicitní dekodér, bez trimování či normalizace. Volitelná pole se vynechávají; null je povolen pouze tam, kde jej přesná maska výslovně obsahuje.

### BROWSER_COOKIE_LOCAL_STORAGE_V1

| Pole | Význam | Typ | Přítomnost | Validace / navržené limity | Pointer do návrhového JSON |
|---|---|---|---|---|---|
| variant | Explicitní diskriminátor importní masky | string | required | {"const":"BROWSER_COOKIE_LOCAL_STORAGE_V1"} | #/contracts/7/schema/oneOf/0/properties/variant |
| cookies | Explicitní cookie položky; identity a doménová způsobilost podle níže uvedených predicates | array | required | {"maxItems":4096,"uniqueItems":true} | #/contracts/7/schema/oneOf/0/properties/cookies |
| cookies[].name | Přesný název cookie/storage položky | string | required | {"minLength":1,"maxLength":4096} | #/contracts/7/schema/oneOf/0/properties/cookies/items/properties/name |
| cookies[].value | Přesná původní hodnota položky | string | required | {"maxLength":1048576} | #/contracts/7/schema/oneOf/0/properties/cookies/items/properties/value |
| cookies[].domain | Explicitní cookie domain | string | required | {"minLength":1,"maxLength":4096} | #/contracts/7/schema/oneOf/0/properties/cookies/items/properties/domain |
| cookies[].path | Explicitní cookie path | string | required | {"pattern":"^/"} | #/contracts/7/schema/oneOf/0/properties/cookies/items/properties/path |
| cookies[].secure | Cookie Secure příznak | boolean | required | viz typ/maska | #/contracts/7/schema/oneOf/0/properties/cookies/items/properties/secure |
| cookies[].httpOnly | Cookie HttpOnly příznak | boolean | required | viz typ/maska | #/contracts/7/schema/oneOf/0/properties/cookies/items/properties/httpOnly |
| cookies[].sameSite | Explicitní SameSite varianta | str | required | {"enum":["Strict","Lax","None"]} | #/contracts/7/schema/oneOf/0/properties/cookies/items/properties/sameSite |
| cookies[].expires | Expirace cookie; navržená session varianta null je označená maskou | null &#124; integer | required | viz typ/maska | #/contracts/7/schema/oneOf/0/properties/cookies/items/properties/expires |
| origins | Explicitní webové origins a příslušné storage položky | array | required | {"maxItems":4096,"uniqueItems":true} | #/contracts/7/schema/oneOf/0/properties/origins |
| origins[].origin | Explicitní origin storage | string | required | {"format":"uri","pattern":"^https?://"} | #/contracts/7/schema/oneOf/0/properties/origins/items/properties/origin |
| origins[].localStorage | Explicitní dvojice localStorage; žádný obecný libovolný object | array | required | {"maxItems":4096,"uniqueItems":true} | #/contracts/7/schema/oneOf/0/properties/origins/items/properties/localStorage |
| origins[].localStorage[].name | Přesný název cookie/storage položky | string | required | {"minLength":1,"maxLength":4096} | #/contracts/7/schema/oneOf/0/properties/origins/items/properties/localStorage/items/properties/name |
| origins[].localStorage[].value | Přesná původní hodnota položky | string | required | {"maxLength":1048576} | #/contracts/7/schema/oneOf/0/properties/origins/items/properties/localStorage/items/properties/value |

**Vazby a semantická odmítnutí:**

- All cookie predicates above apply
- Origin exact scheme+host+port; no path/query/fragment/userinfo; duplicate origin rejects
- localStorage name unique perorigin even differentvalue; exact strings no normalization
- Imported state is untrusted data, not server BrowserStateBundle receipt; server verifies enginecapability, expectedaccount/tenant, auth/credentialepoch, contentdigest before candidate capture/activation
- No sessionStorage/IndexedDB/permissions/WebAuthn/privatekey/rawprofile implicit capture in this restricted variant

**Konzument / podporované varianty:**

```json
"Browser serializer declares BROWSER_COOKIE_LOCAL_STORAGE_V1 and exact supported state kinds; restores freshcontext before navigation then proves authenticated account condition (§13.15); failure does not create partialauthenticated success"
```

**Přesné navržené chyby:**

```json
[
  "BROWSER_STATE_ORIGIN_INVALID",
  "BROWSER_STATE_DUPLICATE_ORIGIN",
  "BROWSER_STATE_DUPLICATE_STORAGE_KEY",
  "BROWSER_STATE_MEMBER_UNSUPPORTED",
  "BROWSER_STATE_AUTH_POSTCONDITION_FAILED"
]
```

**Konkrétní otázky pro přezkum:**

- Approve restricted cookies/localStorage initial variant; otherallowedSSOTmembers require future declared variants
- Approve importonlydata separate from server-created bundle metadata/immutablelineage

## SSH_CREDENTIAL

**Doložená autorita:** SSOT §8.2: Type exists; SSOT §72.21 secret.value: TYPE_SPECIFIC + NO_SILENT_NORMALIZATION required; SSOT §8.4 /25.6: Encrypted immutable version, server cipher/digest metadata

**Nový návrh:** níže uvedená maska a její semantické podmínky. Veškeré str fields zachovávají původní UTF-8 bytes; BASE32/PEM mají vlastní explicitní dekodér, bez trimování či normalizace. Volitelná pole se vynechávají; null je povolen pouze tam, kde jej přesná maska výslovně obsahuje.

### SSH_PASSWORD_V1

| Pole | Význam | Typ | Přítomnost | Validace / navržené limity | Pointer do návrhového JSON |
|---|---|---|---|---|---|
| variant | Explicitní diskriminátor importní masky | string | required | {"const":"SSH_PASSWORD_V1"} | #/contracts/8/schema/oneOf/0/properties/variant |
| username | Účet příslušného konzumenta | string | required | {"minLength":1,"maxLength":4096} | #/contracts/8/schema/oneOf/0/properties/username |
| password | Přesná citlivá hodnota hesla | string | required | {"minLength":1,"maxLength":1048576} | #/contracts/8/schema/oneOf/0/properties/password |

### SSH_OPENSSH_PRIVATE_KEY_V1

| Pole | Význam | Typ | Přítomnost | Validace / navržené limity | Pointer do návrhového JSON |
|---|---|---|---|---|---|
| variant | Explicitní diskriminátor importní masky | string | required | {"const":"SSH_OPENSSH_PRIVATE_KEY_V1"} | #/contracts/8/schema/oneOf/1/properties/variant |
| username | Účet příslušného konzumenta | string | required | {"minLength":1,"maxLength":4096} | #/contracts/8/schema/oneOf/1/properties/username |
| privateKeyPem | Původní přesné OpenSSH PEM bytes | string | required | {"minLength":1,"maxLength":1048576} | #/contracts/8/schema/oneOf/1/properties/privateKeyPem |
| passphrase | Přesná volitelná passphrase; žádná implicitní konverze | string | optional (omission) | {"minLength":1,"maxLength":1048576} | #/contracts/8/schema/oneOf/1/properties/passphrase |

**Vazby a semantická odmítnutí:**

- PASSWORD variant exactnonempty UTF8 username/password
- KEY variant exactlyone OPENSSH PRIVATE KEY PEM block complete parse; encryptedkey requires explicit passphrase, unencryptedkey forbids passphrase (semanticcondition)
- No conversion to PKCS8 or silentalgorithmfallback; supportedalgorithm bound by SSH adapter
- Endpoint/host-key fingerprint trusted binding separate; import cannot assert trust or disablehost-key verification

**Konzument / podporované varianty:**

```json
"SSH adapter declares exact variant; pins server-authorized target/host-key verification policy before authentication"
```

**Přesné navržené chyby:**

```json
[
  "SSH_KEY_INVALID",
  "SSH_KEY_PASSPHRASE_REQUIRED",
  "SSH_KEY_PASSPHRASE_UNEXPECTED",
  "SSH_HOST_KEY_MISMATCH",
  "SECRET_VARIANT_UNSUPPORTED"
]
```

**Konkrétní otázky pro přezkum:**

- Approve password and OpenSSHkey variants; PKCS8agent/hardwareauth absent
- Approve encrypted-key passphrase as distinct sensitive field; no autodetectfallback

