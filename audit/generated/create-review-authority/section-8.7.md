### 8.7 Secret bindings

Secret binding určuje source object a exact revision, secret ID nebo stable name, version selector, účel použití, volitelný external target/browser account, lifecycle, activation-set relation a auditní původ. `allSecrets`, wildcard source a zděděný grant nejsou přípustné.

OWNER UI podporuje:

- přímé bind/unbind,
- bulk bind s impact preview,
- binding odvozený z component dependency nebo agent tool bindingu,
- runtime-only binding,
- časově omezený binding,
- test resolve,
- rotaci s okamžitou invalidací závislého session state,
- zobrazení bindings z pohledu secretu i každého používajícího objektu.

