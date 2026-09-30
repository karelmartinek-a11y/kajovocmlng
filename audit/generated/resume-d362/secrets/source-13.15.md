### 13.15 Přihlášení, credentials, account continuity a state bundle

OWNER může přihlášení provést:

1. vložením Secret stable name nebo credential do dedikovaného pole,
2. zadáním credential v trusted chatu,
3. přímým převzetím browseru a přihlášením,
4. vyřešením challenge nebo device-bound loginu přes OWNER Device Bridge,
5. použitím exact client-certificate nebo virtual-authenticator bindingu podle account policy.

Akce **Uložit účet** vytvoří nebo aktualizuje `browser_account_binding`. Binding obsahuje target/service, stable account key, očekávanou account/tenant identity, username metadata, credential Secret refs, Browser state bundle, auth mode, ověřovací authenticated condition, allowed origins, external session family, auth epoch, account concurrency mode, expiration, rotation relation, poslední úspěšné ověření a usage.

Authenticated condition musí prokázat konkrétní účet a tenant/organization, pokud služba tenant používá. Pouhá absence login formuláře, přítomnost session cookie nebo HTTP 200 nestačí. Postcondition používá semantic account marker, provider account API, profile identity nebo jiný exact adapter. Pokud je účet nejednoznačný, session přejde do reauthentication/challenge a nesmí provést business mutaci.

Přímé OWNER psaní hesla do webové stránky samo o sobě nevytvoří dlouhodobý password Secret. OWNER zvolí **Uložit credential** nebo použije dedikované credential pole. Session cookies a storage lze uložit samostatně jako Browser state bundle, pokud OWNER požádá o zachování přihlášení.

Browser state bundle je encrypted secret-grade immutable artifact. Podle engine capability a explicitního serializer contractu může obsahovat:

- cookies včetně domain, path, SameSite, secure/httpOnly, expiry a partition/partition-key metadata,
- localStorage oddělený podle exact origin,
- explicitně povolený IndexedDB auth state,
- deklarovaný sessionStorage snapshot per page/origin,
- origin permissions potřebná pro workflow,
- client-certificate binding metadata bez exportu neexportovatelného private key,
- pouze explicitní virtual WebAuthn credential testovacího/automatizačního účtu,
- origin inventory, account/auth epoch, credential version, engine/build/serializer capability a content digest.

Bundle standardně neobsahuje browser cache, HTTP cache, service-worker executable/runtime state, memory-only JS state, open websocket, unsaved form, raw browser profile, extension state, download temp directory, OS credential store ani reálnou platformní passkey/private key. Provider-specific adapter může přidat další state pouze jako verzovaný, šifrovaný, testovaný bundle member s compatibility a cleanup contractem.

Capture probíhá po mutation barrieru a quiescent authenticated postcondition. Runtime nejprve ověří, že neexistuje pending unknown side effect, stabilizuje relevantní pages, přesně inventarizuje origins/storage kinds a teprve potom vytvoří candidate bundle. Aktivace pointeru je CAS nad account binding/auth epoch/credential version.

Restore vždy vytváří fresh context nebo exact bridge profile attachment. Cookies/storage se instalují před první page navigation podle serializer order; sessionStorage se vkládá před application bootstrap pouze přes explicitní init adapter. Poté runtime otevře safe start URL, ověří current account/tenant, credential/auth epoch a required origin state. Browser cache nebo service-worker readiness se znovu vytvoří webem a nesmí nahrazovat authenticated condition.

Third-party cookie policy, storage partitioning, anti-CSRF, device/IP binding, risk challenge, provider session-family limit nebo credential rotation mohou bundle učinit neportable. V takovém případě runtime nepokračuje s částečně přihlášeným stavem; provede deterministic relogin nebo `CHALLENGE_REQUIRED`.

Rotace password/OAuth/certificate credentialu, explicitní logout, account disable, provider invalidation, změna expected account identity nebo account auth epoch invaliduje dotčené bundles a živé session podle relation. Concurrent logout nebo credential rotation nesmí být přepsány starým bundle capturem.

