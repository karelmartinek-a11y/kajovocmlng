# Fáze 4 — uzavření UI registrů, expozice a technologického kontraktu

**Stav fáze 4: PARTIAL.** Fáze 1, 2 a 3 zůstávají samostatně **PARTIAL**. Nejde o prohlášení celého SSOT za dokončený ani freeze-ready.

## Výchozí stav a autorita

- Výchozí commit: `6180d9fe67dfaa5365190301dfd58cc8d9812f3d`, větev `main`.
- Výchozí `git status --short --branch`: `## main...origin/main`, pracovní strom již byl dirty. Obsahoval necommitnuté opravy fází 1–3, jejich auditní výstupy, současné UI registry/projekce, QA a stackové podklady; existující změny byly zachovány. Na začátku nebyl nalezen použitelný `AGENTS.md` v repozitáři ani v kontrolovaných rodičovských/aktivních podadresářích. Fáze 4 nic necommitovala ani nepublikovala.
- UI autoritou jsou vložené `KCML-UI-RESOURCE`, `KCML-CLOSURE-RESOURCE` a `KCML-EXPERIENCE-RESOURCE` bloky v `00_SSOT/KajovoCMLNG_SSOT.md`. Fyzické UI JSON/CSV/Markdown soubory se generují z těchto zdrojů. Starší fyzické registry a obrázky byly použity jako důkaz dříve výslovně definovaných a zobrazených funkcí, nikoli jako důvod slepě převzít větší počet.
- Původní rozpor byl skutečný: vložené UI registry měly 136 akcí, fyzické registry 152; rozdílem bylo přesně 16 uvedených akcí. Referenční dashboard `04_UI_VIEWS/en/768x1024/live-context-menu-en.png` zobrazuje objektové akce (mj. start, stop, restart, soubory, historii, vstupy/výstupy, chat a odstranění); původní UI záznamy obsahovaly jejich účel a vazby. Akce byly proto obnoveny do vložených autoritativních registrů a odpovídajících ploch `live-experience`, ne odstraněny z projekcí.
- Obsahově byla strojově inventarizována všechna aktuální UI stránková/akční spojení a jejich cílové operace. Ručně jsem podrobně zkontroloval 16 obnovených akcí, čtyři jmenované expoziční případy, stackový kontrakt a referenční obrazovku `04_UI_VIEWS/en/768x1024/live-context-menu-en.png`; vizuálně potvrzuje plochu objektových akcí včetně start/stop/restart, historie, vstupů/výstupů, souborů, chatu a delete. Neprováděl jsem úplnou ruční sémantickou revizi všech 152 akcí ani úplnou vizuální revizi všech obrázků.

## Počty a výsledek sjednocení

| Oblast | Před | Po |
|---|---:|---:|
| Akce ve vloženém UI registru | 136 | 152 |
| Vazby action → operation/local action | 136 | 152 |
| Plochy v `live-experience` | 136 | 152 |
| Akce navíc jen ve fyzických projekcích | 16 | 0 |
| Stránky UI | 20 | 20 |
| Stránky s trasou, poli, akcemi, stavy, panely a referenčním souborem v UI matici | 20 | 20 |
| Ovládací prvky v projekci | 226 | 242 |
| Plně sémanticky ověřené UI akce | 0 | 0 |
| Přímé vazby blokované třídou expozice | 4 historicky označené případy | 3 otevřené |

Výsledné rozdělení 152 akcí v `phase4-ui-action-matrix.json`: 16 statických/lokálních vazeb; 3 akce s blokovaným interním/automatizovaným cílem; 121 akcí bez doloženého mapování hodnot formuláře na request a jeho response/event použití; 12 dynamických dispatchů bez úplného výběru operace a validace specifické pro její schéma. Tyto skupiny nejsou prohlášeny za end-to-end ověřené.

Obnovených 16 akcí: `dashboard.contextChat`, `dashboard.copy`, `dashboard.detail`, `dashboard.files`, `dashboard.history`, `dashboard.inputs`, `dashboard.lastRun`, `dashboard.logs`, `dashboard.outputs`, `dashboard.remove`, `dashboard.restart`, `dashboard.start`, `dashboard.status`, `dashboard.stop`, `gen.editSpec`, `gen.reviewSpec`.

## Opravy

- Promítnuty byly původní definice akcí a vazeb, zachováno pořadí ze sledovaného UI registru a doplněno 16 odpovídajících `dashboardSurfaceBindings`. Následné projekce mají stejnou množinu 152 akcí; strojová kontrola ověřuje shodu obsahu, nikoli jen počet.
- `monitoring.repair` byl přesměrován z `monitor.repair.enqueue` (`AUTOMATED_MAINTENANCE`) na `component.repair.request` (`OWNER_COMMAND`). Odůvodnění je konkrétní: autoritativní UI akce používá `COMPONENT.REPAIR` a ostatní odpovídající OWNER repair akce používají tentýž facade. Mapování argumentů, response a chyb ale zůstává neověřeno.
- Z kandidátů `registered.repair` byla odstraněna přímá automatizovaná operace `monitor.repair.enqueue`; zůstaly tři doložené OWNER operace. Výběr cíle podle druhu objektu a payloadu stále nemá úplné per-operation mapování, proto dispatcher zůstává `NOT_VERIFIED`.
- `dashboard.start` → `runtime.instance.start` a `dashboard.stop` → `runtime.stop` jsou stále `AUTOMATED_MAINTENANCE`; `gen.editSpec` → `generation.spec.propose` je stále `INTERNAL_PROTOCOL`. Zkoumaný SSOT nedokládá ekvivalentní OWNER fasádu pro přesně stejný záměr. Nezaměnil jsem je za `component.enable/disable` nebo schválení specifikace a nepřeznačil expozici. Tyto tři UI akce jsou zachovány, ale blokovány do vyjasnění fasády.
- `scripts/regenerate_ui_projections.py` nyní čte vložené SSOT zdroje přímo, generuje i obě fyzické registry a má deterministický `--check`. Tím se zabrání tomu, aby 152 neautoritativních fyzických položek znovu převážilo nad vloženými zdroji bez kontroly. `scripts/build_parity.py` byl následně znovu spuštěn.
- UI matice nyní nese inventář všech 20 tras včetně polí, akcí, požadovaných stavů, panelů a HTML reference; počty polí/akcí regeneruje projekční skript z autoritativního registru. Do katalogu dialogů byly doplněny potvrzovací/impact-preview kontrakty obnovených `dashboard.stop`, `dashboard.restart` a `dashboard.remove`; první dvě akce zůstávají výslovně zakázány, dokud nebude vyřešena expozice.
- Opraven výchozí vstup vloženého `ui/scripts/verify_ui.py`: při spuštění z kořene dohledá `00_SSOT/KajovoCMLNG_SSOT.md` relativně ke skriptu místo neplatné cesty s poškozeným názvem. Obálka embedded resource má aktualizovaný digest a projekce je regenerována.
- Základ stacku byl sjednocen s normativním `live-experience.stack`: React/React DOM 18.3.1, Vite 6.3.5, XYFlow 12.8.5 a TanStack Table 8.21.3; srovnány také přesné Radix, CSV, Excel, PDF a dnd-kit verze. Rozpor ve čtyřech historicky označených hlavních balíčcích je 4 → 0. Verze byly ověřeny přes oficiální npm registry a izolovaný TypeScript probe.
- `@radix-ui/react-dropdown-menu`, `@tanstack/react-virtual` a `dompurify` zůstávají ve fyzickém rozšířeném stack kontraktu, ale nejsou součástí vloženého normativního stacku ani stávajícího compile probe. Nebyly odebrány ani povýšeny do SSOT bez rozhodnutí o jejich potřebnosti. V repozitáři není aplikační `package.json` ani lockfile; probe proto není produkční build.

## Kumulativní stav předávek a závislosti předchozích fází

> `audit/phase2-handoff-matrix.json` zůstává historickým artefaktem. Nová `phase4-current-handoff-matrix.json` byla znovu odvozena ze současného pracovního SSOT; identifikuje HEAD, branch, hash celé aktuální SSOT a manifest hashů vložených zdrojů, takže identita není založena pouze na HEAD. Ověřovač fáze 4 porovnává celý uložený obsah s čerstvým sestavením; pouhý hash zdroje nestačí. Historický PASS 77 obsahových kontrol nebyl automaticky přenesen jako důkaz po změně vstupů.

Aktuální graf obsahuje 619 operací, 19 generačních druhů uzlů, 14 integračních kroků, 66 specialist input pozic, 3 204 inventarizovaných hran a 1 009 kandidátních zdrojových výskytů. Zůstává 27 nemapovaných R11 pozic / 23 druhů artefaktů, 152 nerozhodnutých událostních hranic, 2 765 hran `NOT_VERIFIED` a 439 `BLOCKED_MISSING_CONTRACT`. To je aktualizovaný census, nikoli PASS kompatibility.

- Fáze 1 zůstává PARTIAL: 619 operací / 542 tras; 260 nerozlišených schema odkazů u 130 operací; 509 obecných tras; 8 selhání z 108 kontrol; 152 nevyjasněných event hranic.
- Fáze 2 zůstává PARTIAL: 27 R11 pozic / 23 druhů, 152 event hranic a sémanticky neuzavřený graf. Historická matice byla po změnách SSOT zastaralá; aktuální matice fáze 4 ji nenahrazuje ani zpětně nepřepisuje.
- Fáze 3 zůstává PARTIAL: dva konflikty schema identity jsou odstraněny, ale osm konečných stavových slovníků zůstává neuzavřeno; R11 → `ArtifactRef` hydratace a význam `BrowserPresencePointer.sequence` také. `secret.value.read` má opravený výsledkový kontrakt.
- `NO_PRESERVED_R10_MARKER` a `CONTRACT_PACK_DRIFT scripts/ssot/audit_checks.py` zůstaly ve výchozích kontrolách. Nezjistil jsem, že by bránily UI extrakci/projekci: přímý parser vložených UI bloků, checksumově kontrolovaný UI validátor a shoda generovaných projekcí prošly. Zůstávají však viditelnými blokátory globální integrity SSOT.

## Kontroly

Úspěšné kontroly jsou dílčí důkazy, ne uzavření fáze:

- `python scripts/regenerate_ui_projections.py --check` — exit 0; 152 akcí, 242 ovládacích prvků, žádná zastaralá projekce.
- `python scripts/verify_phase4_ui.py` — exit 0; 12 strukturálních/source checks PASS, 3 expoziční blokátory explicitně ponechány. Ověřuje přesnou rovnost celé současné handoff matice s čerstvou rekonstrukcí i zdrojový hash; hash samotný nestačí. Kontrola také selže, pokud `phase4-unresolved.json` vynechá některý expoziční blokátor.
- `python 01_UI_CONTRACT/ui/scripts/verify_ui.py` — exit 0; 20 stránek, 17 navigačních sekcí, 30 acceptance gates, 4 vložené zdroje.
- `python scripts/build_parity.py` — exit 0; 152 UI funkcí, 619 operací; report sám upozorňuje, že počty nedokládají sémantickou paritu.
- `python scripts/verify_experience.py` — exit 0; 21 statických stavových, expozičních, umístěňovacích a event fixture kontrol.
- `python scripts/verify_observability.py` — exit 0; 12 query/result/semantic kontrol.
- `python scripts/verify_ui_stack.py` — exit 0; metadata 14 normativních npm balíčků dohledána proti přesným oficiálním registry URL.
- `python scripts/probe_ui_stack.py` — exit 0; `npm install --ignore-scripts --no-audit --no-fund` i TypeScript 6.0.3 kompilace exit 0 na Node 24.18.1. Není to Ubuntu deployment ani produkční aplikace.
- `python scripts/verify_reference_interactions.py` — exit 0; 6 průchodů prototypu (CS/EN × desktop/tablet/mobile), klávesnice, touch, menu/dialog focus, bez horizontálního přetečení a JS chyb. Jde pouze o prezentační HTML prototyp bez backend volání.
- `git diff --check` — exit 0; Git pouze upozornil na obvyklé CRLF/LF normalizace již změněných souborů.

Izolovaný regresní běh `python scripts/phase4_run_regressions.py` provedl 14 příkazů: 9 exit 0, 5 exit 1. Historické soubory fází 1–3 zůstaly zachovány. Pět skutečných selhání (nepřepisováno ani nepovažováno za schválený baseline):

| Příkaz | Exit | Skutečný výsledek |
|---|---:|---|
| `python scripts/verify_schema_references.py` | 1 | 2 932 kontrolovaných odkazů, 260 selhání, žádný neparsovaný zdroj |
| `python scripts/verify_phase1_contracts.py` | 1 | 8 selhání z 108 kontrol |
| `python scripts/phase2_handoff_closure.py --check` | 1 | `MATRIX_COVERAGE_OR_CONTENT_DRIFT` — zachovaná historická matice fáze 2 neodpovídá dnešnímu SSOT |
| `python r11/scripts/verify_r11.py 00_SSOT/KajovoCMLNG_SSOT.md` | 1 | `NO_PRESERVED_R10_MARKER` |
| `python scripts/ssot/ssot_control.py 00_SSOT/KajovoCMLNG_SSOT.md --check` | 1 | `CONTRACT_PACK_DRIFT scripts/ssot/audit_checks.py: Embedded bytes differ` |

Nová současná matice fáze 4 je přesto znovu sestavena z aktuálních zdrojů a její source identity se ověřuje samostatně; historickou matici fáze 2 jsem neopravoval zpětně. Všech 14 výsledků včetně stdout/stderr je v `audit/generated/phase4-regression-checks.json`.

Přímý parser vložených UI/closure/experience zdrojů, jejich checksumy, fyzická projekce a vložený UI validator uspěly i přes `NO_PRESERVED_R10_MARKER` a `CONTRACT_PACK_DRIFT scripts/ssot/audit_checks.py`. Tyto chyby blokují obecný SSOT/R10 integrity gate, ale provedená extrakce ukazuje, že neblokují důvěryhodné načtení ani projekci UI. Marker ani očekávané hashe nebyly falešně doplněny. Vizuální ověření je omezeno na uvedenou referenční obrazovku; render/interakční běhy se týkají HTML prototypů, ne produkční aplikace.

## Otevřené blokátory a podklady pro fázi 5

1. Získat doloženou OWNER fasádu pro `dashboard.start`, `dashboard.stop` a `gen.editSpec`, nebo přesné normativní rozhodnutí, že taková uživatelská akce není povolena. Do té doby zůstávají cíle s `AUTOMATED_MAINTENANCE` / `INTERNAL_PROTOCOL` zakázané pro UI.
2. Doplnit pro 121 operacemi vázaných akcí skutečné zdrojové hodnoty polí, mapování requestu, validační schéma, použití response/event a chybové UI větve. U 12 dispatcherů určit úplný diskriminátor a validaci vůči konkrétně vybrané operaci. UI nesmí prezentovat pending/blocked jako dokončený úspěch.
3. Dovyřešit 27 R11 vstupů / 23 kind mapování, 152 událostních hranic, osm stavových slovníků, hydrataci reference a sequence semantics podle auditů fází 1–3.
4. Rozhodnout o třech doplňkových balíčcích mimo vložený stack a dodat skutečný lockfile/build + integrační test až v odpovídajícím implementačním rozsahu; tato fáze produkční aplikaci nevytváří.
5. Fáze 5 má převzít producer-specific chybové podmínky a error presentation, pravidla zobrazování/skrývání secrets a rozpory provozních politik. Musí také využít nyní opravené UI action registry a 3 zbývající expoziční případy.

Výstupy: `audit/phase4-ui-closure.md`, `audit/phase4-ui-action-matrix.json`, `audit/phase4-current-handoff-matrix.json` a `audit/phase4-unresolved.json`.
