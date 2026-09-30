### 12.18 OWNER otázky a automatická technická rozhodnutí

Systém žádá OWNERa pouze o:

- business význam a požadované chování,
- explicitní pravidlo nebo prioritu,
- účet, credential, URL, identifikátor, obsah nebo soubor, který nelze odvodit,
- rozhodnutí mezi skutečně odlišnými business výsledky,
- OpenAI model.

Technické naming, IDs, schemas, timeouts, retries, leases, queues, resource limity, monitoring, testy, code structure a deployment systém odvozuje a validuje automaticky.

Open question obsahuje exact field path, důvod, možné volby, dopad a source evidence. Schválení je blokované pouze otázkou, která mění funkční kontrakt nebo vyžaduje chybějící OWNER input. Technická nejistota se řeší výzkumem, capability lookupem nebo validator experimentem.

