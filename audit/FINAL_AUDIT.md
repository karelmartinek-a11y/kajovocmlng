# Audit výsledného SSOT balíku

Stav auditu: **ROZPRACOVÁNO — závěrečná kontrola dosud není uzavřena**.

Tento soubor zatím není důkazem dokončení ani nezávislého auditu. Kanonický obsah zůstává v `00_SSOT/KajovoCMLNG_SSOT.md`; auditní evidence je oddělená od normativní vrstvy.

Výchozí commit: `0ea5bf6b90ae4246956d1d76387ab540dc842f79`, větev `main`. Přesnou identifikaci výsledného stavu musí po dokončení obsahových změn doložit hash manifest a kontrolní účtenka.

## Dosavadní ověření

- Existující brány R10, R16, UI, CLOSURE a R17 prošly; jejich rozsah nepokrývá všechny nově zjištěné nedostatky.
- Nové kontraktní kontroly prověřují stavové přechody, události, lokalizační klíče, parity bindings, OWNER dispatchery, chybové zprávy a omezený retry profil.
- Podle AUD-004 byly zachovány skutečné bajty osmi poškozených historických artefaktů v `provenance`; původní deklarované hashe se nevydávají za platné.
- Podle AUD-005 smějí obecné dispatchery nabízet pouze 480 doložených OWNER operací.
- Kontrola 40 původních Secrets/credential sekcí proti výchozímu commitu potvrdila zachování jejich obsahu.

Aktuální konkrétní výsledky jsou v `generated`. Starší výsledek nad jiným hashem není potvrzení aktuálního obsahu.

## Otevřené části kontroly

- Kontrola konkrétních schémat odhalila 260 nerozlišených schema ID pro 130 operací. Seznam je v `generated/schema-reference-validation.json`. Existující registr je označuje za úplné operace, ale samotná deklarace nenahrazuje definici schématu.
- Některé route payloady mají obecné `values`/`canonicalJson` místo uzavřených doménových vstupů. Je nutné posoudit jejich konkrétní význam a authoritative vazby.
- Dokončuje se celobalíková lokalizační, vizuální a sémantická kontrola starších UI podkladů a vložených vrstev.
- Dokončuje se oddělení historických formulací od normativního prvopisu, indexy, regenerace souvisejících podkladů a finální integrita.

## Gate

Kritéria jsou uvedena v `../QUALITY_ASSURANCE.md`. Žádný cílový status není v této rozpracované podobě přiznán: FORENSICALLY COMPLETE, IMPLEMENTATION READY, VISUALLY CLOSED, CONTRACT CLOSED a FREEZE READY zůstávají **BLOCKED / neprokázáno** do uzavření příslušných povinných kontrol.
