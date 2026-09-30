### 11.24 Centrální systémový AI chat

Centrální chat je kanonický platformní AI agent s vlastní component a runtime identitou. Používá stejný OpenAI runtime, strict tool binding compiler, guardrails, session model, tracing, approval a audit jako ostatní agenti.

Chat přijímá běžný jazyk a vrací lidský text spolu se strojově čitelnými action výsledky. Každá autentizovaná OWNER zpráva, která žádá akci, vytvoří immutable OWNER-intent candidate svázaný s message ID, selected object/browser contextem, explicitními target references a canonical message digestem. Server jej validuje a překládá na centrální object-action registry nebo generation workflow; modelová interpretace je proposal, nikoli samostatná autorita. Chat nemá zvláštní bypass binding, schema, confirmation, idempotency nebo lifecycle pravidel.

Persistentní konverzace, stream, attachments, tool calls, actions, correlation IDs a evidence jsou dostupné v UI i přes produkční API. Požadavek na vytvoření nové schopnosti založí nebo otevře generation job a zachová vazbu mezi chat conversation, OWNER message, specification a výslednými objekty.

Chat může založit, připojit, zobrazit a řídit browser session prostřednictvím Browser Interaction Plane. Browser session je explicitně svázaná s conversation ID, OWNER message, OWNER-intent digestem a operation contextem; model nepracuje s neurčitým „aktuálním browserem“. OWNER může ve zprávě vložit Browser target reference, například označené tlačítko, pole, text nebo část stránky. Chat před každou akcí ověří current runtime-build/host-or-bridge/context generation, session, page/page generation, frame attachment, document epoch, control epoch/fence, account/auth epoch, operation scope a target freshness. Před mutující akcí používá serverový action proposal s earliest mutation triggerem, postcondition a reconciliation class; chatové tvrzení samo není outcome.

