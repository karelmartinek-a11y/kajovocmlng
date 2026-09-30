### 50.11 Sandbox launch linearizační body

Runtime host spouští právě jeden current generated handler process tree pro runtime generation. Launch probíhá:

1. ověření current runtime instance snapshotu, release digests a activation eligibility,
2. otevření immutable release root přes trusted directory FD a digest manifest,
3. vytvoření `AF_UNIX SOCK_STREAM|SOCK_CLOEXEC` socketpair,
4. `clone3` s PID tracking a new user, mount, network, IPC, UTS, PID a cgroup namespace,
5. child-side mount setup, private root, `/proc`, `/dev` a tmpfs,
6. UID/GID mapping pouze do runtime-host host UID/GID; generated process nemá capability v parent user namespace,
7. uzavření všech neallowlisted FD přes `close_range`,
8. dup capability endpoint na FD `3`, standard streams na přesné FD a žádné další inherited handles,
9. drop všech capabilities, securebits a setgroups,
10. `PR_SET_NO_NEW_PRIVS`, parent-death signal, seccomp a environment allowlist,
11. exec trusted component SDK bootstrap,
12. bootstrap nastaví `FD_CLOEXEC` na capability FD před importem generated module,
13. handler HELLO/READY s export/schema/runtime digests,
14. runtime host input/output conformance test,
15. guarded readiness evidence a teprve potom runtime admission.

Autoritativní start linearizační bod je commit readiness evidence odpovídající stejné runtime generation a živému pidfd. Process start bez tohoto commitu není ready a nepřijímá business call.

