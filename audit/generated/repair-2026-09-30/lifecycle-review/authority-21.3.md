### 21.3 MFA

TOTP MFA je pro interaktivní OWNER přihlášení povinné. Není-li dosud aktivní, první správné zadání username a hesla vytvoří pouze omezenou enrollment relaci, zobrazí QR kód i záložní manual seed pro autentizační aplikaci a vyžádá první šestimístný kód. Až jeho úspěšné ověření atomicky aktivuje MFA, označí relaci jako MFA-ověřenou a jednorázově zobrazí recovery codes; před dokončením enrollmentu nesmí relace volat MFA-chráněné endpointy. Další přihlášení vždy vyžadují TOTP nebo nepoužitý jednorázový recovery kód. Důvěryhodné zařízení má konfigurovatelnou dobu.

