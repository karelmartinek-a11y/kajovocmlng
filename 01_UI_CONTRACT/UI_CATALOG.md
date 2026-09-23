# KájovoCML NG — UI katalog

Odvozený pohled `ui/contracts/ui-control-registry.json`. Backend vazby určuje `closure/contracts/ui-action-resolution.json`.

## Prihlaseni

`auth.login` · `/login`

Overit jedinou pevnou OWNER identitu bez napovedy username a bez user-management vetve.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `login.submit` — Prihlasit se | `owner.auth.login` | PREAUTH_ONLY | PREAUTH_ONLY |

## MFA / enrollment / recovery

`auth.mfa` · `/login/mfa`

Dokoncit povinne TOTP MFA nebo jednorazovy recovery flow pred vznikem plne OWNER session.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `mfa.verify` — Ověřit | `owner.auth.loginMfa` | PREAUTH_ONLY | PREAUTH_ONLY |
| `mfa.showSeed` — Zobrazit ruční seed | `owner.mfa.enroll` | PREAUTH_ONLY | PREAUTH_ONLY |
| `mfa.copyRecovery` — Kopírovat recovery kódy | `CLIENT_ONLY` | PREAUTH_ONLY | PREAUTH_ONLY |

## Centrální chat

`central.chat` · `/chat`

Jednotne konverzacni rozhrani pro dotazy, prikazy, diagnostiku, generation a browser spolupraci.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `chat.new` — Nová konverzace | `chat.conversation.create` | AVAILABLE | CANONICAL_DISPATCH |
| `chat.send` — Odeslat | `chat.ask` | AVAILABLE | CANONICAL_DISPATCH |
| `chat.steer` — Upravit směr | `chat.turn.steer` | AVAILABLE | CANONICAL_DISPATCH |
| `chat.cancel` — Zrušit běh | `chat.conversation.cancel` | AVAILABLE | CANONICAL_DISPATCH |
| `chat.openWeb` — Otevřít web | `chat.browser.session.create / chat.browser.session.attach` | AVAILABLE | CANONICAL_DISPATCH |
| `chat.takeover` — Převzít ovládání | `chat.browser.control.acquire` | AVAILABLE | CANONICAL_DISPATCH |
| `chat.returnAi` — Vrátit AI | `chat.browser.control.returnToAi` | AVAILABLE | CANONICAL_DISPATCH |
| `chat.pickTarget` — Vybrat prvek | `CLIENT_ONLY` | AVAILABLE | CLIENT_ACTION_CARD |
| `chat.loginHuman` — Přihlásit se | `chat.browser.control.acquire` | AVAILABLE | CANONICAL_DISPATCH |
| `chat.saveAccount` — Uložit účet | `browser.account.save` | AVAILABLE | CANONICAL_DISPATCH |
| `chat.closeBrowser` — Zavřít relaci | `browser.session.close` | AVAILABLE | CANONICAL_DISPATCH |

## Dashboard

`dashboard` · `/dashboard`

Zobrazit a ovladat zivou topologii komponent, vazeb, portu, secrets, external targetu a runtime udalosti.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `dashboard.fit` — Přizpůsobit | `CLIENT_ONLY` | AVAILABLE | CLIENT_ACTION_CARD |
| `dashboard.connect` — Propojit | `binding.create` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.disconnect` — Odpojit | `binding.remove` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.bindSecret` — Připojit secret | `secret.bind` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.activate` — Aktivovat | `component.activate` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.enable` — Zapnout | `component.enable` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.disable` — Vypnout | `component.disable` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.repair` — Opravit | `component.repair.request` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.recertify` — Recertifikovat | `component.recertify` | AVAILABLE | CANONICAL_DISPATCH |
| `dashboard.e2e` — Spustit E2E | `component.e2e.start` | AVAILABLE | CANONICAL_DISPATCH |
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
| `gen.create` — Nové zadání | `generation.job.create` | AVAILABLE | CANONICAL_DISPATCH |
| `gen.send` — Odeslat | `generation.message.append` | AVAILABLE | CANONICAL_DISPATCH |
| `gen.steer` — Upravit směr | `generation.turn.interrupt` | AVAILABLE | CANONICAL_DISPATCH |
| `gen.approveSpec` — Schválit specifikaci | `generation.spec.approve` | AVAILABLE | CANONICAL_DISPATCH |
| `gen.resolveBlocker` — Vyřešit blocker | `generation.blocker.resolve` | AVAILABLE | CANONICAL_DISPATCH |
| `gen.retry` — Opakovat | `generation.job.retry` | AVAILABLE | CANONICAL_DISPATCH |
| `gen.cancel` — Zrušit | `generation.job.cancel` | AVAILABLE | CANONICAL_DISPATCH |
| `gen.selftest` — Spustit self-test | `selfTest.run.start` | AVAILABLE | CANONICAL_DISPATCH |
| `gen.bypass` — Obejít blokaci | `FORBIDDEN` | FORBIDDEN | FORBIDDEN |
| `gen.editSpec` — Upravit zadání | `generation.spec.propose` | AVAILABLE | CANONICAL_DISPATCH |
| `gen.reviewSpec` — Zkontrolovat zadání | `generation.spec.precheck` | AVAILABLE | CANONICAL_DISPATCH |

## AI agenti

`agents` · `/agents`

Katalog, revision editor, tool/handoff/browser bindingy, run console, eval a lifecycle AI agentu.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `agent.newRevision` — Nová revize | `CLIENT_ONLY` | AVAILABLE | CLIENT_ACTION_CARD |
| `agent.saveRevision` — Uložit revizi | `agent.revision.publish` | AVAILABLE | CANONICAL_DISPATCH |
| `agent.validate` — Validovat | `agent.revision.validate` | AVAILABLE | CANONICAL_DISPATCH |
| `agent.run` — Spustit | `agent.run.start` | AVAILABLE | CANONICAL_DISPATCH |
| `agent.pause` — Pozastavit | `agent.run.pause` | AVAILABLE | CANONICAL_DISPATCH |
| `agent.resume` — Pokračovat | `agent.run.resume` | AVAILABLE | CANONICAL_DISPATCH |
| `agent.cancel` — Zrušit | `agent.run.cancel` | AVAILABLE | CANONICAL_DISPATCH |
| `agent.activate` — Aktivovat | `agent.revision.activate` | AVAILABLE | CANONICAL_DISPATCH |
| `agent.rollback` — Rollback | `agent.revision.activate` | AVAILABLE | CANONICAL_DISPATCH |

## MCP servery a nástroje

`mcp` · `/mcp`

MCP katalog, protocol/wire inspector, request builder, MRTR/subscription/task konzole a activation diagnostika.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `mcp.discover` — server/discover | `mcp.server.discover` | AVAILABLE | CANONICAL_DISPATCH |
| `mcp.send` — Odeslat request | `mcp.server.discover / mcp.tools.list / mcp.tools.call / mcp.resources.list / mcp.resources.templates.list / mcp.resources.read / mcp.prompts.list / mcp.prompts.get / mcp.subscription.listen / mcp.task.get / mcp.task.update / mcp.task.cancel` | AVAILABLE | CANONICAL_DISPATCH |
| `mcp.cancel` — Zrušit | `mcp.tools.cancel / mcp.task.cancel / mcp.subscription.cancel` | AVAILABLE | CANONICAL_DISPATCH |
| `mcp.verify` — Ověřit | `mcp.wire.verify` | AVAILABLE | CANONICAL_DISPATCH |
| `mcp.activate` — Aktivovat | `component.activate` | AVAILABLE | CANONICAL_DISPATCH |
| `mcp.repair` — Opravit | `component.repair.request` | AVAILABLE | CANONICAL_DISPATCH |

## Browser relace a automatizace

`browser` · `/browser`

Globalni inventory browser sessions, live preview, human handoff, visual collaboration, teaching a deterministic automation lifecycle.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `browser.new` — Nová relace | `browser.session.create` | AVAILABLE | CANONICAL_DISPATCH |
| `browser.navigate` — Otevřít URL | `browser.action.start` | AVAILABLE | CANONICAL_DISPATCH |
| `browser.takeover` — Převzít ovládání | `browser.control.acquire` | AVAILABLE | CANONICAL_DISPATCH |
| `browser.returnAi` — Vrátit AI | `browser.control.transfer` | AVAILABLE | CANONICAL_DISPATCH |
| `browser.modeBrowse` — Procházet | `CLIENT_ONLY` | AVAILABLE | CLIENT_ACTION_CARD |
| `browser.modeMarkup` — Označit | `CLIENT_ONLY` | AVAILABLE | CLIENT_ACTION_CARD |
| `browser.modeTarget` — Vybrat prvek | `CLIENT_ONLY` | AVAILABLE | CLIENT_ACTION_CARD |
| `browser.modePointer` — Ukazatel | `CLIENT_ONLY` | AVAILABLE | CLIENT_ACTION_CARD |
| `browser.annotationCommit` — Uložit označení | `browser.annotation.create` | AVAILABLE | CANONICAL_DISPATCH |
| `browser.focusAi` — Požádat AI: zaměř se sem | `browser.focus.request` | AVAILABLE | CANONICAL_DISPATCH |
| `browser.focusOwner` — OWNER: podívej se sem | `browser.focus.request` | AVAILABLE | CANONICAL_DISPATCH |
| `browser.saveAccount` — Uložit účet | `browser.account.save` | AVAILABLE | CANONICAL_DISPATCH |
| `browser.close` — Zavřít relaci | `browser.session.close` | AVAILABLE | CANONICAL_DISPATCH |
| `browser.teach` — Vytvořit automatizaci | `browser.automation.createFromTeaching` | AVAILABLE | CANONICAL_DISPATCH |

## Registrované prvky

`registered` · `/registered`

Provozni zkraceny prehled vsech aktivnich/registrovanych objektu a rychlych akci.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `registered.open` — Otevřít detail | `component.read / agent.definition.read / mcp.catalog.tool.read / browser.automation.read / external.target.read / secret.metadata.read` | AVAILABLE | CANONICAL_DISPATCH |
| `registered.enable` — Zapnout | `component.enable / browser.automation.enable` | AVAILABLE | CANONICAL_DISPATCH |
| `registered.disable` — Vypnout | `component.disable / browser.automation.disable` | AVAILABLE | CANONICAL_DISPATCH |
| `registered.repair` — Opravit | `component.repair.request / browser.automation.repair / agent.repair.request / monitor.repair.enqueue` | AVAILABLE | CANONICAL_DISPATCH |

## Katalog komponent

`components` · `/components`

Plny registr komponent, revisions, releases, runtime, contracts, relations, bindings a lifecycle operaci.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `component.register` — Registrovat | `component.register` | AVAILABLE | CANONICAL_DISPATCH |
| `component.generate` — Generovat | `generation.job.create` | AVAILABLE | CANONICAL_DISPATCH |
| `component.import` — Importovat | `component.import` | AVAILABLE | CANONICAL_DISPATCH |
| `component.export` — Exportovat | `component.export` | AVAILABLE | CANONICAL_DISPATCH |
| `component.validate` — Validovat | `component.validate` | AVAILABLE | CANONICAL_DISPATCH |
| `component.verify` — Ověřit | `component.verify` | AVAILABLE | CANONICAL_DISPATCH |
| `component.activate` — Aktivovat | `component.activate` | AVAILABLE | CANONICAL_DISPATCH |
| `component.rollback` — Rollback | `component.rollback` | AVAILABLE | CANONICAL_DISPATCH |
| `component.archive` — Archivovat | `component.retire` | AVAILABLE | CANONICAL_DISPATCH |
| `component.deregister` — Deregistrovat | `component.deregister` | AVAILABLE | CANONICAL_DISPATCH |

## Externí systémy

`external` · `/external`

Sprava external targetu, auth bindingu, inbound endpointu, outbound calls, webhooku, circuit breakeru a jejich monitoringu.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `external.save` — Uložit target | `external.target.create / external.target.patch` | AVAILABLE | CANONICAL_DISPATCH |
| `external.test` — Otestovat request | `external.target.test` | AVAILABLE | CANONICAL_DISPATCH |
| `external.challenge` — Otestovat challenge | `external.webhook.test` | AVAILABLE | CANONICAL_DISPATCH |
| `external.circuitOpen` — Otevřít circuit | `external.circuit.open` | AVAILABLE | CANONICAL_DISPATCH |
| `external.circuitClose` — Zavřít circuit | `external.circuit.close` | AVAILABLE | CANONICAL_DISPATCH |
| `external.circuitReset` — Resetovat circuit | `external.circuit.reset` | AVAILABLE | CANONICAL_DISPATCH |

## Monitoring

`monitoring` · `/monitoring`

Probes, SLO, heartbeat, alerts, scheduler, resource metrics, runbook, repair a recertification.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `monitoring.ack` — Potvrdit alert | `monitor.alert.acknowledge` | AVAILABLE | CANONICAL_DISPATCH |
| `monitoring.suppress` — Potlačit | `monitor.alert.suppress` | AVAILABLE | CANONICAL_DISPATCH |
| `monitoring.close` — Uzavřít alert | `monitor.alert.close` | AVAILABLE | CANONICAL_DISPATCH |
| `monitoring.repair` — Opravit | `monitor.repair.enqueue` | AVAILABLE | CANONICAL_DISPATCH |
| `monitoring.probe` — Spustit kontrolu | `monitor.probe.request` | AVAILABLE | CANONICAL_DISPATCH |
| `monitoring.saveProfile` — Uložit profil | `monitor.profile.replace` | AVAILABLE | CANONICAL_DISPATCH |

## API klíč a runtime vazby

`runtime-access` · `/runtime-access`

Sprava singleton OWNER API key a detailni zobrazeni runtime/exact contract/Secret/external/bridge vazeb bez permission registry.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `runtime.revealKey` — Zobrazit API klíč | `ownerApiKey.reveal` | AVAILABLE | CANONICAL_DISPATCH |
| `runtime.copyKey` — Kopírovat API klíč | `CLIENT_ONLY` | AVAILABLE | CLIENT_ACTION_CARD |
| `runtime.rotateKey` — Rotovat API klíč | `ownerApiKey.rotate` | AVAILABLE | CANONICAL_DISPATCH |
| `runtime.testBinding` — Otestovat vazbu | `binding.test` | AVAILABLE | CANONICAL_DISPATCH |
| `runtime.revokeBridge` — Revokovat bridge certifikát | `browser.bridge.revoke` | AVAILABLE | CANONICAL_DISPATCH |

## Secrets a hesla

`secrets` · `/secrets`

Plny OWNER Password Manager nad Secret Managerem vcetne hodnot, verzi, rotace, bindings, usage a auditu.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `secret.create` — Nový secret | `secret.create` | AVAILABLE | CANONICAL_DISPATCH |
| `secret.reveal` — Zobrazit | `secret.value.read` | AVAILABLE | CANONICAL_DISPATCH |
| `secret.copy` — Kopírovat | `CLIENT_ONLY` | AVAILABLE | CLIENT_ACTION_CARD |
| `secret.newVersion` — Nová verze | `secret.version.create` | AVAILABLE | CANONICAL_DISPATCH |
| `secret.activateVersion` — Aktivovat verzi | `secret.version.activate` | AVAILABLE | CANONICAL_DISPATCH |
| `secret.rotate` — Rotovat | `secret.rotate` | AVAILABLE | CANONICAL_DISPATCH |
| `secret.bind` — Připojit | `secret.bind` | AVAILABLE | CANONICAL_DISPATCH |
| `secret.unbind` — Odpojit | `secret.unbind` | AVAILABLE | CANONICAL_DISPATCH |
| `secret.delete` — Smazat | `secret.delete` | AVAILABLE | CANONICAL_DISPATCH |
| `secret.export` — Exportovat | `secret.export` | AVAILABLE | CANONICAL_DISPATCH |
| `secret.testResolve` — Test resolve | `secret.resolve.test` | AVAILABLE | CANONICAL_DISPATCH |

## Audit a logy

`audit` · `/audit`

Zive i historicke logy, audit chain, diffy, payloady, correlation graph, export a integrity.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `audit.live` — Živý přenos | `log.stream` | AVAILABLE | CANONICAL_DISPATCH |
| `audit.search` — Hledat | `log.query` | AVAILABLE | CANONICAL_DISPATCH |
| `audit.saveQuery` — Uložit dotaz | `audit.savedQuery.create` | AVAILABLE | CANONICAL_DISPATCH |
| `audit.exportJsonl` — Export JSONL | `log.export` | AVAILABLE | CANONICAL_DISPATCH |
| `audit.exportCsv` — Export CSV | `log.export` | AVAILABLE | CANONICAL_DISPATCH |
| `audit.verify` — Ověřit integritu | `audit.integrity.verify` | AVAILABLE | CANONICAL_DISPATCH |

## Konfigurace

`configuration` · `/configuration`

Jednotny registr OWNER-input/preference/system-managed parametru s desired/effective version, aplikaci, verification a rollbackem.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `config.edit` — Upravit | `CLIENT_ONLY` | AVAILABLE | CLIENT_ACTION_CARD |
| `config.apply` — Použít | `config.apply` | AVAILABLE | CANONICAL_DISPATCH |
| `config.cancelEdit` — Zrušit změny | `CLIENT_ONLY` | AVAILABLE | CLIENT_ACTION_CARD |
| `config.rollback` — Vrátit předchozí | `config.rollback` | AVAILABLE | CANONICAL_DISPATCH |
| `config.refresh` — Obnovit účinný stav | `config.setting.read` | AVAILABLE | CANONICAL_DISPATCH |

## Testy a API

`tests-api` · `/tests-api`

Self-test katalog a skutecny API explorer nad produkcnim API rootem se stejnymi validacemi jako UI/chat.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `test.runAll` — Spustit vše | `selfTest.run.start` | AVAILABLE | CANONICAL_DISPATCH |
| `test.runSelected` — Spustit vybrané | `selfTest.run.start` | AVAILABLE | CANONICAL_DISPATCH |
| `test.cancel` — Zrušit test | `selfTest.run.cancel` | AVAILABLE | CANONICAL_DISPATCH |
| `api.execute` — Odeslat API request | `acceptance.run.cancel / acceptance.run.list / acceptance.run.start / agent.approval.approve / agent.approval.reject / agent.approval.request / agent.checkpoint.created / agent.definition.create / agent.definition.list / agent.definition.patch / agent.definition.read / agent.delegate.request / agent.delegate.result / agent.eval.result / agent.eval.start / agent.evalRun.cases.read / agent.evalRun.read / agent.evalSuite.create / agent.evalSuite.list / agent.evalSuite.read / agent.memory.item.remove / agent.memory.read / agent.memory.write / agent.message.append / agent.model.completed / agent.model.started / agent.repair.request / agent.revision.activate / agent.revision.compatibility / agent.revision.guardrail.list / agent.revision.handoff.list / agent.revision.list / agent.revision.promotionGate.list / agent.revision.publish / agent.revision.read / agent.revision.toolBinding.list / agent.revision.toolBinding.preview / agent.revision.validate / agent.revision.verify / agent.run.approval.list / agent.run.cancel / agent.run.checkpoint.list / agent.run.complete / agent.run.events.read / agent.run.fail / agent.run.handoff.list / agent.run.list / agent.run.manualReview / agent.run.pause / agent.run.resume / agent.run.start / agent.run.status / agent.run.toolCall.list / agent.session.close / agent.session.compact / agent.session.items.read / agent.session.list / agent.session.read / agent.state.report / agent.tool.failed / agent.tool.request / agent.tool.result / agent.trigger.create / agent.trigger.list / agent.trigger.patch / agent.trigger.remove / agentic.security.event.list / agentic.security.event.read / agentic.security.event.record / agentic.security.evidence.export / audit.archive.complete / audit.archive.enqueue / audit.archive.list / audit.event.append / audit.event.list / audit.event.read / audit.integrity.read / audit.integrity.verify / audit.savedQuery.create / audit.stream.ack / audit.stream.replay.request / audit.stream.replay.result / authority.actionPlan.compile / authority.actionPlan.list / authority.actionPlan.validate / authority.context.create / authority.context.read / authority.context.validate / authority.intent.compile / authority.intent.read / authority.intent.validate / authority.lineage.append / authority.lineage.graph / authority.lineage.resolve / backup.create / backup.list / backup.restore / backup.verify / binding.create / binding.list / binding.preview / binding.read / binding.remove / binding.replace / binding.test / browser.account.authEpoch.increment / browser.account.list / browser.account.logout / browser.account.metadata.patch / browser.account.read / browser.account.reauthenticate / browser.account.save / browser.account.verify / browser.action.attempt.list / browser.action.cancel / browser.action.complete / browser.action.dispatchPhase / browser.action.fail / browser.action.reconcile / browser.action.resolveOutcome / browser.action.start / browser.action.status / browser.annotation.create / browser.annotation.list / browser.annotation.reanchor / browser.annotation.tombstone / browser.artifact.created / browser.auth.verify / browser.authAttempt.list / browser.automation.activate / browser.automation.artifact.list / browser.automation.artifact.read / browser.automation.authBinding.create / browser.automation.authBinding.list / browser.automation.cancel / browser.automation.create / browser.automation.createFromTeaching / browser.automation.disable / browser.automation.enable / browser.automation.list / browser.automation.metadata.patch / browser.automation.preflight / browser.automation.read / browser.automation.reauthenticate / browser.automation.reconcile / browser.automation.repair / browser.automation.revision.list / browser.automation.revision.publish / browser.automation.revision.read / browser.automation.rollback / browser.automation.run / browser.automation.run.list / browser.automation.run.read / browser.automation.run.step.list / browser.automation.schedule.create / browser.automation.schedule.list / browser.automation.schedule.patch / browser.automation.verify / browser.bridge.assign / browser.bridge.connect / browser.bridge.connection.list / browser.bridge.enroll / browser.bridge.enrollment.complete / browser.bridge.list / browser.bridge.profile.list / browser.bridge.read / browser.bridge.release / browser.bridge.revoke / browser.bridge.rotateCertificate / browser.bridge.test / browser.challenge.required / browser.challenge.resolve / browser.cleanup.resume / browser.confirmation.respond / browser.control.acquire / browser.control.changed / browser.control.read / browser.control.release / browser.control.transfer / browser.control.transfer.list / browser.dialog.opened / browser.dialog.respond / browser.document.changed / browser.document.list / browser.download.list / browser.download.persist / browser.download.started / browser.download.verify / browser.focus.acknowledge / browser.focus.open / browser.focus.request / browser.focus.resolve / browser.frame.list / browser.frame.observed / browser.host.drain / browser.host.ready / browser.host.recover / browser.navigation.list / browser.navigation.observed / browser.observation.request / browser.operationScope.set / browser.page.activate / browser.page.close / browser.page.list / browser.page.observed / browser.page.open / browser.page.read / browser.permission.request / browser.permission.respond / browser.preview.connect / browser.preview.latest / browser.preview.resync / browser.preview.ticket.create / browser.preview.viewer.connected / browser.preview.viewer.disconnected / browser.profile.acquire / browser.profile.release / browser.research.cancel / browser.research.extract / browser.research.plan / browser.research.publish / browser.research.start / browser.research.verify / browser.run.manualReview / browser.runtimeBuild.register / browser.runtimeBuild.verify / browser.schedule.evaluate / browser.session.artifact.list / browser.session.attach / browser.session.close / browser.session.create / browser.session.credentials.submit / browser.session.events.read / browser.session.list / browser.session.observe / browser.session.pause / browser.session.recover / browser.session.resume / browser.session.snapshot.read / browser.session.state / browser.state.activate / browser.state.capture / browser.state.invalidate / browser.state.verify / browser.stateBundle.list / browser.stateBundle.read / browser.target.list / browser.target.pick / browser.target.revalidate / browser.teaching.compile / browser.teaching.list / browser.teaching.read / browser.teaching.start / browser.teaching.stop / browser.upload.consume / browser.upload.create / chat.ask / chat.browser.control.acquire / chat.browser.control.returnToAi / chat.browser.directive.compile / chat.browser.session.attach / chat.browser.session.create / chat.browser.session.list / chat.browser.target.attach / chat.command.execute / chat.conversation.cancel / chat.conversation.create / chat.conversation.list / chat.conversation.read / chat.message.append / chat.message.list / chat.response.stream / chat.turn.steer / component.activate / component.control.ack / component.control.disable / component.control.enable / component.deregister / component.deregistration.preview / component.disable / component.e2e.start / component.enable / component.export / component.heartbeat / component.heartbeat.challenge / component.import / component.list / component.metadata.patch / component.quarantine / component.read / component.recertify / component.register / component.release.list / component.repair.request / component.restore / component.retire / component.revision.list / component.revision.publish / component.revision.read / component.rollback / component.state.query / component.state.report / component.state.request / component.suspend / component.suspension.set / component.usage.read / component.validate / component.verify / config.apply / config.export / config.import / config.rollback / config.setting.list / config.setting.read / config.setting.replace / config.setting.reset / config.validate / dashboard.events.read / dashboard.identityCards.list / dashboard.layout.replace / dashboard.topology.read / deployment.list / external.authBinding.create / external.authBinding.list / external.authBinding.patch / external.circuit.close / external.circuit.open / external.circuit.reset / external.request.list / external.target.create / external.target.list / external.target.patch / external.target.read / external.target.test / external.targetBinding.create / external.targetBinding.list / external.targetBinding.remove / external.webhook.list / external.webhook.test / generation.activation.prepare / generation.activation.rollback / generation.activation.switch / generation.activationSet.read / generation.artifact.list / generation.artifactManifest.list / generation.authority.read / generation.blocker.list / generation.blocker.open / generation.blocker.resolve / generation.candidate.publish / generation.capability.resolve / generation.capabilitySnapshot.list / generation.checkpoint.list / generation.contractCandidate.list / generation.fact.list / generation.integration.step / generation.job.cancel / generation.job.complete / generation.job.create / generation.job.events.read / generation.job.followUp / generation.job.list / generation.job.read / generation.job.resume / generation.job.retry / generation.job.snapshot.read / generation.message.append / generation.message.list / generation.model.execute / generation.ownerDecision.list / generation.phase.list / generation.phase.read / generation.phase.start / generation.plan.create / generation.plan.list / generation.plan.read / generation.plan.validate / generation.research.bind / generation.research.refresh / generation.source.add / generation.source.list / generation.source.read / generation.spec.approve / generation.spec.current / generation.spec.precheck / generation.spec.propose / generation.spec.revision.list / generation.spec.revision.read / generation.toolEvent.list / generation.turn.interrupt / generation.turn.list / generation.validation.run / generation.validationRun.list / generation.validationRun.read / generation.workspace.file.list / generation.workspace.patch / generation.workspace.patch.list / generation.workspace.revision.list / generation.workspace.revision.read / generation.workspace.validate / log.correlation.read / log.export / log.query / log.stream / maintenance.service.restart / mcp.alias.create / mcp.alias.list / mcp.alias.preview / mcp.alias.remove / mcp.cache.invalidate / mcp.callRun.events.read / mcp.callRun.list / mcp.callRun.outcome.read / mcp.callRun.read / mcp.catalog.prompt.list / mcp.catalog.prompt.read / mcp.catalog.resource.list / mcp.catalog.resource.read / mcp.catalog.resourceTemplate.list / mcp.catalog.resourceTemplate.read / mcp.catalog.tool.callers.list / mcp.catalog.tool.list / mcp.catalog.tool.read / mcp.catalog.tool.register / mcp.catalog.tool.revision.list / mcp.catalog.tool.usage.read / mcp.contract.compatibility / mcp.contract.validate / mcp.discovery.invalidate / mcp.discovery.snapshot / mcp.discovery.snapshot.diff / mcp.discovery.snapshot.list / mcp.discovery.snapshot.read / mcp.era.invalidate / mcp.era.probe / mcp.extension.snapshot.refresh / mcp.input.required / mcp.input.respond / mcp.inputExchange.list / mcp.inputExchange.read / mcp.legacy.adapt / mcp.legacy.probe / mcp.prompts.get / mcp.prompts.list / mcp.registrationProbe.list / mcp.request.finalize / mcp.request.reserveId / mcp.request.validateJsonRpc / mcp.request.validateTransport / mcp.requestEvent.list / mcp.requestEvent.raw.read / mcp.requestEvent.read / mcp.resources.list / mcp.resources.read / mcp.resources.templates.list / mcp.server.discover / mcp.stateHandle.close / mcp.stateHandle.create / mcp.stateHandle.list / mcp.stateHandle.read / mcp.stateHandle.resolve / mcp.subscription.acknowledge / mcp.subscription.cancel / mcp.subscription.complete / mcp.subscription.list / mcp.subscription.listen / mcp.subscription.notifications.read / mcp.subscription.notify / mcp.subscription.read / mcp.task.cancel / mcp.task.create / mcp.task.events.read / mcp.task.expire / mcp.task.get / mcp.task.list / mcp.task.notify / mcp.task.update / mcp.tools.call / mcp.tools.cancel / mcp.tools.list / mcp.tools.progress / mcp.tools.reconcile / mcp.wire.verify / monitor.alert.acknowledge / monitor.alert.close / monitor.alert.delivery.list / monitor.alert.list / monitor.alert.open / monitor.alert.read / monitor.alert.suppress / monitor.alert.update / monitor.channel.test / monitor.heartbeat.observe / monitor.overview.read / monitor.probe.list / monitor.probe.request / monitor.probe.result / monitor.profile.list / monitor.profile.replace / monitor.repair.enqueue / monitor.state.transition / monitor.stateHistory.read / openai.modelCall.checkpoint.list / openai.modelCall.continuation.list / openai.modelCall.events.read / openai.modelCall.list / openai.modelCall.outputItem.list / openai.modelCall.read / openai.modelCall.reconcile / openai.modelCall.requestCancel / openai.modelCall.requestDescriptor.read / openai.modelCall.resumeStream / openai.modelCall.retrieve / openai.modelCall.toolDispatch.list / openai.modelCapability.list / openai.modelCapability.read / openai.modelCapability.refresh / openai.sdk.capability.snapshot.refresh / operation.catalog.list / operation.invoke / owner.auth.login / owner.auth.loginMfa / owner.auth.logout / owner.mfa.enroll / owner.mfa.reset / owner.mfa.verify / owner.recoveryCodes.rotate / owner.security.read / owner.session.current / owner.session.list / owner.session.reauthenticate / owner.session.revoke / owner.session.revokeAll / owner.session.revokeOthers / ownerApiKey.read / ownerApiKey.reveal / ownerApiKey.rotate / ownerApiKey.session.exchange / ownerApiKey.usage.read / provenance.content.graph / provenance.content.read / provenance.content.register / provenance.segment.compile / provenance.valueDerivation.create / provenance.valueDerivation.list / release.activate / release.list / release.read / release.rollback / runtime.boundary.evidence.read / runtime.boundary.verify / runtime.call.list / runtime.cancel / runtime.cleanup.read / runtime.cleanup.resume / runtime.connection.inspect / runtime.connection.list / runtime.drain / runtime.execution.list / runtime.execution.read / runtime.heartbeat / runtime.instance.list / runtime.instance.read / runtime.instance.reconcile / runtime.instance.restart / runtime.instance.start / runtime.invoke / runtime.prepare / runtime.process.list / runtime.ready.report / runtime.sandbox.read / runtime.state.report / runtime.stop / runtime.workerHeartbeat.list / secret.bind / secret.binding.bulkApply / secret.binding.bulkPreview / secret.binding.list / secret.create / secret.delete / secret.export / secret.import / secret.list / secret.metadata.patch / secret.metadata.read / secret.password.generate / secret.resolve / secret.resolve.test / secret.rotate / secret.unbind / secret.usage.read / secret.usage.report / secret.useContext.create / secret.useContext.list / secret.value.read / secret.version.activate / secret.version.create / secret.version.list / selfTest.catalog.list / selfTest.evidence.export / selfTest.evidence.read / selfTest.faultCatalog.list / selfTest.model.list / selfTest.registeredElement.run / selfTest.run.cancel / selfTest.run.cleanup / selfTest.run.events.read / selfTest.run.history.read / selfTest.run.list / selfTest.run.replay / selfTest.run.shrink / selfTest.run.start / selfTest.run.status / system.capability.list / system.closure.read / system.health.read / system.readiness.read / system.recovery.read / system.version.read` | AVAILABLE | CANONICAL_DISPATCH |
| `test.export` — Exportovat evidence | `selfTest.evidence.export` | AVAILABLE | CANONICAL_DISPATCH |

## Bezpečnost

`security` · `/security`

Zabezpeceni jedine pevne identity, MFA, recovery, sessions a platform security evidence; zadna sprava uzivatelu/roli.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `security.mfaEnroll` — Nastavit MFA | `owner.mfa.enroll` | AVAILABLE | CANONICAL_DISPATCH |
| `security.mfaReset` — Resetovat MFA | `owner.mfa.reset` | AVAILABLE | CANONICAL_DISPATCH |
| `security.recovery` — Zobrazit recovery stav | `owner.security.read` | AVAILABLE | CANONICAL_DISPATCH |
| `security.revokeSession` — Revokovat relaci | `owner.session.revoke` | AVAILABLE | CANONICAL_DISPATCH |
| `security.revokeOthers` — Odhlásit ostatní relace | `owner.session.revokeOthers` | AVAILABLE | CANONICAL_DISPATCH |
| `security.revokeAll` — Odhlásit všechny relace | `owner.session.revokeAll` | AVAILABLE | CANONICAL_DISPATCH |
| `security.changePassword` — Změnit heslo v aplikaci | `FORBIDDEN` | FORBIDDEN | FORBIDDEN |

## Releases a provoz

`releases` · `/releases`

Application/component releases, pointers, deployment, health, migrations, backups, acceptance a rollback evidence.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `release.open` — Otevřít release | `release.read` | AVAILABLE | CANONICAL_DISPATCH |
| `release.activate` — Aktivovat | `release.activate` | AVAILABLE | CANONICAL_DISPATCH |
| `release.rollback` — Rollback | `release.rollback` | AVAILABLE | CANONICAL_DISPATCH |
| `release.backup` — Spustit backup | `backup.create` | AVAILABLE | CANONICAL_DISPATCH |
| `release.restore` — Obnovit ze zálohy | `backup.restore` | AVAILABLE | CANONICAL_DISPATCH |
| `release.acceptance` — Spustit acceptance | `acceptance.run.start` | AVAILABLE | CANONICAL_DISPATCH |

## Command palette

`command-palette` · `GLOBAL_OVERLAY`

Globalni navigace, hledani objektu a vykonani stejnych canonical object actions bez alternativni logiky.

| Akce | Backend | Dashboard | Chat |
|---|---|---|---|
| `palette.execute` — Provést | `acceptance.run.cancel / acceptance.run.list / acceptance.run.start / agent.approval.approve / agent.approval.reject / agent.approval.request / agent.checkpoint.created / agent.definition.create / agent.definition.list / agent.definition.patch / agent.definition.read / agent.delegate.request / agent.delegate.result / agent.eval.result / agent.eval.start / agent.evalRun.cases.read / agent.evalRun.read / agent.evalSuite.create / agent.evalSuite.list / agent.evalSuite.read / agent.memory.item.remove / agent.memory.read / agent.memory.write / agent.message.append / agent.model.completed / agent.model.started / agent.repair.request / agent.revision.activate / agent.revision.compatibility / agent.revision.guardrail.list / agent.revision.handoff.list / agent.revision.list / agent.revision.promotionGate.list / agent.revision.publish / agent.revision.read / agent.revision.toolBinding.list / agent.revision.toolBinding.preview / agent.revision.validate / agent.revision.verify / agent.run.approval.list / agent.run.cancel / agent.run.checkpoint.list / agent.run.complete / agent.run.events.read / agent.run.fail / agent.run.handoff.list / agent.run.list / agent.run.manualReview / agent.run.pause / agent.run.resume / agent.run.start / agent.run.status / agent.run.toolCall.list / agent.session.close / agent.session.compact / agent.session.items.read / agent.session.list / agent.session.read / agent.state.report / agent.tool.failed / agent.tool.request / agent.tool.result / agent.trigger.create / agent.trigger.list / agent.trigger.patch / agent.trigger.remove / agentic.security.event.list / agentic.security.event.read / agentic.security.event.record / agentic.security.evidence.export / audit.archive.complete / audit.archive.enqueue / audit.archive.list / audit.event.append / audit.event.list / audit.event.read / audit.integrity.read / audit.integrity.verify / audit.savedQuery.create / audit.stream.ack / audit.stream.replay.request / audit.stream.replay.result / authority.actionPlan.compile / authority.actionPlan.list / authority.actionPlan.validate / authority.context.create / authority.context.read / authority.context.validate / authority.intent.compile / authority.intent.read / authority.intent.validate / authority.lineage.append / authority.lineage.graph / authority.lineage.resolve / backup.create / backup.list / backup.restore / backup.verify / binding.create / binding.list / binding.preview / binding.read / binding.remove / binding.replace / binding.test / browser.account.authEpoch.increment / browser.account.list / browser.account.logout / browser.account.metadata.patch / browser.account.read / browser.account.reauthenticate / browser.account.save / browser.account.verify / browser.action.attempt.list / browser.action.cancel / browser.action.complete / browser.action.dispatchPhase / browser.action.fail / browser.action.reconcile / browser.action.resolveOutcome / browser.action.start / browser.action.status / browser.annotation.create / browser.annotation.list / browser.annotation.reanchor / browser.annotation.tombstone / browser.artifact.created / browser.auth.verify / browser.authAttempt.list / browser.automation.activate / browser.automation.artifact.list / browser.automation.artifact.read / browser.automation.authBinding.create / browser.automation.authBinding.list / browser.automation.cancel / browser.automation.create / browser.automation.createFromTeaching / browser.automation.disable / browser.automation.enable / browser.automation.list / browser.automation.metadata.patch / browser.automation.preflight / browser.automation.read / browser.automation.reauthenticate / browser.automation.reconcile / browser.automation.repair / browser.automation.revision.list / browser.automation.revision.publish / browser.automation.revision.read / browser.automation.rollback / browser.automation.run / browser.automation.run.list / browser.automation.run.read / browser.automation.run.step.list / browser.automation.schedule.create / browser.automation.schedule.list / browser.automation.schedule.patch / browser.automation.verify / browser.bridge.assign / browser.bridge.connect / browser.bridge.connection.list / browser.bridge.enroll / browser.bridge.enrollment.complete / browser.bridge.list / browser.bridge.profile.list / browser.bridge.read / browser.bridge.release / browser.bridge.revoke / browser.bridge.rotateCertificate / browser.bridge.test / browser.challenge.required / browser.challenge.resolve / browser.cleanup.resume / browser.confirmation.respond / browser.control.acquire / browser.control.changed / browser.control.read / browser.control.release / browser.control.transfer / browser.control.transfer.list / browser.dialog.opened / browser.dialog.respond / browser.document.changed / browser.document.list / browser.download.list / browser.download.persist / browser.download.started / browser.download.verify / browser.focus.acknowledge / browser.focus.open / browser.focus.request / browser.focus.resolve / browser.frame.list / browser.frame.observed / browser.host.drain / browser.host.ready / browser.host.recover / browser.navigation.list / browser.navigation.observed / browser.observation.request / browser.operationScope.set / browser.page.activate / browser.page.close / browser.page.list / browser.page.observed / browser.page.open / browser.page.read / browser.permission.request / browser.permission.respond / browser.preview.connect / browser.preview.latest / browser.preview.resync / browser.preview.ticket.create / browser.preview.viewer.connected / browser.preview.viewer.disconnected / browser.profile.acquire / browser.profile.release / browser.research.cancel / browser.research.extract / browser.research.plan / browser.research.publish / browser.research.start / browser.research.verify / browser.run.manualReview / browser.runtimeBuild.register / browser.runtimeBuild.verify / browser.schedule.evaluate / browser.session.artifact.list / browser.session.attach / browser.session.close / browser.session.create / browser.session.credentials.submit / browser.session.events.read / browser.session.list / browser.session.observe / browser.session.pause / browser.session.recover / browser.session.resume / browser.session.snapshot.read / browser.session.state / browser.state.activate / browser.state.capture / browser.state.invalidate / browser.state.verify / browser.stateBundle.list / browser.stateBundle.read / browser.target.list / browser.target.pick / browser.target.revalidate / browser.teaching.compile / browser.teaching.list / browser.teaching.read / browser.teaching.start / browser.teaching.stop / browser.upload.consume / browser.upload.create / chat.ask / chat.browser.control.acquire / chat.browser.control.returnToAi / chat.browser.directive.compile / chat.browser.session.attach / chat.browser.session.create / chat.browser.session.list / chat.browser.target.attach / chat.command.execute / chat.conversation.cancel / chat.conversation.create / chat.conversation.list / chat.conversation.read / chat.message.append / chat.message.list / chat.response.stream / chat.turn.steer / component.activate / component.control.ack / component.control.disable / component.control.enable / component.deregister / component.deregistration.preview / component.disable / component.e2e.start / component.enable / component.export / component.heartbeat / component.heartbeat.challenge / component.import / component.list / component.metadata.patch / component.quarantine / component.read / component.recertify / component.register / component.release.list / component.repair.request / component.restore / component.retire / component.revision.list / component.revision.publish / component.revision.read / component.rollback / component.state.query / component.state.report / component.state.request / component.suspend / component.suspension.set / component.usage.read / component.validate / component.verify / config.apply / config.export / config.import / config.rollback / config.setting.list / config.setting.read / config.setting.replace / config.setting.reset / config.validate / dashboard.events.read / dashboard.identityCards.list / dashboard.layout.replace / dashboard.topology.read / deployment.list / external.authBinding.create / external.authBinding.list / external.authBinding.patch / external.circuit.close / external.circuit.open / external.circuit.reset / external.request.list / external.target.create / external.target.list / external.target.patch / external.target.read / external.target.test / external.targetBinding.create / external.targetBinding.list / external.targetBinding.remove / external.webhook.list / external.webhook.test / generation.activation.prepare / generation.activation.rollback / generation.activation.switch / generation.activationSet.read / generation.artifact.list / generation.artifactManifest.list / generation.authority.read / generation.blocker.list / generation.blocker.open / generation.blocker.resolve / generation.candidate.publish / generation.capability.resolve / generation.capabilitySnapshot.list / generation.checkpoint.list / generation.contractCandidate.list / generation.fact.list / generation.integration.step / generation.job.cancel / generation.job.complete / generation.job.create / generation.job.events.read / generation.job.followUp / generation.job.list / generation.job.read / generation.job.resume / generation.job.retry / generation.job.snapshot.read / generation.message.append / generation.message.list / generation.model.execute / generation.ownerDecision.list / generation.phase.list / generation.phase.read / generation.phase.start / generation.plan.create / generation.plan.list / generation.plan.read / generation.plan.validate / generation.research.bind / generation.research.refresh / generation.source.add / generation.source.list / generation.source.read / generation.spec.approve / generation.spec.current / generation.spec.precheck / generation.spec.propose / generation.spec.revision.list / generation.spec.revision.read / generation.toolEvent.list / generation.turn.interrupt / generation.turn.list / generation.validation.run / generation.validationRun.list / generation.validationRun.read / generation.workspace.file.list / generation.workspace.patch / generation.workspace.patch.list / generation.workspace.revision.list / generation.workspace.revision.read / generation.workspace.validate / log.correlation.read / log.export / log.query / log.stream / maintenance.service.restart / mcp.alias.create / mcp.alias.list / mcp.alias.preview / mcp.alias.remove / mcp.cache.invalidate / mcp.callRun.events.read / mcp.callRun.list / mcp.callRun.outcome.read / mcp.callRun.read / mcp.catalog.prompt.list / mcp.catalog.prompt.read / mcp.catalog.resource.list / mcp.catalog.resource.read / mcp.catalog.resourceTemplate.list / mcp.catalog.resourceTemplate.read / mcp.catalog.tool.callers.list / mcp.catalog.tool.list / mcp.catalog.tool.read / mcp.catalog.tool.register / mcp.catalog.tool.revision.list / mcp.catalog.tool.usage.read / mcp.contract.compatibility / mcp.contract.validate / mcp.discovery.invalidate / mcp.discovery.snapshot / mcp.discovery.snapshot.diff / mcp.discovery.snapshot.list / mcp.discovery.snapshot.read / mcp.era.invalidate / mcp.era.probe / mcp.extension.snapshot.refresh / mcp.input.required / mcp.input.respond / mcp.inputExchange.list / mcp.inputExchange.read / mcp.legacy.adapt / mcp.legacy.probe / mcp.prompts.get / mcp.prompts.list / mcp.registrationProbe.list / mcp.request.finalize / mcp.request.reserveId / mcp.request.validateJsonRpc / mcp.request.validateTransport / mcp.requestEvent.list / mcp.requestEvent.raw.read / mcp.requestEvent.read / mcp.resources.list / mcp.resources.read / mcp.resources.templates.list / mcp.server.discover / mcp.stateHandle.close / mcp.stateHandle.create / mcp.stateHandle.list / mcp.stateHandle.read / mcp.stateHandle.resolve / mcp.subscription.acknowledge / mcp.subscription.cancel / mcp.subscription.complete / mcp.subscription.list / mcp.subscription.listen / mcp.subscription.notifications.read / mcp.subscription.notify / mcp.subscription.read / mcp.task.cancel / mcp.task.create / mcp.task.events.read / mcp.task.expire / mcp.task.get / mcp.task.list / mcp.task.notify / mcp.task.update / mcp.tools.call / mcp.tools.cancel / mcp.tools.list / mcp.tools.progress / mcp.tools.reconcile / mcp.wire.verify / monitor.alert.acknowledge / monitor.alert.close / monitor.alert.delivery.list / monitor.alert.list / monitor.alert.open / monitor.alert.read / monitor.alert.suppress / monitor.alert.update / monitor.channel.test / monitor.heartbeat.observe / monitor.overview.read / monitor.probe.list / monitor.probe.request / monitor.probe.result / monitor.profile.list / monitor.profile.replace / monitor.repair.enqueue / monitor.state.transition / monitor.stateHistory.read / openai.modelCall.checkpoint.list / openai.modelCall.continuation.list / openai.modelCall.events.read / openai.modelCall.list / openai.modelCall.outputItem.list / openai.modelCall.read / openai.modelCall.reconcile / openai.modelCall.requestCancel / openai.modelCall.requestDescriptor.read / openai.modelCall.resumeStream / openai.modelCall.retrieve / openai.modelCall.toolDispatch.list / openai.modelCapability.list / openai.modelCapability.read / openai.modelCapability.refresh / openai.sdk.capability.snapshot.refresh / operation.catalog.list / operation.invoke / owner.auth.login / owner.auth.loginMfa / owner.auth.logout / owner.mfa.enroll / owner.mfa.reset / owner.mfa.verify / owner.recoveryCodes.rotate / owner.security.read / owner.session.current / owner.session.list / owner.session.reauthenticate / owner.session.revoke / owner.session.revokeAll / owner.session.revokeOthers / ownerApiKey.read / ownerApiKey.reveal / ownerApiKey.rotate / ownerApiKey.session.exchange / ownerApiKey.usage.read / provenance.content.graph / provenance.content.read / provenance.content.register / provenance.segment.compile / provenance.valueDerivation.create / provenance.valueDerivation.list / release.activate / release.list / release.read / release.rollback / runtime.boundary.evidence.read / runtime.boundary.verify / runtime.call.list / runtime.cancel / runtime.cleanup.read / runtime.cleanup.resume / runtime.connection.inspect / runtime.connection.list / runtime.drain / runtime.execution.list / runtime.execution.read / runtime.heartbeat / runtime.instance.list / runtime.instance.read / runtime.instance.reconcile / runtime.instance.restart / runtime.instance.start / runtime.invoke / runtime.prepare / runtime.process.list / runtime.ready.report / runtime.sandbox.read / runtime.state.report / runtime.stop / runtime.workerHeartbeat.list / secret.bind / secret.binding.bulkApply / secret.binding.bulkPreview / secret.binding.list / secret.create / secret.delete / secret.export / secret.import / secret.list / secret.metadata.patch / secret.metadata.read / secret.password.generate / secret.resolve / secret.resolve.test / secret.rotate / secret.unbind / secret.usage.read / secret.usage.report / secret.useContext.create / secret.useContext.list / secret.value.read / secret.version.activate / secret.version.create / secret.version.list / selfTest.catalog.list / selfTest.evidence.export / selfTest.evidence.read / selfTest.faultCatalog.list / selfTest.model.list / selfTest.registeredElement.run / selfTest.run.cancel / selfTest.run.cleanup / selfTest.run.events.read / selfTest.run.history.read / selfTest.run.list / selfTest.run.replay / selfTest.run.shrink / selfTest.run.start / selfTest.run.status / system.capability.list / system.closure.read / system.health.read / system.readiness.read / system.recovery.read / system.version.read` | AVAILABLE | CANONICAL_DISPATCH |
| `palette.close` — Zavřít | `CLIENT_ONLY` | AVAILABLE | CLIENT_ACTION_CARD |

