"""Check source-code coverage, schema, locales and negative error fixtures."""
import copy
import json
import sys
from jsonschema import Draft202012Validator
from ssot_sources import ROOT, resources, resource_index


def run():
    rs=resource_index();c=json.loads(rs['ui/contracts/error-presentation.json']['raw'])
    schema=json.loads(rs['ui/contracts/error-presentation.schema.json']['raw'])
    original=json.loads(rs['contracts/generation/generation-contracts.schema.json']['raw'])['$defs']
    expected={code for i in range(107,117) for code in original['SourceEnum'+str(i)]['enum']}
    checks=[]
    def check(id,condition):checks.append({'id':id,'status':'PASS' if condition else 'FAIL'})
    Draft202012Validator.check_schema(schema);v=Draft202012Validator(schema)
    errors=list(v.iter_errors(c));check('schema.valid',not errors)
    check('codes.exact-source-set',{r['error_code'] for r in c['entries']}==expected)
    check('codes.unique',len({r['error_code'] for r in c['entries']})==len(c['entries']))
    all_entries=c['entries']+c['providerErrors']
    check('provider.codes-unique',len({r['error_code'] for r in all_entries})==len(all_entries))
    check('provider.targets-resolve',all(r['error_code'] in {e['error_code'] for e in all_entries} for r in c['providerAdapters']['rules']))
    check('provider.messages-cs-en',all(e['user_message_cs'] and e['user_message_en'] for e in c['providerErrors']))
    check('messages.cs-en-complete',all(r['user_message_cs'] and r['user_message_en'] and r['messageKey'] for r in c['entries']))
    check('conditions.exact-code-match',all(r['technical_condition']['value']==r['error_code'] for r in c['entries']))
    check('fallback.no-blind-retry',c['fallback']['automatic_retry_policy']['maxAttempts']==0)
    broken=copy.deepcopy(c);del broken['entries'][0]['automatic_retry_policy'];check('negative.missing-retry-rejected',bool(list(v.iter_errors(broken))))
    broken=copy.deepcopy(c);broken['entries'][0]['unregisteredField']=True;check('negative.extra-field-rejected',bool(list(v.iter_errors(broken))))
    broken=copy.deepcopy(c);broken['entries'][0]['user_message_en']='';check('negative.empty-translation-rejected',bool(list(v.iter_errors(broken))))
    result={'checks':checks,'schemaErrors':[e.message for e in errors],
        'completeErrorContract':'BLOCKED','reason':'Per-provider technical adapters are not fully materialized. The approved bounded default retry profile supplies numeric limits only for already-authorized replay; translation coverage does not close provider mapping.'}
    out=ROOT/'audit/generated/error-validation.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return result


if __name__=='__main__':
    r=run();print(json.dumps(r));sys.exit(any(x['status']=='FAIL' for x in r['checks']))
