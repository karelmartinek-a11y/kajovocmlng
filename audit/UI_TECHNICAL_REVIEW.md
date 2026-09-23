# Technická revize UI

## Rozsah důkazu

Konkrétní frontendový framework nebyl nalezen v čitelných normativních kapitolách ani v přímých vložených zdrojích. Stávající reference jsou HTML/CSS/JavaScript. Specifikace zachovává TypeScript a Node baseline SSOT; nedoplňuje další runtime infrastrukturu.

Výběr je uložen v kanonickém `ui/contracts/live-experience.json`, jehož autoritou je vložený blok v hlavním SSOT. Přesné vydané verze, licence, peer dependencies, engines a integrita distribučních balíků jsou doložené odpověďmi oficiálního npm registru v `generated/ui-package-evidence.json`. Tyto důkazy nejsou testem kompatibility celé aplikace.

| Capability | Konkrétní realizace | Ověřený podklad a omezení |
|---|---|---|
| Graf, uzly, hrany, pan/zoom, minimapa | React Flow 12.8.5 | [ReactFlow API](https://reactflow.dev/api-reference/react-flow), [Controls](https://reactflow.dev/api-reference/components/controls), [přístupnost](https://reactflow.dev/learn/advanced-use/accessibility). Klávesnicové přesuny nejsou náhradou formuláře pro propojení portů. |
| Kontextové menu, dialog, tooltip a touch nápověda | Radix Primitives, přesné verze v registru | [Context Menu](https://www.radix-ui.com/primitives/docs/components/context-menu), [úvod](https://www.radix-ui.com/primitives/docs/overview/introduction). Tooltip samotný nepokrývá touch; použije se explicitní tlačítko a popover. |
| Tabulky | TanStack React Table 8.21.3 | [Dokumentace v8](https://tanstack.com/table/v8/docs/overview). Headless knihovna; návrh vyžaduje vlastní markup, stránkování a přístupnost. |
| Drag and drop | React Flow pro graf; dnd-kit pro seznamy | Přesné release a peer metadata ověřena v npm. Klávesnicové a touch chování celého produktu vyžaduje integrační test. |
| Live vizualizace | SVG/CSS a EventSource | Efekty jsou projekcí backend událostí; knihovna neřeší korelaci, deduplikaci ani business stav. Referenční reducer má negativní testy. |
| CSV, Excel, PDF | PapaParse, ExcelJS, PDF.js | Přesné release a licence ověřeny v npm. Návrh nepoužívá spouštění maker ani výpočty Excel vzorců. Ostatní formáty mají stažení originálu. |

Webová dokumentace je průběžně aktualizovaná; její aktuální znění se nesmí vydávat za garantovanou dokumentaci každé uzamčené verze. Verze balíků jsou ověřené odděleně. Kompatibilita všech kombinací a cílového Ubuntu není prokázána pouhým renderem HTML.

## Grafické podklady

Generátor `scripts/render_live_views.py` vytváří 12 stavů a 48 renderů. HTML podklady používají SVG, formuláře a CSS odpovídající navrženým komponentám. Jejich interakce jsou pouze prezentační a každá stránka trvale uvádí ukázková data. Nevolají provozní backend.

Mobilní zobrazení používá čitelný seznam uzlů a jejich vazeb místo zmenšení celého grafu na nečitelné popisky. Desktop a tablet mají graf a explicitní nabídku akcí. Provozní animace nejsou v mockupu vydávány za aktuální komunikaci.

## Neuzavřené důkazy

- Instalace přesných verzí a striktní TypeScript probe prošly s React 18.3.1; důkaz je v `generated/ui-stack-probe.json`. Původní neúspěšný pokus s React 19 je zachován v `provenance/ui-stack-first-probe.json`. Ověření proběhlo na místním Node 24.18.1, nikoli na cílovém Ubuntu s Node 24.21.0. Produktová runtime kompatibilita tím není prokázána.
- Anglické klíče kontraktu jsou ověřované; veškerý starší UI obsah a všechny texty grafických návrhů ještě vyžadují úplnou lokalizační kontrolu.
- Absence horizontálního přetečení není automatickým důkazem čitelnosti nebo úplné přístupnosti.
