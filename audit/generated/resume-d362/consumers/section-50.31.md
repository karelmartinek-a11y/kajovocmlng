### 50.31 Runtime cleanup a boot recovery

Každý runtime instance/generation má persistentní `runtime_cleanup_operation` s inventory:

- systemd unit a cgroup,
- main/handler/child pidfd identities,
- runtime gateway connection IDs,
- anonymous handler channel,
- active request/stream IDs,
- namespace/process-tree evidence,
- temporary directories, tmpfs a artifacts,
- materialized service credentials,
- socket/path evidence,
- outstanding side-effect/reconciliation operations,
- lease/concurrency/capacity claims.

Cleanup pořadí:

1. stop new admission a mark runtime draining,
2. persist cancellation/drain intent,
3. reconcile pending side effects,
4. close handler capability channel a broker streams,
5. SIGTERM process tree a bounded grace,
6. SIGKILL unit cgroup a wait until `populated=0`,
7. close pidfds, accepted sockets a buffers,
8. unmount/remove private tmpfs a runtime-generation paths,
9. release concurrency/capacity/leases pod current fence,
10. verify no current pointer, route, binding nebo execution context references generation,
11. store final evidence a mark `COMPLETE`.

Boot recovery:

- systemd socket units and root tmpfiles restore canonical directories/paths,
- PostgreSQL runtime instances v non-terminal state se reconciliují proti actual units, invocation IDs, cgroups a PIDs,
- unknown process bez matching runtime instance se zastaví a eviduje jako orphan,
- stale DB process identity bez live unit se označí exited a pending calls se reconciliují,
- stale socket path se neotevře ani slepě nepřepíše,
- credential materialization z předchozího invocation se nepoužije,
- nový dispatch začne až po runtime inventory convergence.

