"""Author own six bounded response dictionaries; never entire operation closure."""
import argparse,copy,hashlib,json,re
from ssot_sources import ROOT,SSOT,resources,resource_index
from author_resource_updates import rewrite
from phase1_repair_contracts import encoded
PATCH=ROOT/'audit/generated/resume-d362/sql-lifecycle/field-patch.json'
PATH='closure/contracts/operation-state-receipts.json'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 text=SSOT.read_text();items=list(resources(text));rs=resource_index(items);proposal=json.loads(PATCH.read_text())
 resource=proposal['resource'];doc=json.loads(rs[resource]['raw']);records={r['operationId']:(i,r) for i,r in enumerate(doc['records'])}
 fields=[]
 for patch in proposal['patch']:
  i,row=records[patch['operationId']];field=patch['path'].split('/')[-1];previous=row['responseSchema']['properties'][field]
  assert previous in [patch['oldValue'],patch['value']], 'FOREIGN_FIELD_CHANGE:'+patch['operationId']+'.'+field
  assert field in row['responseSchema']['required'], 'REQUIRED_STATE_FIELD_REMOVED'
  row['responseSchema']['properties'][field]=copy.deepcopy(patch['value'])
  fields.append({'operationId':patch['operationId'],'field':field,'schemaPointer':resource+'/records/'+str(i)+'/responseSchema/properties/'+field,'mask':patch['value'],'authority':'00_SSOT/KajovoCMLNG_SSOT.md#section.12.50'})
 cancel=records['acceptance.run.cancel'][1]['responseSchema']
 rule={'if':{'properties':{'state':{'const':'CANCELLED'}},'required':['state']},'then':{'properties':{'cleanupStatus':{'const':'COMPLETE'},'reconciliationStatus':{'const':'COMPLETE'}},'required':['cleanupStatus','reconciliationStatus']}}
 if rule not in cancel.setdefault('allOf',[]):cancel['allOf'].append(rule)
 meaning=(ROOT/'audit/generated/resume-d362/sql-lifecycle/state-definitions.md').read_text()
 normative='### 12.50 Own operation response state dictionaries\n\n'+meaning.split('\n',1)[1].lstrip()+'\n'
 contract={'format':'KCML-OPERATION-STATE-RECEIPTS/1','authority':['12.18','21.3','11.24','25.14','29.5','49.4','49.5','12.50'],'fields':fields,'scope':'Six bounded own response dictionary definitions, not whole operation/worker/transaction closure','receiptKinds':{'owner.mfa.reset':'IMMUTABLE_AS_COMMITTED_RESET_POSTCONDITION','chat.turn.steer':'IMMUTABLE_AS_COMMITTED_INSTRUCTION_INTENT','acceptance.run.start':'IMMUTABLE_AS_COMMITTED_QUEUE_ADMISSION','acceptance.run.cancel':'PERSISTED_CANCELLATION_STAGE_UNTIL_IMMUTABLE_TERMINAL_OUTCOME'},'terminalPredicate':'CANCELLED requires exact run/release/plan/fixture obligations, actual retained successful cleanup/terminal effect+check evidence, no unknown/orphan/manual requirement and typed frozen finalization joins; digest-shaped strings or bool flags are insufficient','implementationAcceptance':'NOT_EVALUATED'}
 updates={resource:encoded(doc,rs[resource]['raw']),PATH:(json.dumps(contract,ensure_ascii=False,indent=2)+'\n').encode()}
 manifest=json.loads(rs['manifest.json']['raw']);manifest['resources'].setdefault(PATH,{}).update(kind='JSON',sizeBytes=len(updates[PATH]),sha256='sha256:'+hashlib.sha256(updates[PATH]).hexdigest());manifest['resourceCount']=len(manifest['resources']);updates['manifest.json']=encoded(manifest,rs['manifest.json']['raw'])
 pending=[p for p,raw in updates.items() if p!='manifest.json' and (p not in rs or rs[p]['raw']!=raw)]
 current_manifest=json.loads(rs['manifest.json']['raw'])
 if current_manifest['resources'].get(PATH)!=manifest['resources'][PATH]:pending.append('manifest.json#/resources/'+PATH)
 global_count_matches=current_manifest.get('resourceCount')==len(current_manifest['resources'])
 physical={ROOT/'01_UI_CONTRACT'/p:updates[p] for p in [resource,PATH]}
 pending += ['projection:'+p.relative_to(ROOT).as_posix() for p,raw in physical.items() if not p.exists() or p.read_bytes()!=raw]
 if a.check:print(json.dumps({'status':'PASS' if not pending and normative in text else 'BLOCKED','pending':pending,'normativePresent':normative in text,'scope':'Six authored fields, their normative contract/projections and own manifest entry; global integrity is independently gated','globalManifestResourceCountMatches':global_count_matches}));return int(bool(pending) or normative not in text)
 text=rewrite(text,items,updates)
 match=re.search(r'^### 12\.50 Own operation response state dictionaries\n.*?(?=^### 12\.|^## 13\.)',text,re.M|re.S)
 if match:text=text[:match.start()]+normative+text[match.end():]
 else:
  end=re.search(r'^## 13\.',text,re.M);assert end;text=text[:end.start()]+normative+text[end.start():]
 SSOT.write_text(text,encoding='utf8',newline='\n')
 for p,raw in physical.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 print(json.dumps({'authored':PATH,'fields':len(fields),'scope':contract['scope']}));return 0
if __name__=='__main__':raise SystemExit(main())
