### 7.2 Jediný OWNER API klíč

KájovoCML NG udržuje právě jeden produkční API credential se stable name `KCML_OWNER_API_KEY`. Klíč je kryptograficky náhodná hodnota nejméně 256 bitů, je uložen šifrovaně v Secret Manageru a pro ověření má samostatný constant-time hash a krátký fingerprint. Neobsahuje role, scopes, audience varianty, expiraci ani vazbu na uživatelský účet.

Klíč poskytuje plnou OWNER autoritu nad hlavním API i kanonickými komponentními HTTPS hranicemi. Volání používá:

```json
{
  "headerName": "Authorization",
  "implementation": "scripts/ssot/boundary_codecs.py:authorization",
  "credentialSource": "CURRENT_OWNER_API_OR_ENDPOINT_LOCAL_BINDING",
  "inputNeverFromModel": true
}
```

Po úspěšném ověření session nebo klíče server přiřadí konstantní access mode `OWNER_FULL`. Jde o větev v serverovém kódu, nikoli o roli, scope, permission záznam nebo konfigurovatelnou policy. Každá operace deklarovaná v OWNER operation catalogu je dostupná bez dalšího autorizačního rozhodnutí.

OWNER může klíč zobrazit, kopírovat a atomicky rotovat v UI nebo centrálním chatu. Existuje vždy právě jedna active verze; rotace uloží novou šifrovanou hodnotu a hash v jedné transakci a předchozí hodnotu ihned zneplatní. Protože je current hodnota revealable z platné OWNER session, ztracená odpověď po rotaci nezpůsobí lockout. Každé použití ukládá fingerprint, channel, source address, timestamp, correlation a audit.

Stable name `KCML_OWNER_API_KEY` je rezervovaný systémový Secret. Obecné Secret CRUD jej nesmí odstranit, přejmenovat, deaktivovat ani přepnout na jinou verzi; tyto requesty se směrují na read/reveal/rotate kontrakt této jediné credential nebo se odmítnou beze změny stavu.

Neexistuje token list, token CRUD, per-token policy, component access token, service token, JWT issuer ani obecný credential registry.

