# Kontrola souběžných vzdálených změn

Výchozí lokální commit: `0ea5bf6b90ae4246956d1d76387ab540dc842f79`.
Na stejném ověřeném remote byly při fetch nalezeny commity `f3626be` a `d7e121bdc5f9c0b4aa0cc476f35178bacdfadd2e`.

Vzdálená větev mění 118 cest; 38 již existuje také v rozpracovaném lokálním výsledku. Nezapisující třícestný náhled hlavního SSOT obsahuje 10 konfliktních bloků. Náhled je pouze v pracovní cache, nikoli v normativním balíku. Skutečný merge dosud nebyl proveden a žádný push neproběhl.

## Rozhodnutí vlastníka

- AUD-007 čeká na odpověď: nová vzdálená pravidla Secrets omezují předávání hodnot modelu a zobrazení oproti výchozímu SSOT/AUD-003. Tato část se bez rozhodnutí neslučuje.
- AUD-008 čeká na odpověď: vzdálené `dashboard.start` / `dashboard.stop` volají automatizované operace. Návrh používá OWNER `component.enable` / `component.disable` pro zapnutí/vypnutí komponenty a odděluje práci s konkrétním během podle capability.

## Technická kontrola stacku

Vzdálené přesné npm verze byly ověřeny proti oficiálnímu registru; výsledek je v `generated/upstream-ui-package-evidence.json`. První striktní kompilace neprošla: dnd-kit 6.3.1 odkazuje na globální JSX namespace a TanStack Table 9 používá jiné API než verze 8.

Přizpůsobený probe používá `useTable({features, data, columns})` podle skutečných typů balíku 9.2.4. Úzký typový most deklaruje pouze `JSX.Element = React.JSX.Element` a `JSX.IntrinsicElements = React.JSX.IntrinsicElements`. S `skipLibCheck: false` kompilace prošla. Zdroj probe, jeho SHA256, hash package-lock a skutečný výstup jsou v `generated/upstream-ui-stack-adapted-probe.json`.

Tyto výsledky umožňují zachovat novější vzdálený stack při sjednocení, pokud se typový most a konkrétní API stanou součástí jeho reprodukovatelného technického kontraktu. Nejde o důkaz běhu produktu nebo instalace na produkčním Ubuntu.

## Evidence

- `generated/upstream-comparison.json`: soubory a jejich lokální/vzdálené SHA256.
- `generated/upstream-resource-comparison.json`: vložené zdroje a rozdíly jejich obsahu.
- `generated/upstream-ui-stack-probe.json`: původní neúspěšný compile probe.

Výsledky tohoto porovnání nesmějí být vydávány za validaci dosud nesloučeného celku.
