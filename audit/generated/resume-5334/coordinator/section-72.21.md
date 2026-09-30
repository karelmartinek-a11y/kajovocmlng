### 72.21 Secrets a hesla — `/secrets`

**Účel:** Plny OWNER Password Manager nad Secret Managerem vcetne hodnot, verzi, rotace, bindings, usage a auditu.

**Povinné panely / oblasti:** Search/filter/groups/tags; Table/card view; Secret detail; Value/reveal area; Versions timeline; Bindings matrix; Usage graph; TOTP/countdown; Import/export; Bulk actions; Audit/live logs.

**Vstupy a zobrazované hodnoty**

| ID | Prvek | Typ / kapacita | Proč je v UI | Povinný | Validace | Editovatelnost / zdroj |
|---|---|---|---|---|---|---|
| `secret.search` | Hledat | search · TEXT_1 · oček. 1 řádků | Fulltext stable/display name, tags, group a metadata. | ne | `BOUNDED_SEARCH_QUERY` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `secret.stableName` | Stable name | text · TEXT_1 · oček. 1 řádků | Nemenny logicky nazev secretu po vytvoreni podle contractu. | ano | `STABLE_SECRET_NAME_UNIQUE` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `secret.displayName` | Název | text · TEXT_1 · oček. 1 řádků | OWNER display label. | ano | `NONEMPTY` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `secret.description` | Popis | textarea · TEXT_8 · oček. 2-8 řádků | Business popis ucelu secretu. | ne | `DOMAIN_LENGTH` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `secret.type` | Typ | select | PASSWORD/API_KEY/.../GENERIC_BINARY. | ano | `SECRET_TYPE_ENUM` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `secret.value` | Hodnota | secret · SECRET_50 · oček. 1-50+ řádků | Plaintext hodnota nove secret version. | ano | `TYPE_SPECIFIC + NO_SILENT_NORMALIZATION` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `secret.url` | URL | url · TEXT_1 · oček. 1 řádků | Volitelne metadata podle typu. | ne | `URL_IF_PRESENT` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `secret.username` | Username | text · TEXT_1 · oček. 1 řádků | Volitelne metadata podle typu. | ne | `DOMAIN_LENGTH` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `secret.notes` | Poznámky | textarea · TEXT_8 · oček. 2-8 řádků | OWNER poznamky. | ne | `DOMAIN_LENGTH` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `secret.expiration` | Expirace | datetime | Volitelna expirace verze/polozky. | ne | `TIMESTAMP/POLICY` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |

**Tlačítka a akce**

| ID | Tlačítko / akce | Účel | Operation binding | Aktivní právě když | Disabled právě když | Confirm |
|---|---|---|---|---|---|---|
| `secret.create` | Nový secret | Vytvori secret + prvni version. | `SECRET.CREATE` | required metadata/value valid and stableName available | validation/uniqueness failure | `NONE` |
| `secret.reveal` | Zobrazit | Reveal plaintext active/selected version. | `SECRET.REVEAL` | secret exists and version revealable | deleted/unavailable version | `NONE` |
| `secret.copy` | Kopírovat | Kopiruje revealovanou hodnotu. | `SECRET.COPY` | plaintext currently revealed | not revealed | `NONE` |
| `secret.newVersion` | Nová verze | Vytvori immutable new secret version. | `SECRET.VERSION_CREATE` | secret mutable metadata exists and value valid | reserved system secret special contract OR invalid value | `NONE` |
| `secret.activateVersion` | Aktivovat verzi | Atomicky prepnuti active version s invalidaci dependent state dle contractu. | `SECRET.VERSION_ACTIVATE` | selected version eligible/current state valid | same active/ineligible/stale state | `NONE` |
| `secret.rotate` | Rotovat | Vytvori/aktivuje novou hodnotu podle rotation policy. | `SECRET.ROTATE` | rotation permitted | policy/state blocks | `NONE` |
| `secret.bind` | Připojit | Vytvori exact binding source revision -> secret/version/purpose. | `SECRET.BIND` | source/revision/purpose exact and compatible | wildcard/ambiguous/stale source | `NONE` |
| `secret.unbind` | Odpojit | Retiruje exact binding po impact validation. | `SECRET.UNBIND` | binding removable | active required dependency | `IMPACT_PREVIEW` |
| `secret.delete` | Smazat | Lifecycle delete pouze pokud contract dovoluje; system-reserved key nelze obecnym CRUD smazat. | `SECRET.DELETE` | delete eligible | reserved/current required/retention dependency | `EXPLICIT_CONFIRM` |
| `secret.export` | Exportovat | Export selected item/version podle contractu. | `SECRET.EXPORT` | exportable value/metadata selected | not exportable | `NONE` |
| `secret.testResolve` | Test resolve | Otestuje exact binding resolution bez zmeny consumer state. | `SECRET.TEST_RESOLVE` | binding active/current | binding inactive/stale | `NONE` |

**Povinné UI stavy:** `LOADING`, `EMPTY`, `READY`, `PARTIAL`, `STALE_RECONNECTING`, `ERROR`, `SUCCESS`.

