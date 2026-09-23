"""Resolve concrete JSON pointers in authoritative operation schema bindings."""
import json
import sys
from urllib.parse import unquote
from ssot_sources import ROOT, resources, resource_index
from operation_catalog import catalog


def resolve(value, pointer):
    if not pointer:
        return value
    if not pointer.startswith('/'):
        raise ValueError('JSON Pointer must start with /')
    for token in pointer[1:].split('/'):
        token = unquote(token).replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def run():
    documents = {}
    source_resources = resource_index()
    for resource in source_resources.values():
        if resource['path'].endswith('.json'):
            try:
                documents.setdefault(resource['path'], []).append(json.loads(resource['raw']))
            except ValueError:
                pass
    checks = []
    schema_ids = {}
    def index_schemas(value):
        if isinstance(value, dict):
            if isinstance(value.get('$id'), str):
                schema_ids.setdefault(value['$id'], []).append(value)
            for child in value.values():
                index_schemas(child)
        elif isinstance(value, list):
            for child in value:
                index_schemas(child)
    for candidates in documents.values():
        for value in candidates:
            index_schemas(value)
    for record in catalog(source_resources).values():
        for field in ('commandSchemaRef', 'responseSchemaRef'):
            reference = record.get(field)
            if not reference:
                continue
            result = {'operationId': record.get('operationId'), 'field': field, 'reference': reference}
            try:
                if isinstance(reference, dict):
                    if 'schemaId' in reference:
                        targets = schema_ids.get(reference['schemaId'], [])
                        if not targets:
                            raise ValueError('UNRESOLVED_SCHEMA_ID:'+reference['schemaId'])
                        if any(target != targets[0] for target in targets[1:]):
                            raise ValueError('CONFLICTING_SCHEMA_ID:'+reference['schemaId'])
                        result['status'] = 'PASS'
                        checks.append(result)
                        continue
                    candidates = documents[reference['catalog']]
                    if len(candidates) != 1:
                        raise ValueError('Ambiguous resource path')
                    routes = {r['routeId']:r for r in candidates[0]['records']}
                    schema_field = 'requestSchema' if field=='commandSchemaRef' else 'responseSchema'
                    if not reference['routeIds']:
                        raise ValueError('Empty route selection')
                    for route in reference['routeIds']:
                        target = routes[route][schema_field]
                        if not isinstance(target, (dict,bool)):
                            raise ValueError('Route target is not a schema')
                    result['status'] = 'PASS'
                    checks.append(result)
                    continue
                path, separator, pointer = reference.partition('#')
                candidates = documents[path]
                if len(candidates) != 1:
                    raise ValueError('Ambiguous resource path')
                target = resolve(candidates[0], pointer)
                if not isinstance(target, (dict, bool)):
                    raise ValueError('Target is not a schema')
                result['status'] = 'PASS'
            except (KeyError, IndexError, ValueError, TypeError) as exc:
                result.update(status='FAIL', reason=str(exc))
            checks.append(result)
    result = {'scope': 'Concrete commandSchemaRef and responseSchemaRef bindings; not all prose references.',
              'checks': checks, 'checked': len(checks), 'failed': sum(c['status']=='FAIL' for c in checks)}
    (ROOT/'audit/generated/schema-reference-validation.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    report = run()
    print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
    sys.exit(report['failed'] > 0 or report['checked'] == 0)
