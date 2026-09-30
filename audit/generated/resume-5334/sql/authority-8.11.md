### 8.11 Secret create request admission

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

