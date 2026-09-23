# KájovoCML NG - Dialog / overlay catalog

Kapitola 72 does not create a separate dialog namespace. Bounded entry may use a modal/drawer; destructive and guarded actions use the declared confirmation level. This catalog maps every action that requires confirmation to one visual template and also defines global recovery overlays required by the UI contract.

## IMPACT_IF_NONIDLE

| Route | Action | Label | Operation binding | Enabled when | Required content |
|---|---|---|---|---|---|
| `/chat` | `chat.closeBrowser` | Zavřít relaci | `BROWSER.SESSION_CLOSE` | session closeable and no blocking unknown effect | No modal while idle; if non-idle, show running work and impact before confirm. |
| `/browser` | `browser.close` | Zavřít relaci | `BROWSER.SESSION_CLOSE` | session closeable | No modal while idle; if non-idle, show running work and impact before confirm. |

## IMPACT_PREVIEW

| Route | Action | Label | Operation binding | Enabled when | Required content |
|---|---|---|---|---|---|
| `/dashboard` | `dashboard.disconnect` | Odpojit | `BINDING.DISCONNECT` | active binding selected and impact preview complete | Fresh affected objects/bindings/runs preview and current stateVersion before confirm. |
| `/dashboard` | `dashboard.disable` | Vypnout | `COMPONENT.DISABLE` | action registry enables for current state | Fresh affected objects/bindings/runs preview and current stateVersion before confirm. |
| `/agents` | `agent.rollback` | Rollback | `AGENT.ROLLBACK` | valid rollback point exists and safety checks PASS | Fresh affected objects/bindings/runs preview and current stateVersion before confirm. |
| `/components` | `component.rollback` | Rollback | `COMPONENT.ROLLBACK` | rollback point valid | Fresh affected objects/bindings/runs preview and current stateVersion before confirm. |
| `/secrets` | `secret.unbind` | Odpojit | `SECRET.UNBIND` | binding removable | Fresh affected objects/bindings/runs preview and current stateVersion before confirm. |
| `/configuration` | `config.rollback` | Vrátit předchozí | `CONFIG.ROLLBACK` | previous snapshot exists and rollback allowed | Fresh affected objects/bindings/runs preview and current stateVersion before confirm. |
| `/releases` | `release.rollback` | Rollback | `RELEASE.ROLLBACK` | valid rollback target and migration/runtime safety PASS | Fresh affected objects/bindings/runs preview and current stateVersion before confirm. |

## IMPACT_IF_REQUIRED

| Route | Action | Label | Operation binding | Enabled when | Required content |
|---|---|---|---|---|---|
| `/registered` | `registered.disable` | Vypnout | `OBJECT.DISABLE` | action registry says enabled | Conditional impact preview only when current server state says it is required. |

## MANDATORY_IMPACT_PREVIEW

| Route | Action | Label | Operation binding | Enabled when | Required content |
|---|---|---|---|---|---|
| `/components` | `component.deregister` | Deregistrovat | `COMPONENT.DEREGISTER` | all required detach/cleanup preconditions PASS | Same as IMPACT_PREVIEW; confirm disabled until preview is current and complete. |
| `/releases` | `release.restore` | Obnovit ze zálohy | `BACKUP.RESTORE` | selected backup verified and restore preflight PASS | Same as IMPACT_PREVIEW; confirm disabled until preview is current and complete. |

## EXPLICIT_CONFIRM

| Route | Action | Label | Operation binding | Enabled when | Required content |
|---|---|---|---|---|---|
| `/runtime-access` | `runtime.rotateKey` | Rotovat API klíč | `OWNER_API_KEY.ROTATE` | OWNER session current and no rotate pending | Object identity, exact operation, impact summary, Cancel + explicit confirm. No invented typed phrase. |
| `/runtime-access` | `runtime.revokeBridge` | Revokovat bridge certifikát | `BRIDGE.CERT_REVOKE` | certificate current and revocable | Object identity, exact operation, impact summary, Cancel + explicit confirm. No invented typed phrase. |
| `/secrets` | `secret.delete` | Smazat | `SECRET.DELETE` | delete eligible | Object identity, exact operation, impact summary, Cancel + explicit confirm. No invented typed phrase. |
| `/security` | `security.mfaReset` | Resetovat MFA | `AUTH.MFA_RESET` | current session reauthenticated and operation allowed | Object identity, exact operation, impact summary, Cancel + explicit confirm. No invented typed phrase. |
| `/security` | `security.revokeSession` | Revokovat relaci | `AUTH.SESSION_REVOKE` | selected revocable session exists | Object identity, exact operation, impact summary, Cancel + explicit confirm. No invented typed phrase. |
| `/security` | `security.revokeOthers` | Odhlásit ostatní relace | `AUTH.SESSIONS_REVOKE_OTHERS` | other active sessions exist | Object identity, exact operation, impact summary, Cancel + explicit confirm. No invented typed phrase. |
| `/security` | `security.revokeAll` | Odhlásit všechny relace | `AUTH.SESSIONS_REVOKE_ALL` | authenticated/re-authenticated | Object identity, exact operation, impact summary, Cancel + explicit confirm. No invented typed phrase. |

## Global recovery / entry overlays

- `CONFLICT`: current server snapshot + OWNER edited value + changed items; no automatic noncommutative merge.
- `MANUAL_REVIEW`: evidence, possible external effect, automatic retry blocked, only canonical OWNER decisions.
- `PENDING`: accepted/running state with logical operation/correlation and Cancel only when operation contract permits.
- `VALIDATION_ERROR`: field-level client shape plus canonical server error; dialog stays open and preserves input.
- `DIRTY_STATE`: leaving a changed editor requires preserve/discard behavior defined by the edit contract; no silent data loss.
- `ACTION_FAILED`: stable error code, human explanation, correlation and exact recovery directive.
- `BROWSER_CHALLENGE`: typed browser challenge/human takeover; the required field depends on the concrete challenge contract.
- `SECRET_ENTRY`: bounded secret creation/version editor using the fields declared on `/secrets`.

## Průběh operace

`pending-operation` je neblokující procesní panel, nikoli modální dialog. Používá `process-visual-registry.json`; modál je vyhrazen skutečnému potvrzení nebo potřebnému lidskému vstupu.
