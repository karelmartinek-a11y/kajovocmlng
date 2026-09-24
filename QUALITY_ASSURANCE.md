# Ověřování SSOT balíku

Kontroly se spouštějí z kořene repozitáře. Python závislosti jsou připnuté v `requirements-audit.txt`; renderování navíc vyžaduje `python -m playwright install chromium`. Instalace závislostí není důkaz ověření kontraktů.

| Kontrola | Příkaz | Důkaz v `audit/generated` |
|---|---|---|
| Inventář, formáty, vložené hashe a komprimované podklady | `python scripts/audit_inventory.py` | `inventory.json` |
| Pět existujících SSOT bran | `python scripts/run_baseline_gates.py` | `baseline-gates.json` |
| Stavy, události, lokalizace a parity bindings | `python scripts/verify_experience.py` | `experience-validation.json` |
| Chybový registr a negativní případy | `python scripts/verify_errors.py` | `error-validation.json` |
| Priorita a podmínky klasifikace poskytovatelů | `python scripts/verify_provider_mapping.py` | `provider-mapping-validation.json` |
| Omezený retry profil a jeho zákazy | `python scripts/verify_retry_profile.py` | `retry-validation.json` |
| Historické dotazy a úplnost dat | `python scripts/verify_observability.py` | `observability-validation.json` |
| Konkrétní odkazy na command/response schémata | `python scripts/verify_schema_references.py` | `schema-reference-validation.json` |
| Strukturální matice hranic fáze 1 | `python scripts/phase1_schema_closure.py` | `audit/phase1-operation-schema-matrix.json`, `audit/phase1-unresolved.json` |
| Negativní případy a otevřené doménové mezery | `python scripts/verify_phase1_contracts.py` | `phase1-contract-tests.json`, `phase1-fixtures.json` |
| Reprodukce oprav z výchozího commitu | `python scripts/phase1_repair_contracts.py --verify-from-baseline` | `phase1-reproduction.json` |
| Zachování pravidel Secrets | `python scripts/verify_preserved_policy.py` | `preserved-policy.json` |
| Shoda projekcí | `python scripts/project_experience.py --check` | výstup příkazu; zahrnuto v experience validation |
| Inventář UI a operací | `python scripts/build_parity.py` | `function-parity.json` |
| Pokrytí chyb | `python scripts/audit_errors.py` | `error-coverage.json` |
| Prezentační interakce | `python scripts/verify_reference_interactions.py` | `reference-interactions.json` |
| Metadata vybraných UI verzí | `python scripts/verify_ui_stack.py` | `ui-package-evidence.json` |
| Instalace a striktní typová kompatibilita UI knihoven | `python scripts/probe_ui_stack.py` | `ui-stack-probe.json` |
| Render CS / EN | `python scripts/render_live_views.py --render [--locale en]` | `live-render-checks*.json` |

Selhání se neopravuje oslabením testu. Negativní případy musí zůstat odmítnuté. Referenční testovací oracle není implementace backendu. Kontrola přetečení nezastupuje vizuální kontrolu čitelnosti, překryvů a funkční konzistence.

## Kritéria výsledných gate

| Gate | Nutné podmínky |
|---|---|
| FORENSICALLY COMPLETE | Úplný inventář všech vrstev, dohledatelná autorita a pokrytí, žádný nevypořádaný rozpor nebo nekontrolovaný normativní obsah. |
| IMPLEMENTATION READY | Konkrétní schémata vstupů a výstupů, uzavřené lifecycle a recovery, ověřený stack, přesná realizovatelná rozhraní bez povinných chybějících rozhodnutí. |
| VISUALLY CLOSED | Povinné stavy a viewporty mají aktuální render, vizuální kontrolu, přístupné ovládání, úplnou CS/EN lokalizaci a vazbu na platné kontrakty. |
| CONTRACT CLOSED | Každá operace, událost, chyba a přechod má úplný kontrakt; reference se rozlišují na konkrétní platné cíle; negativní testy odmítají porušení pravidel. |
| FREEZE READY | Všechny předchozí gate splněné, aktuální manifesty a hash integrita, žádný neuzavřený povinný požadavek. Samotný freeze není povolen. |

Výsledek rozhoduje audit, nikoli existence souboru nebo počet položek. Tato vlastní kontrola není nezávislý audit.

## Pořadí závěrečné kontroly a integrity

Po každé opravě se zopakují dotčené kontroly. Před uzavřením se spustí celá sada nad finálním obsahem. Auditní výsledky musí vzniknout před posledním hashováním. Následuje `python scripts/package_integrity.py --generate` a `python scripts/package_integrity.py --receipt`; po poslední změně znovu `python scripts/package_integrity.py`.

Hashují se přesné bajty všech souborů balíku včetně auditní evidence. Vyloučeny jsou `.git`, `.cache`, `__pycache__` a `node_modules`, protože jde o historii Gitu nebo pracovní a instalační výstupy. Explicitní výjimky ze souborů jsou samotný `FILE_MANIFEST_SHA256.json` a následná `audit/generated/integrity-receipt.json`, která uvádí jeho hash. Tyto výjimky řeší sebeodkazování; nemohou být rozšířeny bez změny a kontroly pravidel integritního skriptu.
