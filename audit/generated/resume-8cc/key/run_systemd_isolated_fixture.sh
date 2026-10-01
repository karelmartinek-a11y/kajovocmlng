#!/bin/bash
# Reproduction only: disposable root systemd VM, never a production host.
set -euo pipefail
[ "$(id -u)" = 0 ]
[ "$(cat /proc/1/comm)" = systemd ]
systemctl is-system-running >/dev/null || [ "$(systemctl is-system-running)" = degraded ]
fixture_dir=$(mktemp -d /tmp/kcml-systemd-key-fixture.XXXXXX)
fixture_unit="kcml-key-fixture-$(cat /proc/sys/kernel/random/uuid)"
trap 'rm -rf "$fixture_dir"' EXIT
chmod 0755 "$fixture_dir"
python3 - "$fixture_dir" <<'PY'
import sys,secrets,os
from pathlib import Path
p=Path(sys.argv[1])/'synthetic-key';p.write_bytes(secrets.token_bytes(32));p.chmod(0o600)
PY
systemd-creds encrypt --with-key=host --name=kcml-master-key "$fixture_dir/synthetic-key" "$fixture_dir/key.encrypted"
chmod 0600 "$fixture_dir/key.encrypted"
[ "$(stat -c '%u:%a' "$fixture_dir/key.encrypted")" = 0:600 ]
rm "$fixture_dir/synthetic-key"
cp "$(dirname "$0")/systemd_fixture_worker.py" "$fixture_dir/worker.py"
chmod 0644 "$fixture_dir/worker.py"
systemd-run --unit="$fixture_unit" --wait --pipe --collect \
 --property=User=nobody --property=Group=nogroup --property=Type=exec \
 --property="LoadCredentialEncrypted=kcml-master-key:$fixture_dir/key.encrypted" \
 --property=PrivateTmp=no --property=NoNewPrivileges=yes \
 /usr/bin/python3 "$fixture_dir/worker.py"
# Repeat an isolated invocation over same encrypted source: compare fingerprint,
# require different InvocationID. Rotation+registry+protected-row producer proof
# is still a separate mandatory fixture, not supplied by this minimal script.
