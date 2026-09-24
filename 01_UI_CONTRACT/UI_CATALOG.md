# KájovoCML NG — UI katalog

Odvozený pohled kanonického vloženého registru. Backendové vazby určuje vložený registr `closure/contracts/ui-action-resolution.json`.

## Prihlaseni

`auth.login` · `/login`

Overit jedinou pevnou OWNER identitu bez napovedy username a bez user-management vetve.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `login.submit` — Prihlasit se | `owner.auth.login` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## MFA / enrollment / recovery

`auth.mfa` · `/login/mfa`

Dokoncit povinne TOTP MFA nebo jednorazovy recovery flow pred vznikem plne OWNER session.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `mfa.verify` — Ověřit | `owner.auth.loginMfa` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `mfa.showSeed` — Zobrazit ruční seed | `owner.mfa.enroll` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `mfa.copyRecovery` — Kopírovat recovery kódy | `CLIENT_ONLY` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Centrální chat

`central.chat` · `/chat`

Jednotne konverzacni rozhrani pro dotazy, prikazy, diagnostiku, generation a browser spolupraci.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `chat.new` — Nová konverzace | `chat.conversation.create` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `chat.send` — Odeslat | `chat.ask` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `chat.steer` — Upravit směr | `chat.turn.steer` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `chat.cancel` — Zrušit běh | `chat.conversation.cancel` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `chat.openWeb` — Otevřít web | `chat.browser.session.create / chat.browser.session.attach` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `chat.takeover` — Převzít ovládání | `chat.browser.control.acquire` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `chat.returnAi` — Vrátit AI | `chat.browser.control.returnToAi` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `chat.pickTarget` — Vybrat prvek | `CLIENT_ONLY` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `chat.loginHuman` — Přihlásit se | `chat.browser.control.acquire` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `chat.saveAccount` — Uložit účet | `browser.account.save` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `chat.closeBrowser` — Zavřít relaci | `browser.session.close` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Dashboard

`dashboard` · `/dashboard`

Zobrazit a ovladat zivou topologii komponent, vazeb, portu, secrets, external targetu a runtime udalosti.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `dashboard.fit` — Přizpůsobit | `CLIENT_ONLY` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `dashboard.connect` — Propojit | `binding.create` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `dashboard.disconnect` — Odpojit | `binding.remove` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `dashboard.bindSecret` — Připojit secret | `secret.bind` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `dashboard.activate` — Aktivovat | `component.activate` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `dashboard.enable` — Zapnout | `component.enable` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `dashboard.disable` — Vypnout | `component.disable` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `dashboard.repair` — Opravit | `component.repair.request` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `dashboard.recertify` — Recertifikovat | `component.recertify` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `dashboard.e2e` — Spustit E2E | `component.e2e.start` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `dashboard.detail` — Otevřít detail | `component.read` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.history` — Zobrazit historii | `log.query` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.lastRun` — Poslední běh | `agent.run.list / browser.automation.run.list / generation.job.list / selfTest.run.list / acceptance.run.list / runtime.execution.list` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.inputs` — Zobrazit vstupy | `log.query` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.outputs` — Zobrazit výstupy | `log.query` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.files` — Zobrazit soubory | `generation.artifact.list / browser.automation.artifact.list / browser.session.artifact.list` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.contextChat` — Zeptat se v chatu | `chat.conversation.create` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.remove` — Odstranit prvek | `component.deregister` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.start` — Spustit prvek | `runtime.instance.start` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.stop` — Zastavit prvek | `runtime.stop` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.restart` — Restartovat prvek | `runtime.instance.restart` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.status` — Zkontrolovat stav | `component.state.request` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.logs` — Zobrazit log | `log.query` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.copy` — Kopírovat data | `CLIENT_ONLY` | AVAILABLE | CLIENT_ACTION_CARD |

## Generování

`generation` · `/generation`

Od OWNER zadani pres diskusi/specifikaci az po validovany, aktivovany a monitorovany vysledek bez moznosti obejit blocking gate.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `gen.create` — Nové zadání | `generation.job.create` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `gen.send` — Odeslat | `generation.message.append` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `gen.steer` — Upravit směr | `generation.turn.interrupt` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `gen.approveSpec` — Schválit specifikaci | `generation.spec.approve` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `gen.resolveBlocker` — Vyřešit blocker | `generation.blocker.resolve` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `gen.retry` — Opakovat | `generation.job.retry` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `gen.cancel` — Zrušit | `generation.job.cancel` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `gen.selftest` — Spustit self-test | `selfTest.run.start` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `gen.bypass` — Obejít blokaci | `FORBIDDEN` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `gen.editSpec` — Upravit zadání | `generation.spec.propose` | AVAILABLE | CANONICAL_DISPATCH |
| `gen.reviewSpec` — Zkontrolovat zadání | `generation.spec.precheck` | AVAILABLE | CANONICAL_DISPATCH |

## AI agenti

`agents` · `/agents`

Katalog, revision editor, tool/handoff/browser bindingy, run console, eval a lifecycle AI agentu.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `agent.newRevision` — Nová revize | `CLIENT_ONLY` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `agent.saveRevision` — Uložit revizi | `agent.revision.publish` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `agent.validate` — Validovat | `agent.revision.validate` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `agent.run` — Spustit | `agent.run.start` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `agent.pause` — Pozastavit | `agent.run.pause` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `agent.resume` — Pokračovat | `agent.run.resume` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `agent.cancel` — Zrušit | `agent.run.cancel` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `agent.activate` — Aktivovat | `agent.revision.activate` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `agent.rollback` — Rollback | `agent.revision.activate` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## MCP servery a nástroje

`mcp` · `/mcp`

MCP katalog, protocol/wire inspector, request builder, MRTR/subscription/task konzole a activation diagnostika.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `mcp.discover` — server/discover | `mcp.server.discover` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `mcp.send` — Odeslat request | `mcp.server.discover / mcp.tools.list / mcp.tools.call / mcp.resources.list / mcp.resources.templates.list / mcp.resources.read / mcp.prompts.list / mcp.prompts.get / mcp.subscription.listen / mcp.task.get / mcp.task.update / mcp.task.cancel` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `mcp.cancel` — Zrušit | `mcp.tools.cancel / mcp.task.cancel / mcp.subscription.cancel` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `mcp.verify` — Ověřit | `mcp.wire.verify` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `mcp.activate` — Aktivovat | `component.activate` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `mcp.repair` — Opravit | `component.repair.request` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Browser relace a automatizace

`browser` · `/browser`

Globalni inventory browser sessions, live preview, human handoff, visual collaboration, teaching a deterministic automation lifecycle.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `browser.new` — Nová relace | `browser.session.create` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `browser.navigate` — Otevřít URL | `browser.action.start` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `browser.takeover` — Převzít ovládání | `browser.control.acquire` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `browser.returnAi` — Vrátit AI | `browser.control.transfer` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `browser.modeBrowse` — Procházet | `CLIENT_ONLY` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `browser.modeMarkup` — Označit | `CLIENT_ONLY` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `browser.modeTarget` — Vybrat prvek | `CLIENT_ONLY` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `browser.modePointer` — Ukazatel | `CLIENT_ONLY` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `browser.annotationCommit` — Uložit označení | `browser.annotation.create` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `browser.focusAi` — Požádat AI: zaměř se sem | `browser.focus.request` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `browser.focusOwner` — OWNER: podívej se sem | `browser.focus.request` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `browser.saveAccount` — Uložit účet | `browser.account.save` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `browser.close` — Zavřít relaci | `browser.session.close` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `browser.teach` — Vytvořit automatizaci | `browser.automation.createFromTeaching` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Registrované prvky

`registered` · `/registered`

Provozni zkraceny prehled vsech aktivnich/registrovanych objektu a rychlych akci.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `registered.open` — Otevřít detail | `component.read / agent.definition.read / mcp.catalog.tool.read / browser.automation.read / external.target.read / secret.metadata.read` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `registered.enable` — Zapnout | `component.enable / browser.automation.enable` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `registered.disable` — Vypnout | `component.disable / browser.automation.disable` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `registered.repair` — Opravit | `component.repair.request / browser.automation.repair / agent.repair.request` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Katalog komponent

`components` · `/components`

Plny registr komponent, revisions, releases, runtime, contracts, relations, bindings a lifecycle operaci.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `component.register` — Registrovat | `component.register` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `component.generate` — Generovat | `generation.job.create` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `component.import` — Importovat | `component.import` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `component.export` — Exportovat | `component.export` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `component.validate` — Validovat | `component.validate` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `component.verify` — Ověřit | `component.verify` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `component.activate` — Aktivovat | `component.activate` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `component.rollback` — Rollback | `component.rollback` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `component.archive` — Archivovat | `component.retire` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `component.deregister` — Deregistrovat | `component.deregister` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Externí systémy

`external` · `/external`

Sprava external targetu, auth bindingu, inbound endpointu, outbound calls, webhooku, circuit breakeru a jejich monitoringu.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `external.save` — Uložit target | `external.target.create / external.target.patch` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `external.test` — Otestovat request | `external.target.test` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `external.challenge` — Otestovat challenge | `external.webhook.test` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `external.circuitOpen` — Otevřít circuit | `external.circuit.open` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `external.circuitClose` — Zavřít circuit | `external.circuit.close` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `external.circuitReset` — Resetovat circuit | `external.circuit.reset` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Monitoring

`monitoring` · `/monitoring`

Probes, SLO, heartbeat, alerts, scheduler, resource metrics, runbook, repair a recertification.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `monitoring.ack` — Potvrdit alert | `monitor.alert.acknowledge` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `monitoring.suppress` — Potlačit | `monitor.alert.suppress` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `monitoring.close` — Uzavřít alert | `monitor.alert.close` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `monitoring.repair` — Opravit | `component.repair.request` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `monitoring.probe` — Spustit kontrolu | `monitor.probe.request` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `monitoring.saveProfile` — Uložit profil | `monitor.profile.replace` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## API klíč a runtime vazby

`runtime-access` · `/runtime-access`

Sprava singleton OWNER API key a detailni zobrazeni runtime/exact contract/Secret/external/bridge vazeb bez permission registry.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `runtime.revealKey` — Zobrazit API klíč | `ownerApiKey.reveal` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `runtime.copyKey` — Kopírovat API klíč | `CLIENT_ONLY` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `runtime.rotateKey` — Rotovat API klíč | `ownerApiKey.rotate` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `runtime.testBinding` — Otestovat vazbu | `binding.test` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `runtime.revokeBridge` — Revokovat bridge certifikát | `browser.bridge.revoke` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Secrets a hesla

`secrets` · `/secrets`

Plny OWNER Password Manager nad Secret Managerem vcetne hodnot, verzi, rotace, bindings, usage a auditu.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `secret.create` — Nový secret | `secret.create` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `secret.reveal` — Zobrazit | `secret.value.read` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `secret.copy` — Kopírovat | `CLIENT_ONLY` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `secret.newVersion` — Nová verze | `secret.version.create` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `secret.activateVersion` — Aktivovat verzi | `secret.version.activate` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `secret.rotate` — Rotovat | `secret.rotate` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `secret.bind` — Připojit | `secret.bind` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `secret.unbind` — Odpojit | `secret.unbind` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `secret.delete` — Smazat | `secret.delete` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `secret.export` — Exportovat | `secret.export` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `secret.testResolve` — Test resolve | `secret.resolve.test` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Audit a logy

`audit` · `/audit`

Zive i historicke logy, audit chain, diffy, payloady, correlation graph, export a integrity.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `audit.live` — Živý přenos | `log.stream` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `audit.search` — Hledat | `log.query` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `audit.saveQuery` — Uložit dotaz | `audit.savedQuery.create` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `audit.exportJsonl` — Export JSONL | `log.export` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `audit.exportCsv` — Export CSV | `log.export` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `audit.verify` — Ověřit integritu | `audit.integrity.verify` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Konfigurace

`configuration` · `/configuration`

Jednotny registr OWNER-input/preference/system-managed parametru s desired/effective version, aplikaci, verification a rollbackem.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `config.edit` — Upravit | `CLIENT_ONLY` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `config.apply` — Použít | `config.apply` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `config.cancelEdit` — Zrušit změny | `CLIENT_ONLY` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `config.rollback` — Vrátit předchozí | `config.rollback` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `config.refresh` — Obnovit účinný stav | `config.setting.read` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Testy a API

`tests-api` · `/tests-api`

Self-test katalog a skutecny API explorer nad produkcnim API rootem se stejnymi validacemi jako UI/chat.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `test.runAll` — Spustit vše | `selfTest.run.start` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `test.runSelected` — Spustit vybrané | `selfTest.run.start` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `test.cancel` — Zrušit test | `selfTest.run.cancel` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `api.execute` — Odeslat API request | `acceptance.run.cancel / acceptance.run.list / acceptance.run.start / agent.approval.approve / agent.approval.reject / agent.definition.create / agent.definition.list / agent.definition.patch / agent.definition.read / agent.eval.start / agent.evalRun.cases.read / agent.evalRun.read / agent.evalSuite.create / agent.evalSuite.list / agent.evalSuite.read / agent.memory.item.remove / agent.memory.read / agent.memory.write / agent.message.append / agent.repair.request / agent.revision.activate / agent.revision.compatibility / agent.revision.guardrail.list / agent.revision.handoff.list / agent.revision.list / agent.revision.promotionGate.list / agent.revision.publish / agent.revision.read / agent.revision.toolBinding.list / agent.revision.toolBinding.preview / agent.revision.validate / agent.revision.verify / agent.run.approval.list / agent.run.cancel / agent.run.checkpoint.list / agent.run.events.read / agent.run.handoff.list / agent.run.list / agent.run.pause / agent.run.resume / agent.run.start / agent.run.status / agent.run.toolCall.list / agent.session.close / agent.session.compact / agent.session.items.read / agent.session.list / agent.session.read / agent.trigger.create / agent.trigger.list / agent.trigger.patch / agent.trigger.remove / agentic.security.event.list / agentic.security.event.read / agentic.security.evidence.export / audit.archive.list / audit.event.list / audit.event.read / audit.integrity.read / audit.integrity.verify / audit.savedQuery.create / authority.actionPlan.list / authority.context.read / authority.intent.read / authority.lineage.graph / authority.lineage.resolve / backup.create / backup.list / backup.restore / backup.verify / binding.create / binding.list / binding.preview / binding.read / binding.remove / binding.replace / binding.test / browser.account.list / browser.account.logout / browser.account.metadata.patch / browser.account.read / browser.account.reauthenticate / browser.account.save / browser.account.verify / browser.action.attempt.list / browser.action.cancel / browser.action.reconcile / browser.action.resolveOutcome / browser.action.start / browser.action.status / browser.annotation.create / browser.auth.verify / browser.authAttempt.list / browser.automation.activate / browser.automation.artifact.list / browser.automation.artifact.read / browser.automation.authBinding.create / browser.automation.authBinding.list / browser.automation.cancel / browser.automation.create / browser.automation.createFromTeaching / browser.automation.disable / browser.automation.enable / browser.automation.list / browser.automation.metadata.patch / browser.automation.preflight / browser.automation.read / browser.automation.reauthenticate / browser.automation.reconcile / browser.automation.repair / browser.automation.revision.list / browser.automation.revision.publish / browser.automation.revision.read / browser.automation.rollback / browser.automation.run / browser.automation.run.list / browser.automation.run.read / browser.automation.run.step.list / browser.automation.schedule.create / browser.automation.schedule.list / browser.automation.schedule.patch / browser.automation.verify / browser.bridge.assign / browser.bridge.connection.list / browser.bridge.enroll / browser.bridge.list / browser.bridge.profile.list / browser.bridge.read / browser.bridge.release / browser.bridge.revoke / browser.bridge.rotateCertificate / browser.bridge.test / browser.challenge.resolve / browser.cleanup.resume / browser.confirmation.respond / browser.control.acquire / browser.control.read / browser.control.release / browser.control.transfer / browser.control.transfer.list / browser.dialog.respond / browser.document.list / browser.download.list / browser.focus.request / browser.frame.list / browser.navigation.list / browser.observation.request / browser.operationScope.set / browser.page.activate / browser.page.close / browser.page.list / browser.page.open / browser.page.read / browser.permission.respond / browser.preview.latest / browser.preview.resync / browser.preview.ticket.create / browser.research.cancel / browser.research.extract / browser.research.plan / browser.research.publish / browser.research.start / browser.research.verify / browser.run.manualReview / browser.runtimeBuild.verify / browser.session.artifact.list / browser.session.attach / browser.session.close / browser.session.create / browser.session.credentials.submit / browser.session.events.read / browser.session.list / browser.session.pause / browser.session.recover / browser.session.resume / browser.session.snapshot.read / browser.session.state / browser.state.activate / browser.state.capture / browser.state.invalidate / browser.state.verify / browser.stateBundle.list / browser.stateBundle.read / browser.target.list / browser.target.pick / browser.target.revalidate / browser.teaching.compile / browser.teaching.list / browser.teaching.read / browser.teaching.start / browser.teaching.stop / browser.upload.create / chat.ask / chat.browser.control.acquire / chat.browser.control.returnToAi / chat.browser.directive.compile / chat.browser.session.attach / chat.browser.session.create / chat.browser.session.list / chat.browser.target.attach / chat.command.execute / chat.conversation.cancel / chat.conversation.create / chat.conversation.list / chat.conversation.read / chat.message.append / chat.message.list / chat.response.stream / chat.turn.steer / component.activate / component.deregister / component.deregistration.preview / component.disable / component.e2e.start / component.enable / component.export / component.heartbeat.challenge / component.import / component.list / component.metadata.patch / component.quarantine / component.read / component.recertify / component.register / component.release.list / component.repair.request / component.restore / component.retire / component.revision.list / component.revision.publish / component.revision.read / component.rollback / component.state.request / component.suspend / component.suspension.set / component.usage.read / component.validate / component.verify / config.apply / config.export / config.import / config.rollback / config.setting.list / config.setting.read / config.setting.replace / config.setting.reset / config.validate / dashboard.events.read / dashboard.identityCards.list / dashboard.layout.replace / dashboard.topology.read / deployment.list / external.authBinding.create / external.authBinding.list / external.authBinding.patch / external.circuit.close / external.circuit.open / external.circuit.reset / external.request.list / external.target.create / external.target.list / external.target.patch / external.target.read / external.target.test / external.targetBinding.create / external.targetBinding.list / external.targetBinding.remove / external.webhook.list / external.webhook.test / generation.activationSet.read / generation.artifact.list / generation.artifactManifest.list / generation.authority.read / generation.blocker.list / generation.blocker.resolve / generation.capability.resolve / generation.capabilitySnapshot.list / generation.checkpoint.list / generation.contractCandidate.list / generation.fact.list / generation.job.cancel / generation.job.create / generation.job.events.read / generation.job.followUp / generation.job.list / generation.job.read / generation.job.resume / generation.job.retry / generation.job.snapshot.read / generation.message.append / generation.message.list / generation.ownerDecision.list / generation.phase.list / generation.phase.read / generation.plan.list / generation.plan.read / generation.plan.validate / generation.research.bind / generation.research.refresh / generation.source.add / generation.source.list / generation.source.read / generation.spec.approve / generation.spec.current / generation.spec.precheck / generation.spec.revision.list / generation.spec.revision.read / generation.toolEvent.list / generation.turn.interrupt / generation.turn.list / generation.validation.run / generation.validationRun.list / generation.validationRun.read / generation.workspace.file.list / generation.workspace.patch.list / generation.workspace.revision.list / generation.workspace.revision.read / log.correlation.read / log.export / log.query / log.stream / maintenance.service.restart / mcp.alias.create / mcp.alias.list / mcp.alias.preview / mcp.alias.remove / mcp.callRun.events.read / mcp.callRun.list / mcp.callRun.outcome.read / mcp.callRun.read / mcp.catalog.prompt.list / mcp.catalog.prompt.read / mcp.catalog.resource.list / mcp.catalog.resource.read / mcp.catalog.resourceTemplate.list / mcp.catalog.resourceTemplate.read / mcp.catalog.tool.callers.list / mcp.catalog.tool.list / mcp.catalog.tool.read / mcp.catalog.tool.register / mcp.catalog.tool.revision.list / mcp.catalog.tool.usage.read / mcp.contract.compatibility / mcp.contract.validate / mcp.discovery.snapshot / mcp.discovery.snapshot.diff / mcp.discovery.snapshot.list / mcp.discovery.snapshot.read / mcp.era.probe / mcp.input.respond / mcp.inputExchange.list / mcp.inputExchange.read / mcp.registrationProbe.list / mcp.requestEvent.list / mcp.requestEvent.raw.read / mcp.requestEvent.read / mcp.stateHandle.close / mcp.stateHandle.list / mcp.stateHandle.read / mcp.subscription.cancel / mcp.subscription.list / mcp.subscription.notifications.read / mcp.subscription.read / mcp.task.events.read / mcp.task.list / mcp.tools.cancel / mcp.tools.reconcile / mcp.wire.verify / monitor.alert.acknowledge / monitor.alert.close / monitor.alert.delivery.list / monitor.alert.list / monitor.alert.read / monitor.alert.suppress / monitor.channel.test / monitor.overview.read / monitor.probe.list / monitor.probe.request / monitor.profile.list / monitor.profile.replace / monitor.stateHistory.read / openai.modelCall.checkpoint.list / openai.modelCall.continuation.list / openai.modelCall.events.read / openai.modelCall.list / openai.modelCall.outputItem.list / openai.modelCall.read / openai.modelCall.reconcile / openai.modelCall.requestCancel / openai.modelCall.requestDescriptor.read / openai.modelCall.resumeStream / openai.modelCall.retrieve / openai.modelCall.toolDispatch.list / openai.modelCapability.list / openai.modelCapability.read / openai.modelCapability.refresh / operation.catalog.list / operation.invoke / owner.auth.logout / owner.mfa.enroll / owner.mfa.reset / owner.mfa.verify / owner.recoveryCodes.rotate / owner.security.read / owner.session.current / owner.session.list / owner.session.reauthenticate / owner.session.revoke / owner.session.revokeAll / owner.session.revokeOthers / ownerApiKey.read / ownerApiKey.reveal / ownerApiKey.rotate / ownerApiKey.session.exchange / ownerApiKey.usage.read / provenance.content.graph / provenance.content.read / provenance.valueDerivation.list / release.activate / release.list / release.read / release.rollback / runtime.boundary.evidence.read / runtime.boundary.verify / runtime.call.list / runtime.cleanup.read / runtime.connection.inspect / runtime.connection.list / runtime.drain / runtime.execution.list / runtime.execution.read / runtime.instance.list / runtime.instance.read / runtime.instance.reconcile / runtime.instance.restart / runtime.process.list / runtime.sandbox.read / runtime.workerHeartbeat.list / secret.bind / secret.binding.bulkApply / secret.binding.bulkPreview / secret.binding.list / secret.create / secret.delete / secret.export / secret.import / secret.list / secret.metadata.patch / secret.metadata.read / secret.password.generate / secret.resolve.test / secret.rotate / secret.unbind / secret.usage.read / secret.useContext.list / secret.value.read / secret.version.activate / secret.version.create / secret.version.list / selfTest.catalog.list / selfTest.evidence.export / selfTest.evidence.read / selfTest.faultCatalog.list / selfTest.model.list / selfTest.registeredElement.run / selfTest.run.cancel / selfTest.run.cleanup / selfTest.run.events.read / selfTest.run.history.read / selfTest.run.list / selfTest.run.replay / selfTest.run.shrink / selfTest.run.start / selfTest.run.status / system.capability.list / system.closure.read / system.health.read / system.readiness.read / system.recovery.read / system.version.read` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `test.export` — Exportovat evidence | `selfTest.evidence.export` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Bezpečnost

`security` · `/security`

Zabezpeceni jedine pevne identity, MFA, recovery, sessions a platform security evidence; zadna sprava uzivatelu/roli.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `security.mfaEnroll` — Nastavit MFA | `owner.mfa.enroll` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `security.mfaReset` — Resetovat MFA | `owner.mfa.reset` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `security.recovery` — Zobrazit recovery stav | `owner.security.read` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `security.revokeSession` — Revokovat relaci | `owner.session.revoke` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `security.revokeOthers` — Odhlásit ostatní relace | `owner.session.revokeOthers` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `security.revokeAll` — Odhlásit všechny relace | `owner.session.revokeAll` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `security.changePassword` — Změnit heslo v aplikaci | `FORBIDDEN` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Releases a provoz

`releases` · `/releases`

Application/component releases, pointers, deployment, health, migrations, backups, acceptance a rollback evidence.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `release.open` — Otevřít release | `release.read` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `release.activate` — Aktivovat | `release.activate` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `release.rollback` — Rollback | `release.rollback` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `release.backup` — Spustit backup | `backup.create` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `release.restore` — Obnovit ze zálohy | `backup.restore` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `release.acceptance` — Spustit acceptance | `acceptance.run.start` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

## Command palette

`command-palette` · `GLOBAL_OVERLAY`

Globalni navigace, hledani objektu a vykonani stejnych canonical object actions bez alternativni logiky.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `palette.execute` — Provést | `acceptance.run.cancel / acceptance.run.list / acceptance.run.start / agent.approval.approve / agent.approval.reject / agent.definition.create / agent.definition.list / agent.definition.patch / agent.definition.read / agent.eval.start / agent.evalRun.cases.read / agent.evalRun.read / agent.evalSuite.create / agent.evalSuite.list / agent.evalSuite.read / agent.memory.item.remove / agent.memory.read / agent.memory.write / agent.message.append / agent.repair.request / agent.revision.activate / agent.revision.compatibility / agent.revision.guardrail.list / agent.revision.handoff.list / agent.revision.list / agent.revision.promotionGate.list / agent.revision.publish / agent.revision.read / agent.revision.toolBinding.list / agent.revision.toolBinding.preview / agent.revision.validate / agent.revision.verify / agent.run.approval.list / agent.run.cancel / agent.run.checkpoint.list / agent.run.events.read / agent.run.handoff.list / agent.run.list / agent.run.pause / agent.run.resume / agent.run.start / agent.run.status / agent.run.toolCall.list / agent.session.close / agent.session.compact / agent.session.items.read / agent.session.list / agent.session.read / agent.trigger.create / agent.trigger.list / agent.trigger.patch / agent.trigger.remove / agentic.security.event.list / agentic.security.event.read / agentic.security.evidence.export / audit.archive.list / audit.event.list / audit.event.read / audit.integrity.read / audit.integrity.verify / audit.savedQuery.create / authority.actionPlan.list / authority.context.read / authority.intent.read / authority.lineage.graph / authority.lineage.resolve / backup.create / backup.list / backup.restore / backup.verify / binding.create / binding.list / binding.preview / binding.read / binding.remove / binding.replace / binding.test / browser.account.list / browser.account.logout / browser.account.metadata.patch / browser.account.read / browser.account.reauthenticate / browser.account.save / browser.account.verify / browser.action.attempt.list / browser.action.cancel / browser.action.reconcile / browser.action.resolveOutcome / browser.action.start / browser.action.status / browser.annotation.create / browser.auth.verify / browser.authAttempt.list / browser.automation.activate / browser.automation.artifact.list / browser.automation.artifact.read / browser.automation.authBinding.create / browser.automation.authBinding.list / browser.automation.cancel / browser.automation.create / browser.automation.createFromTeaching / browser.automation.disable / browser.automation.enable / browser.automation.list / browser.automation.metadata.patch / browser.automation.preflight / browser.automation.read / browser.automation.reauthenticate / browser.automation.reconcile / browser.automation.repair / browser.automation.revision.list / browser.automation.revision.publish / browser.automation.revision.read / browser.automation.rollback / browser.automation.run / browser.automation.run.list / browser.automation.run.read / browser.automation.run.step.list / browser.automation.schedule.create / browser.automation.schedule.list / browser.automation.schedule.patch / browser.automation.verify / browser.bridge.assign / browser.bridge.connection.list / browser.bridge.enroll / browser.bridge.list / browser.bridge.profile.list / browser.bridge.read / browser.bridge.release / browser.bridge.revoke / browser.bridge.rotateCertificate / browser.bridge.test / browser.challenge.resolve / browser.cleanup.resume / browser.confirmation.respond / browser.control.acquire / browser.control.read / browser.control.release / browser.control.transfer / browser.control.transfer.list / browser.dialog.respond / browser.document.list / browser.download.list / browser.focus.request / browser.frame.list / browser.navigation.list / browser.observation.request / browser.operationScope.set / browser.page.activate / browser.page.close / browser.page.list / browser.page.open / browser.page.read / browser.permission.respond / browser.preview.latest / browser.preview.resync / browser.preview.ticket.create / browser.research.cancel / browser.research.extract / browser.research.plan / browser.research.publish / browser.research.start / browser.research.verify / browser.run.manualReview / browser.runtimeBuild.verify / browser.session.artifact.list / browser.session.attach / browser.session.close / browser.session.create / browser.session.credentials.submit / browser.session.events.read / browser.session.list / browser.session.pause / browser.session.recover / browser.session.resume / browser.session.snapshot.read / browser.session.state / browser.state.activate / browser.state.capture / browser.state.invalidate / browser.state.verify / browser.stateBundle.list / browser.stateBundle.read / browser.target.list / browser.target.pick / browser.target.revalidate / browser.teaching.compile / browser.teaching.list / browser.teaching.read / browser.teaching.start / browser.teaching.stop / browser.upload.create / chat.ask / chat.browser.control.acquire / chat.browser.control.returnToAi / chat.browser.directive.compile / chat.browser.session.attach / chat.browser.session.create / chat.browser.session.list / chat.browser.target.attach / chat.command.execute / chat.conversation.cancel / chat.conversation.create / chat.conversation.list / chat.conversation.read / chat.message.append / chat.message.list / chat.response.stream / chat.turn.steer / component.activate / component.deregister / component.deregistration.preview / component.disable / component.e2e.start / component.enable / component.export / component.heartbeat.challenge / component.import / component.list / component.metadata.patch / component.quarantine / component.read / component.recertify / component.register / component.release.list / component.repair.request / component.restore / component.retire / component.revision.list / component.revision.publish / component.revision.read / component.rollback / component.state.request / component.suspend / component.suspension.set / component.usage.read / component.validate / component.verify / config.apply / config.export / config.import / config.rollback / config.setting.list / config.setting.read / config.setting.replace / config.setting.reset / config.validate / dashboard.events.read / dashboard.identityCards.list / dashboard.layout.replace / dashboard.topology.read / deployment.list / external.authBinding.create / external.authBinding.list / external.authBinding.patch / external.circuit.close / external.circuit.open / external.circuit.reset / external.request.list / external.target.create / external.target.list / external.target.patch / external.target.read / external.target.test / external.targetBinding.create / external.targetBinding.list / external.targetBinding.remove / external.webhook.list / external.webhook.test / generation.activationSet.read / generation.artifact.list / generation.artifactManifest.list / generation.authority.read / generation.blocker.list / generation.blocker.resolve / generation.capability.resolve / generation.capabilitySnapshot.list / generation.checkpoint.list / generation.contractCandidate.list / generation.fact.list / generation.job.cancel / generation.job.create / generation.job.events.read / generation.job.followUp / generation.job.list / generation.job.read / generation.job.resume / generation.job.retry / generation.job.snapshot.read / generation.message.append / generation.message.list / generation.ownerDecision.list / generation.phase.list / generation.phase.read / generation.plan.list / generation.plan.read / generation.plan.validate / generation.research.bind / generation.research.refresh / generation.source.add / generation.source.list / generation.source.read / generation.spec.approve / generation.spec.current / generation.spec.precheck / generation.spec.revision.list / generation.spec.revision.read / generation.toolEvent.list / generation.turn.interrupt / generation.turn.list / generation.validation.run / generation.validationRun.list / generation.validationRun.read / generation.workspace.file.list / generation.workspace.patch.list / generation.workspace.revision.list / generation.workspace.revision.read / log.correlation.read / log.export / log.query / log.stream / maintenance.service.restart / mcp.alias.create / mcp.alias.list / mcp.alias.preview / mcp.alias.remove / mcp.callRun.events.read / mcp.callRun.list / mcp.callRun.outcome.read / mcp.callRun.read / mcp.catalog.prompt.list / mcp.catalog.prompt.read / mcp.catalog.resource.list / mcp.catalog.resource.read / mcp.catalog.resourceTemplate.list / mcp.catalog.resourceTemplate.read / mcp.catalog.tool.callers.list / mcp.catalog.tool.list / mcp.catalog.tool.read / mcp.catalog.tool.register / mcp.catalog.tool.revision.list / mcp.catalog.tool.usage.read / mcp.contract.compatibility / mcp.contract.validate / mcp.discovery.snapshot / mcp.discovery.snapshot.diff / mcp.discovery.snapshot.list / mcp.discovery.snapshot.read / mcp.era.probe / mcp.input.respond / mcp.inputExchange.list / mcp.inputExchange.read / mcp.registrationProbe.list / mcp.requestEvent.list / mcp.requestEvent.raw.read / mcp.requestEvent.read / mcp.stateHandle.close / mcp.stateHandle.list / mcp.stateHandle.read / mcp.subscription.cancel / mcp.subscription.list / mcp.subscription.notifications.read / mcp.subscription.read / mcp.task.events.read / mcp.task.list / mcp.tools.cancel / mcp.tools.reconcile / mcp.wire.verify / monitor.alert.acknowledge / monitor.alert.close / monitor.alert.delivery.list / monitor.alert.list / monitor.alert.read / monitor.alert.suppress / monitor.channel.test / monitor.overview.read / monitor.probe.list / monitor.probe.request / monitor.profile.list / monitor.profile.replace / monitor.stateHistory.read / openai.modelCall.checkpoint.list / openai.modelCall.continuation.list / openai.modelCall.events.read / openai.modelCall.list / openai.modelCall.outputItem.list / openai.modelCall.read / openai.modelCall.reconcile / openai.modelCall.requestCancel / openai.modelCall.requestDescriptor.read / openai.modelCall.resumeStream / openai.modelCall.retrieve / openai.modelCall.toolDispatch.list / openai.modelCapability.list / openai.modelCapability.read / openai.modelCapability.refresh / operation.catalog.list / operation.invoke / owner.auth.logout / owner.mfa.enroll / owner.mfa.reset / owner.mfa.verify / owner.recoveryCodes.rotate / owner.security.read / owner.session.current / owner.session.list / owner.session.reauthenticate / owner.session.revoke / owner.session.revokeAll / owner.session.revokeOthers / ownerApiKey.read / ownerApiKey.reveal / ownerApiKey.rotate / ownerApiKey.session.exchange / ownerApiKey.usage.read / provenance.content.graph / provenance.content.read / provenance.valueDerivation.list / release.activate / release.list / release.read / release.rollback / runtime.boundary.evidence.read / runtime.boundary.verify / runtime.call.list / runtime.cleanup.read / runtime.connection.inspect / runtime.connection.list / runtime.drain / runtime.execution.list / runtime.execution.read / runtime.instance.list / runtime.instance.read / runtime.instance.reconcile / runtime.instance.restart / runtime.process.list / runtime.sandbox.read / runtime.workerHeartbeat.list / secret.bind / secret.binding.bulkApply / secret.binding.bulkPreview / secret.binding.list / secret.create / secret.delete / secret.export / secret.import / secret.list / secret.metadata.patch / secret.metadata.read / secret.password.generate / secret.resolve.test / secret.rotate / secret.unbind / secret.usage.read / secret.useContext.list / secret.value.read / secret.version.activate / secret.version.create / secret.version.list / selfTest.catalog.list / selfTest.evidence.export / selfTest.evidence.read / selfTest.faultCatalog.list / selfTest.model.list / selfTest.registeredElement.run / selfTest.run.cancel / selfTest.run.cleanup / selfTest.run.events.read / selfTest.run.history.read / selfTest.run.list / selfTest.run.replay / selfTest.run.shrink / selfTest.run.start / selfTest.run.status / system.capability.list / system.closure.read / system.health.read / system.readiness.read / system.recovery.read / system.version.read` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |
| `palette.close` — Zavřít | `CLIENT_ONLY` | NOT_DECLARED_IN_ACTION_RECORD | NOT_DECLARED_IN_ACTION_RECORD |

