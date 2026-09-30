"""Publish actual-byte FOLLOW_UP predicates and account for historical fixtures."""
import hashlib,json,re,subprocess
from ssot_sources import ROOT,SSOT,resources,resource_index
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded

NORM='''### 12.53 FOLLOW_UP actual-byte eligibility and retained diagnostics

Čerstvé admission podle §§12.49–12.51 ověřuje skutečné immutable source bytes, jejich identity, digest, přesnou pinned native masku a doménové vztahy. Příznaky consistent/sufficient/publishedFinal nejsou serverovou autoritou. Chyby mají konkrétní finite diagnostic skutečně selhaného validatoru. Staré FOLLOW_UP_BASIS_INCONSISTENT, FOLLOW_UP_BASIS_INSUFFICIENT a FOLLOW_UP_FINAL_OUTPUT_UNPUBLISHED zůstávají pouze pro byte-identical čtení/replay již uloženého failure receipt pod jeho původním pinned kontraktem; nejsou novými podmínkami založenými na deklaraci volajícího. Retained replay i nadále vyžaduje aktuální autentizaci a přesný frozen scope; neprovádí novou interpretaci původního výsledku.

`contracts/generation/follow-up-coverage-disposition.json` dokládá přechod historických324 na318 kontrol: šest flag-only negativů nahrazují šest pozitivně odvozených porušení actual bytes/native obsahu; unpublished boolean nahrazuje chybějící immutable final-output declaration. Současných324 scénářů není míra připravenosti. Požadované SQL locks, dostupnost podkladu při použití, kryptografické otevření a celá producer-consumer předávka zůstávají samostatné předgenerační závazky, nikoli důsledek počtu testů.

'''

def main():
    text=SSOT.read_text();items=list(resources(text));rs=resource_index(items)
    historical=subprocess.check_output(['git','show','d362487:audit/generated/repair-2026-09-30/design-current/verify_follow_up_contracts/follow-up-tests.json'],cwd=ROOT)
    proof=json.loads((ROOT/'audit/generated/follow-up-tests/follow-up-tests.json').read_text())
    doc={'version':'FOLLOW_UP_NATIVE_COVERAGE_DISPOSITION_V1','authority':['SSOT12.49','SSOT12.51','SSOT12.53'], 'historicalInput':{'commit':'d362487999bd795d4723c2a930e93fc7aa8aa295','reportSha256':hashlib.sha256(historical).hexdigest(),'checked':324},'intermediateChecked':318,'currentChecked':324,'replacements':proof['nativeCoverageReplacements'],'publicationReplacement':{'historicalCase':'PUBLISHED_FINAL_OUTPUT/unpublished','replacementCase':'PUBLISHED_FINAL_OUTPUT/missing-final-declaration','reason':'Actual immutable output declaration replaces caller-like publication boolean'},'closureClaim':False,'implementationProductionAcceptance':'NOT_EVALUATED'}
    path='contracts/generation/follow-up-coverage-disposition.json';raw=(json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode()
    manifest=json.loads(rs['manifest.json']['raw']);manifest['resources'][path]={'kind':'JSON','sizeBytes':len(raw),'sha256':'sha256:'+hashlib.sha256(raw).hexdigest()};manifest['resourceCount']=len(manifest['resources'])
    text=rewrite(text,items,{path:raw,'manifest.json':encoded(manifest,rs['manifest.json']['raw'])})
    m=re.search(r'^### 12\.53 .*?(?=^### 12\.|^## 13\.)',text,re.M|re.S)
    if m:text=text[:m.start()]+NORM+text[m.end():]
    else:
        m=re.search(r'^## 13\.',text,re.M);assert m;text=text[:m.start()]+NORM+text[m.start():]
    SSOT.write_text(text,encoding='utf8',newline='\n')
    p=ROOT/'01_UI_CONTRACT'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    print(json.dumps({'authored':path,'wholeOperationsClosed':0}))
if __name__=='__main__':main()
