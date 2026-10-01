from pathlib import Path
import json,sys
ROOT=Path('/workspace/kajovocmlng');OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'scripts'))
from verify_operation_sql_literals import literal_arguments,expressions
f=json.loads((OUT/'owner-query-family.json').read_text())['family'];cases=[]
for x in f:
 plan=next(args[0]for name,args in map(literal_arguments,expressions(x['sourceSql'].encode()))if name=='kcml_apply_exact_domain_plan_v1')
 x['originalPlan']=json.loads(plan);cases.append(' WHEN '+"'"+x['operationId']+"' THEN '"+plan.replace("'","''")+"'::jsonb")
function="CREATE FUNCTION public.kcml_owner_query_expected_plan_v1(p_operation text)RETURNS jsonb LANGUAGE sql IMMUTABLE SET search_path=pg_catalog AS $$SELECT CASE p_operation\n"+'\n'.join(cases)+" END$$;\nREVOKE ALL ON FUNCTION public.kcml_owner_query_expected_plan_v1(text)FROM PUBLIC;\n"
p=OUT/'owner-query-helpers.sql';s=p.read_text();start=s.find('CREATE FUNCTION public.kcml_owner_query_expected_plan_v1');
if start>=0:
 end=s.index('CREATE FUNCTION public.kcml_apply_exact_domain_plan_v1',start);s=s[:start]+s[end:]
idx=s.index('CREATE FUNCTION public.kcml_apply_exact_domain_plan_v1');s=s[:idx]+function+s[idx:]
needle=" -- No fieldUpdatePlan/slot/storage fallback interpreter. Exact static projection."
s=s.replace(" IF p_plan IS DISTINCT FROM public.kcml_owner_query_expected_plan_v1(c->>'operation_id') THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_QUERY_EXACT_PLAN_MISMATCH';END IF;\n",'')
s=s.replace(needle," IF p_plan IS DISTINCT FROM public.kcml_owner_query_expected_plan_v1(c->>'operation_id') THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='OWNER_QUERY_EXACT_PLAN_MISMATCH';END IF;\n"+needle)
p.write_text(s);(OUT/'owner-query-family.json').write_text(json.dumps({'sourceDocumentSha256':json.loads((OUT/'owner-query-family.json').read_text())['sourceDocumentSha256'],'sourceResourceSha256':json.loads((OUT/'owner-query-family.json').read_text()).get('sourceResourceSha256'),'family':f},indent=2)+'\n')
