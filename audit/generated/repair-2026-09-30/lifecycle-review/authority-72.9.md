### 72.9 MFA / enrollment / recovery — `/login/mfa`

**Účel:** Dokoncit povinne TOTP MFA nebo jednorazovy recovery flow pred vznikem plne OWNER session.

**Povinné panely / oblasti:** Enrollment QR/seed panel; TOTP/recovery form; One-time recovery codes panel.

**Vstupy a zobrazované hodnoty**

| ID | Prvek | Typ / kapacita | Proč je v UI | Povinný | Validace | Editovatelnost / zdroj |
|---|---|---|---|---|---|---|
| `mfa.code` | Overovaci kod | text · TEXT_1 · oček. 1 řádků | Sestimistny TOTP kod. | ano | `EXACT_6_DIGITS + SERVER_TOTP_VERIFY` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `mfa.recovery` | Recovery kod | text · TEXT_1 · oček. 1 řádků | Alternativni nepouzity jednorazovy recovery kod. | ne | `SERVER_RECOVERY_CODE_VERIFY` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `mfa.trusted` | Důvěryhodné zařízení | checkbox | OWNER preference pro dobu duveryhodneho zarizeni podle current konfigurace. | ne | `BOOLEAN` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |

**Tlačítka a akce**

| ID | Tlačítko / akce | Účel | Operation binding | Aktivní právě když | Disabled právě když | Confirm |
|---|---|---|---|---|---|---|
| `mfa.verify` | Ověřit | Dokonci TOTP/recovery autentizaci. | `AUTH.MFA_VERIFY` | exactly one of valid TOTP/recovery inputs present AND not pending | both empty OR conflicting modes OR pending | `NONE` |
| `mfa.showSeed` | Zobrazit ruční seed | Zobrazi manual seed pouze v enrollment session. | `AUTH.MFA_ENROLLMENT_SEED_REVEAL` | enrollment session active | MFA already active OR session not enrollment | `NONE` |
| `mfa.copyRecovery` | Kopírovat recovery kódy | Kopiruje jednorazove zobrazene recovery codes. | `AUTH.RECOVERY_CODES_COPY` | fresh enrollment completion response contains codes | codes no longer revealable | `NONE` |

**Povinné UI stavy:** `ENROLLMENT_REQUIRED`, `READY`, `VERIFYING`, `VERIFIED`, `FAILED`, `RECOVERY_USED`.

