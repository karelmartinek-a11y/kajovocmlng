"""Inventory stable source error codes and expose missing normative error fields."""
import json
from ssot_sources import ROOT,resources,resource_index

FIELDS=['error_code','source','category','severity','technical_condition','user_message_cs','user_message_en',
        'operator_detail','recoverability','automatic_retry_policy','manual_recovery','correlation_requirements','logging_requirements']


def build():
    rs=resource_index(); schema=json.loads(rs['contracts/generation/generation-contracts.schema.json']['raw'])
    presentation=json.loads(rs['ui/contracts/error-presentation.json']['raw'])
    by_code={r['error_code']:r for r in presentation['entries']}
    rows=[]
    for i in range(107,117):
        enum='SourceEnum'+str(i)
        for code in schema['$defs'][enum]['enum']:
            rows.append({'error_code':code,'sourceRef':'contracts/generation/generation-contracts.schema.json#/$defs/'+enum,
                'correlation_requirements':['correlationId','logicalOperationId','affectedObject','currentSnapshot'],
                'logging_requirements':'SSOT 19 and 32; Secrets remain under trusted-perimeter policy.',
                'missingNormativeFields':[f for f in FIELDS if f not in by_code.get(code,{})],
                'messageRef':'ui/contracts/error-presentation.json#/entries/'+str(presentation['entries'].index(by_code[code])) if code in by_code else None,
                'status':'PRESENTATION_MAPPED_RETRY_POLICY_REQUIRES_OPERATION_BINDING' if code in by_code else 'REQUIRES_SOURCE_SEMANTIC_BINDING'})
    out=ROOT/'audit/generated/error-coverage.json';out.parent.mkdir(parents=True,exist_ok=True)
    report={'format':'KCML-ERROR-COVERAGE/1','errors':rows,'summary':{'sourceCodes':len(rows),'presentationRecords':len(by_code),'completeRegistryRecords':0},
            'limitation':'Enum membership and general recovery rules do not establish per-code technical conditions, deterministic localization or exact retry policy.'}
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':print(json.dumps(build()['summary']))
