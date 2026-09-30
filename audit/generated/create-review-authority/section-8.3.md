### 8.3 Datový kontrakt secretu

Secret obsahuje:

- UUID,
- stable name,
- display name,
- popis,
- typ,
- purpose kind a volitelný target object ID,
- tags a skupinu,
- URL, username a poznámky podle typu,
- status,
- active version,
- lock version,
- created/updated/deleted timestamps,
- expiration a rotation policy,
- seznam exact secret bindings,
- usage history,
- audit history.

Secret version obsahuje version number, encrypted value, fingerprint, key ID, algorithm, createdAt, activatedAt, retiredAt a author.

