"""Deterministic adapter fixtures, without credentials or provider calls."""
import json
import sys
from ssot_sources import ROOT, load_resource


def matches(condition, record):
    for key, expected in condition.items():
        if key == 'anyOf':
            if not any(matches(branch,record) for branch in expected):
                return False
            continue
        actual=record.get(key)
        if isinstance(expected,dict):
            if 'in' in expected and actual not in expected['in']:
                return False
            if 'startsWith' in expected and (not isinstance(actual,str) or not actual.startswith(expected['startsWith'])):
                return False
        elif actual != expected:
            return False
    return True


def run():
    c=json.loads(load_resource('ui/contracts/error-presentation.json')['raw'])
    rules=c['providerAdapters']['rules']
    def classify(value):
        for rule in rules:
            if matches(rule['when'],value):
                return rule['error_code'],rule['retryDirective']
        return c['providerAdapters']['fallback'],'DO_NOT_RETRY'
    fixtures=[
      ('billing-before-rate',{'providerId':'openai','httpStatus':429,'providerCode':'credit_balance_exhausted'},'PROVIDER_BILLING_BLOCKED','DO_NOT_RETRY'),
      ('quota-type',{'providerId':'openai','httpStatus':429,'providerType':'insufficient_quota'},'PROVIDER_BILLING_BLOCKED','DO_NOT_RETRY'),
      ('rate-only',{'providerId':'openai','httpStatus':429,'providerCode':'slow_down'},'PROVIDER_RATE_LIMITED','CANONICAL_OPERATION_POLICY_ONLY'),
      ('overloaded',{'providerId':'openai','httpStatus':503},'OPENAI_PROVIDER_TRANSIENT','CANONICAL_OPERATION_POLICY_ONLY'),
      ('authentication',{'httpStatus':401},'PROVIDER_AUTHENTICATION_FAILED','DO_NOT_RETRY'),
      ('permission',{'httpStatus':403},'PROVIDER_ACCESS_DENIED','DO_NOT_RETRY'),
      ('bad-request',{'httpStatus':400},'PROVIDER_REQUEST_INVALID','DO_NOT_RETRY'),
      ('timeout',{'transportFailure':'TIMEOUT'},'PROVIDER_TRANSPORT_TIMEOUT','RECONCILE_BEFORE_RETRY'),
      ('invalid-response',{'responseValidation':'INVALID_JSON'},'PROVIDER_RESPONSE_INVALID','RECONCILE_BEFORE_RETRY'),
      ('db-unique',{'sqlState':'23505'},'DATABASE_CONSTRAINT_REJECTED','DO_NOT_RETRY'),
      ('db-deadlock',{'sqlState':'40P01'},'DATABASE_TRANSACTION_CONFLICT','CANONICAL_OPERATION_POLICY_ONLY'),
      ('db-serialization',{'sqlState':'40001'},'DATABASE_TRANSACTION_CONFLICT','CANONICAL_OPERATION_POLICY_ONLY'),
      ('unknown-empty',{},'UNCLASSIFIED_ERROR','DO_NOT_RETRY'),
      ('never-parse-message',{'message':'credit_balance_exhausted'},'UNCLASSIFIED_ERROR','DO_NOT_RETRY'),
      ('provider-isolation',{'providerId':'other','providerCode':'credit_balance_exhausted'},'UNCLASSIFIED_ERROR','DO_NOT_RETRY')]
    checks=[]
    for name,value,code,retry in fixtures:
        actual=classify(value)
        checks.append({'id':name,'status':'PASS' if actual==(code,retry) else 'FAIL','actual':actual})
    result={'scope':'Adapter selection reference fixtures. RetryDirective never overrides operation replay authorization.', 'checks':checks}
    (ROOT/'audit/generated/provider-mapping-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    report=run();print(json.dumps(report));sys.exit(any(c['status']=='FAIL' for c in report['checks']))
