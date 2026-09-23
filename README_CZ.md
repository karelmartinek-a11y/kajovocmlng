# KájovoCMLNG — SSOT balík

Kanonický dokument je [00_SSOT/KajovoCMLNG_SSOT.md](00_SSOT/KajovoCMLNG_SSOT.md). Vložené strojové kontrakty jsou jeho autoritativní součástí; soubory v `01_UI_CONTRACT` jsou příslušné projekce. Auditní evidence není druhý zdroj normativních pravidel.

Balík obsahuje specifikaci a prezentační podklady, nikoli implementaci produktu. Aktuální stav a neuzavřené kontroly uvádí [audit](audit/FINAL_AUDIT.md). Platnost celého balíku nelze odvodit z úspěchu jedné validační sady.

- [UI reference](03_UI_REFERENCE/index.html), [Dashboard](03_UI_REFERENCE/pages/dashboard.html), [English Dashboard](03_UI_REFERENCE/pages/dashboard-en.html).
- [Matice funkcí](01_UI_CONTRACT/FUNCTION_PARITY.csv) a [matice nových pohledů](01_UI_CONTRACT/LIVE_VIEW_MATRIX.csv).
- [Způsob ověřování](QUALITY_ASSURANCE.md), [rozhodnutí vlastníka](audit/DECISIONS.md), [technická revize UI](audit/UI_TECHNICAL_REVIEW.md).
- [Pracovní plán auditu](audit/WORK_PLAN.md); `audit/generated` obsahuje výsledky skutečně spuštěných kontrol.

Změny kanonických vložených JSON kontraktů se promítají pomocí `python scripts/project_experience.py`. Kontrola shody používá `--check`. Návrhy vytváří `python scripts/render_live_views.py --render`, anglické rendery stejný příkaz s `--locale en`. Všechny provozní příklady jsou označená ukázková data.

Manifesty spravuje `scripts/package_integrity.py`. Výjimky z hashování jsou explicitní a neobsahují normativní dokumenty. Hash manifest nehashuje sám sebe; výsledná kontrolní účtenka odkazuje na jeho konečný SHA256.

Tato práce neprovádí freeze, release, produkční nasazení ani reálné externí obchodní operace. Případné schválení FREEZE READY musí vycházet z doloženého výsledku všech povinných kontrol a z následného nezávislého auditu.
