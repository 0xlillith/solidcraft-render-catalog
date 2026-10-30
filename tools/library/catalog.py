"""Build or check the complete, deterministic authoring catalog (no packaging)."""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import posixpath
import re
from pathlib import Path

from common import ROOT, CATEGORIES, FUTURE_PATHS, asset_records, confined, digest, href, json_text, markdown, read_json, write_text
from browser import render_browser
from attributions import build_attributions


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-') or 'unclassified'


def link_from(folder: str, target: str) -> str:
    return href(posixpath.relpath(target, folder or '.'))


def source_urls(value):
    found = {}
    def visit(obj):
        if isinstance(obj, dict):
            candidates = [obj.get('url'), obj.get('source_url')] + (obj.get('urls', []) if isinstance(obj.get('urls'), list) else [])
            for url in candidates:
                if isinstance(url, str) and url.startswith(('https://', 'http://')):
                    found.setdefault(url, {'url': url, 'title': str(obj.get('title') or obj.get('name') or obj.get('label') or url), 'role': str(obj.get('role') or 'source'), 'authors': obj.get('authors', [])})
            for child in obj.values(): visit(child)
        elif isinstance(obj, list):
            for child in obj: visit(child)
    visit(value)
    return sorted(found.values(), key=lambda x: x['url'])


def flatten_strings(value):
    if isinstance(value, str): return [value]
    if isinstance(value, (float, int)): return [str(value)]
    if isinstance(value, list): return [s for v in value for s in flatten_strings(v)]
    if isinstance(value, dict): return [s for v in value.values() for s in flatten_strings(v)]
    return []


def representation_records(root: Path, row: dict, definition: dict):
    folder = root / row['path']
    originals = {f['path']: f for f in read_json(folder / 'FILES.json').get('files', [])} if (folder / 'FILES.json').is_file() else {}
    names = {('files/' + f['path']): f.get('label', '') for f in definition.get('files', []) if isinstance(f, dict) and isinstance(f.get('path'), str)}
    result = []
    def add(relative, label, role='payload', note=''):
        if not relative or any(r['relative_path'] == relative for r in result): return
        target = confined(folder, relative)
        original = originals.get(relative)
        # The published catalog describes repository availability, not workstation caches.
        tracked = target.is_file() and not relative.startswith('files/')
        item = {'label': label or Path(relative).name, 'path': row['path'] + '/' + relative,
                'relative_path': relative, 'role': role, 'format': target.suffix.lstrip('.').upper() or 'DATA',
                'available': tracked, 'storage': 'repository' if tracked else 'historical-original' if original else 'unavailable',
                'availability': 'tracked' if tracked else 'restore_required' if original else 'unknown',
                'bytes': target.stat().st_size if tracked else original.get('bytes') if original else None,
                'sha256': digest(target) if tracked else original.get('sha256') if original else None,
                'note': note}
        if original:
            item['restoration'] = {'archive': original['archive'], 'member': original['member'], 'receipt': row['path'] + '/FILES.json'}
        result.append(item)
    active = row.get('active_appearance')
    if active:
        add(active, 'Active authored appearance profile', 'appearance-definition', 'Read this profile for supported maps, physical scale and native limitations.')
        profile = read_json(confined(folder, active))
        for role, spec in profile.get('maps', {}).items():
            add((Path(active).parent / spec['path']).as_posix(), role.replace('_', ' ').title(), 'texture-map')
    for relative in row.get('entrypoints', []):
        add(relative, names.get(relative) or Path(relative).name)
    for relative in row.get('previews', []):
        add(relative, 'Preview', 'preview', 'A preview is evidence or illustration, not an interchangeable material or model.')
    if not result:
        add(row.get('definition', 'definition.json'), 'Reference definition', 'reference-data')
    return result, originals


def evidence(root: Path, row: dict, definition_sha: str):
    folder = root / row['path']
    fresh = folder / 'validation/fresh-native-20261027.json'
    baseline = row.get('evidence_baseline', {})
    current = baseline.get('definition_sha256') == definition_sha
    if row.get('active_appearance') and baseline.get('active_appearance_sha256'):
        profile_path = folder / row['active_appearance']
        current = current and digest(profile_path) == baseline['active_appearance_sha256']
        profile = read_json(profile_path)
        for spec in profile.get('maps', {}).values():
            payload = confined(profile_path.parent, spec['path'])
            current = current and payload.is_file() and digest(payload) == spec.get('sha256')
    if fresh.is_file():
        receipt = read_json(fresh)
        return ('Current native sample' if current else 'Needs revalidation'), {
            'scope': 'A bounded sample test of the recorded definition and representation; not full UI, measured optics or engineering qualification.',
            'file': row['path'] + '/validation/fresh-native-20261027.json', 'version': receipt.get('version'),
            'passed': receipt.get('passed', []), 'baseline_matches': current, 'premium_qualified': False}
    authored_previews = [p for p in row.get('previews', []) if p.startswith('authored/')]
    if authored_previews:
        return 'Software preview', {'scope': 'Authored software preview; not a native screenshot or material qualification.', 'premium_qualified': False}
    history = folder / 'validation/native-history.json'
    if history.is_file() or row.get('historical_evidence'):
        return 'Historical evidence', {'scope': row.get('quality_note', 'Historical source evidence; inspect recorded scope.'), 'premium_qualified': False}
    return 'Not recorded', {'scope': row.get('quality_note', 'No current consumer acceptance recorded.'), 'premium_qualified': False}


def make_record(root: Path, row: dict) -> dict:
    folder = root / row['path']
    definition_path = confined(folder, row.get('definition', 'definition.json'))
    definition = read_json(definition_path)
    attribution_path = folder / 'attribution.json'
    attribution = read_json(attribution_path) if attribution_path.is_file() else {}
    representations, originals = representation_records(root, row, definition)
    payloads = [r for r in representations if r['role'] != 'preview']
    present = sum(r['available'] for r in payloads)
    archived = sum(r['storage'] == 'historical-original' for r in payloads)
    availability = 'mixed' if present and archived else 'tracked' if present else 'restore_required' if archived else 'metadata_only'
    validation, quality = evidence(root, row, digest(definition_path))
    # Detailed attribution stays in the generated, evidence-backed per-asset record.
    license_label = attribution.get('display_license') or attribution.get('license_expression') or definition.get('license')
    if not isinstance(license_label, str):
        license_label = 'Original authoring: MIT OR Apache-2.0; references retain source terms'
    authors = attribution.get('display_authors') or attribution.get('authors') or []
    if isinstance(authors, dict): authors = list(authors)
    if isinstance(authors, list):
        authors = [a if isinstance(a, str) else a.get('name', a.get('value', '')) for a in authors if isinstance(a, (str, dict))]
    else: authors = []
    sources = source_urls(attribution)
    source_authors = sorted(set(flatten_strings([s.get('authors', []) for s in attribution.get('sources', []) if isinstance(s, dict)])))
    tags = sorted(set([row['category'], row['type'], row['family'], row['method']] + flatten_strings(row.get('facets', {})) + list(row.get('tags', [])) + source_authors))
    preview = next((r['path'] for r in representations if r['role'] == 'preview' and r['available']), None)
    return {
        'id': row['id'], 'name': row.get('name') or definition.get('name') or row['id'],
        'path': row['path'], 'category': row['category'], 'type': row['type'], 'family': row['family'], 'method': row['method'],
        'legacy_kind': row.get('legacy_kind', row.get('kind')), 'origin': row.get('origin', {}),
        'origin_collection': row.get('origin', {}).get('collection', ''),
        'description': definition.get('description') or str(definition.get('physical_scope') or definition.get('appearance_status') or definition.get('condition') or ''),
        'tags': tags, 'facets': row.get('facets', {}), 'license': license_label, 'authors': authors, 'source_authors': source_authors, 'sources': sources,
        'attribution': row['path'] + '/attribution.json', 'attribution_page': row['path'] + '/ATTRIBUTIONS.md',
        'relations': row.get('relations', []), 'related': [r['id'] for r in row.get('relations', []) if 'id' in r],
        'dependencies': row.get('runtime_dependencies', []), 'availability': availability,
        'validation': validation, 'quality': quality, 'compatibility': row.get('compatibility', {}),
        'representations': representations, 'preview': preview,
        'original_file_count': len(originals), 'original_bytes': sum(f.get('bytes', 0) for f in originals.values()),
        'definition_sha256': digest(definition_path), 'descriptor_sha256': digest(folder / 'asset.json'),
    }


def resource_page(record: dict, all_by_id: dict) -> str:
    p = record['path']
    out = [f"# {markdown(record['name'])}", '',
           f"[Library index]({link_from(p, 'INDEX.md')}) · [Category]({link_from(p, 'assets/' + record['category'] + '/README.md')}) · [Attributions](ATTRIBUTIONS.md)", '',
           record['description'], '', '| Field | Value |', '|---|---|',
           f"| Stable ID | `{record['id']}` |", f"| Type | {markdown(record['type'])} |", f"| Family | {markdown(record['family'])} |",
           f"| Method | {markdown(record['method'])} |", f"| Repository payloads | {record['availability']} |",
           f"| Evidence | {record['validation']} |", f"| Source collection | {record['origin_collection']} |", '',
           '## Edit and inspect', '', '[Editable descriptor](asset.json) · [Typed definition](definition.json) · [Complete attribution record](attribution.json)', '',
           'Edit the descriptor, definition, recipes or optional `credits.json`; regenerate this page with `python tools/library/catalog.py build`. The original `extra.json`, file receipts and provenance retain their historical scope.', '',
           '## Representations and files', '', '| Representation | Role / format | Availability |', '|---|---|---|']
    for r in record['representations']:
        title = f"[{markdown(r['label'])}]({href(r['relative_path'])})" if r['available'] else markdown(r['label'])
        available = 'Present in repository' if r['available'] else 'Restore original separately' if r['storage'] == 'historical-original' else 'Not available'
        out.append(f"| {title} | {r['role']} / {r['format']} | {available} |")
    if record['original_file_count']:
        out += ['', f"The original receipt lists **{record['original_file_count']} files**. [FILES.json](FILES.json) records their exact hashes and restoration locators; it does not certify later edits.", '']
    else:
        out += ['', 'No historical archive members are recorded for this resource. Use the declared source definition and representations above.', '']
    out += ['## Evidence and scope', '', record['quality']['scope'], '']
    if record['quality'].get('file'):
        out += [f"[Recorded sample test]({link_from(p, record['quality']['file'])})", '']
    if record['relations']:
        out += ['## Related references', '', 'These links describe meaning and provenance; they are not automatic material assignments or package installation dependencies.', '']
        for rel in record['relations']:
            target = all_by_id.get(rel['id'])
            if target:
                out.append(f"- {rel['role']}: [{markdown(target['name'])}]({link_from(p, target['path'] + '/README.md')}) (`{rel['id']}`).")
        out.append('')
    out += ['## Credits and license', '', f"{markdown(record['license'])}. See [ATTRIBUTIONS.md](ATTRIBUTIONS.md) for authors, original notices, sources and unresolved terms. Source publications do not inherit the license of the authoring code.", '']
    return '\n'.join(out)


def listing_page(title: str, records: list[dict], relative_folder: str, extra_nav=''):
    out = ['<!-- Generated by tools/library/catalog.py -->', f'# {markdown(title)}', '', f'[Complete library index]({link_from(relative_folder, "INDEX.md")})' + extra_nav, '',
           f'{len(records)} entries on this page. Availability and evidence refer to the stated representations.', '',
           '| Resource | Type | Method | Evidence | Credits |', '|---|---|---|---|---|']
    for r in records:
        out.append(f"| [{markdown(r['name'])}]({link_from(relative_folder, r['path'] + '/README.md')})<br>`{r['id']}` | {r['type']} | {r['method']} | {r['validation']} | [Attributions]({link_from(relative_folder, r['attribution_page'])}) |")
    return '\n'.join(out) + '\n'


def build(root: Path = ROOT, check=False):
    descriptors = asset_records(root)
    if not descriptors: raise ValueError('No asset descriptors found')
    attribution_summary = build_attributions(root, descriptors, check=check)
    if attribution_summary.get('errors'):
        raise ValueError('Attribution generation failed: ' + str(attribution_summary['errors'][:10]))
    records = [make_record(root, row) for row in descriptors]
    records.sort(key=lambda r: (r['category'], r['family'].casefold(), r['name'].casefold(), r['id']))
    by_id = {r['id']: r for r in records}
    category_counts = collections.Counter(r['category'] for r in records)
    summary = {'total': len(records), 'categories': [{'id': key, 'label': label, 'path': 'assets/' + key, 'count': category_counts[key], 'planned': category_counts[key] == 0} for key, label, _ in CATEGORIES],
               'types': dict(sorted(collections.Counter(r['type'] for r in records).items())),
               'availability': dict(sorted(collections.Counter(r['availability'] for r in records).items())),
               'validation': dict(sorted(collections.Counter(r['validation'] for r in records).items()))}
    write_text(root / 'catalog/paths.json', json_text({'schema': 'solidcraft-library-paths/1', 'assets': dict(sorted((r['id'], r['path']) for r in records))}), check=check)
    write_text(root / 'catalog/index.json', json_text({'schema': 'solidcraft-library-catalog/1', 'scope': 'Authoring catalog; not an installation format', 'count': len(records), 'summary': summary, 'items': records}), check=check)
    write_text(root / 'catalog/summary.json', json_text(summary), check=check)
    buf = io.StringIO(newline='')
    writer = csv.DictWriter(buf, fieldnames=['id', 'name', 'type', 'category', 'family', 'method', 'availability', 'validation', 'license', 'path'], lineterminator='\n')
    writer.writeheader()
    writer.writerows({key: r[key] for key in writer.fieldnames} for r in records)
    write_text(root / 'catalog/assets.csv', buf.getvalue(), check=check)
    groups = collections.defaultdict(list)
    for r in records: groups[(r['category'], r['family'])].append(r)
    index = ['# Complete resource index', '', '[Overview](README.md) · [Offline search](index.html) · [Collections](collections/README.md) · [Attributions](ATTRIBUTIONS.md) · [JSON](catalog/index.json) · [CSV](catalog/assets.csv)', '',
             f'**{len(records):,} individually identified resources.** Every resource is listed on a family page below and has its own description and attribution page. Counts include visual variants, scientific references and settings; they are not counts of unique engineering materials.', '',
             '## Categories', '', '| Category | Resources | State |', '|---|---:|---|']
    for cat in summary['categories']:
        index.append(f"| [{cat['label']}]({cat['path']}/README.md) | {cat['count']} | {'Prepared for future content' if cat['planned'] else 'Populated'} |")
    index += ['', '## All families', '', '| Category / family | Entries | Complete listing |', '|---|---:|---|']
    family_pages = {}
    for (category, family), group in sorted(groups.items()):
        family_key = slug(family) + '-' + hashlib.sha256(family.encode('utf-8')).hexdigest()[:8]
        pages = [f'catalog/pages/{category}--{family_key}--{n // 150 + 1:02}.md' for n in range(0, len(group), 150)]
        family_pages[(category, family)] = pages
        for i, page in enumerate(pages):
            nav = ' · ' + ' · '.join(f'[{n + 1}]({Path(p).name})' for n, p in enumerate(pages)) if len(pages) > 1 else ''
            write_text(root / page, listing_page(f'{family} — {category} ({i + 1}/{len(pages)})', group[i * 150:(i + 1) * 150], 'catalog/pages', nav), check=check)
        page_links = ' · '.join(f'[Page {n + 1}]({p})' for n, p in enumerate(pages))
        index.append(f'| {category} / {markdown(family)} | {len(group)} | {page_links} |')
    expected_pages = {p for pages in family_pages.values() for p in pages}
    for old in (root / 'catalog/pages').glob('*.md'):
        if old.relative_to(root).as_posix() not in expected_pages:
            if check: raise ValueError('Orphaned generated family page: ' + str(old))
            if not old.read_text(encoding='utf-8-sig').startswith('<!-- Generated by tools/library/catalog.py -->'):
                raise ValueError('Unmanaged file in generated pages directory: ' + str(old))
            old.unlink()
    write_text(root / 'INDEX.md', '\n'.join(index) + '\n', check=check)
    for category, label, description in CATEGORIES:
        p = 'assets/' + category
        rows = [r for r in records if r['category'] == category]
        lines = [f'# {label}', '', f'[Complete index]({link_from(p, "INDEX.md")}) · [Attributions]({link_from(p, "ATTRIBUTIONS.md")})', '', description, '',
                 f'**{len(rows)} registered resources.**' if rows else '**Prepared category: no resources have been registered yet.**', '',
                 'New entries need a stable ID, an explicit type, attribution, representation requirements and appropriate evidence. A reserved folder does not announce application support.', '']
        for (cat, family), pages in sorted(family_pages.items()):
            if cat == category:
                links = ' · '.join(f'[Page {n + 1}]({link_from(p, page)})' for n, page in enumerate(pages))
                lines.append(f'- **{markdown(family)}** ({len(groups[(cat, family)])}): {links}')
        if FUTURE_PATHS.get(category):
            lines += ['', '## Subcategories', '']
            for sub in FUTURE_PATHS[category]:
                folder = root / p / sub
                child_rows = [r for r in rows if r['path'].startswith(p + '/' + sub + '/')]
                lines.append(f'- [{sub}]({sub}/README.md): {len(child_rows)} resources.' if child_rows else f'- [{sub}]({sub}/README.md): prepared.')
                body = listing_page(sub.replace('-', ' ').title(), child_rows, p + '/' + sub) if child_rows else f'# {sub.replace("-", " ").title()}\n\n[Category](../README.md) · [Library index]({link_from(p + "/" + sub, "INDEX.md")})\n\nPrepared for future {sub.replace("-", " ")} resources. No assets or application support are implied. Add a descriptor, sources and credits before registering content.\n'
                write_text(folder / 'README.md', body, check=check)
        write_text(root / p / 'README.md', '\n'.join(lines) + '\n', check=check)
    for record in records:
        write_text(root / record['path'] / 'README.md', resource_page(record, by_id), check=check)
    folder_groups = collections.defaultdict(list)
    for record in records:
        if record['category'] != 'render':
            folder_groups[posixpath.dirname(record['path'])].append(record)
    for folder, members in sorted(folder_groups.items()):
        write_text(root / folder / 'README.md', listing_page(members[0]['family'], members, folder), check=check)
    collections_index = []
    collection_guide = ['# Curated collections', '', '[Complete resource index](../INDEX.md)', '',
                        'These editable selections group existing assets without creating a pack, coupling versions or downloading payloads. A resource may appear in several collections.', '']
    for spec_path in sorted((root / 'collections').glob('*.json')):
        spec = read_json(spec_path)
        if spec.get('schema') != 'solidcraft-library-collection/1': raise ValueError('Unsupported collection schema')
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', spec['id']): raise ValueError('Invalid collection identity')
        allowed = {'category', 'type', 'family', 'method'}
        for selector in spec['include']:
            if not selector or set(selector) - allowed: raise ValueError('Unsupported collection selector')
        members = [r for r in records if any(all(r[key] == value for key, value in selector.items()) for selector in spec['include'])]
        page = 'collections/' + spec['id'] + '.md'
        collection_guide += [f"- [{markdown(spec['name'])}]({spec['id']}.md): **{len(members)}** resources. {markdown(spec.get('description', ''))}"]
        write_text(root / page, listing_page(spec['name'], members, 'collections'), check=check)
        collections_index.append({'id': spec['id'], 'name': spec['name'], 'definition': spec_path.relative_to(root).as_posix(), 'count': len(members), 'members': [r['id'] for r in members]})
    write_text(root / 'collections/README.md', '\n'.join(collection_guide) + '\n', check=check)
    write_text(root / 'catalog/collections.json', json_text({'schema': 'solidcraft-library-collections/1', 'items': collections_index}), check=check)
    write_text(root / 'index.html', render_browser(records, summary), check=check)
    return {'status': 'PASS', 'assets': len(records), 'family_pages': sum(len(p) for p in family_pages.values()), 'categories': len(CATEGORIES),
            'attributions': {k: v for k, v in attribution_summary.items() if k not in {'records', 'changed_files'}},
            'scope': 'Catalog, attribution and navigation consistency; no new native qualification'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build', 'check'])
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(build(args.root, check=args.action == 'check'), indent=2, default=str))
