# Závěrečný audit SSOT

Stav: **BLOCKED**. Strukturální kontroly: **PASS**. Freeze neproveden.

Rozsah: celý strom, vložené resources a kapsle, projekce UI, JSON/CSV, schémata, integrita a šest dílčích autoritativních validátorů. Automatické kontroly nejsou důkazem úplné ruční sémantické revize.

## Ověřené počty

- embeddedResources: 325
- capsuleResources: 21
- repositoryFiles: 284
- actions: 152
- controls: 242
- processFamilies: 34
- steps: 30
- statuses: 13
- errors: 288

## Skutečné blockery

### F-PAYLOAD

Business payloads are requirementId/canonicalJson bags; closed envelopes do not type individual domain fields.

Concrete domain input/output fields, constraints and positive/negative examples for each route; exact command/query profile bindings.

### F-ERROR

Inherited codes have class-level messages and unmaterialized domain predicates/retry bindings.

Review and define code-specific producer predicate, bilingual text and exact recovery binding; retain original semantics.

### F-PRVOPIS

Normative prose still contains provenance/precedence layers; lossless semantic consolidation is not complete.

Consolidate every overlapping norm, migrate historical explanation out of normative prose, prove no requirement lost with full traceability.

## Strukturální chyby

[]

Definitivní prvopis ani FREEZE READY se neprohlašuje. Přesné strojové důkazy a návratové kódy jsou v `final-audit.json`.
