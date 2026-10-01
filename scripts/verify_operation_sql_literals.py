"""PostgreSQL parser evidence for exact wrapper literals; no DB/runtime certification."""
import hashlib,json,re,sys
from pathlib import Path
import pglast
from ssot_sources import ROOT,SSOT,resource_index
from repair_operation_sql_literals import PATH,CALLS,repair,TOKEN

def expressions(raw):
    return re.findall(r'^\s*(?:PERFORM|RETURN) (.*);$',raw.decode('utf8'),re.M)

def literal_arguments(expression):
    tree=json.loads(pglast.parser.parse_sql_json('SELECT '+expression))
    call=tree['stmts'][0]['stmt']['SelectStmt']['targetList'][0]['ResTarget']['val']['FuncCall']
    name=call['funcname'][0]['String']['sval']
    if name not in CALLS:raise ValueError('UNREVIEWED_CALL:'+name)
    args=call['args']
    if args[0].get('ColumnRef',{}).get('fields') != [{'String':{'sval':'p_ctx'}}]:
        raise ValueError('CONTEXT_BINDING_CHANGED')
    values=[]
    for arg in args[1:]:
        if 'TypeCast' in arg:
            cast=arg['TypeCast']
            if cast['typeName']['names'] != [{'String':{'sval':'jsonb'}}]:raise ValueError('UNEXPECTED_CAST')
            arg=cast['arg']
        if 'A_Const' not in arg or 'sval' not in arg['A_Const']:raise ValueError('ARGUMENT_IS_NOT_STRING_LITERAL:'+name)
        values.append(arg['A_Const']['sval']['sval'])
    if name=='kcml_apply_exact_domain_plan_v1':json.loads(values[0])
    return name,values

def audit(raw):
    failures=[];calls=[]
    try:count=len(pglast.parse_sql(raw.decode()))
    except Exception as exc:return {'status':'BLOCKED','diagnostic':'SQL_PARSE','reason':str(exc)}
    exprs=expressions(raw)
    for i,expr in enumerate(exprs):
        try:calls.append(literal_arguments(expr))
        except Exception as exc:failures.append({'expressionIndex':i,'diagnostic':type(exc).__name__,'reason':str(exc)})
    if len(exprs)!=count*4:failures.append({'diagnostic':'WRAPPER_STATEMENT_COVERAGE'})
    return {'status':'BLOCKED' if failures else 'PASS','functions':count,'expressions':len(exprs),'failures':failures,'calls':calls}

def main():
    rs=resource_index();raw=rs[PATH]['raw'];r=audit(raw)
    baseline=ROOT/'audit/generated/repair-2026-09-30/sql/operation-functions-baseline.sql'
    old=baseline.read_bytes();expected=repair(old)
    # Independently decode the original JSON literals and compare every argument
    # with the PostgreSQL AST value, including apostrophes and JSON escapes.
    original=[]
    for expr in expressions(old):
        name=expr.split('(',1)[0];original.append((name,[json.loads(m[0]) for m in TOKEN.finditer(expr)]))
    preservation=r.get('calls')==original and raw==expected
    positive="kcml_assert_operation_descriptor_v1(p_ctx, 'owner''s.operation', 'sha256:"+'a'*64+"')"
    probe=literal_arguments(positive)
    negatives=[]
    for bad in [positive.replace("'owner''s.operation'",'"owner.operation"'),positive.replace("'owner''s.operation'",'NULL')]:
        try:literal_arguments(bad);negatives.append(False)
        except ValueError as exc:negatives.append(str(exc).startswith('ARGUMENT_IS_NOT_STRING_LITERAL'))
    definitions=set()
    for path,item in rs.items():
        if path.endswith('.sql'):
            definitions.update(re.findall(r'(?i)CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(?:[a-zA-Z_][\w]*\.)?(\w+)',item['raw'].decode()))
    missing=sorted(CALLS-definitions)
    callsite_path='contracts/sql-helper-call-sites.json'
    coverage={'status':'BLOCKED','diagnostic':'CALLSITE_REGISTRY_MISSING'}
    if callsite_path in rs:
        registry=json.loads(rs[callsite_path]['raw'])
        rows=registry.get('wrappers',[])
        expected_operations={values[0] for name,values in r.get('calls',[]) if name=='kcml_assert_operation_descriptor_v1'}
        covered_operations={v.get('operationId') for v in rows}
        exact=(registry.get('sourceResourceSha256')==hashlib.sha256(raw).hexdigest()
               and len(rows)==len(expected_operations)==r.get('functions')
               and covered_operations==expected_operations
               and sum(len(v.get('calls',[])) for v in rows)==len(expressions(raw)))
        unresolved=[v['operationId'] for v in rows if v.get('definitionApplicability')=='UNIMPLEMENTED']
        coverage={'status':'PASS' if exact and not unresolved else 'BLOCKED',
                  'registryExact':exact,'wrapperCount':len(rows),'unresolvedTypedHandlers':unresolved,
                  'referenceImplemented':registry.get('referenceImplementedWrappers'),
                  'dispatchVerified':registry.get('dispatchVerifiedWrappers'),
                  'runtimeAcceptance':'NOT_EVALUATED',
                  'scope':'Required exact typed callsites; helper names alone are insufficient'}
    r.pop('calls',None)
    r.update(sourceDocumentSha256=hashlib.sha256(SSOT.read_bytes()).hexdigest(),resourceSha256=hashlib.sha256(raw).hexdigest(),
        parserVersion=pglast.__version__,parserScope='PostgreSQL 17 syntax AST; PostgreSQL 18.6 execution NOT_RUN',
        argumentValuePreservation=preservation,positiveWitness=probe[1],negativeLiteralChecks=negatives,
        mandatoryHelperDefinitions={'status':'BLOCKED' if missing else 'PRESENT_NOT_EXECUTED','missing':missing},
        executableDatabaseClosure='BLOCKED: helpers, physical relations, transaction/lock/idempotency/outbox/recovery execution unverified')
    if not preservation or not all(negatives):r['status']='BLOCKED'
    r['literalStatus']=r['status']
    r['mandatoryCallsiteCoverage']=coverage
    if missing or coverage['status']!='PASS':r['status']='BLOCKED'
    out=ROOT/'audit/generated/repair-2026-09-30/sql';out.mkdir(parents=True,exist_ok=True)
    (out/'literal-verification.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ['failures','positiveWitness']}))
    return int(r['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
