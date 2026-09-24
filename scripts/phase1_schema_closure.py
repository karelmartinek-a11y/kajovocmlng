"""Offline, fail-closed operation boundary inventory. Not a semantic certification."""
import argparse
import base64
from collections import Counter, defaultdict
import hashlib
import json
import lzma
import re
import subprocess
import sys
from urllib.parse import unquote

from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012
from ssot_sources import ROOT, SSOT, resources, resource_index
from operation_catalog import catalog


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def walk(value, pointer=''):
    yield pointer, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, pointer+'/'+key.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from walk(child, pointer+'/'+str(i))


def pointer(value, fragment):
    fragment = unquote(fragment)
    if not fragment:
        return value
    if not fragment.startswith('/'):
        raise ValueError('UNSUPPORTED_ANCHOR:'+fragment)
    for token in fragment[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def schema_children(schema):
    """Only schema-valued keywords, never property maps, defaults or examples."""
    for key,value in schema.items():
        if key in ('properties','$defs','definitions','patternProperties','dependentSchemas','dependencies') and isinstance(value,dict):
            yield from (v for v in value.values() if isinstance(v,(dict,bool)))
        elif key in ('items','additionalItems','additionalProperties','unevaluatedProperties','unevaluatedItems',
                     'contains','not','if','then','else','propertyNames','contentSchema'):
            yield from value if isinstance(value,list) else [value]
        elif key in ('oneOf','anyOf','allOf','prefixItems') and isinstance(value,list):
            yield from value


def schema_nodes(schema):
    if isinstance(schema,dict):
        yield schema
        for child in schema_children(schema):
            yield from schema_nodes(child)


class Inventory:
    def __init__(self, text):
        self.items = list(resources(text))
        self.rs = resource_index(self.items)
        starts = re.findall(r'^<!-- (KCML-[\w-]+) path="([^"]+)"', text, re.M)
        parsed = {(r['family'], r['path']) for r in self.items}
        self.unparsed = sorted(set(map(tuple, starts))-parsed)
        self.docs = {}
        self.origins = {}
        self.ids = defaultdict(list)
        self.capsules = []
        for path, r in self.rs.items():
            if path.endswith('.json'):
                self.add(path, json.loads(r['raw']), {'family': r['family'], 'line': r['line'],
                         'resourceSha256': r['sha256']})
        for path, doc in list(self.docs.items()):
            if isinstance(doc, dict) and doc.get('format') == 'KCML-UTF8-RESOURCE-MAP-XZ/1':
                compressed = base64.b64decode(''.join(doc['dataSegments']), validate=True)
                raw = lzma.decompress(compressed)
                for key, data in [('compressed', compressed), ('decoded', raw)]:
                    if len(data) != doc[key+'Bytes'] or 'sha256:'+hashlib.sha256(data).hexdigest() != doc[key+'Sha256']:
                        raise ValueError('CAPSULE_INTEGRITY:'+path)
                nested = json.loads(raw)
                if set(nested) != set(doc['resourcePaths']):
                    raise ValueError('CAPSULE_PATHS:'+path)
                for name, content in nested.items():
                    self.capsules.append({'container': path, 'path': name,
                                          'sha256': hashlib.sha256(content.encode()).hexdigest()})
                    if name.endswith('.json'):
                        self.add(name, json.loads(content), {'capsule': path})
        # Inline schemas outside resource envelopes are inspected separately. They
        # may supply aliases but cannot silently supersede embedded definitions.
        spans = [r['match'].span() for r in self.items]
        for m in re.finditer(r'^```json\n(.*?)^```\s*$', text, re.M | re.S):
            if any(a <= m.start() < b for a, b in spans):
                continue
            try:
                doc = json.loads(m.group(1))
            except ValueError:
                continue
            if isinstance(doc, dict) and ('$schema' in doc or '$id' in doc):
                name = 'inline:line:'+str(text.count('\n', 0, m.start())+1)
                self.add(name, doc, {'inline': True})
        self.conflicts = {identity:[{'source':p+'#'+q,'sha256':digest(v)} for p,q,v in candidates]
                          for identity,candidates in self.ids.items() if len({digest(v) for _,_,v in candidates})>1}
        unsafe_documents = {p for identity in self.conflicts for p,_,_ in self.ids[identity]}
        self.registry = Registry()
        for path, doc in self.docs.items():
            if path not in unsafe_documents and isinstance(doc, dict) and '$schema' in doc:
                self.registry = self.registry.with_resource(path, Resource.from_contents(doc))
        for identity, candidates in self.ids.items():
            if identity not in self.conflicts and not any(p in unsafe_documents for p,_,_ in candidates):
                self.registry = self.registry.with_resource(identity,
                    Resource.from_contents(candidates[0][2], default_specification=DRAFT202012))
        self.registry = self.registry.crawl()
        self.boundary_cache = {}

    def add(self, path, doc, origin):
        if path in self.docs and self.docs[path] != doc:
            raise ValueError('RESOURCE_CONFLICT:'+path)
        self.docs[path] = doc
        self.origins[path] = origin
        for p, v in walk(doc):
            if isinstance(v, dict) and isinstance(v.get('$id'), str):
                self.ids[v['$id']].append((path, p, v))

    def resolve(self, reference):
        path, _, fragment = reference.partition('#')
        if path in self.docs:
            return path, fragment, pointer(self.docs[path], fragment)
        candidates = self.ids.get(path, [])
        if not candidates:
            raise ValueError('MISSING_DEFINITION:'+path)
        if len({digest(v) for _, _, v in candidates}) != 1:
            raise ValueError('CONFLICTING_ID:'+path)
        source, p, target = candidates[0]
        return source, p+fragment, pointer(target, fragment)

    def validator(self, reference):
        path, p, schema = self.resolve(reference)
        # Keep the original document's resolution scope when validating a $defs entry.
        doc = self.docs[path]
        dialect = schema.get('$schema', doc.get('$schema')) if isinstance(schema, dict) else doc.get('$schema')
        if not dialect:
            raise ValueError('MISSING_DIALECT:'+reference)
        cls = validator_for({'$schema': dialect}, default=None)
        if cls is None:
            raise ValueError('UNSUPPORTED_DIALECT:'+dialect)
        cls.check_schema(schema)
        checker=FormatChecker()
        for value in schema_nodes(schema):
            if 'format' in value and value['format'] not in checker.checkers:
                raise ValueError('UNAVAILABLE_FORMAT_CHECKER:'+value['format'])
        base = doc.get('$id', path)
        if '$schema' not in doc:
            base = schema.get('$id')
            if not base:
                raise ValueError('MISSING_SCHEMA_SCOPE:'+reference)
            fragment = ''
        else:
            fragment = '#'+p
        return cls({'$ref': base+fragment}, registry=self.registry, format_checker=checker)

    def boundary(self, role, reference, mechanism):
        if reference in self.boundary_cache:
            return {**self.boundary_cache[reference], 'role': role, 'mechanism': mechanism}
        result = {'role': role, 'reference': reference, 'mechanism': mechanism}
        try:
            path, p, schema = self.resolve(reference)
            if not isinstance(schema, (dict, bool)):
                raise ValueError('TARGET_NOT_SCHEMA')
            generic = [q for q, v in walk(schema) if isinstance(v, dict) and
                       ('canonicalJson' in v.get('properties', {}) or
                        {'schemaId', 'values'} <= set(v.get('properties', {})))]
            result.update(resolution='RESOLVED', target=path+'#'+p,
                          targetIdentity=schema.get('$id') if isinstance(schema, dict) else None,
                          targetVersion=self.docs[path].get('revision', self.docs[path].get('schemaVersion')),
                          targetSha256=digest(schema), source=self.origins[path],
                          concreteness='GENERIC_ENVELOPE' if generic else 'SEMANTIC_REVIEW_REQUIRED',
                          reason='Unbound values/canonicalJson domain slots' if generic else
                          'Reference resolution alone does not prove domain completeness',
                          genericLocations=generic)
            v = self.validator(reference)
            unresolved = []
            # Resolve nested references with the library's actual scoped resolver.
            def visit(s, resolver, seen):
                if not isinstance(s, dict):
                    return
                if '$id' in s:
                    resolver = resolver.in_subresource(Resource.from_contents(s, default_specification=DRAFT202012))
                if 'format' in s and s['format'] not in FormatChecker.checkers:
                    unresolved.append({'format':s['format'],'reason':'UNAVAILABLE_FORMAT_CHECKER'})
                for keyword in ('$ref','$dynamicRef','$recursiveRef'):
                    if keyword not in s:continue
                    ref = s[keyword]
                    key = (getattr(resolver, '_base_uri', ''), ref)
                    if key not in seen:
                        seen.add(key)
                        try:
                            resolved = resolver.lookup(ref)
                            visit(resolved.contents, resolved.resolver, seen)
                        except Exception as exc:
                            unresolved.append({'reference': ref, 'reason': str(exc)})
                for child in schema_children(s):visit(child,resolver,seen)
            visit(v.schema, self.registry.resolver(), set())
            result['nestedReferenceFailures'] = unresolved
        except Exception as exc:
            reason=str(exc)
            kind=('CONFLICTING_DEFINITION' if 'CONFLICT' in reason else
                  'MISSING_DEFINITION' if 'MISSING_DEFINITION' in reason else
                  'INVALID_REFERENCE' if isinstance(exc,(KeyError,IndexError)) else 'INVALID_SCHEMA_OR_DIALECT')
            result.update(resolution='CONFLICT' if 'CONFLICT' in reason else 'UNRESOLVED', reason=reason,issueKind=kind)
        self.boundary_cache[reference] = result
        return result


def build(text):
    inv = Inventory(text)
    print('Inventoried documents:', len(inv.docs), flush=True)
    ops = catalog(inv.rs)
    overlay = inv.docs['closure/contracts/operation-overlay.json']
    if set(ops) != set(overlay['finalOperationIds']):
        raise ValueError('OPERATION_UNIVERSE_MISMATCH')
    routes = defaultdict(list)
    for path, doc in inv.docs.items():
        if not isinstance(doc, dict): continue
        for i, r in enumerate(doc.get('records', [])):
            if isinstance(r, dict) and 'requestSchema' in r and 'responseSchema' in r and r.get('operationId') in ops:
                routes[r['operationId']].append((path, i, r))
    rows = []
    for oid, op in sorted(ops.items()):
        row = {'operationId': oid, 'exposure': op.get('exposureClass', 'NOT_EXPLICIT_IN_OPERATION'),
               'source': op['sourceRef'], 'sourceDigest': op.get('canonicalDigest', op.get('operationContractDigest')),
               'authoritySourceRefs':op.get('authoritySourceRefs',[]),
               'routes': [], 'boundaries': []}
        for path, i, r in routes[oid]:
            route = {k: r.get(k) for k in ('routeId', 'method', 'path', 'base')}
            route['source'] = path+'#/records/'+str(i)
            route['boundaries'] = [inv.boundary(role, route['source']+'/'+field, 'inline '+field)
                for role, field in [('request', 'requestSchema'), ('response', 'responseSchema'), ('event', 'eventSchema')] if field in r]
            if 'eventSchema' not in r:
                route['eventApplicability'] = 'UNSPECIFIED_NOT_ASSUMED_ABSENT'
            row['routes'].append(route)
        for role, fields in [('request', ['commandSchemaRef', 'requestSchemaRef']), ('response', ['responseSchemaRef']), ('event', ['eventSchemaRef'])]:
            for field in fields:
                ref = op.get(field)
                if isinstance(ref, str): row['boundaries'].append(inv.boundary(role, ref, field))
                elif isinstance(ref, dict) and 'schemaId' in ref:
                    row['boundaries'].append(inv.boundary(role, ref['schemaId'], field+'.schemaId'))
                elif isinstance(ref, dict) and 'catalog' in ref:
                    sf = 'requestSchema' if role == 'request' else 'responseSchema'
                    for rid in ref['routeIds']:
                        matches = [(i,r) for i,r in enumerate(inv.docs[ref['catalog']]['records']) if r['routeId']==rid]
                        if len(matches)!=1: raise ValueError('ROUTE_SELECTION:'+rid)
                        i,r = matches[0]
                        row['boundaries'].append(inv.boundary(role, ref['catalog']+'#/records/'+str(i)+'/'+sf, field+'.catalog/routeIds'))
            definition = op.get(role+'Definition')
            if definition and not any(b['role']==role for b in row['boundaries']):
                candidates = op[role+'SchemaAuthority'].split(' + ')
                matches = [p for p in candidates if definition in inv.docs[p].get('$defs', {})]
                if len(matches)!=1: raise ValueError('DEFINITION_AUTHORITY:'+oid)
                row['boundaries'].append(inv.boundary(role, matches[0]+'#/$defs/'+definition, role+'Definition + '+role+'SchemaAuthority'))
        if 'route' in op:
            row['routes'].append({'routeId': None, 'method':op['method'], 'path':op['route'], 'source':op['sourceRef'], 'boundaries':[]})
        row['eventApplicability'] = 'ROUTE_EVENT_SCHEMA' if any(b['role']=='event' for r in row['routes'] for b in r['boundaries']) else 'UNSPECIFIED_NOT_ASSUMED_ABSENT'
        rows.append(row)
    boundaries = [b for r in rows for b in r['boundaries']]
    route_rows = [rt for r in rows for rt in r['routes']]
    unique_boundaries = {b['reference']:b for b in boundaries+[b for r in route_rows for b in r['boundaries']]}
    summary = {'operations':len(rows), 'routes':len(route_rows),
               'unresolvedOperationReferences':sum(b['resolution']=='UNRESOLVED' for b in boundaries),
               'operationsWithUnresolvedReferences':sum(any(b['resolution']=='UNRESOLVED' for b in r['boundaries']) for r in rows),
               'conflictingOperationReferences':sum(b['resolution']=='CONFLICT' for b in boundaries),
               'genericRoutes':sum(any(b.get('concreteness')=='GENERIC_ENVELOPE' for b in r['boundaries']) for r in route_rows),
               'genericBoundaryDefinitions':sum(b.get('concreteness')=='GENERIC_ENVELOPE' for b in unique_boundaries.values()),
               'nestedReferenceFailures':sum(len(b.get('nestedReferenceFailures',[])) for b in unique_boundaries.values()),
               'unreviewedConcreteBoundaryDefinitions':sum(b.get('concreteness')=='SEMANTIC_REVIEW_REQUIRED' for b in unique_boundaries.values()),
               'conflictingSchemaIdentities':len(inv.conflicts),
               'unspecifiedEventApplicability':sum(r['eventApplicability']=='UNSPECIFIED_NOT_ASSUMED_ABSENT' for r in rows),
               'unparsedResources':len(inv.unparsed)}
    candidates = []
    for path, doc in inv.docs.items():
        count = sum(isinstance(v,dict) and any(k in v for k in ('operationId','canonicalOperationId','requestSchemaRef','requestDefinition')) for _,v in walk(doc))
        if count:
            unknown = sorted({v[k] for _,v in walk(doc) if isinstance(v,dict)
                              for k in ('operationId','canonicalOperationId') if isinstance(v.get(k),str) and v[k] not in ops})
            candidates.append({'source':path,'recordsMentioningOperations':count,'origin':inv.origins[path],
                               'identifiersOutsideEffectiveUniverse':unknown,
                               'selectionRule':'Only explicit R16 promotion and closure finalOperationIds select effective operations; other occurrences are evidence, not implicit additions.'})
    return inv, {'format':'KCML-PHASE1-SCHEMA-MATRIX/1','summary':summary,'operations':rows,
                 'routeNormalization':{'sourceOccurrences':len(inv.docs['contracts/execution/route-catalog.json']),
                    'explicitBindings':len(inv.docs['r8/registries/route-bindings.json']['records']),
                    'source':'r8/registries/route-bindings.json#/records',
                    'coveredSourceOccurrences':sorted({i for r in inv.docs['r8/registries/route-bindings.json']['records'] for i in r['sourceOccurrenceIds']})},
                 'sourceFamilies':dict(Counter(r['family'] for r in inv.items)),
                 'unparsedResources':inv.unparsed,'capsules':inv.capsules,'discoveredSourceFamilies':candidates,
                 'conflictingSchemaIdentities':inv.conflicts,
                 'authority':'SSOT 55.2; R16 explicit promotion; closure operation overlay finalOperationIds',
                 'scope':'All effective catalog operations, discovered payload records and R16 definition references; semantic completeness remains unverified.'}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--baseline', action='store_true'); args=parser.parse_args()
    text = subprocess.check_output(['git','show','6180d9fe67dfaa5365190301dfd58cc8d9812f3d:00_SSOT/KajovoCMLNG_SSOT.md']).decode() if args.baseline else SSOT.read_text(encoding='utf8')
    inv, report = build(text)
    suffix='-before' if args.baseline else ''
    dest=ROOT/'audit'/('phase1-operation-schema-matrix'+suffix+'.json')
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if not args.baseline:
        unresolved=[]
        for row in report['operations']:
            all_boundaries = {b['reference']:b for b in row['boundaries']+[b for r in row['routes'] for b in r['boundaries']]}
            for b in all_boundaries.values():
                if b['resolution']!='RESOLVED' or b.get('concreteness')=='GENERIC_ENVELOPE' or b.get('nestedReferenceFailures'):
                    unresolved.append({'operationId':row['operationId'],'source':row['source'],**b,
                        'authoritySourceRefs':row['authoritySourceRefs'],
                        'investigationStatus':'IDENTITY_AND_STRUCTURE_SEARCH_COMPLETE; PER_OPERATION_SEMANTIC_RECONSTRUCTION_NOT_COMPLETE',
                        'workRemaining':'Establish exact domain boundary mapping, required fields, nullability and variants from SSOT; do not substitute a transport envelope or a similarly named artifact. Escalate only fields demonstrably undecidable from those sources.',
                        'impact':'Boundary cannot be certified for implementation.'})
            if row['eventApplicability']=='UNSPECIFIED_NOT_ASSUMED_ABSENT':
                unresolved.append({'operationId':row['operationId'],'source':row['source'],'role':'event',
                                   'resolution':'APPLICABILITY_UNSPECIFIED','requiredDecision':'Bind emitted events to schemas or provide a normative no-event contract.'})
        (ROOT/'audit/phase1-unresolved.json').write_text(json.dumps({'status':'PARTIAL','summary':report['summary'],'items':unresolved},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report['summary']))
    blocking=('unresolvedOperationReferences','conflictingOperationReferences','genericRoutes',
              'nestedReferenceFailures','unreviewedConcreteBoundaryDefinitions','conflictingSchemaIdentities',
              'unspecifiedEventApplicability','unparsedResources')
    return int(any(report['summary'][key] for key in blocking))


if __name__=='__main__':
    sys.exit(main())
