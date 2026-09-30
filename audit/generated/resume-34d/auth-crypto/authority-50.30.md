### 50.30 Systemd credential lifecycle a deployment

Secret-bearing host credentials jsou service-specific a materializují se pouze systemd credential mechanismem. Source je root-owned mode `0600`, persistentní forma je encrypted, service dostane read-only per-invocation materialization v systemd credential directory.

Credential rotation operation:

1. vytvoří novou immutable credential version/fingerprint,
2. atomicky nahradí root-owned source nebo encrypted credential blob,
3. inkrementuje desired credential generation,
4. restartuje pouze exact affected service units,
5. ověří nový `InvocationID`, effective credential fingerprint/generation, readiness a dependent smoke,
6. uzavře accepted connections staré service generation,
7. označí previous generation retired až po effective confirmation.

Generated handler credential directory nevidí. Runtime launch manifest credential neobsahuje bearer secret a rotuje s runtime generation/release reconciliation. Master encryption key, DB credential, TLS private key a bridge CA zůstávají pouze u exact platform service.

Application deployment switch mění `applicationDeploymentEpoch`. Proces se starým epoch nemůže po restart/symlink race provést authoritative write. Gateway readiness je false při mixed DB epoch, filesystem `current`, process release, systemd invocation nebo heartbeat evidence.

