# Rozhodnutí vlastníka zadání

Tento soubor je auditní evidence, nikoli druhý normativní zdroj.

| ID | Rozhodnutí | Původ |
|---|---|---|
| AUD-001 | Rozporná tvrzení připravenosti se nahradí výsledkem nového auditu. Předchozí PASS ani BLOCKED nejsou důkazem aktuálního stavu. | Výslovné rozhodnutí uživatele před schválením plánu. |
| AUD-002 | Autorita se odvozuje pouze z explicitního nahrazení konkrétní oblasti; samotné pořadí kapitol neurčuje přednost. Další skutečné rozpory rozhoduje uživatel. | Výslovná odpověď uživatele během realizace. |
| AUD-003 | Secrets, credentials, přístup chatu/modelu a logging zachovávají pravidla aktuálního SSOT. Požadavky zadání, které je mění, se nepoužijí. | Oprava zadání uživatelem před plánováním. |
| AUD-004 | Poškozené historické vložené podklady se zachovají pouze jako auditní historie s původními deklaracemi a skutečným hashem. Současná integrita se ověří nově; nelze tvrdit platnost původních hashů. | Výslovná odpověď uživatele během realizace. |
| AUD-005 | API explorer a paleta smějí spouštět pouze operace s doloženou OWNER dostupností. Interní a automatizované operace jsou dostupné pouze jako diagnostické informace. | Výslovná odpověď uživatele během realizace. |
| AUD-006 | Omezený výchozí retry profil smí doplnit chybějící číselné limity: nejvýše 3 opakování, prodlevy 500/1000/2000 ms a deterministický jitter 0–250 ms, s respektem k deadline a Retry-After. Pouze při výslovném oprávnění kanonické operace k replay; nejistý účinek, změněné zadání a lidský zásah automatické opakování nepovolují. Konkrétní existující policy má přednost. | Výslovné schválení uživatelem při pokračování auditu. |

Výchozí commit: `0ea5bf6b90ae4246956d1d76387ab540dc842f79`.
Výchozí pracovní strom byl čistý, větev `main`, remote `git@github.com:karelmartinek-a11y/kajovocmlng.git`.
