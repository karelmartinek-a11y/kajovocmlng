from pathlib import Path
import re,json,hashlib,sys
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).parent;P=ROOT/'00_SSOT/KajovoCMLNG_SSOT.md';raw=P.read_bytes();lines=raw.decode().splitlines(keepends=True);offsets=[];pos=0
for l in lines:offsets.append(pos);pos+=len(l.encode())
selections={
 'AUTH_OWNER_FULL':('### 7.1 ',6),'AUTH_API_PARITY':('### 7.2 ',25),'SESSION_READ_AND_REVOKE':('### 21.4 ',3),'SESSION_PHYSICAL_FIELDS':('#### `owner_session`',10),'HTTP_CURSOR_CAS':('### 26.1 ',17),'SESSION_SECURITY':('### 30.2 ',14),'VERSIONED_POLICY':('### 41.10 ',28),'LOCK_HIERARCHY':('### 51.6 ',15),'SESSION_VERSION_CAS':('### 51.9 ',25),'IDEMPOTENCY_SCOPE':('### 51.12 ',58)}
records=[]
for ident,(prefix,count)in selections.items():
 found=[i for i,l in enumerate(lines)if l.startswith(prefix)]
 if len(found)!=1:raise RuntimeError((ident,found))
 start=found[0];end=min(start+count,len(lines));chunk=''.join(lines[start:end]);records.append({'sourceId':ident,'path':'00_SSOT/KajovoCMLNG_SSOT.md','sourceDocumentSha256':hashlib.sha256(raw).hexdigest(),'lineStart':start+1,'lineEnd':end,'byteStart':offsets[start],'byteLength':len(chunk.encode()),'excerptSha256':hashlib.sha256(chunk.encode()).hexdigest(),'excerpt':chunk,'coverage':'SELECTED_AUTHORITATIVE_PASSAGE_NOT_WHOLE_SECTION_REVIEW'})
(OUT/'authoritative-excerpts.json').write_text(json.dumps({'records':records},indent=2,ensure_ascii=False)+'\n')
