# Stav explicitních kontraktů v aktuálním SSOT

**BLOCKED — program zatím není připraven k bezchybné generaci.** Jedinou autoritou je `00_SSOT/KajovoCMLNG_SSOT.md`, včetně dekódovaného katalogu R9. Aktuální SHA-256 celého dokumentu je `4ee82539e50ce3b538f58d18b03206aef28ab7607201e878f15a61e8cb783450`.

## Uzavřené v tomto kroku

Kontrakty `route.0000` (`component.control.enable`) a `route.0001` (`component.control.disable`) mají konkrétní povinnou vstupní masku s rozlišeným `desiredState`, command ID, logical operation ID, důvodem, correlation/causation, deadline, digestem, idempotency key, target lineage a state/version guardy. Výstupní `response.output` a navazující `event.payload` používají **stejný JSON Schema objekt a schema ID**. Maska výslovně odmítá `body: null` i dřívější obecný `values` kontejner. Podmínky pro `ACCEPTED` rozlišují durable admission a dokončení efektu; `UNKNOWN` vyžaduje reconciliation. Technický tvar je odvozen z textu § 42.1.1, 44.4, 44.5 a 49.22. Editace je reprodukovatelná pomocí `scripts/close_component_control_masks.py` a je vložená do samotného R9.

Schémata request, response a event všech čtyř upravených tras prošla kontrolou Draft 2020-12. Negativní request s `body: null` je odmítnut a výstupní maska je totožná se vstupem navazující události. `scripts/audit_r9_masks.py` znovu prošel všechny fyzické R9 resources a jejich SHA-256; nevrátil žádný digest mismatch. Oba audity správně končí nenulovým kódem, protože nezbylé kontrakty nejsou uzavřené.

## Aktuální otevřené odchylky

| Kontrola | Zbývající počet | Význam |
| --- | ---: | --- |
| Generické R9 request / response / event masky | 505 / 505 / 505 | Doménová pole a varianty nejsou vymezena |
| R9 request masky připouštějící `body: null` | 503 | Povinnost těla vyžaduje věcnou kontrolu podle operace |
| Chybějící command/response identity v R9 | 260 u 130 operací | Záznam odkazuje na nedefinovanou masku |
| Efektivní operace a trasy v celém SSOT | 619 / 542 | Zahrnují pozdější explicitní specializace |
| Obecné efektivní hranice | 1 515 | Širší audit `scripts/verify_mask_parity.py` |
| Neověřené předávky | 3 204 | Shoda digestu sama nedokazuje stejný transport a adaptér |
| Digest mismatch vložených R9 resources | 0 | Integrita není sémantická úplnost |

Soubor `audit/generated/current-r9-mask-inventory.json` ukazuje pro každou R9 trasu jednotlivé role, zdrojový JSON pointer a aktuální generičnost. `audit/generated/mask-parity.json` je širší odvozená evidence; žádná auditní matice nenahrazuje aktuální SSOT. Následující kontrakty musí dostat konkrétní masku podle vlastního textu SSOT, být provázány na jejich konzumenty a znovu projít celým auditem. Stav `CONTRACT CLOSED` ani `FREEZE READY` zatím nelze prohlásit.

Bezprostředně následující `route.0002` (`component.state.query`) podle § 44.2 vyžaduje bounded state keys a pro každý klíč typovaný payload se schema/payload digestem. V aktuálních vložených zdrojích zatím není uzavřená konečná mapa `state key → payload schema`, kterou by šlo bezpečně vložit jako `oneOf`/diskriminátor do této odpovědi. Volný JSON nebo řetězec s digestem by tento požadavek nesplnil. Tuto trasu proto audit ponechává jako otevřenou; při jejím návrhu musí vzniknout i autoritativní mapa stavových klíčů a jejích přesných schémat.

## Další dvě doplněné trasy

`route.0003` (`component.heartbeat`) používá původní vloženou masku `ComponentHeartbeat` se všemi deseti závislými definicemi, konkrétní potvrzení přijetí podle § 44.1 a totožnou masku v response/event. `route.0004` (`component.control.ack`) má povinný ACK status, lineage, source sequence, digesty a observed state podle § 44.5 a 49.22; výstupní potvrzení zpracování je identické v response/event. Komponentové target guardy u enable/disable jsou po opravě určeny pouze jednou v request envelope, takže dvě rozdílné kopie téže hodnoty nemohou projít validací. Jejich kompatibilita se všemi dalšími konzumenty stále vyžaduje sémantické potvrzení.
