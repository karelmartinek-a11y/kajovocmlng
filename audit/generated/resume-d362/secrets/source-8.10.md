### 8.10 Password Manager UI

Stránka **Secrets a hesla** obsahuje:

- search a filtry,
- skupiny a tags,
- tabulku a card view,
- stav, typ, expiraci, verzi a usage count,
- rychlé reveal/copy/edit/rotate/bind/delete akce,
- detail s plnou hodnotou,
- versions timeline,
- bindings matrix,
- usage graph,
- TOTP kód a countdown,
- import/export,
- bulk actions,
- audit a live logs.

Po bootstrapu se provozní secrets spravují prostřednictvím tohoto UI či centrálního chatu. Výjimkou je deployment heslo `PASS` a nezbytné prvotní infrastrukturní vstupy z 28.11; použitelné provozní hodnoty instalátor při zprovoznění Secret Manageru idempotentně importuje. Jejich další použití v zabezpečeném vývojově-provozním celku je přímé a plně viditelné OWNERovi.

