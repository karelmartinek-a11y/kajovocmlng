"""Contract and negative-fixture checks, not a backend implementation test."""
import copy
import json
import re
import sys
from jsonschema import Draft202012Validator, FormatChecker
from ssot_sources import ROOT, resources, resource_index
from project_experience import project
from operation_catalog import owner_candidates, catalog


def run():
    rs=resource_index(); c=json.loads(rs['ui/contracts/live-experience.json']['raw'])
    checks=[]
    def check(name,fn):
        try: fn(); checks.append({'id':name,'status':'PASS'})
        except Exception as exc: checks.append({'id':name,'status':'FAIL','reason':str(exc)})
    def require(condition,reason):
        if not condition: raise ValueError(reason)
    states={s['state_id']:s for s in c['states']}
    def state_check():
        require(len(states)==len(c['states']),'duplicate state')
        for s in states.values():
            require(set(s['allowedNext'])<=states.keys(),'unknown transition')
            require(not s['terminal'] or not s['allowedNext'],'terminal reopening')
            require(s['entry'] and s['exit'] and s['eventSource'],'missing guard/source')
        for state in states:
            seen=set(); pending=[state]
            while pending:
                current=pending.pop()
                if current in seen: continue
                seen.add(current);pending.extend(states[current]['allowedNext'])
            require(any(states[x]['terminal'] for x in seen),'no terminal path: '+state)
    check('states.transitions-and-terminal-reachability',state_check)
    def locales():
        for key,record in c['messages'].items():
            require(set(record)=={'cs','en'} and all(record.values()),'missing translation: '+key)
            require(set(re.findall(r'\{([^}]+)\}',record['cs']))==set(re.findall(r'\{([^}]+)\}',record['en'])),'placeholder mismatch: '+key)
        for s in states.values(): require(s['messageKey'] in c['messages'],'unknown state message')
    check('locales.keys-and-placeholders',locales)
    check('projections.exact-source-match',lambda:project(check=True))
    def authority():
        identical=[{'path':'fixture.json','sha256':'a'},{'path':'fixture.json','sha256':'a'}]
        require(len(resource_index(identical))==1,'identical projections not deduplicated')
        try:
            resource_index([identical[0],{'path':'fixture.json','sha256':'b'}])
        except ValueError as exc:
            require('SSOT_NORMATIVE_CONFLICT' in str(exc),'wrong conflict classification')
        else:
            raise ValueError('conflicting sources silently selected')
    check('authority.no-implicit-last-wins',authority)
    def references():
        universe=set(json.loads(rs['closure/contracts/operation-overlay.json']['raw'])['finalOperationIds'])
        for v in c['views']:
            require(v['state'] in states,'unknown view state')
            require(set(v['operations'])<=universe,'unknown operations '+str(set(v['operations'])-universe))
        families={f['id'] for f in json.loads(rs['r16/contracts/process-family-registry.json']['raw'])['processFamilies']}
        require({p['familyId'] for p in c['processProfiles']}==families,'incomplete process-family coverage')
    check('references.operations-process-families',references)
    def dispatchers():
        allowed=owner_candidates(rs)
        require(c['dispatcherExposure']['ownerOperationEvidence']==allowed,'stale owner evidence projection')
        for row in json.loads(rs['closure/contracts/ui-action-resolution.json']['raw'])['bindings']:
            if row['actionId'] in ('api.execute','palette.execute'):
                require(set(row['candidateOperationIds'])==set(allowed),'dispatcher includes non-OWNER operation or omits proven OWNER operation')
        require('component.control.ack' not in allowed,'internal acknowledgement admitted')
        require('component.enable' in allowed,'OWNER component enable missing')
    check('dispatchers.exact-owner-allowlist-and-internal-denial',dispatchers)
    def placements():
        registry=json.loads(rs['ui/contracts/ui-control-registry.json']['raw'])
        expected={('ui.'+a['id'],p['id'],a['id']) for p in registry['pages'] for a in p['actions']}
        rows=c['dashboardSurfaceBindings']
        require(len(rows)==len(expected),'duplicate/missing placement')
        require({(r['functionId'],r['pageId'],r['actionId']) for r in rows}==expected,'placement coverage differs from UI registry')
        bindings=json.loads(rs['closure/contracts/ui-action-resolution.json']['raw'])['bindings']
        for row in rows:
            index=int(row['commandBindingRef'].rsplit('/',1)[1]);binding=bindings[index]
            require((binding['pageId'],binding['actionId'])==(row['pageId'],row['actionId']),'placement points to wrong command')
            if not row['pageId'].startswith('auth.'):
                require(row['dashboard']['mode']=='IN_PLACE_DRAWER','ordinary operation navigates away')
                require(row['dashboard']['panelId']=='dashboard.drawer.'+row['pageId'],'wrong drawer identity')
            require(row['disabledReason'] and row['availabilityRef'],'missing disabled reason/guard')
    check('dashboard.complete-action-placement-and-command-identity',placements)
    schema=c['eventSchema']; validator=Draft202012Validator(schema,format_checker=FormatChecker())
    check('event.schema-meta',lambda:Draft202012Validator.check_schema(schema))
    event={'eventId':'e1','streamId':'s1','runId':'r1','correlationId':'c1','operationId':'component.read',
        'nodeId':'n1','attemptId':'a1','sourceId':'n1','targetId':'n2','edgeId':'edge1',
        'occurredAt':'2026-09-23T12:00:00Z','recordedAt':'2026-09-23T12:00:01Z','sequence':1,'stateVersion':1,
        'kind':'request','state_id':'ACTIVE','payloadRef':None,'demo':False}
    check('event.valid-fixture',lambda:validator.validate(event))
    for name,mutate in [('unknown-state',lambda e:e.update(state_id='INVENTED')),('missing-correlation',lambda e:e.pop('correlationId')),
                        ('negative-sequence',lambda e:e.update(sequence=-1)),('invalid-time',lambda e:e.update(occurredAt='yesterday')),
                        ('reserved-field',lambda e:e.update(secret='not-a-secret'))]:
        broken=copy.deepcopy(event);mutate(broken)
        check('event.reject-'+name,lambda b=broken:require(bool(list(validator.iter_errors(b))),'invalid event accepted'))
    # Small oracle of presentation admission. Business effects are deliberately absent.
    def admission(e,seen,cursor,version,stream='s1'):
        if e['demo'] or e['streamId']!=stream:return 'REJECT'
        if e['eventId'] in seen or e['sequence']<=cursor:return 'HISTORY_ONLY'
        if e['sequence']!=cursor+1:return 'REPLAY_REQUIRED'
        if e['stateVersion']<version:return 'SNAPSHOT_REQUIRED'
        return 'APPLY'
    cases=[('duplicate',{}, {'e1'},0,0,'HISTORY_ONLY'),('late',{},set(),2,2,'HISTORY_ONLY'),
           ('gap',{'sequence':3},set(),0,0,'REPLAY_REQUIRED'),('regression',{},set(),0,2,'SNAPSHOT_REQUIRED'),
           ('production-demo',{'demo':True},set(),0,0,'REJECT'),('wrong-stream',{'streamId':'s2'},set(),0,0,'REJECT'),
           ('snapshot-watermark',{'sequence':11,'stateVersion':8},set(),10,8,'APPLY')]
    for name,patch,seen,cursor,version,expected in cases:
        e={**event,**patch};check('oracle.'+name,lambda e=e,se=seen,cu=cursor,ve=version,ex=expected:require(admission(e,se,cu,ve)==ex,'wrong admission'))
    result={'scope':'Static contract validation and reference-oracle fixtures; no backend or provider call.', 'checks':checks}
    out=ROOT/'audit/generated/experience-validation.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    r=run(); print(json.dumps(r)); sys.exit(any(x['status']=='FAIL' for x in r['checks']))
