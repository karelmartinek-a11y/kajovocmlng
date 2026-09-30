# Návrhy konkrétních Secret variant

**PENDING_OWNER_FORMAT_REVIEW — nejde o účinný SSOT kontrakt ani VERIFIED.**

Schválen je princip explicitních variant. Následující formáty, pole a rozsahy vyžadují samostatný přezkum. SSOT výslovně stanoví typy (§8.2), TYPE_SPECIFIC + NO_SILENT_NORMALIZATION (§72.21), šifrované immutable verze (§8.4/25.6); konkrétní zde uvedené formáty dosud nestanoví.

| Typ | Navržené explicitní varianty | Stav |
|---|---|---|
| OAUTH_CLIENT | OAUTH_CLIENT_SECRET_V1 | PENDING_OWNER_FORMAT_REVIEW |
| OAUTH_TOKEN_SET | OAUTH_BEARER_TOKEN_SET_V1 | PENDING_OWNER_FORMAT_REVIEW |
| TOTP_SEED | TOTP_BASE32_V1 | PENDING_OWNER_FORMAT_REVIEW |
| CERTIFICATE | X509_PEM_CHAIN_V1 | PENDING_OWNER_FORMAT_REVIEW |
| PRIVATE_KEY | PKCS8_PEM_PRIVATE_KEY_V1 | PENDING_OWNER_FORMAT_REVIEW |
| DATABASE_CREDENTIAL | DATABASE_USER_PASSWORD_V1 | PENDING_OWNER_FORMAT_REVIEW |
| COOKIE_JAR | HTTP_COOKIE_JAR_V1 | PENDING_OWNER_FORMAT_REVIEW |
| SESSION_STATE | BROWSER_COOKIE_LOCAL_STORAGE_V1 | PENDING_OWNER_FORMAT_REVIEW |
| SSH_CREDENTIAL | SSH_PASSWORD_V1, SSH_OPENSSH_PRIVATE_KEY_V1 | PENDING_OWNER_FORMAT_REVIEW |

Přiloženo 60 syntetických kontrol kandidátních JSON schemas; všechny splnily očekávané přijetí/odmítnutí. Připraveno je také 18 sémantických positive/negative fixtures se stavem NOT_EXECUTED_PROPOSAL a konkrétním očekávaným kódem/pointerem. To dokládá pouze strukturální konzistenci návrhů. Sémantické predicates, skutečné crypto/browser/OAuth konzumenty ani runtime pipeline tím nejsou ověřeny.

Certifikát a privátní klíče byly nově vygenerovány výhradně jako syntetické testovací materiály. Žádná hodnota nebyla získána z prostředí, skutečného Secret Manageru ani produkce.

Původní §8.6.1 dovoluje explicitní OWNER reveal a další business použití hodnot. Nový zákaz úniku platí pro create/import response, event, log a audit důkazy; nerozšiřovat jej bez rozhodnutí na zrušení existující OWNER reveal funkce.

## OAUTH_CLIENT

- Is token endpoint mandatory within Secret value or wholly external binding?
- Approve this client-secret variant; public-client and private_key_jwt are deliberately absent

Navržené sémantické podmínky:
- clientId/clientSecret exact nonempty UTF8; preserve whitespace
- tokenEndpoint absolute HTTPS with no userinfo or fragment; origin bound by server exact auth target
- scopes unique exact strings; do not split whitespace or infer grant type

## OAUTH_TOKEN_SET

- Approve Bearer-only initial variant; MAC/DPoP not implied
- Approve candidate-import expiry handling separately from runtime-use rejection

Navržené sémantické podmínky:
- Tokens exact UTF8 bytes, no sniffing JWT/decode or recoding
- expiresAt explicit absolute time; expired imported value may be stored as candidate but not used without consumer expiry rule
- Refresh permitted only when exact adapter declares refresh procedure; secret create performs no provider call

## TOTP_SEED

- Approve Base32-only import instead of hex/otpauth URI
- Approve seed min10bytes, algorithm list, digits and period bound (not existing SSOT constants)

Navržené sémantické podmínky:
- Strict unpadded uppercase RFC4648 Base32; decode/reencode equality including trailing padbits; no whitespace/case normalization
- Decoded seed length >=10 bytes (proposed security minimum)
- Generator uses current selected immutable version, declared algorithm/digits/period and server boundedclockskew

## CERTIFICATE

- Approve PEM-chain vs DER singlecert variants
- Approve bounded32chain and leaf-first order; imported selfsigned allowed as candidate but not auto trusted

Navržené sémantické podmínky:
- Each item contains exactly one PEM CERTIFICATE block with valid DER X.509; reject extra key/unknown blocks/trailing nonwhitespace
- Leaf-first chain: adjacent subject/issuer and signatures valid; duplicates rejected by DER fingerprint, not PEM spelling
- No implicit trust installation or claim of valid target hostname/time/CA; exact consumer validates trust/usage at use

## PRIVATE_KEY

- Approve unencrypted PKCS8 vs encryptedPKCS8/OpenSSH/PKCS1 import variants
- Approve keeping algorithm policy in exact consumer rather than global RSA-only rule

Navržené sémantické podmínky:
- Exactly one unencrypted PRIVATE KEY PEM PKCS8 block; complete cryptographic parse, no extra block
- Algorithm allowed only by exact consumer key contract; parser support alone does not authorize algorithm
- No implicit password decryption, certificate matching or key conversion; preserve original PEM UTF8 bytes

## DATABASE_CREDENTIAL

- Approve minimaluser/password and optional database value shape
- Approve target endpoint remains bindingmetadata instead of secretvalue

Navržené sémantické podmínky:
- Exact username/password UTF8 bytes without normalization
- Endpoint/vendor/TLS/network guard remains in exact target binding; no credentials embedded in URI
- Consumer rejects absent database if its explicit connection contract requires it; import itself performs no login

## COOKIE_JAR

- Approve unpartitioned cookie variant; partitioned/browserengine additions require declared variant
- Approve sessionexpiry null and epochsecond expiration schema

Navržené sémantické podmínky:
- Cookie key(name,domain,path) unique; reject exactdom duplicate even if value differs
- Domain syntax valid and actual allowedtarget scope separately verified; path absolute
- SameSite None requires secure=true; session expires=null, otherwise Unixsecondsinteger
- Cookie value exact; no URLdecode/trim, no opaque extra partition metadata fallback

## SESSION_STATE

- Approve restricted cookies/localStorage initial variant; otherallowedSSOTmembers require future declared variants
- Approve importonlydata separate from server-created bundle metadata/immutablelineage

Navržené sémantické podmínky:
- All cookie predicates above apply
- Origin exact scheme+host+port; no path/query/fragment/userinfo; duplicate origin rejects
- localStorage name unique perorigin even differentvalue; exact strings no normalization
- Imported state is untrusted data, not server BrowserStateBundle receipt; server verifies enginecapability, expectedaccount/tenant, auth/credentialepoch, contentdigest before candidate capture/activation
- No sessionStorage/IndexedDB/permissions/WebAuthn/privatekey/rawprofile implicit capture in this restricted variant

## SSH_CREDENTIAL

- Approve password and OpenSSHkey variants; PKCS8agent/hardwareauth absent
- Approve encrypted-key passphrase as distinct sensitive field; no autodetectfallback

Navržené sémantické podmínky:
- PASSWORD variant exactnonempty UTF8 username/password
- KEY variant exactlyone OPENSSH PRIVATE KEY PEM block complete parse; encryptedkey requires explicit passphrase, unencryptedkey forbids passphrase (semanticcondition)
- No conversion to PKCS8 or silentalgorithmfallback; supportedalgorithm bound by SSH adapter
- Endpoint/host-key fingerprint trusted binding separate; import cannot assert trust or disablehost-key verification
