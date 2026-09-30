### 8.9 OpenAI credential

OpenAI integration používá jediný Secret Manager stable name `OPENAI_API_KEY`. Stejná hodnota obsluhuje centrální chat, generation chat, technické generování, výzkum, AI agenty, evaluace, AI podporované Playwright iterace, development, testy, produkční provoz a další AI funkce.

Všechny OpenAI požadavky vznikají prostřednictvím oficiálních balíčků `openai` a `@openai/agents` a společné serverové `OpenAIClientService`. Responses API obsluhuje modelovou hranici a Agents SDK vícekolové agentní workflow. Volba modelu probíhá v UI nebo centrálním chatu a vždy vybírá model OpenAI.

Secret `OPENAI_API_KEY` se zadává, zobrazuje, mění a testuje v Password Manageru. Development a testovací nástroje získávají stejnou hodnotu přes kanonické API nebo přímo uvnitř důvěryhodného celku. Stav bez aktivního klíče zachovává plně spuštěnou aplikaci a označuje pouze AI capabilities stavem `OPENAI_CONFIGURATION_REQUIRED`. OpenAI client, request descriptor, capability, submit/retrieve a SDK recovery kontrakt určuje kapitola 52.

