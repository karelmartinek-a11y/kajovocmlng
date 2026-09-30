### 51.11 Singleton OWNER, platform heads a bootstrap

`owner_identity`, `owner_api_credential`, `platform_incarnation`, `activation_head`, `application_deployment_head` a `audit_head` používají fyzický singleton key:

```sql
ALTER TABLE owner_identity ADD CONSTRAINT ck_owner_identity_singleton CHECK (singleton_key = 1);
CREATE UNIQUE INDEX uq_owner_identity_singleton ON owner_identity (singleton_key);
ALTER TABLE owner_identity ALTER COLUMN singleton_key SET DEFAULT 1;
ALTER TABLE owner_identity ALTER COLUMN singleton_key SET NOT NULL;
ALTER TABLE owner_api_credential ADD CONSTRAINT ck_owner_api_credential_singleton CHECK (singleton_key = 1);
CREATE UNIQUE INDEX uq_owner_api_credential_singleton ON owner_api_credential (singleton_key);
ALTER TABLE owner_api_credential ALTER COLUMN singleton_key SET DEFAULT 1;
ALTER TABLE owner_api_credential ALTER COLUMN singleton_key SET NOT NULL;
ALTER TABLE platform_incarnation ADD CONSTRAINT ck_platform_incarnation_singleton CHECK (singleton_key = 1);
CREATE UNIQUE INDEX uq_platform_incarnation_singleton ON platform_incarnation (singleton_key);
ALTER TABLE platform_incarnation ALTER COLUMN singleton_key SET DEFAULT 1;
ALTER TABLE platform_incarnation ALTER COLUMN singleton_key SET NOT NULL;
ALTER TABLE activation_head ADD CONSTRAINT ck_activation_head_singleton CHECK (singleton_key = 1);
CREATE UNIQUE INDEX uq_activation_head_singleton ON activation_head (singleton_key);
ALTER TABLE activation_head ALTER COLUMN singleton_key SET DEFAULT 1;
ALTER TABLE activation_head ALTER COLUMN singleton_key SET NOT NULL;
ALTER TABLE application_deployment_head ADD CONSTRAINT ck_application_deployment_head_singleton CHECK (singleton_key = 1);
CREATE UNIQUE INDEX uq_application_deployment_head_singleton ON application_deployment_head (singleton_key);
ALTER TABLE application_deployment_head ALTER COLUMN singleton_key SET DEFAULT 1;
ALTER TABLE application_deployment_head ALTER COLUMN singleton_key SET NOT NULL;
ALTER TABLE audit_head ADD CONSTRAINT ck_audit_head_singleton CHECK (singleton_key = 1);
CREATE UNIQUE INDEX uq_audit_head_singleton ON audit_head (singleton_key);
ALTER TABLE audit_head ALTER COLUMN singleton_key SET DEFAULT 1;
ALTER TABLE audit_head ALTER COLUMN singleton_key SET NOT NULL;
```

Bootstrap migrace pod advisory namespace `BOOTSTRAP_SINGLETON` vloží chybějící rows a ověří přesně jeden row každého druhu. Trigger zakáže změnu singleton key a `DELETE`. Readiness selže, pokud row chybí nebo jeho fixní hodnoty neodpovídají SSOT.

`owner_identity.username` může používat existující `citext` storage, ale login nepoužívá jeho case-insensitive porovnání. Přijaté username se exact porovná jako text s COLLATE "C" proti `KRMAR78`, bez trimu nebo case foldingu, podle 26.2 a OWNER-03. Uloženou hodnotu vynucuje `CHECK (username::text COLLATE "C" = 'KRMAR78')` a singleton primary key. Jiný case nebo whitespace je neplatný vstup, ne volba jiného účtu; unique constraint zůstává.

Každá autoritativní transakce získá `platform_incarnation FOR SHARE` a `application_deployment_head FOR SHARE` před business rooty. Restore nebo deployment epoch switch získá oba rows `FOR UPDATE`; nemůže tedy commitnout současně s transakcí, která byla přijata pod starou incarnation/epoch, aniž by jednoznačně nastalo pořadí commitů.

