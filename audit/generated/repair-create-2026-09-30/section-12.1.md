### 12.1 Účel generátoru

Generátor KájovoCML převádí OWNERem schválený funkční záměr na aktivovaný, monitorovaný a rollbackovatelný soubor komponent. Generátor vyrábí nebo aktualizuje:

- MCP server,
- MCP tool, resource nebo prompt,
- AI agenta,
- AI agent tool adapter,
- agent-as-tool nebo handoff vazbu,
- platformní komponentu,
- managed runtime,
- external API connector,
- webhook handler,
- PULSE integration,
- browser automation,
- webové OWNER UI pro generovanou schopnost,
- supporting schemas, bindings, tests, monitoring a dokumentaci.

Generátor je deterministicky řízený výrobní systém. OpenAI model analyzuje, navrhuje a vytváří typované kandidáty; serverová state machine, schemas, validátory, testy, exact bindings, workery a activation controller rozhodují o každém autoritativním zápisu a provozním side effectu.

