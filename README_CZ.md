# KájovoCML NG — SSOT pro přípravu vývoje

Stav balíku: **BLOCKED před freeze**. Definitivní prvopis a úplná implementační připravenost se zatím neprohlašují. Konkrétní důvody, počty a provedené kontroly jsou v [závěrečném auditu](audit/FINAL_AUDIT.md) a [strojovém výsledku](audit/final-audit.json).

## Kanonické podklady

- [Hlavní SSOT](00_SSOT/KajovoCMLNG_SSOT.md): normativní text a vložené kontrakty. Identita vloženého zdroje je dvojice `(family, path)`.
- [UI registry](01_UI_CONTRACT/ui/contracts/ui-control-registry.json) a [přesné operace](01_UI_CONTRACT/closure/contracts/ui-action-resolution.json): synchronizované projekce vložených UI/CLOSURE resources.
- [Procesní zobrazení](01_UI_CONTRACT/ui/contracts/process-visual-registry.json), [event schema](01_UI_CONTRACT/ui/contracts/live-event.schema.json), [live stream](01_UI_CONTRACT/ui/contracts/live-stream-policy.json).
- [Registr chyb a hlášek](01_UI_CONTRACT/ui/contracts/error-message-registry.json): přesně označuje i neuzavřené doménové podmínky původních kódů.
- [Historie programu](01_UI_CONTRACT/ui/contracts/observability-query-contract.json), [strukturované zadání](01_UI_CONTRACT/ui/contracts/solution-planning-contract.json), [Secrets](01_UI_CONTRACT/ui/contracts/secrets-channel-parity.json).
- [UI funkční parita](01_UI_CONTRACT/UI_FUNCTION_PARITY.csv): odvozená matice, nikoli alternativní command registry.
- [Technický UI stack](01_UI_CONTRACT/ui/contracts/ui-stack-contract.json), [vazby vizualizací A–L](01_UI_CONTRACT/ui/contracts/visual-artifact-bindings.json), [index grafiky](06_UI_OVERVIEWS/VIEW_INDEX.md).

## Kontroly

Python 3.11+ a `jsonschema` jsou potřeba pro validaci. Pillow a Playwright slouží pouze k regeneraci grafiky.

```bash
python scripts/verify_package.py
python scripts/verify_package.py --freeze
```

První příkaz kontroluje strukturu a integritu. Druhý navíc odmítne všechny skutečné obsahové blockery. Úspěch prvního neznamená FREEZE READY. Vložené historické auditní PASS nejsou aktuálním certifikátem balíku. Archivní fragment s `authority=AUDIT_ONLY` není produkční skript; případné syntaktické poškození zůstává výslovně uvedené v auditu.

## Referenční UI

```bash
python -m http.server 8765
```

Otevřete `http://localhost:8765/03_UI_REFERENCE/pages/dashboard.html`. Přepínač referenčních stavů zpřístupňuje 12 scénářů. Data jsou výslovně označené fixtures. Akce zobrazují přesný kontrakt; referenční dokumentace neprovádí produkční operace a nevytváří fiktivní úspěch.

Regenerace:

```bash
python scripts/regenerate_ui_projections.py
node scripts/render_reference.mjs
python scripts/render_overviews.py
python scripts/refresh_embedded_integrity.py
python scripts/verify_package.py --write-audit --skip-manifest
python scripts/update_manifests.py
python scripts/verify_package.py
```

`render_reference.mjs` přijímá `PLAYWRIGHT_MODULE` a případně `CHROMIUM_PATH`. Spustí vlastní lokální statický server. Produkční runtime je samostatný implementační cíl na Ubuntu a není předmětem tvrzení o vykreslení referencí.

`PACKAGE_MANIFEST.json` inventarizuje obsah. `FILE_MANIFEST_SHA256` pokrývá každý soubor kromě sebe sama, včetně package manifestu. Vlastní integritu hashového manifestu poskytuje Git blob a commit. Celý strom je verzovaný přímo na `main`; nevzniká druhá kopie SSOT ani jiná větev.
