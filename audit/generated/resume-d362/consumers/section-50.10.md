### 50.10 Runtime instance a launch manifest

`runtime_instance` je serverový objekt svázaný s exact component runtime targetem. Jeho immutable start snapshot obsahuje:

- component ID a source revision,
- release ID, artifact digest a runtime digest,
- dependency lock digest,
- binding-set revision a activation epoch,
- application deployment epoch a platform incarnation,
- runtime instance ID a runtime generation,
- systemd unit name a expected service class,
- resource profile digest,
- namespace, seccomp, environment a FD profile digests,
- handler entrypoint a export/schema digests,
- state schema revision,
- cleanup inventory template.

Systemd může snapshot materializovat jako `LoadCredential=runtime-manifest.json:<root-owned-source>`. Tento soubor je read-only launch input, nikoli bearer credential. Runtime host před readiness načte DB row a porovná canonical manifest digest. Nesoulad končí `RUNTIME_LAUNCH_MANIFEST_MISMATCH`, handler se nespustí a unit není ready.

Žádná hodnota z launch manifestu nemůže aktivovat inactive revision, vytvořit binding nebo obejít current DB head. Runtime gateway při každém callu ověřuje current head nezávisle na manifestu.

