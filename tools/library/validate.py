"""Validate resource identities, links, attribution coverage and preserved bytes."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

from common import ROOT, SCHEMA, CATEGORIES, FUTURE_PATHS, asset_records, confined, digest, read_json


def validate(root: Path = ROOT, *, migration: bool = False) -> dict:
    rows = asset_records(root)
    ids = {r['id'] for r in rows}
    paths = read_json(root / 'catalog/paths.json')['assets']
    expected = {r['id']: r['path'] for r in rows}
    if paths != dict(sorted(expected.items())): raise ValueError('Path catalog does not match descriptors')
    index = read_json(root / 'catalog/index.json')
    if index['count'] != len(rows) or {r['id'] for r in index['items']} != ids or len(index['items']) != len(rows):
        raise ValueError('Incomplete or duplicate generated catalog')
    by_id = {r['id']: r for r in index['items']}
    kinds = {r['type'] for r in rows}
    categories = {r[0] for r in CATEGORIES}
    original_entries = 0
    for row in rows:
        p = confined(root, row['path'])
        for key in ('id', 'name', 'type', 'category', 'family', 'method', 'definition'):
            if not isinstance(row.get(key), str) or not row[key]: raise ValueError(f'Missing {key}: {row["id"]}')
        if row.get('schema') != SCHEMA: raise ValueError('Unsupported descriptor schema')
        if row['category'] not in categories: raise ValueError('Unknown category')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', row['id']): raise ValueError('Unsafe ID')
        definition = read_json(confined(p, row['definition']))
        if definition.get('id') != row.get('source_id', row['id']): raise ValueError('Original definition identity changed')
        for role in row.get('relations', []):
            if role.get('id') not in ids: raise ValueError('Unresolved semantic relation')
            if role.get('role') not in {'physical_reference', 'element_reference', 'derived_from', 'related', 'example'}:
                raise ValueError('Unknown semantic relation role')
        for dep in row.get('runtime_dependencies', []):
            identity = dep if isinstance(dep, str) else dep.get('id')
            if identity not in ids: raise ValueError('Unresolved required runtime dependency')
        for file in ('README.md', 'ATTRIBUTIONS.md', 'attribution.json'):
            if not (p / file).is_file(): raise ValueError('Missing per-asset navigation/attribution: ' + str(p / file))
        attribution = read_json(p / 'attribution.json')
        attr_id = attribution.get('id') or attribution.get('asset_id')
        if attr_id is not None and attr_id != row['id']: raise ValueError('Attribution belongs to another identity')
        entry = by_id[row['id']]
        if entry['descriptor_sha256'] != digest(p / 'asset.json') or entry['definition_sha256'] != digest(p / row['definition']):
            raise ValueError('Catalog describes stale inputs: ' + row['id'])
        if entry['attribution_page'] != row['path'] + '/ATTRIBUTIONS.md': raise ValueError('Incorrect attribution link')
        for representation in entry['representations']:
            target = confined(root, representation['path'])
            if not target.resolve().is_relative_to(p.resolve()): raise ValueError('Representation escapes asset folder')
            if representation['available']:
                if not target.is_file(): raise ValueError('Advertised payload is absent')
                if representation['sha256'] != digest(target): raise ValueError('Advertised payload digest changed')
        if (p / 'FILES.json').is_file(): original_entries += len(read_json(p / 'FILES.json')['files'])
    # Detect cycles in actual required dependencies; scientific relationships are not install dependencies.
    graph = {r['id']: [(d if isinstance(d, str) else d['id']) for d in r.get('runtime_dependencies', [])] for r in rows}
    active, done = set(), set()
    def visit(identity):
        if identity in active: raise ValueError('Cyclic required dependency')
        if identity in done: return
        active.add(identity)
        for other in graph[identity]: visit(other)
        active.remove(identity); done.add(identity)
    for identity in ids: visit(identity)
    planned = 0
    for category, _, _ in CATEGORIES:
        folder = root / 'assets' / category
        if not (folder / 'README.md').is_file(): raise ValueError('Category not represented in Git')
        if not any(r['category'] == category for r in rows): planned += 1
        for sub in FUTURE_PATHS.get(category, []):
            if not (folder / sub / 'README.md').is_file(): raise ValueError('Prepared subcategory is absent')
    # Validate navigation only. Frozen source reports retain historical links by design.
    pages = [root / p for p in ('README.md', 'INDEX.md', 'ATTRIBUTIONS.md', 'CONTRIBUTING.md')]
    pages += list((root / 'docs').glob('*.md')) + list((root / 'catalog/pages').glob('*.md'))
    pages += [root / r['path'] / 'ATTRIBUTIONS.md' for r in rows]
    pages += [p for p in (root / 'assets').rglob('README.md') if 'provenance' not in p.relative_to(root).parts and 'files' not in p.relative_to(root).parts]
    pages += list((root / 'collections').glob('*.md'))
    pages += [root / p / 'README.md' for p in ('LICENSES', 'schemas', 'packages', 'resources', 'provenance')]
    broken = []
    links = 0
    pattern = re.compile(r'(?<!!)\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)')
    for page in pages:
        for raw in pattern.findall(page.read_text(encoding='utf-8-sig')):
            if raw.startswith(('#', 'https://', 'http://', 'mailto:')): continue
            if urlsplit(raw).scheme: raise ValueError('Unexpected navigation URL scheme')
            relative = unquote(raw.split('#', 1)[0])
            if not relative: continue
            target = (page.parent / relative).resolve()
            links += 1
            if not target.is_relative_to(root.resolve()) or not target.exists():
                broken.append({'from': page.relative_to(root).as_posix(), 'to': raw})
    if broken: raise ValueError('Broken active navigation links: ' + json.dumps(broken[:25]))
    preserved = {}
    if migration:
        manifest = read_json(root / 'provenance/layout-migration-20261030.json')
        if set(manifest['definition_sha256']) != ids: raise ValueError('Migration dropped or added an identity')
        for identity, sha in manifest['definition_sha256'].items():
            if digest(root / paths[identity] / 'definition.json') != sha:
                raise ValueError('Original scientific/visual definition changed during reorganization: ' + identity)
        baseline = manifest['source_commit']
        tree = subprocess.check_output(['git', '-C', str(root), 'ls-tree', '-r', '-z', baseline])
        preserved_count = preserved_bytes = 0
        missing = []
        for record in tree.split(b'\0'):
            if not record: continue
            metadata, path_bytes = record.split(b'\t', 1)
            mode, kind, sha = metadata.decode().split()
            old = path_bytes.decode('utf-8')
            new = None
            if old.startswith('extras/'):
                parts = old.split('/')
                if len(parts) > 2 and parts[1] in paths:
                    tail = '/'.join(parts[2:])
                    if tail == 'README.md': tail = 'provenance/legacy-readme.md'
                    new = paths[parts[1]] + '/' + tail
                else: new = 'archive/legacy/' + old
            elif old.startswith(('catalog/', 'authoring/', 'distribution/')):
                new = 'archive/legacy/' + old
            if not new or kind != 'blob': continue
            path = root / new
            if not path.is_file(): missing.append(new); continue
            content = path.read_bytes()
            actual = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
            if actual != sha: raise ValueError('Moved source bytes changed: ' + new)
            preserved_count += 1; preserved_bytes += len(content)
        if missing: raise ValueError('Missing moved source files: ' + json.dumps(missing[:20]))
        preserved = {'original_blobs_preserved': preserved_count, 'original_bytes_preserved': preserved_bytes, 'definitions_preserved': len(ids)}
    return {'status': 'PASS', 'assets': len(rows), 'types': len(kinds), 'categories': len(CATEGORIES), 'prepared_empty_categories': planned,
            'attribution_pages': len(rows) + 1, 'original_file_receipts': original_entries, 'navigation_links_checked': links,
            **preserved, 'scope': 'Structure, navigation, attribution coverage, advertised file digests and optional migration preservation; no new visual/native qualification'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--migration', action='store_true', help='Also compare all moved original blobs with the recorded baseline commit')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = validate(args.root, migration=args.migration)
    text = json.dumps(result, indent=2) + '\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding='utf-8')
    print(text)
