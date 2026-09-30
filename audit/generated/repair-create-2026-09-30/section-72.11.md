### 72.11 Dashboard — `/dashboard`

**Účel:** Zobrazit a ovladat zivou topologii komponent, vazeb, portu, secrets, external targetu a runtime udalosti.

**Povinné panely / oblasti:** Metric strip; Topology canvas; Filter/search bar; Selection inspector; Live event stream; Correlation detail drawer.

**Vstupy a zobrazované hodnoty**

| ID | Prvek | Typ / kapacita | Proč je v UI | Povinný | Validace | Editovatelnost / zdroj |
|---|---|---|---|---|---|---|
| `dashboard.search` | Hledat | search · TEXT_1 · oček. 1 řádků | Fulltext nad komponentami, porty, bindingy a souvisejicimi objekty. | ne | `BOUNDED_SEARCH_QUERY` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `dashboard.category` | Kategorie | multiselect | Filtr component category. | ne | `KNOWN_COMPONENT_CATEGORY` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `dashboard.lifecycle` | Lifecycle | multiselect | Filtr lifecycle stavu. | ne | `KNOWN_LIFECYCLE_ENUM` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `dashboard.operational` | Operational | multiselect | Filtr operational projection. | ne | `KNOWN_OPERATIONAL_ENUM` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |
| `dashboard.criticality` | Criticality | multiselect | Filtr business criticality. | ne | `KNOWN_CRITICALITY_ENUM` | ALWAYS_WHEN_SECTION_EDITABLE / OWNER_INPUT |

**Tlačítka a akce**

| ID | Tlačítko / akce | Účel | Operation binding | Aktivní právě když | Disabled právě když | Confirm |
|---|---|---|---|---|---|---|
| `dashboard.fit` | Přizpůsobit | Fitne topology canvas do viewportu. | `UI.DASHBOARD_FIT` | canvas loaded | canvas unavailable | `NONE` |
| `dashboard.connect` | Propojit | Zalozi exact contract binding mezi kompatibilnimi porty. | `BINDING.CREATE` | source,target selected AND compatibility PASS AND versions current | missing endpoint OR incompatible/stale contract | `NONE` |
| `dashboard.disconnect` | Odpojit | Odstrani/retiruje exact binding podle lifecycle. | `BINDING.DISCONNECT` | active binding selected and impact preview complete | binding not removable OR protected activation set | `IMPACT_PREVIEW` |
| `dashboard.bindSecret` | Připojit secret | Zalozi exact secret binding. | `SECRET.BIND` | source revision and secret version selector valid | wildcard/invalid target OR stale revision | `NONE` |
| `dashboard.activate` | Aktivovat | Aktivuje validovany activation set/component revision. | `COMPONENT.ACTIVATE` | all blocking readiness gates PASS and candidate current | any gate not PASS OR current pointer conflict | `NONE` |
| `dashboard.enable` | Zapnout | Enable component/runtime pres control state machine. | `COMPONENT.ENABLE` | action registry enables for current state | already enabled OR lifecycle/readiness disallows | `NONE` |
| `dashboard.disable` | Vypnout | Disable component/runtime pres control state machine. | `COMPONENT.DISABLE` | action registry enables for current state | already disabled OR transition forbidden | `IMPACT_PREVIEW` |
| `dashboard.repair` | Opravit | Spusti deduplikovany repair workflow. | `COMPONENT.REPAIR` | repair eligible and no duplicate active repair | no evidence/eligible target OR repair already active | `NONE` |
| `dashboard.recertify` | Recertifikovat | Spusti recertification checks. | `COMPONENT.RECERTIFY` | component registered and recertifiable | terminal/deregistered OR run already active | `NONE` |
| `dashboard.e2e` | Spustit E2E | Spusti canonical E2E scenario. | `TEST.E2E_RUN` | scenario exists and dependencies ready | no scenario OR readiness blocker | `NONE` |

**Povinné UI stavy:** `LOADING`, `EMPTY`, `READY`, `LIVE`, `STALE`, `RECONNECTING`, `PARTIAL`, `ERROR`.

