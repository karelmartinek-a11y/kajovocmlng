"""Author only the existing49.4 retention specialization, no cleanup activation."""
import argparse,hashlib,re
from ssot_sources import SSOT
TEXT='''### 8.17 Secret retained results and tombstone reason

§49.4 forbids expiry while any legitimate replay/recovery source remains and
permanently reserves the stable locator. No guessed numeric TTL is authorized.
For Secret retained outcomes, a server-internal PostgreSQL timestamptz infinity
may represent no scheduled cleanup. It is not an API timestamp or client input.
A finite retention update requires the existing authorized cleanup decision and
proof that all legitimate replay/recovery references are exhausted; immutable
outcome creation timestamps and original sensitive bytes remain unchanged.
Absent such a producer, evidence may not be deleted. This definition does not
activate the currently blocked retention producer or supply a systemd fixture.

If retained terminal details are unavailable, the original reserved locator
must not execute create again. The existing IDEMPOTENCY_CONFLICT response may
carry only machineReason=RESULT_RETAINED_AS_TOMBSTONE, classification=CONFLICT,
retryDirective=DO_NOT_RETRY. Exact optional masks are published in the native
response and HttpCreateFailure definitions by create completion authoring.
Fresh authentication still precedes lookup; no new root/event or fabricated
success is permitted. Full archived-codec and command-owned outcome mappings
remain required. A rootless outcome event proposal is not an activated event.

'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();text=SSOT.read_text()
 old=re.search(r'^### 8\.17 Secret retained results and tombstone reason\n.*?(?=^### 8\.18 |^## 9\.)',text,re.M|re.S)
 if a.check:
  ok=bool(old) and old.group()==TEXT;print('PASS' if ok else 'BLOCKED');return int(not ok)
 if old:text=text[:old.start()]+TEXT+text[old.end():]
 else:
  m=re.search(r'^## 9\.',text,re.M)
  if not m:raise ValueError('SECRET_SECTION_END_MISSING')
  text=text[:m.start()]+TEXT+text[m.start():]
 SSOT.write_text(text,encoding='utf8',newline='\n');print(hashlib.sha256(SSOT.read_bytes()).hexdigest());return 0
if __name__=='__main__':raise SystemExit(main())
