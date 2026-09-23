# Ověření zdrojů pro klasifikaci chyb

Ověřeno čtením oficiálních podkladů dne 2026-09-23, bez přihlášení k účtu a bez volání provozního API.

- [OpenAI error codes](https://developers.openai.com/api/docs/guides/error-codes): autentizace, přístup, rozdíl mezi omezením rychlosti a vyčerpaným kreditem či limitem útraty, nedostupnost služby. Adaptér rozlišuje billing dříve než obecný HTTP 429; neodvozuje kategorii z textu zprávy.
- [OpenAI rate limits](https://developers.openai.com/api/docs/guides/rate-limits): omezené opakování s prodlevou. Číselné limity KájovoCMLNG určuje schválený profil AUD-006, nikoli tvrzení, že je stanovuje poskytovatel.
- [PostgreSQL 18 SQLSTATE](https://www.postgresql.org/docs/18/errcodes-appendix.html): třída 23 označuje porušení integrity, 40001 selhání serializace a 40P01 deadlock. Detekce používá kód, nikoli lokalizovanou zprávu.

Pravidla jsou vložena v kanonickém `ui/contracts/error-presentation.json`. Tento dokument je evidence zdrojů, nikoli alternativní definice adaptéru. Pokrytí obecných tříd neprokazuje úplnost všech poskytovatelů ani bezpečnost replay konkrétní operace.
