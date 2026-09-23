# KájovoCML NG - UI katalog

Pages: 20. Canonical navigation sections: 17.

## Prihlaseni - `/login`

Overit jedinou pevnou OWNER identitu bez napovedy username a bez user-management vetve.

**Panels:** Login card; Validation/error region; Throttle/locked notice

**Required states:** READY, VALIDATION_ERROR, AUTH_FAILED, THROTTLED, LOCKED, PENDING

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `login.username` | Uzivatelske jmeno | `text` / `TEXT_1` | yes | `NONEMPTY + SERVER_EXACT_SINGLETON_USERNAME` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Rucne zadany username pevne identity. UI nesmi zobrazit ani predvyplnit KRMAR78. |
| `login.password` | Heslo | `password` / `SECRET_1` | yes | `NONEMPTY + SERVER_ARGON2_VERIFY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Deployment-managed heslo pevne identity. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `login.submit` | Prihlasit se | `AUTH.LOGIN` | username,password locally valid AND not pending | missing field OR local invalid OR throttle/lock active OR request pending | `NONE` | Spusti password fazi autentizace. |

## MFA / enrollment / recovery - `/login/mfa`

Dokoncit povinne TOTP MFA nebo jednorazovy recovery flow pred vznikem plne OWNER session.

**Panels:** Enrollment QR/seed panel; TOTP/recovery form; One-time recovery codes panel

**Required states:** ENROLLMENT_REQUIRED, READY, VERIFYING, VERIFIED, FAILED, RECOVERY_USED

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `mfa.code` | Overovaci kod | `text` / `TEXT_1` | yes | `EXACT_6_DIGITS + SERVER_TOTP_VERIFY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Sestimistny TOTP kod. |
| `mfa.recovery` | Recovery kod | `text` / `TEXT_1` | no | `SERVER_RECOVERY_CODE_VERIFY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Alternativni nepouzity jednorazovy recovery kod. |
| `mfa.trusted` | Důvěryhodné zařízení | `checkbox` / `None` | no | `BOOLEAN` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | OWNER preference pro dobu duveryhodneho zarizeni podle current konfigurace. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `mfa.verify` | Ověřit | `AUTH.MFA_VERIFY` | exactly one of valid TOTP/recovery inputs present AND not pending | both empty OR conflicting modes OR pending | `NONE` | Dokonci TOTP/recovery autentizaci. |
| `mfa.showSeed` | Zobrazit ruční seed | `AUTH.MFA_ENROLLMENT_SEED_REVEAL` | enrollment session active | MFA already active OR session not enrollment | `NONE` | Zobrazi manual seed pouze v enrollment session. |
| `mfa.copyRecovery` | Kopírovat recovery kódy | `AUTH.RECOVERY_CODES_COPY` | fresh enrollment completion response contains codes | codes no longer revealable | `NONE` | Kopiruje jednorazove zobrazene recovery codes. |

## Centrální chat - `/chat`

Jednotne konverzacni rozhrani pro dotazy, prikazy, diagnostiku, generation a browser spolupraci.

**Panels:** Conversation list; Message timeline; Tool/action activity; Composer; Context/evidence drawer; Pinned Browser Preview Surface

**Required states:** LOADING, EMPTY, READY, STREAMING, ACTION_RUNNING, OPENAI_CONFIGURATION_REQUIRED, BROWSER_CHALLENGE, RECONNECTING, ERROR

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `chat.conversation` | Konverzace | `select` / `None` | no | `EXISTING_CONVERSATION_ID` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Vyber persistentni konverzace nebo aktivniho threadu. |
| `chat.model` | OpenAI model | `select` / `None` | yes | `OPENAI_SUPPORTED_MODEL + CAPABILITY_CHECK` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | OWNER volba globalniho nebo kontextoveho OpenAI modelu. |
| `chat.message` | Zpráva | `textarea` / `TEXT_50` | yes | `NONEMPTY_AFTER_UI_ONLY_WHITESPACE_CHECK; ORIGINAL_CONTENT_PRESERVED` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Prirozeny OWNER dotaz, prikaz nebo zadani. |
| `chat.url` | URL | `url` / `TEXT_1` | no | `ABSOLUTE_HTTPS_OR_ALLOWED_SCHEME + SSRF/NAVIGATION_POLICY_SERVER` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Volitelny webovy zdroj nebo cil pro browser session. |
| `chat.credential` | Credential | `secret` / `SECRET_50` | no | `SECRET_TYPE/PLACEMENT_SERVER_VALIDATION` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Volitelny business credential vlozeny do aktualniho operation contextu. |
| `chat.browserSession` | Browser session | `select` / `None` | no | `CURRENT_ATTACHABLE_BROWSER_SESSION` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Pripoji exact existujici browser session ke konverzaci. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `chat.new` | Nová konverzace | `CHAT.CONVERSATION_CREATE` | session authenticated | request pending | `NONE` | Zalozi novou persistentni konverzaci. |
| `chat.send` | Odeslat | `CHAT.MESSAGE_SEND` | message has content OR attachment/url/target reference AND model capability ready | empty submission OR OPENAI_CONFIGURATION_REQUIRED for AI turn OR pending same submit | `NONE` | Vytvori OWNER message a model/action turn. |
| `chat.steer` | Upravit směr | `CHAT.STEER` | turn nonterminal AND operation permits steer | terminal turn OR reconciliation/manual-review barrier | `NONE` | Vlozi novou OWNER instrukci do beziciho turnu s checkpoint/reconciliation. |
| `chat.cancel` | Zrušit běh | `CHAT.CANCEL` | current turn cancellable and nonterminal | no cancellable turn OR cancellation already committed | `NONE` | Pozada o canonical cancellation current turn/run. |
| `chat.openWeb` | Otevřít web | `BROWSER.SESSION_OPEN` | browser capability available AND valid target URL/intention | browser capability unavailable OR recovery barrier | `NONE` | Zalozi nebo pripoji browser session pro URL/intention. |
| `chat.takeover` | Převzít ovládání | `BROWSER.CONTROL_TAKEOVER` | session READY/PAUSED and controller != OWNER and no incompatible transfer pending | already OWNER OR transfer/recovery pending | `NONE` | Fenced transfer browser control lease na OWNERa. |
| `chat.returnAi` | Vrátit AI | `BROWSER.CONTROL_RETURN_AI` | OWNER holds current control lease AND AI consumer attached AND challenge resolved | OWNER not controller OR stale epoch OR unresolved challenge | `NONE` | Fenced transfer browser control z OWNERa zpet AI consumeru. |
| `chat.pickTarget` | Vybrat prvek | `BROWSER.TARGET_PICK_START` | live preview current and document identity current | no current document OR preview stale | `NONE` | Prepne preview do TARGET_PICK bez page mutation. |
| `chat.loginHuman` | Přihlásit se | `BROWSER.HUMAN_CHALLENGE_TAKEOVER` | typed login/challenge pending | no challenge/login flow | `NONE` | Preda browser OWNERovi pro human login/challenge. |
| `chat.saveAccount` | Uložit účet | `BROWSER.ACCOUNT_SAVE` | authenticated account marker verified and state save eligible | account not verified OR possible mutation unresolved | `NONE` | Otevre account/state binding summary a ulozi pouze potvrzeny rozsah. |
| `chat.closeBrowser` | Zavřít relaci | `BROWSER.SESSION_CLOSE` | session closeable and no blocking unknown effect | reconciliation/manual-review blocks destructive close | `IMPACT_IF_NONIDLE` | Uzavre browser session pres lifecycle/reconciliation. |

## Dashboard - `/dashboard`

Zobrazit a ovladat zivou topologii komponent, vazeb, portu, secrets, external targetu a runtime udalosti.

**Panels:** Metric strip; Topology canvas; Filter/search bar; Selection inspector; Live event stream; Correlation detail drawer

**Required states:** LOADING, EMPTY, READY, LIVE, STALE, RECONNECTING, PARTIAL, ERROR

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `dashboard.search` | Hledat | `search` / `TEXT_1` | no | `BOUNDED_SEARCH_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Fulltext nad komponentami, porty, bindingy a souvisejicimi objekty. |
| `dashboard.category` | Kategorie | `multiselect` / `None` | no | `KNOWN_COMPONENT_CATEGORY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Filtr component category. |
| `dashboard.lifecycle` | Lifecycle | `multiselect` / `None` | no | `KNOWN_LIFECYCLE_ENUM` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Filtr lifecycle stavu. |
| `dashboard.operational` | Operational | `multiselect` / `None` | no | `KNOWN_OPERATIONAL_ENUM` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Filtr operational projection. |
| `dashboard.criticality` | Criticality | `multiselect` / `None` | no | `KNOWN_CRITICALITY_ENUM` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Filtr business criticality. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `dashboard.fit` | Přizpůsobit | `UI.DASHBOARD_FIT` | canvas loaded | canvas unavailable | `NONE` | Fitne topology canvas do viewportu. |
| `dashboard.connect` | Propojit | `BINDING.CREATE` | source,target selected AND compatibility PASS AND versions current | missing endpoint OR incompatible/stale contract | `NONE` | Zalozi exact contract binding mezi kompatibilnimi porty. |
| `dashboard.disconnect` | Odpojit | `BINDING.DISCONNECT` | active binding selected and impact preview complete | binding not removable OR protected activation set | `IMPACT_PREVIEW` | Odstrani/retiruje exact binding podle lifecycle. |
| `dashboard.bindSecret` | Připojit secret | `SECRET.BIND` | source revision and secret version selector valid | wildcard/invalid target OR stale revision | `NONE` | Zalozi exact secret binding. |
| `dashboard.activate` | Aktivovat | `COMPONENT.ACTIVATE` | all blocking readiness gates PASS and candidate current | any gate not PASS OR current pointer conflict | `NONE` | Aktivuje validovany activation set/component revision. |
| `dashboard.enable` | Zapnout | `COMPONENT.ENABLE` | action registry enables for current state | already enabled OR lifecycle/readiness disallows | `NONE` | Enable component/runtime pres control state machine. |
| `dashboard.disable` | Vypnout | `COMPONENT.DISABLE` | action registry enables for current state | already disabled OR transition forbidden | `IMPACT_PREVIEW` | Disable component/runtime pres control state machine. |
| `dashboard.repair` | Opravit | `COMPONENT.REPAIR` | repair eligible and no duplicate active repair | no evidence/eligible target OR repair already active | `NONE` | Spusti deduplikovany repair workflow. |
| `dashboard.recertify` | Recertifikovat | `COMPONENT.RECERTIFY` | component registered and recertifiable | terminal/deregistered OR run already active | `NONE` | Spusti recertification checks. |
| `dashboard.e2e` | Spustit E2E | `TEST.E2E_RUN` | scenario exists and dependencies ready | no scenario OR readiness blocker | `NONE` | Spusti canonical E2E scenario. |

## Generování - `/generation`

Od OWNER zadani pres diskusi/specifikaci az po validovany, aktivovany a monitorovany vysledek bez moznosti obejit blocking gate.

**Panels:** Discussion panel; Web tab; Specification tab; Evidence tab; Progress tab; Source/fact inventory; Capability coverage matrix; Target graph; Generation DAG; Files/diff; Validation/eval results; Blockers; Candidate/release/activation panel

**Required states:** DRAFT, DISCUSSING, BLOCKED, SPEC_READY, APPROVAL_REQUIRED, RUNNING, VALIDATING, ACTIVATING, COMPLETED, FAILED, CANCELLING, MANUAL_REVIEW

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `gen.intent` | Funkční záměr | `textarea` / `TEXT_50` | yes | `NONEMPTY + ATTACHMENT/URL/TARGET REFERENCES ALLOWED` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Primarni business zadani OWNERa pro novou/menenou schopnost. |
| `gen.url` | Zdrojová URL | `url` / `TEXT_1` | no | `ABSOLUTE_URL + SERVER_NAVIGATION_POLICY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Volitelny zdroj pro research/browser. |
| `gen.credential` | Credential | `secret` / `SECRET_50` | no | `SECRET_USE_CONTEXT_REQUIRED` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Volitelny chybejici business credential pro konkretni research/configuration krok. |
| `gen.blockerResponse` | Odpověď na blocker | `textarea` / `TEXT_8` | no | `BLOCKER_SCHEMA` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Pouze skutecne chybejici OWNER business vstup k exact blockeru. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `gen.create` | Nové zadání | `GENERATION.CREATE` | authenticated and base capability available | create pending OR platform recovery barrier | `NONE` | Zalozi generation job a persistentni diskusi. |
| `gen.send` | Odeslat | `GENERATION.MESSAGE_SEND` | nonempty message/source and job nonterminal | job terminal OR no input | `NONE` | Prida OWNER message/source do generation discussion. |
| `gen.steer` | Upravit směr | `GENERATION.STEER` | job nonterminal and current phase steerable | mutation reconciliation/manual review OR terminal | `NONE` | Steer current generation/model/browser read-only loop. |
| `gen.approveSpec` | Schválit specifikaci | `GENERATION.SPEC_APPROVE` | spec current, all required questions resolved, validation PASS | open question, stale revision, invalid spec, missing authority | `NONE` | Atomicky schvali exact immutable specification revision. |
| `gen.resolveBlocker` | Vyřešit blocker | `GENERATION.BLOCKER_RESOLVE` | blocker OPEN and required input valid | no open blocker OR invalid/stale blocker | `NONE` | Odesle schema-valid OWNER odpoved na exact blocker. |
| `gen.retry` | Opakovat | `GENERATION.RETRY` | current failed phase exposes retry directive allowing retry | unknown effect/manual review/no retry directive | `NONE` | Retry pouze podle canonical recovery directive. |
| `gen.cancel` | Zrušit | `GENERATION.CANCEL` | job cancellable and nonterminal | terminal OR cancellation already committed | `NONE` | Canonical cancellation generation jobu. |
| `gen.selftest` | Spustit self-test | `SELFTEST.RUN_FOR_JOB` | job has testable artifacts/object refs | nothing testable OR conflicting run | `NONE` | Spusti relevantni canonical self-test katalog. |
| `gen.bypass` | Obejít blokaci | `FORBIDDEN` | NEVER | ALWAYS | `NONE` | Tato akce NESMI existovat. |

## AI agenti - `/agents`

Katalog, revision editor, tool/handoff/browser bindingy, run console, eval a lifecycle AI agentu.

**Panels:** Agent catalog; Revision editor; Tool binding graph; Handoff graph; Guardrails/approval; Session/memory browser; Run console; Browser panel; Eval suite; Usage/SLO; Triggers/schedules; Activation/rollback; Secrets/bindings/logs/audit

**Required states:** LOADING, EMPTY, READY, EDITING, VALIDATING, RUNNING, PAUSED, APPROVAL_REQUIRED, FAILED, MANUAL_REVIEW

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `agent.search` | Hledat agenta | `search` / `TEXT_1` | no | `BOUNDED_SEARCH_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Fulltext agent catalogu. |
| `agent.instructions` | Canonical instrukce | `textarea` / `TEXT_50` | yes | `REVISION_SCHEMA + PROVENANCE/INSTRUCTION_AUTHORITY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Normativni instrukce konkretni agent revision. |
| `agent.inputSchema` | Input schema | `code` / `CODE_50` | yes | `JSON_SCHEMA_2020_12 + OPENAI_COMPATIBILITY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Strict vstupni schema agent revision. |
| `agent.outputSchema` | Output schema | `code` / `CODE_50` | yes | `JSON_SCHEMA_2020_12 + OPENAI_COMPATIBILITY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Strict vystupni schema agent revision. |
| `agent.model` | OpenAI model | `select` / `None` | yes | `SUPPORTED_MODEL/CAPABILITY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Model pro revision. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `agent.newRevision` | Nová revize | `AGENT.REVISION_CREATE` | agent exists and lifecycle allows revision | terminal/deregistered OR create pending | `NONE` | Vytvori editable candidate revision bez mutace active revision. |
| `agent.saveRevision` | Uložit revizi | `AGENT.REVISION_SAVE` | candidate dirty and local/schema validation PASS | read-only active revision OR validation errors | `NONE` | Persistuje candidate revision s validaci. |
| `agent.validate` | Validovat | `AGENT.VALIDATE` | candidate/current revision exists | no revision OR validation active | `NONE` | Spusti full contract/binding/schema validation. |
| `agent.run` | Spustit | `AGENT.RUN` | active ready revision, bindings current, OpenAI configured | not active/ready OR stale binding OR OPENAI_CONFIGURATION_REQUIRED | `NONE` | Spusti agent run. |
| `agent.pause` | Pozastavit | `AGENT.RUN_PAUSE` | run supports pause and nonterminal | no run OR phase not pausable | `NONE` | Pozastavi resumable run na checkpointu. |
| `agent.resume` | Pokračovat | `AGENT.RUN_RESUME` | paused checkpoint current and dependencies valid | stale checkpoint/binding/model capability | `NONE` | Resume exact checkpoint. |
| `agent.cancel` | Zrušit | `AGENT.RUN_CANCEL` | run cancellable | terminal/unknown effect barrier | `NONE` | Canonical cancel runu. |
| `agent.activate` | Aktivovat | `AGENT.ACTIVATE` | promotion/eval/readiness PASS | any blocking gate not PASS | `NONE` | Aktivuje validated revision v activation setu. |
| `agent.rollback` | Rollback | `AGENT.ROLLBACK` | valid rollback point exists and safety checks PASS | no rollback point OR incompatible migration/effect | `IMPACT_PREVIEW` | Vrati na overeny predchozi release/revision pointer. |

## MCP servery a nástroje - `/mcp`

MCP katalog, protocol/wire inspector, request builder, MRTR/subscription/task konzole a activation diagnostika.

**Panels:** Server catalog; Protocol era/revision header; Discover inspector; HTTP/JSON-RPC inspector; Capabilities/extensions; Discovery snapshots/cache; Tools/resources/prompts explorer; Schema/projection viewer; Request builder; Raw JSON-RPC/SSE evidence; MRTR console; Subscription console; State handle browser; Task console; Binding graph; Idempotency/concurrency/reconciliation; Runtime/health/monitoring; Activation/rollback; Logs/audit

**Required states:** LOADING, EMPTY, READY, DISCOVERING, EXECUTING, STREAMING, INPUT_REQUIRED, TASK_ACTIVE, STALE_SNAPSHOT, PROTOCOL_ERROR, RECONCILING, MANUAL_REVIEW

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `mcp.search` | Hledat | `search` / `TEXT_1` | no | `BOUNDED_SEARCH_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Hleda servery, tools, resources, prompts a adaptery. |
| `mcp.method` | Method | `select` / `None` | yes | `METHOD_SUPPORTED_BY_SELECTED_REVISION` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Exact MCP/JSON-RPC method request builderu. |
| `mcp.name` | Name / URI / Task ID | `text` / `TEXT_1` | no | `EXACT_METHOD_ROUTING_SCHEMA` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Method-specific target routing field. |
| `mcp.meta` | Request _meta | `code` / `CODE_50` | yes | `MCP_NATIVE_SCHEMA` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Per-request protocolVersion/capabilities a povolena metadata. |
| `mcp.headers` | HTTP headers | `code` / `CODE_50` | no | `SINGLETON_HEADER + HEADER/BODY_MATCH` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Routing headers a custom schema-recognized headers. |
| `mcp.params` | Params / body | `code` / `CODE_50` | no | `NATIVE_JSON_SCHEMA + SIZE/DEPTH_LIMITS` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Typed JSON-RPC params podle exact tool/method contractu. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `mcp.discover` | server/discover | `MCP.DISCOVER` | selected endpoint/auth binding valid | no endpoint OR auth/binding invalid | `NONE` | Provede fresh discovery a ulozi evidence snapshot. |
| `mcp.send` | Odeslat request | `MCP.REQUEST_EXECUTE` | all request fields valid and selected contract current | malformed/mismatch/stale contract/binding | `NONE` | Provede exact request po protocol/schema/binding preflightu. |
| `mcp.cancel` | Zrušit | `MCP.REQUEST_CANCEL` | current operation cancellable | terminal/noncancellable/unknown-effect reconciliation | `NONE` | Cancel current cancellable MCP request/task podle contractu. |
| `mcp.verify` | Ověřit | `MCP.VERIFY` | server revision selected | verification active OR no revision | `NONE` | Spusti protocol/compatibility verification. |
| `mcp.activate` | Aktivovat | `MCP.ACTIVATE` | discovery/schema/E2E/bindings PASS | era unknown/ambiguous OR any gate fail | `NONE` | Aktivuje verified MCP revision/activation relation. |
| `mcp.repair` | Opravit | `MCP.REPAIR` | repairable failure/evidence | no repair basis OR duplicate active repair | `NONE` | Spusti repair s evidence. |

## Browser relace a automatizace - `/browser`

Globalni inventory browser sessions, live preview, human handoff, visual collaboration, teaching a deterministic automation lifecycle.

**Panels:** Session inventory table; Preview surface; URL/page tree; Control holder banner; Operation/current action target; Challenge card; Mode toolbar; Annotation toolbar; Annotation/focus list; Account save card; Artifacts/evidence; Automation teaching/replay panel

**Required states:** CREATING, READY, AI_CONTROLS, TAKING_OVER, OWNER_CONTROLS, AUTOMATION_CONTROLS, CHALLENGE, PAUSED, RECOVERING, CLOSED, FAILED, STALE_ANNOTATION

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `browser.search` | Hledat relaci | `search` / `TEXT_1` | no | `BOUNDED_SEARCH_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Filtr session ID, parentu, consumeru, accountu, URL/title a purpose. |
| `browser.url` | URL | `url` / `TEXT_1` | no | `ABSOLUTE_URL + NAVIGATION_POLICY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Navigacni cil pro novou/ad-hoc relaci. |
| `browser.annotationNote` | Poznámka k označení | `textarea` / `TEXT_2` | no | `MAX_2000 + PRESERVE_CONTENT` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Volitelna komunikacni poznamka persistentni annotation. |
| `browser.focusMessage` | Zpráva „zaměř se sem“ | `textarea` / `TEXT_2` | yes | `NONEMPTY + MAX_4000` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Text BrowserFocusRequestu mezi OWNER a AI. |
| `browser.accountName` | Uložený účet / binding | `select` / `None` | no | `CURRENT_ACCOUNT_BINDING` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Exact browser account binding pro restore/save/login. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `browser.new` | Nová relace | `BROWSER.SESSION_CREATE` | capacity/admission ready | capacity exhausted OR recovery barrier | `NONE` | Zalozi browser session s exact consumer/parent/purpose. |
| `browser.navigate` | Otevřít URL | `BROWSER.NAVIGATE` | controller has write lease and URL valid | no control lease OR stale page/document identity | `NONE` | Naviguje current page pod current control/operation scope. |
| `browser.takeover` | Převzít ovládání | `BROWSER.CONTROL_TAKEOVER` | current session controllable and not already OWNER | stale control epoch/transfer pending | `NONE` | Fenced transfer write authority na OWNERa. |
| `browser.returnAi` | Vrátit AI | `BROWSER.CONTROL_RETURN_AI` | OWNER current controller + AI consumer attached + challenge resolved | not controller OR no AI recipient OR stale epoch | `NONE` | Fenced transfer na exact AI consumer. |
| `browser.modeBrowse` | Procházet | `BROWSER.UI_MODE_BROWSE` | OWNER holds write lease | OWNER not controller for page input | `NONE` | Prepne preview do BROWSE input rezimu. |
| `browser.modeMarkup` | Označit | `BROWSER.UI_MODE_MARKUP` | preview current | preview/document stale | `NONE` | Prepne do MARKUP overlay rezimu; page pointer forwarding MUSI byt off. |
| `browser.modeTarget` | Vybrat prvek | `BROWSER.UI_MODE_TARGET_PICK` | fresh observation/document | no current document | `NONE` | Prepne do TARGET_PICK. |
| `browser.modePointer` | Ukazatel | `BROWSER.UI_MODE_LIVE_POINTER` | preview current | preview stale | `NONE` | Aktivuje ephemeral POINTER/LASER collaboration. |
| `browser.annotationCommit` | Uložit označení | `BROWSER.ANNOTATION_CREATE` | draft geometry valid and lineage unchanged | pointer-up lineage changed without snapshot-only resolution | `NONE` | Commitne BrowserVisualAnnotation s exact anchor/snapshot. |
| `browser.focusAi` | Požádat AI: zaměř se sem | `BROWSER.FOCUS_REQUEST_CREATE` | >=1 resolvable/snapshot annotation selected and AI consumer attached | no annotation OR no AI recipient | `NONE` | Vytvori focus request z vybranych annotations. |
| `browser.focusOwner` | OWNER: podívej se sem | `BROWSER.FOCUS_REQUEST_CREATE_AI` | AI proposal validated server-side | stale AI observation/invalid anchor | `NONE` | AI-side ekvivalent focus requestu; v OWNER UI se zobrazi jako incoming card. |
| `browser.saveAccount` | Uložit účet | `BROWSER.ACCOUNT_SAVE` | account marker verified and no unresolved effect | wrong/unknown account OR incompatible state | `NONE` | Ulozi povoleny state bundle po account verification. |
| `browser.close` | Zavřít relaci | `BROWSER.SESSION_CLOSE` | session closeable | possible mutation unknown/manual review | `IMPACT_IF_NONIDLE` | Lifecycle close se cleanup/reconciliation. |
| `browser.teach` | Vytvořit automatizaci | `BROWSER.AUTOMATION_CREATE_FROM_TEACHING` | replayable deterministic flow + postconditions PASS | visual-only unresolved mutating step OR model-only replay | `NONE` | Prevede verified teaching flow do candidate automation revision. |

## Registrované prvky - `/registered`

Provozni zkraceny prehled vsech aktivnich/registrovanych objektu a rychlych akci.

**Panels:** Metric/status strip; Search/filter bar; Dense table/card switch; Quick action menu; Last event/alarm column

**Required states:** LOADING, EMPTY, READY, PARTIAL, STALE_RECONNECTING, ERROR, SUCCESS

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `registered.search` | Hledat | `search` / `TEXT_1` | no | `BOUNDED_SEARCH_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Fulltext registrovanych objektu. |
| `registered.status` | Stav | `multiselect` / `None` | no | `KNOWN_STATUS_ENUMS` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Filtr lifecycle/operational/monitoring stavu. |
| `registered.kind` | Typ | `multiselect` / `None` | no | `KNOWN_OBJECT_KIND` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Filtr component/MCP/agent/tool/automation druhu. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `registered.open` | Otevřít detail | `UI.OBJECT_OPEN` | object exists | object tombstoned/unavailable | `NONE` | Otevre canonical detail objektu. |
| `registered.enable` | Zapnout | `OBJECT.ENABLE` | action registry says enabled | registry disabled with reason | `NONE` | Quick action ze sdileneho action registry. |
| `registered.disable` | Vypnout | `OBJECT.DISABLE` | action registry says enabled | registry disabled with reason | `IMPACT_IF_REQUIRED` | Quick action ze sdileneho action registry. |
| `registered.repair` | Opravit | `OBJECT.REPAIR` | repair eligible | not eligible/repair active | `NONE` | Quick repair action. |

## Katalog komponent - `/components`

Plny registr komponent, revisions, releases, runtime, contracts, relations, bindings a lifecycle operaci.

**Panels:** Catalog filters; Table/card view; Identity overview; Revision/release tabs; Runtime; Contracts/relations; Secrets/bindings; Monitoring; Logs/audit; Usage graph; Diff viewer; Registration/import panel

**Required states:** LOADING, EMPTY, READY, PARTIAL, STALE_RECONNECTING, ERROR, SUCCESS

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `component.search` | Hledat | `search` / `TEXT_1` | no | `BOUNDED_SEARCH_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Fulltext component catalogu. |
| `component.displayName` | Název | `text` / `TEXT_1` | yes | `NONEMPTY + DOMAIN_LENGTH` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | OWNER display name component candidate/registration. |
| `component.purpose` | Business účel | `textarea` / `TEXT_8` | yes | `NONEMPTY + DOMAIN_LENGTH` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Business purpose komponenty. |
| `component.category` | Kategorie | `select` / `None` | yes | `COMPONENT_CATEGORY_ENUM` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Canonical component category. |
| `component.criticality` | Criticality | `select` / `None` | yes | `CRITICALITY_ENUM` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Business criticality pro monitoring/ops kontext. |
| `component.manifest` | Manifest | `code` / `CODE_50` | no | `MANIFEST_SCHEMA + DIGEST + CROSS_REFERENCES` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Kanonicky registration manifest pri importu/registraci. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `component.register` | Registrovat | `COMPONENT.REGISTER` | required registration fields/manifest valid | schema/naming/uniqueness/dependency failure | `NONE` | Registruje existujici objekt pres canonical validator. |
| `component.generate` | Generovat | `GENERATION.CREATE_FOR_COMPONENT` | authenticated and generation capability available | OPENAI_CONFIGURATION_REQUIRED OR recovery barrier | `NONE` | Preda zamer do generation workflow. |
| `component.import` | Importovat | `COMPONENT.IMPORT` | file/manifest selected and parseable | invalid file/unsupported schema | `NONE` | Nacte candidate manifest/artifact bez tiche aktivace. |
| `component.export` | Exportovat | `COMPONENT.EXPORT` | object exists | no object | `NONE` | Exportuje exact object/revision evidence. |
| `component.validate` | Validovat | `COMPONENT.VALIDATE` | candidate/current revision exists | no revision or run active | `NONE` | Full registration/contract validation. |
| `component.verify` | Ověřit | `COMPONENT.VERIFY` | validation PASS | validation not PASS | `NONE` | Verification/E2E readiness. |
| `component.activate` | Aktivovat | `COMPONENT.ACTIVATE` | all readiness/verification gates PASS | any blocking gate/stale state | `NONE` | Atomic activation pointer/bindings/routes. |
| `component.rollback` | Rollback | `COMPONENT.ROLLBACK` | rollback point valid | no valid point OR safety blocker | `IMPACT_PREVIEW` | Rollback na verified point. |
| `component.archive` | Archivovat | `COMPONENT.ARCHIVE` | archive eligible and no active dependency | active/required dependency | `NONE` | Archivuje neaktivni objekt/revision podle lifecycle. |
| `component.deregister` | Deregistrovat | `COMPONENT.DEREGISTER` | all required detach/cleanup preconditions PASS | active dependency/binding/runtime | `MANDATORY_IMPACT_PREVIEW` | Terminal deregistration s impact preview. |

## Externí systémy - `/external`

Sprava external targetu, auth bindingu, inbound endpointu, outbound calls, webhooku, circuit breakeru a jejich monitoringu.

**Panels:** Target list; Target detail form; Auth binding panel; Inbound/outbound binding matrix; Live request history; Latency/error stats; Circuit panel; Request builder; Webhook inspector; Challenge tester; Monitoring/alarms

**Required states:** LOADING, EMPTY, READY, PARTIAL, STALE_RECONNECTING, ERROR, SUCCESS

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `external.name` | Název targetu | `text` / `TEXT_1` | yes | `NONEMPTY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Display name external targetu. |
| `external.baseUrl` | Base URL | `url` / `TEXT_1` | yes | `ABSOLUTE_URL + EGRESS/SSRF_POLICY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Canonical base URL outbound targetu. |
| `external.pathPrefixes` | Povolené cesty | `textarea` / `TEXT_8` | no | `NORMALIZED_RELATIVE_PREFIX_LIST` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Explicitni allowed path prefixy, jeden na radek. |
| `external.methods` | Metody | `multiselect` / `None` | yes | `KNOWN_HTTP_METHODS` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Allowed HTTP methods. |
| `external.authMode` | Auth režim | `select` / `None` | yes | `EXTERNAL_AUTH_MODE_ENUM` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | NONE/Bearer/API key/OAuth/mTLS/Basic/custom header. |
| `external.secret` | Credential binding | `select` / `None` | no | `CURRENT_COMPATIBLE_SECRET_BINDING` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Exact Secret binding pro target/endpoint. |
| `external.rate` | Business rate limit | `number` / `None` | no | `NONNEGATIVE + BUSINESS_POLICY_BOUNDS` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | OWNER business hranice integrace. |
| `external.requestBody` | Test payload | `code` / `CODE_50` | no | `EXPECTED_RESPONSE/REQUEST_SCHEMA` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Request builder body pro test call. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `external.save` | Uložit target | `EXTERNAL.TARGET_SAVE` | required fields valid | URL/method/auth/binding invalid | `NONE` | Persistuje target candidate/config. |
| `external.test` | Otestovat request | `EXTERNAL.TEST_REQUEST` | target valid/current and test request valid | circuit/policy/binding prevents dispatch | `NONE` | Spusti bounded test pres egress gateway. |
| `external.challenge` | Otestovat challenge | `EXTERNAL.CHALLENGE_TEST` | endpoint challenge contract exists | no challenge contract | `NONE` | Spusti provider challenge tester. |
| `external.circuitOpen` | Otevřít circuit | `EXTERNAL.CIRCUIT_OPEN` | circuit exists and not OPEN | already OPEN | `NONE` | Manual open circuit. |
| `external.circuitClose` | Zavřít circuit | `EXTERNAL.CIRCUIT_CLOSE` | state permits close | state/verification blocks | `NONE` | Manual close/reset according to state machine. |
| `external.circuitReset` | Resetovat circuit | `EXTERNAL.CIRCUIT_RESET` | reset permitted | active unsafe condition | `NONE` | Reset evidence/counters only via canonical op. |

## Monitoring - `/monitoring`

Probes, SLO, heartbeat, alerts, scheduler, resource metrics, runbook, repair a recertification.

**Panels:** Metric cards; Probe/state timeline; Component filters; Severity segments; Alerts/deliveries; Scheduler state; SLO/latency; Heartbeat freshness; Resource charts; Runbook/repair; Profile editor; Debug evidence

**Required states:** LOADING, EMPTY, READY, PARTIAL, STALE_RECONNECTING, ERROR, SUCCESS

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `monitoring.search` | Hledat komponentu | `search` / `TEXT_1` | no | `BOUNDED_SEARCH_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Fulltext monitoring targetu. |
| `monitoring.severity` | Severity | `multiselect` / `None` | no | `ALERT_SEVERITY_ENUM` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | WARNING/HIGH/CRITICAL segmenty. |
| `monitoring.slo` | Business SLO | `number` / `None` | no | `POLICY_UNIT + BOUNDS` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | OWNER-defined SLO target v definovane jednotce. |
| `monitoring.runbook` | Runbook reference | `text` / `TEXT_1` | no | `REFERENCE_FORMAT` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Odkaz/identifikator runbooku. |
| `monitoring.suppressUntil` | Potlačit do | `datetime` / `None` | no | `FUTURE_TIMESTAMP_WITH_POLICY_BOUNDS` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Casovy konec alert suppression. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `monitoring.ack` | Potvrdit alert | `ALERT.ACK` | alert OPEN | not OPEN | `NONE` | ACK current alert bez falsifikace health. |
| `monitoring.suppress` | Potlačit | `ALERT.SUPPRESS` | alert suppressible and interval valid | closed alert OR invalid interval | `NONE` | Nastavi suppression interval. |
| `monitoring.close` | Uzavřít alert | `ALERT.CLOSE` | close preconditions satisfied | active unresolved condition | `NONE` | Uzavre pouze pokud close contract/postcondition dovoluje. |
| `monitoring.repair` | Opravit | `COMPONENT.REPAIR` | repair eligible and evidence current | no eligible component/evidence or repair active | `NONE` | Spusti deduplikovany repair job z evidence. |
| `monitoring.probe` | Spustit kontrolu | `MONITORING.PROBE_RUN` | probe exists and target current | no probe/binding unavailable | `NONE` | Ad-hoc canonical probe. |
| `monitoring.saveProfile` | Uložit profil | `MONITORING.PROFILE_SAVE` | edited values valid | policy conflict/out of bounds | `NONE` | Ulozi OWNER-editable business hodnoty a system-managed policy inputs. |

## API klíč a runtime vazby - `/runtime-access`

Sprava singleton OWNER API key a detailni zobrazeni runtime/exact contract/Secret/external/bridge vazeb bez permission registry.

**Panels:** OWNER API key card; Usage history; Runtime/component identities; Exact contract binding matrix; Secret binding matrix; External auth bindings; Bridge certificates; Evidence/audit drawer

**Required states:** LOADING, EMPTY, READY, PARTIAL, STALE_RECONNECTING, ERROR, SUCCESS

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `runtime.search` | Hledat vazbu | `search` / `TEXT_1` | no | `BOUNDED_SEARCH_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Fulltext identities/bindings. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `runtime.revealKey` | Zobrazit API klíč | `OWNER_API_KEY.REVEAL` | MFA-authenticated OWNER session current | session reauthentication required | `NONE` | Reveal current singleton KCML_OWNER_API_KEY. |
| `runtime.copyKey` | Kopírovat API klíč | `OWNER_API_KEY.COPY` | value revealed in current trusted UI state | not revealed/current value absent | `NONE` | Copy current revealed value. |
| `runtime.rotateKey` | Rotovat API klíč | `OWNER_API_KEY.ROTATE` | OWNER session current and no rotate pending | rotate pending/session invalid | `EXPLICIT_CONFIRM` | Atomicky nahradi jedinou active verzi a starou ihned zneplatni. |
| `runtime.testBinding` | Otestovat vazbu | `BINDING.TEST` | binding current and target/source available | stale/inactive binding | `NONE` | Test resolve/dispatch preflight selected exact binding. |
| `runtime.revokeBridge` | Revokovat bridge certifikát | `BRIDGE.CERT_REVOKE` | certificate current and revocable | already revoked/missing | `EXPLICIT_CONFIRM` | Revokuje exact OWNER Device Bridge cert. |

## Secrets a hesla - `/secrets`

Plny OWNER Password Manager nad Secret Managerem vcetne hodnot, verzi, rotace, bindings, usage a auditu.

**Panels:** Search/filter/groups/tags; Table/card view; Secret detail; Value/reveal area; Versions timeline; Bindings matrix; Usage graph; TOTP/countdown; Import/export; Bulk actions; Audit/live logs

**Required states:** LOADING, EMPTY, READY, PARTIAL, STALE_RECONNECTING, ERROR, SUCCESS

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `secret.search` | Hledat | `search` / `TEXT_1` | no | `BOUNDED_SEARCH_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Fulltext stable/display name, tags, group a metadata. |
| `secret.stableName` | Stable name | `text` / `TEXT_1` | yes | `STABLE_SECRET_NAME_UNIQUE` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Nemenny logicky nazev secretu po vytvoreni podle contractu. |
| `secret.displayName` | Název | `text` / `TEXT_1` | yes | `NONEMPTY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | OWNER display label. |
| `secret.description` | Popis | `textarea` / `TEXT_8` | no | `DOMAIN_LENGTH` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Business popis ucelu secretu. |
| `secret.type` | Typ | `select` / `None` | yes | `SECRET_TYPE_ENUM` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | PASSWORD/API_KEY/.../GENERIC_BINARY. |
| `secret.value` | Hodnota | `secret` / `SECRET_50` | yes | `TYPE_SPECIFIC + NO_SILENT_NORMALIZATION` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Plaintext hodnota nove secret version. |
| `secret.url` | URL | `url` / `TEXT_1` | no | `URL_IF_PRESENT` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Volitelne metadata podle typu. |
| `secret.username` | Username | `text` / `TEXT_1` | no | `DOMAIN_LENGTH` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Volitelne metadata podle typu. |
| `secret.notes` | Poznámky | `textarea` / `TEXT_8` | no | `DOMAIN_LENGTH` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | OWNER poznamky. |
| `secret.expiration` | Expirace | `datetime` / `None` | no | `TIMESTAMP/POLICY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Volitelna expirace verze/polozky. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `secret.create` | Nový secret | `SECRET.CREATE` | required metadata/value valid and stableName available | validation/uniqueness failure | `NONE` | Vytvori secret + prvni version. |
| `secret.reveal` | Zobrazit | `SECRET.REVEAL` | secret exists and version revealable | deleted/unavailable version | `NONE` | Reveal plaintext active/selected version. |
| `secret.copy` | Kopírovat | `SECRET.COPY` | plaintext currently revealed | not revealed | `NONE` | Kopiruje revealovanou hodnotu. |
| `secret.newVersion` | Nová verze | `SECRET.VERSION_CREATE` | secret mutable metadata exists and value valid | reserved system secret special contract OR invalid value | `NONE` | Vytvori immutable new secret version. |
| `secret.activateVersion` | Aktivovat verzi | `SECRET.VERSION_ACTIVATE` | selected version eligible/current state valid | same active/ineligible/stale state | `NONE` | Atomicky prepnuti active version s invalidaci dependent state dle contractu. |
| `secret.rotate` | Rotovat | `SECRET.ROTATE` | rotation permitted | policy/state blocks | `NONE` | Vytvori/aktivuje novou hodnotu podle rotation policy. |
| `secret.bind` | Připojit | `SECRET.BIND` | source/revision/purpose exact and compatible | wildcard/ambiguous/stale source | `NONE` | Vytvori exact binding source revision -> secret/version/purpose. |
| `secret.unbind` | Odpojit | `SECRET.UNBIND` | binding removable | active required dependency | `IMPACT_PREVIEW` | Retiruje exact binding po impact validation. |
| `secret.delete` | Smazat | `SECRET.DELETE` | delete eligible | reserved/current required/retention dependency | `EXPLICIT_CONFIRM` | Lifecycle delete pouze pokud contract dovoluje; system-reserved key nelze obecnym CRUD smazat. |
| `secret.export` | Exportovat | `SECRET.EXPORT` | exportable value/metadata selected | not exportable | `NONE` | Export selected item/version podle contractu. |
| `secret.testResolve` | Test resolve | `SECRET.TEST_RESOLVE` | binding active/current | binding inactive/stale | `NONE` | Otestuje exact binding resolution bez zmeny consumer state. |

## Audit a logy - `/audit`

Zive i historicke logy, audit chain, diffy, payloady, correlation graph, export a integrity.

**Panels:** Filter/search bar; Live tail; Merged timeline; Raw/formatted detail; Before/after diff; Stack trace; Payload/secret view; Correlation graph; Saved queries; Retention/archive state; Integrity panel

**Required states:** LOADING, EMPTY, READY, PARTIAL, STALE_RECONNECTING, ERROR, SUCCESS

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `audit.query` | Fulltext | `search` / `TEXT_1` | no | `BOUNDED_SEARCH_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Fulltext nad log/audit message a indexovanymi poli. |
| `audit.timeFrom` | Od | `datetime` / `None` | no | `TIMESTAMP` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Casovy filtr start. |
| `audit.timeTo` | Do | `datetime` / `None` | no | `TIMESTAMP >= from` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Casovy filtr konec. |
| `audit.level` | Level | `multiselect` / `None` | no | `LOG_LEVEL_ENUM` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | fatal/error/warn/info/debug/trace. |
| `audit.correlation` | Correlation ID | `text` / `TEXT_1` | no | `UUID/DOMAIN_ID_FORMAT` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Exact correlation lookup. |
| `audit.savedName` | Název dotazu | `text` / `TEXT_1` | no | `NONEMPTY_IF_SAVE` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Nazev saved query. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `audit.live` | Živý přenos | `AUDIT.LIVE_TAIL` | stream capability available | disconnected/auth unavailable | `NONE` | Zapne/vypne live tail bez zmeny ulozeneho auditu. |
| `audit.search` | Hledat | `AUDIT.SEARCH` | filter set valid | invalid time range/query | `NONE` | Spusti server query s filtry. |
| `audit.saveQuery` | Uložit dotaz | `AUDIT.SAVED_QUERY_CREATE` | query/name valid | invalid/duplicate according to contract | `NONE` | Persistuje OWNER saved query. |
| `audit.exportJsonl` | Export JSONL | `AUDIT.EXPORT_JSONL` | query resolved | no query/result OR export running | `NONE` | Export current filtered dataset/evidence. |
| `audit.exportCsv` | Export CSV | `AUDIT.EXPORT_CSV` | query resolved | no result/export running | `NONE` | Export projection current resultu. |
| `audit.verify` | Ověřit integritu | `AUDIT.INTEGRITY_VERIFY` | audit store available | verification already running | `NONE` | Spusti audit chain integrity check. |

## Konfigurace - `/configuration`

Jednotny registr OWNER-input/preference/system-managed parametru s desired/effective version, aplikaci, verification a rollbackem.

**Panels:** Search/category navigation; Setting list; Setting detail/editor; Source/management mode badge; Desired/effective version; Derivation explanation; Apply progress; Conflict/recovery panel; Audit history

**Required states:** LOADING, READY, EDITING, VALIDATING, PENDING, APPLYING, VERIFYING, APPLIED, ROLLING_BACK, ROLLED_BACK, FAILED, CONFLICT, MANUAL_REVIEW

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `config.search` | Hledat nastavení | `search` / `TEXT_1` | no | `BOUNDED_SEARCH_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Fulltext key/label/description/category. |
| `config.category` | Kategorie | `multiselect` / `None` | no | `CONFIG_CATEGORY_ENUM` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | network/auth/runtime/integrations/observability/presentation/AI/generation/browser/retention/deployment. |
| `config.value` | Hodnota | `dynamic` / `None` | no | `PARAMETER_VALIDATION_SCHEMA` | `ONLY ownerEditable=true AND managementMode != SYSTEM_MANAGED` / `OWNER_OR_SYSTEM` | Editor dle type/schema konkretniho parametru. |
| `config.reason` | Poznámka ke změně | `textarea` / `TEXT_2` | no | `DOMAIN_LENGTH` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Volitelny OWNER kontext zmeny do auditu. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `config.edit` | Upravit | `CONFIG.EDIT` | ownerEditable=true | SYSTEM_MANAGED or read-only derived value | `NONE` | Prejde selected ownerEditable setting do edit mode. |
| `config.apply` | Použít | `CONFIG.APPLY` | dirty values valid + expected stateVersion current | validation error/stale version/apply active | `NONE` | Commitne desired version a config-apply run. |
| `config.cancelEdit` | Zrušit změny | `UI.CONFIG_EDIT_CANCEL` | dirty local form | no local changes | `NONE` | Zahodi pouze lokalni neodeslane editace. |
| `config.rollback` | Vrátit předchozí | `CONFIG.ROLLBACK` | previous snapshot exists and rollback allowed | no snapshot/mixed manual-review state | `IMPACT_PREVIEW` | Spusti canonical rollback apply run. |
| `config.refresh` | Obnovit účinný stav | `CONFIG.REFRESH` | always when authenticated | request pending | `NONE` | Nacte current desired/effective values a apply status. |

## Testy a API - `/tests-api`

Self-test katalog a skutecny API explorer nad produkcnim API rootem se stejnymi validacemi jako UI/chat.

**Panels:** OWNER API key summary; Operation catalog; OpenAPI/KCIP contracts; Test catalog; Running test progress; Results/evidence/logs/cleanup; API explorer; Response/raw meta viewer

**Required states:** LOADING, EMPTY, READY, PARTIAL, STALE_RECONNECTING, ERROR, SUCCESS

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `test.search` | Hledat test | `search` / `TEXT_1` | no | `BOUNDED_SEARCH_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Filtr suite/domain/object/endpoint/element. |
| `api.method` | HTTP metoda | `select` / `None` | yes | `OPERATION_CATALOG_METHOD` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Metoda API explorer requestu. |
| `api.path` | API cesta | `text` / `TEXT_1` | yes | `OPERATION_CATALOG_PATH` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Cesta pod canonical API root. |
| `api.headers` | Headers | `code` / `CODE_50` | no | `HEADER_SCHEMA + RESERVED_FIELD_REJECTION` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Volitelne request headers mimo server-managed auth fields. |
| `api.body` | JSON body | `code` / `CODE_50` | no | `OPERATION_JSON_SCHEMA` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Request body dle operation schema. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `test.runAll` | Spustit vše | `SELFTEST.RUN_ALL` | no conflicting exclusive run and platform admission ready | exclusive run/recovery barrier | `NONE` | Spusti cely canonical self-test catalog. |
| `test.runSelected` | Spustit vybrané | `SELFTEST.RUN_SELECTED` | selection valid | empty/invalid selection | `NONE` | Spusti selected suite/domain/object/endpoint/element. |
| `test.cancel` | Zrušit test | `SELFTEST.CANCEL` | run cancellable | terminal/noncancellable | `NONE` | Canonical cancel current test run. |
| `api.execute` | Odeslat API request | `API.EXPLORER_EXECUTE` | method/path/body valid and operation exists | invalid/unknown operation/reserved fields | `NONE` | Provede skutecny request pres canonical API boundary. |
| `test.export` | Exportovat evidence | `SELFTEST.EXPORT` | completed/current run has evidence | no evidence | `NONE` | Export test run evidence/logs/artifacts. |

## Bezpečnost - `/security`

Zabezpeceni jedine pevne identity, MFA, recovery, sessions a platform security evidence; zadna sprava uzivatelu/roli.

**Panels:** Identity/password source; MFA/recovery; Sessions; Login history; Security events; Rate limits; Certificates; Master key status; CSP/headers; Dependency audit; Host preflight; Logs/audit

**Required states:** LOADING, EMPTY, READY, PARTIAL, STALE_RECONNECTING, ERROR, SUCCESS

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `security.username` | Username | `readonly` / `TEXT_1` | no | `READ_ONLY_SINGLETON` | `NEVER` / `SERVER_PROJECTION` | Nemenny KRMAR78 zobrazeny pouze read-only. |
| `security.passwordSource` | Zdroj hesla | `readonly` / `TEXT_1` | no | `READ_ONLY` | `NEVER` / `SERVER_PROJECTION` | Zobrazi deployment-managed PASS source a posledni sync metadata, nikoli edit hesla. |
| `security.sessionFilter` | Relace | `select` / `None` | no | `SESSION_ID` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Vyber konkretní aktivni/historicke relace pro detail/revokaci. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `security.mfaEnroll` | Nastavit MFA | `AUTH.MFA_ENROLL` | MFA enrollment permitted/current session reauthenticated | not permitted/re-auth required | `NONE` | Zahaji/obnovi MFA enrollment podle auth state. |
| `security.mfaReset` | Resetovat MFA | `AUTH.MFA_RESET` | current session reauthenticated and operation allowed | reauth missing/pending | `EXPLICIT_CONFIRM` | Canonical reset s re-auth a auditem. |
| `security.recovery` | Zobrazit recovery stav | `AUTH.RECOVERY_VIEW` | session meets sensitivity guard | reauth required | `NONE` | Zobrazi metadata/reveal podle recovery contractu. |
| `security.revokeSession` | Revokovat relaci | `AUTH.SESSION_REVOKE` | selected revocable session exists | no selection/already revoked | `EXPLICIT_CONFIRM` | Revokuje selected web session. |
| `security.revokeOthers` | Odhlásit ostatní relace | `AUTH.SESSIONS_REVOKE_OTHERS` | other active sessions exist | none exist | `EXPLICIT_CONFIRM` | Revokuje vsechny krome current. |
| `security.revokeAll` | Odhlásit všechny relace | `AUTH.SESSIONS_REVOKE_ALL` | authenticated/re-authenticated | guard not met | `EXPLICIT_CONFIRM` | Revokuje vsechny vcetne current podle exact contractu. |
| `security.changePassword` | Změnit heslo v aplikaci | `FORBIDDEN` | NEVER | ALWAYS | `NONE` | Tato akce NESMI existovat; heslo se meni v GitHub Actions PASS. |

## Releases a provoz - `/releases`

Application/component releases, pointers, deployment, health, migrations, backups, acceptance a rollback evidence.

**Panels:** Release list; Current pointer summary; Build/source/digest detail; Deployment timeline; Health/readiness; Rollback panel; Backups; Migrations; Services/systemd; Acceptance runs; Evidence/logs/audit

**Required states:** LOADING, EMPTY, READY, PARTIAL, STALE_RECONNECTING, ERROR, SUCCESS

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `release.search` | Hledat release | `search` / `TEXT_1` | no | `BOUNDED_SEARCH_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Filtr release/build/commit/component. |
| `release.kind` | Typ | `multiselect` / `None` | no | `RELEASE_KIND` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Application/component release filter. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `release.open` | Otevřít release | `RELEASE.OPEN` | release exists | missing release | `NONE` | Otevre exact release evidence/detail. |
| `release.activate` | Aktivovat | `RELEASE.ACTIVATE` | release VALIDATED and all promotion gates PASS | candidate not validated/stale deps/acceptance fail | `NONE` | Promotion/activation pouze pres canonical readiness/acceptance gate. |
| `release.rollback` | Rollback | `RELEASE.ROLLBACK` | valid rollback target and migration/runtime safety PASS | no valid point OR incompatible state | `IMPACT_PREVIEW` | Atomicky prepne na verified rollback point a overi postconditions. |
| `release.backup` | Spustit backup | `BACKUP.RUN` | backup admission ready | backup conflict/capacity/recovery barrier | `NONE` | Canonical local backup podle policy. |
| `release.restore` | Obnovit ze zálohy | `BACKUP.RESTORE` | selected backup verified and restore preflight PASS | unverified/stale/incompatible backup | `MANDATORY_IMPACT_PREVIEW` | Restore pouze pres recovery barrier a production contract. |
| `release.acceptance` | Spustit acceptance | `ACCEPTANCE.RUN` | release deployed/candidate environment ready | environment not ready/run active | `NONE` | Production-shaped acceptance run. |

## Command palette - `GLOBAL_OVERLAY`

Globalni navigace, hledani objektu a vykonani stejnych canonical object actions bez alternativni logiky.

**Panels:** Search input; Grouped navigation results; Object results; Action results with enabled/disabled reason; Keyboard hint/footer

**Required states:** LOADING, EMPTY, READY, PARTIAL, STALE_RECONNECTING, ERROR, SUCCESS

### Fields

| ID | Label | Type/profile | Required | Validation | Editability/source | Purpose |
|---|---|---|---:|---|---|---|
| `palette.query` | Příkaz nebo hledání | `search` / `TEXT_1` | yes | `BOUNDED_QUERY` | `ALWAYS_WHEN_SECTION_EDITABLE` / `OWNER_INPUT` | Jednoradkovy fuzzy/fulltext dotaz na navigation/object/action. |

### Actions

| ID | Label | Operation binding | Enabled when | Disabled when | Confirm | Purpose |
|---|---|---|---|---|---|---|
| `palette.execute` | Provést | `ACTION_REGISTRY.EXECUTE` | one result selected and action enabled | no selection OR action disabled; reason visible | `NONE` | Otevre route nebo spusti selected action pres central action registry. |
| `palette.close` | Zavřít | `UI.OVERLAY_CLOSE` | always | never | `NONE` | Zavre overlay bez side effectu. |

