# Checkpoint dokončení SSOT

Tento checkpoint zachycuje stav aktuálního pracovního stromu. Nenahrazuje
normativní SSOT ani nepřepisuje historické auditní výsledky.

## Vstup

- větev: `work/ssot-completion-2026-09-25`
- výchozí HEAD: `d5bda02` (`Merge audit explicit mask parity`)
- SSOT: `00_SSOT/KajovoCMLNG_SSOT.md`
- SHA-256 SSOT: `4EE82539E50CE3B538F58D18B03206AEF28AB7607201E878F15A61E8CB783450`
- stav při založení větve: čistý pracovní strom

## Aktuální odvozené počty

Počty jsou jednotky aktuálního inventáře, nikoli počty z původního zadání:

| Jednotka | Počet | Definice |
|---|---:|---|
| efektivní operace | 619 | operace po aplikaci účinných overlay vrstev |
| transportní trasy | 542 | konkrétní route/boundary z aktuální projekce |
| nevyřešené odkazy | 260 | role/maska s chybějící definicí schema identity |
| operace s nevyřešenými odkazy | 130 | unikátní operace z předchozího řádku |
| obecné trasy | 509 | trasy s `values`/`canonicalJson` nebo jiným neuzavřeným slotem |
| obecné hranice | 1 527 | hranice, jejichž tvar není doložen konkrétní doménovou maskou |
| nevyjasněná aplikovatelnost eventu | 152 | operace bez normativního event/no-event rozhodnutí |
| matrix rows | 3 204 | inventarizační řádky; nejsou automaticky runtime předávky |

Zdroj souhrnu: `audit/phase1-unresolved.json` a
`audit/phase4-unresolved.json`, obojí musí být vždy interpretováno vůči
hashi aktuálního SSOT.

## Otevřené blokátory

- `ArtifactRef` nemá doložený bezztrátový hydratační adapter;
- 8 stavových/disposition polí připouští `NOT_A_VALID_STATE`, ale SSOT neurčuje
  autoritativní konečné slovníky a guards;
- vazba R11 `schemaDigest` na `bundleDigest`/vybranou definici a okamžik
  mismatch není normativně určena;
- 260 schema odkazů, 509 obecných tras a 152 eventových hranic zůstává
  neuzavřených;
- Phase 2 eviduje 27 nemapovaných R11 vstupních pozic, 23 druhů a 152 event
  blockerů; 3 204 řádků matice není důkazem kompatibility runtime předávek;
- UI audit obsahuje neověřené mapování argumentů/response/event pro akce a
  dynamické dispatchery;
- některá rozhodnutí vyžadují výslovné rozhodnutí OWNERa, nikoli technickou
  opravu validátoru.

## Stav gate

Výsledek je `BLOCKED`, nikoli `PASS`. Nebyl proveden merge do `main` ani freeze.
Historické `PASS` výsledky nejsou použitelné bez shody jejich vstupního hashe.

## Reprodukce

```powershell
Get-FileHash 00_SSOT/KajovoCMLNG_SSOT.md -Algorithm SHA256
python scripts/operation_catalog.py
python scripts/audit_inventory.py
python scripts/verify_schema_references.py
python scripts/verify_mask_parity.py
```

