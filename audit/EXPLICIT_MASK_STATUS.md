# Audit explicitních JSON masek a návaznosti předávek

**Stav: BLOCKED.** Zdrojový snapshot je `main` / `581b4973a49923bee67ebc2b3ec3001584d61cf9`; SHA-256 souboru `00_SSOT/KajovoCMLNG_SSOT.md` je `e5ea095d389a2bb6cdc261e001f194db7885a2ec6ec031a80ca318832b375b7d`. Jediným zdrojem definic je současný text SSOT včetně vložených resources. Odvozené matice jsou pouze evidence.

## Autoritativní kontrola vloženého R9

`python scripts/audit_r9_masks.py` čte **přímo** aktuální bloky `KCML-R9-RESOURCE` z `00_SSOT/KajovoCMLNG_SSOT.md`. Kontroluje všech 21 vložených R9 resources, jejich dekódované bytes, deklarované SHA-256 a duplicitní JSON členy. Zdrojové `contracts/payload-contracts.json` má 519 604 dekódovaných řádků a 32 316 950 bytes; `contracts/operation-contracts.json` má 8 958 685 bytes. Skript postupně prochází všechny uzly každé request, response a event masky a zaznamenává všechny role všech 509 tras. Výstup s autoritativním JSON pointerem každé trasy je v `audit/generated/current-r9-mask-inventory.json`.

| Zjištění přímo z R9 | Počet | Důsledek |
| --- | ---: | --- |
| Operační záznamy / route záznamy | 586 / 509 | Aktuální vložený R9 katalog |
| Chybějící command/response schema identity | 260 u 130 operací | Odkaz nevede na deklarovanou R9 masku |
| Requesty s obecným `values` slotem | 509 | Doménové názvy a typy polí nejsou uzavřené |
| Response s obecným `values` slotem | 509 | Výstupní doménová maska není určená |
| Eventy s obecným `values` slotem | 509 | Událostní doménová maska není určená |
| Request `body` dovolující `null` | 507 | Nutná věcná revize pro každou operaci, u níž je tělo povinné |
| Nesoulad deklarovaných digestů R9 | 0 | Potvrzuje integritu bytes, nikoli úplnost masek |

§ 64.2 výslovně tvrdí, že každá route má vlastní request, response a event schéma se source-bound business payloadem. R9 skutečně obsahuje tři JSON Schema objekty pro každou route, avšak v každé z 1 527 hranic mají jejich hodnoty obecný `slot` bez `enum` či `const`; `canonicalJson` nemá doménové vnořené schéma. To je konkrétní nesoulad mezi textovým významem tvrzení a tím, co samotná maska přijímá. Bez rozhodnutí o přesných doménových polích, variantách a nullabilitě nelze bezpečně přepsat všech 509 tras.

## Rozšíření na současné efektivní operace a předávky

`python scripts/verify_mask_parity.py` rovněž načte celý aktuální SSOT (673 189 řádků) a rozšíří kontrolu na 619 efektivních operací včetně pozdějších explicitních specializací a na 3 204 modelovaných předávek. Každá hrana má samostatný záznam v `audit/generated/mask-parity.json`. Jde o mechanický průchod a kontrolu odkazů a digestů, **nikoli o lidské sémantické přečtení každého řádku** nebo potvrzení správnosti každého pole vůči business požadavkům.

| Zjištění z aktuálního SSOT | Počet | Důsledek |
| --- | ---: | --- |
| Efektivní operace / jejich trasy | 619 / 542 | Rozšířený rozsah včetně dalších specializací |
| Nerozlišené request/response odkazy | 260 u 130 operací | Není k dispozici deklarovaná maska dané identity |
| Trasy s obecnou obálkou | 509 | `values`/`canonicalJson` neomezují doménové pole a varianty |
| Unikátní obecné hranice | 1 527 | Jméno schema ID samo masku nekonkretizuje |
| Další konkrétní hranice bez sémantického potvrzení | 74 | Rozlišená reference není důkaz věcné úplnosti |
| Operace bez explicitního rozhodnutí o eventu | 152 | Nelze odhadnout event ani deklarovat jeho nepřítomnost |
| Předávky se stejným uvedeným digestem obou stran | 19 | I zde chybí úplný důkaz transportu, adapteru a větve |
| Předávky s chybějícím digestem na jedné / obou stranách | 20 / 3 165 | Nelze prokázat identickou vstupní a výstupní masku |
| Předávky označené `NOT_VERIFIED` / `BLOCKED_MISSING_CONTRACT` | 2 765 / 439 | Žádná modelovaná hrana nemá potvrzený úplný handoff |

`scripts/verify_schema_references.py` znovu prověřil 2 932 odkazů a vrátil 260 selhání. `scripts/phase1_schema_closure.py` i nová kontrola končí kódem 1. Nulový počet konfliktů schema identity a vnořených `$ref` selhání nedokazuje, že jsou payloady správné.

## Konkrétní svědci

- `agent.approval.request` v `contracts/operation-contracts.json` odkazuje na `urn:kcml:r9:operation:agent.approval.request:command` a `:response`; obě identity v aktuálních vložených definicích chybějí. Text § 11.12 určuje obsah approval requestu a § 51.21 transakci rozhodnutí, ale neurčuje úplné typy, povinnost, nullabilitu a výsledkovou masku této operace. Jejich vytvoření pouhým přejmenováním jiné masky by bylo nepodložené.
- `secret.create`, trasa `route.0386`, má `body.values` se slotem splňujícím obecný regulární výraz. Maska nepřiřazuje uzavřená jména slotů a typy hodnot pro patnáct druhů secretu z § 8.2; přijme i nevysvětlený slot. § 8.3 popisuje uložený secret a jeho verzi, nikoli přesnou vstupní variantu vytvoření, response a eventu. Současná obálka proto nesplňuje požadavek na explicitní doménovou masku.
- Hrana `specialist:AGENT_ARCHITECTInput:capabilityDecision` deklaruje stejný digest `CapabilityDecision` na obou stranách, ale její evidence výslovně uvádí neověřený převod `ArtifactRef` na kompaktní referenci R11. Shodný digest obsahu sám nepotvrzuje, že příjemce validuje stejné bytes a stejnou transportní obálku.
- § 66.1 tvrdí nulový počet unresolved pro popsaný výrobní řetězec. Toto tvrzení nelze použít jako důkaz uzavření současných operačních masek ani všech předávek: čerstvě odvozené kontraktní matice ukazují výše uvedené mezery. Normativní tvrzení a rozsah jeho platnosti vyžadují při opravě sladění.

## Předání k opravě

`audit/generated/current-r9-mask-inventory.json` obsahuje pro každý z 509 záznamů aktuálního R9 route ID, operation ID, role a přesný pointer i řádek v dekódovaném resource. `audit/generated/mask-parity.json` přidává každé modelované předání, oba digests a důvod neověření. Oprava musí pro každou operaci definovat skutečný doménový request, response a případný event v autoritativním SSOT, svázat výstup producenta s přijatým vstupem konzumenta včetně obálky a následně přepočítat embedded digests a odvozené projekce. Neznámé obchodní varianty se nesmějí nahradit `additionalProperties: true`, libovolným `values` slotem, volným JSON stringem ani univerzálním placeholderem.

Tento audit dosud neobsahuje 619 ručních sémantických rozhodnutí ani opravy chybějících masek. `CONTRACT CLOSED`, `IMPLEMENTATION READY` a `FREEZE READY` zůstávají neprokázané.
