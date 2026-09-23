"""Resolve effective operation records using explicit source promotions only."""
import json


def catalog(rs):
    result={}
    for name,key in [('contracts/operation-contracts.json','records'),
                     ('r11/contracts/r10-operation-contracts.json','records'),
                     ('r16/contracts/r15-visual-operation-closure.json','operations'),
                     ('closure/contracts/operation-overlay.json','operations')]:
        for i,record in enumerate(json.loads(rs[name]['raw'])[key]):
            oid=record['operationId']
            if oid in result:raise ValueError('Duplicate effective operation: '+oid)
            result[oid]={**record,'sourceRef':name+'#/'+key+'/'+str(i)}
    return result


def owner_candidates(rs):
    records=catalog(rs)
    allowed={oid:r['sourceRef']+'/exposureClass' for oid,r in records.items() if r.get('exposureClass') in ('OWNER_QUERY','OWNER_COMMAND')}
    # Explicit OWNER actions are evidence for promoted visual operations which lack
    # exposureClass in their original record. Projection-only rows are not authority.
    for i,b in enumerate(json.loads(rs['closure/contracts/ui-action-resolution.json']['raw'])['bindings']):
        oid=b.get('canonicalOperationId')
        if b['bindingKind']=='CANONICAL_OPERATION' and oid in records and 'exposureClass' not in records[oid]:
            allowed[oid]='closure/contracts/ui-action-resolution.json#/bindings/'+str(i)
    return allowed
