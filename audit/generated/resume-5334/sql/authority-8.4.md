### 8.4 Uložení

Hodnoty jsou šifrované pomocí kanonického master key mechanismu a authenticated encryption. Databáze ukládá ciphertext, nonce, key ID, algorithm a fingerprint. Master key je persistentně uložen jako root-owned encrypted systemd credential source a každé oprávněné service invocation jej získá výhradně read-only systemd credential materializací podle 50.30; jiný host-level mechanismus se v produkci nepoužívá.

