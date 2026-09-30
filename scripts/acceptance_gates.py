"""SSOT 55.21.1: separate design completeness from real implementation evidence."""
DESIGN='SSOT_CONTRACT_READY'
PRODUCTION='IMPLEMENTATION_PRODUCTION_ACCEPTANCE'

def assess(required_design, design_results, required_production, production_results, source_sha256):
    """Explicit universes; only current, successful evidence counts."""
    def gate(required, results, kind):
        if not required or len(required)!=len(set(required)):
            return {'status':'BLOCKED','findings':['INVALID_OR_EMPTY_REQUIRED_UNIVERSE']}
        findings=[]
        for key in required:
            result=results.get(key)
            if not isinstance(result,dict):findings.append('MISSING:'+key);continue
            if result.get('sourceSha256')!=source_sha256:findings.append('STALE:'+key)
            if result.get('gate')!=kind:findings.append('WRONG_GATE:'+key)
            if result.get('passed') is not True:findings.append('FAILED:'+key)
            if kind==PRODUCTION and result.get('evidenceKind')!='EXECUTED_IMPLEMENTATION':
                findings.append('NOT_IMPLEMENTATION_EVIDENCE:'+key)
        findings.extend('UNDECLARED:'+key for key in sorted(set(results)-set(required)))
        return {'status':'BLOCKED' if findings else 'PASS','findings':findings}
    return {DESIGN:gate(required_design,design_results,DESIGN),
            PRODUCTION:gate(required_production,production_results,PRODUCTION)}

def inventory_scope():
    return {DESIGN:{'status':'NOT_EVALUATED','reason':'Inventory/hash integrity is not semantic closure.'},
            PRODUCTION:{'status':'NOT_EVALUATED','reason':'No implementation execution assessed; not a design blocker.'}}
