"""Check original Secrets-related normative sections against the starting commit."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from ssot_sources import ROOT, SSOT

BASE='0ea5bf6b90ae4246956d1d76387ab540dc842f79'


def sections(text):
    headers=list(re.finditer(r'^(#{1,4}) (.+)$',text,re.M))
    result={}
    for index,header in enumerate(headers):
        if not re.search(r'secret|credential|plaintext|hesl',header[2],re.I):
            continue
        following=next((h for h in headers[index+1:] if len(h[1])<=len(header[1])),None)
        value=text[header.start():following.start() if following else len(text)].strip()
        result[header[2]]=hashlib.sha256(value.encode('utf-8')).hexdigest()
    return result


if __name__=='__main__':
    original=subprocess.run(['git','show',BASE+':00_SSOT/KajovoCMLNG_SSOT.md'],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8').replace('\r\n','\n')
    current=SSOT.read_text(encoding='utf-8')
    addition=[]
    from ssot_sources import resource_index
    from create_operation_contracts import PATH as CREATE_DESIGN
    if CREATE_DESIGN in resource_index():
        from close_create_operation_requests import SECRET_TEXT
        addition=[{'section':'8.11 Secret create request admission','status':'PASS' if current.count(SECRET_TEXT)==1 else 'FAIL',
            'scope':'Exact authored technical admission addendum; original policy must remain byte-identical.'}]
        if current.count(SECRET_TEXT)==1:current=current.replace(SECRET_TEXT,'',1)
    if 'contracts/secrets/import.schema.json' in resource_index():
        from close_secret_profile_handoffs import authored_secret_norm
        secret_norm=authored_secret_norm()
        addition.append({'section':'8.12/8.13 Secret explicit profiles and exact browser cookie preservation','status':'PASS'if current.count(secret_norm)==1 else'FAIL','scope':'Exact technical addendum only; all original policy bytes remain compared'})
        if current.count(secret_norm)==1:current=current.replace(secret_norm,'',1)
    if 'database/secret-profile-publication.sql'in resource_index():
        from close_producer_archive_handoffs import SECRET_NORM
        addition.append({'section':'8.14 Trusted profile publication and OWNER binding','status':'PASS'if current.count(SECRET_NORM)==1 else'FAIL','scope':'Exact technical addendum only; original policy remains byte compared'})
        if current.count(SECRET_NORM)==1:current=current.replace(SECRET_NORM,'',1)
    from secret_root_status_authority import ROOT_STATUS_NORM,ENTITY_STATUS_NORM,decision_approved
    for norm,scope in [(ROOT_STATUS_NORM,'8.3'),(ENTITY_STATUS_NORM,'25.6')]:
        ok=decision_approved() and current.count(norm)==1
        addition.append({'section':scope+'/OWNER-SECRET-ROOT-STATUS-2026-10-01','status':'PASS'if ok else'FAIL','scope':'Exact explicitly approved additive derived projection only; original policy stays compared'})
        if ok:current=current.replace(norm,'',1)
    from close_retry_authority_handoffs import SECRET_NORM as OWNER_VALUE_READ_NORM
    from close_secret_effective_handoffs import NORM as DERIVED_STATUS_NORM
    for norm,scope in [(OWNER_VALUE_READ_NORM,'8.15'),(DERIVED_STATUS_NORM,'8.16')]:
        if scope.split('.')[1] and norm in current:
            ok=current.count(norm)==1
            addition.append({'section':scope,'status':'PASS'if ok else'FAIL','scope':'Exact reviewed additive technical handoff only; all original bytes compared'})
            if ok:current=current.replace(norm,'',1)
    from close_secret_retention_contract import TEXT as RETENTION_NORM
    from close_owner_key_reveal_scope import TEXT as REVEAL_SCOPE_NORM
    from close_scoped_sql_helpers import TEXT as SCOPED_HELPER_NORM
    for norm, scope, resource in [
        (RETENTION_NORM, '8.17', 'contracts/create-completion.json'),
        (REVEAL_SCOPE_NORM, '8.18', 'database/operation-helper-owner-query.sql'),
        (SCOPED_HELPER_NORM, '51.39', 'database/operation-helper-owner-query.sql'),
    ]:
        ok = resource in resource_index() and current.count(norm) == 1
        addition.append({'section': scope, 'status': 'PASS' if ok else 'FAIL',
            'scope': 'Exact reviewed additive supplement only; missing/duplicate/changed bytes fail and original policy stays byte-compared.'})
        if ok: current = current.replace(norm, '', 1)
    before=sections(original);after=sections(current)
    checks=[{'section':key,'originalSha256':value,'currentSha256':after.get(key),
             'status':'PASS' if after.get(key)==value else 'FAIL'} for key,value in before.items()]
    checks.extend(addition)
    report={'baseCommit':BASE,'sourceSha256':hashlib.sha256(SSOT.read_bytes()).hexdigest(),'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Secret/credential/password headings and their full subordinate content, compared without publishing content. LF normalization and surrounding whitespace excluded.', 'checks':checks}
    (ROOT/'audit/generated/preserved-policy.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'sections':len(checks),'failures':sum(c['status']=='FAIL' for c in checks)}))
    sys.exit(any(c['status']=='FAIL' for c in checks))
