"""Restore explicit7.2 OWNER catalogue scope without changing genericSecret routing."""
import argparse,re
from ssot_sources import SSOT
TEXT='''### 8.18 Dedicated OWNER API credential read scope

The dedicated ownerApiKey.read and ownerApiKey.reveal catalogue operations,
including GET /owner/api-key/value, accept either a freshly verified current
OWNER API credential or a verified OWNER session with constant OWNER_FULL
according to §7.2 and §26.1. §51.20 explicitly supports session reveal and
loss-response recovery; it does not impose SESSION-only authorization on the
dedicated catalogue operation. A context or fixture possession flag is not a
verifier. Each channel uses its actual verifier, current revocation/expiry and
epoch rules, and a purpose-bound read context; generation/create contexts do
not grant read/reveal authority. Metadata and protected value remain distinct.

Reserved generic Secret CRUD/value-read routing may reject or direct to the
existing dedicated operation under §7.2; it must not remove the dedicated
operation's OWNER_FULL API-key branch. §§8.15–8.16 references to the distinct
OWNER-session reveal contract preserve that supported branch, not an exclusive
channel rule. Reveal remains an explicit authorized sensitive-value response,
never a create/event/log response. Actual audit, current immutable version/key
hydration, read consistency and systemd mechanism requirements remain intact.

'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();s=SSOT.read_text();m=re.search(r'^### 8\.18 Dedicated OWNER API credential read scope\n.*?(?=^### 8\.19 |^## 9\.)',s,re.M|re.S)
 if a.check:
  ok=bool(m)and m.group()==TEXT;print('PASS'if ok else 'BLOCKED');return int(not ok)
 if m:s=s[:m.start()]+TEXT+s[m.end():]
 else:
  e=re.search(r'^## 9\.',s,re.M)
  if not e:raise ValueError('SECRET_SECTION_END_MISSING')
  s=s[:e.start()]+TEXT+s[e.start():]
 SSOT.write_text(s,encoding='utf8',newline='\n');return 0
if __name__=='__main__':raise SystemExit(main())
