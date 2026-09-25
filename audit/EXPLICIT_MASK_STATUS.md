# Stav explicitních kontraktů v aktuálním SSOT

**BLOCKED — program zatím není připraven k bezchybné generaci.** Jedinou autoritou je `00_SSOT/KajovoCMLNG_SSOT.md`, včetně dekódovaného katalogu R9. Aktuální SHA-256 celého dokumentu je `115ef4a1c530e7abd6f36cc79c54da9831dcbd1a668d44e9cf15ece882817cb9`.

## Uzavřené v tomto kroku

Kontrakty `route.0000` (`component.control.enable`) a `route.0001` (`component.control.disable`) mají konkrétní povinnou vstupní masku s rozlišeným `desiredState`, command ID, logical operation ID, důvodem, correlation/causation, deadline, digestem, idempotency key, target lineage a state/version guardy. Výstupní `response.output` a navazující `event.payload` používají **stejný JSON Schema objekt a schema ID**. Maska výslovně odmítá `body: null` i dřívější obecný `values` kontejner. Podmínky pro `ACCEPTED` rozlišují durable admission a dokončení efektu; `UNKNOWN` vyžaduje reconciliation. Technický tvar je odvozen z textu § 42.1.1, 44.4, 44.5 a 49.22. Editace je reprodukovatelná pomocí `scripts/close_component_control_masks.py` a je vložená do samotného R9.

Schémata request, response a event obou tras prošla kontrolou Draft 2020-12. Negativní request s `body: null` je odmítnut a výstupní maska je totožná se vstupem navazující události. `scripts/audit_r9_masks.py` znovu prošel všechny fyzické R9 resources a jejich SHA-256; nevrátil žádný digest mismatch. Oba audity správně končí nenulovým kódem, protože nezbylé kontrakty nejsou uzavřené.

## Aktuální otevřené odchylky

| Kontrola | Zbývající počet | Význam |
| --- | ---: | --- |
| Generické R9 request / response / event masky | 507 / 507 / 507 | Doménová pole a varianty nejsou vymezena |
| R9 request masky připouštějící `body: null` | 505 | Povinnost těla vyžaduje věcnou kontrolu podle operace |
| Chybějící command/response identity v R9 | 260 u 130 operací | Záznam odkazuje na nedefinovanou masku |
| Efektivní operace a trasy v celém SSOT | 619 / 542 | Zahrnují pozdější explicitní specializace |
| Obecné efektivní hranice | 1 521 | Širší audit `scripts/verify_mask_parity.py` |
| Neověřené předávky | 3 204 | Shoda digestu sama nedokazuje stejný transport a adaptér |
| Digest mismatch vložených R9 resources | 0 | Integrita není sémantická úplnost |

Soubor `audit/generated/current-r9-mask-inventory.json` ukazuje pro každou R9 trasu jednotlivé role, zdrojový JSON pointer a aktuální generičnost. `audit/generated/mask-parity.json` je širší odvozená evidence; žádná auditní matice nenahrazuje aktuální SSOT. Následující kontrakty musí dostat konkrétní masku podle vlastního textu SSOT, být provázány na jejich konzumenty a znovu projít celým auditem. Stav `CONTRACT CLOSED` ani `FREEZE READY` zatím nelze prohlásit.
