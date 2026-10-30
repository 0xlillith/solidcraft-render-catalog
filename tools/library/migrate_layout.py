"""One-time, lossless layout migration from the published individual extras tree.

Only repository directories are reorganized. No downloads, packs, release edits,
document conversion, physical-property edits or application changes are performed.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import shutil
import subprocess
from pathlib import Path

from common import ROOT, SCHEMA, CATEGORIES, FUTURE_PATHS, confined, digest, json_text, read_json, write_text


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "unclassified"


def broad_family(row: dict, definition: dict) -> str:
    origin = row["origin_collection"]
    identity = row["id"]
    family = str(definition.get("family", "")).lower()
    if origin == "stage-01-woods": return "wood"
    if origin == "stage-02-alloys": return "metals"
    if origin in ("stage-03-printing", "stage-03b-additive"): return "additive-manufacturing"
    if origin == "stage-04-earth-masonry": return "earth-and-masonry"
    if origin == "stage-05-elements": return "element-studies"
    if origin == "scanned-pbr-r1": return "wood" if "veneer" in identity else "earth-and-masonry"
    if row["kind"] == "physical_reference":
        return {"metal": "metals", "polymer": "polymers", "glass": "glass-and-optics", "wood": "wood", "other": "other-references"}.get(family, slug(family))
    # Editorial source families, never inferred physical properties.
    groups = [
        ("selene", "selene"), ("rover", "selene"),
        ("lunar", "lunar"), ("space", "space"), ("aerospace", "aerospace"),
        ("automotive", "automotive"), ("industrial", "industrial"),
        ("additive", "additive-manufacturing"), ("fdm", "additive-manufacturing"),
        ("resin-printing", "additive-manufacturing"), ("powder-printing", "additive-manufacturing"), ("printer ", "additive-manufacturing"),
        ("wood", "wood"), ("timber", "wood"), ("bamboo", "wood"), ("diy", "wood"),
        ("led", "electronics-and-optics"), ("electro", "electronics-and-optics"), ("pcb", "electronics-and-optics"),
        ("circuit", "electronics-and-optics"), ("battery", "electronics-and-optics"), ("harness", "electronics-and-optics"),
        ("paint", "paints-and-coatings"), ("coating", "paints-and-coatings"),
        ("steel", "metals"), ("aluminium", "metals"), ("copper", "metals"), ("metal", "metals"), ("machined", "metals"),
        ("polymer", "polymers"), ("elastomer", "polymers"), ("foam", "polymers"), ("seal", "polymers"),
        ("glass", "glass-and-optics"), ("optical-window", "glass-and-optics"), ("transparent containment", "glass-and-optics"),
        ("ceramic", "ceramics"), ("porcelain", "ceramics"),
        ("concrete", "earth-and-masonry"), ("stone", "earth-and-masonry"), ("mineral", "earth-and-masonry"),
        ("textile", "textiles"), ("leather", "textiles"),
        ("flooring", "building-products"), ("insulation", "building-products"),
        ("composite", "composites"), ("liquid", "liquids"), ("gel", "liquids"),
        ("optical", "optical-studies"), ("absorbing", "optical-studies"),
    ]
    return next((target for term, target in groups if term in family), "other-appearances")


def classify(row: dict, definition: dict) -> dict:
    kind = row["kind"]
    family = broad_family(row, definition)
    if kind in {"material", "material_appearance", "illustrative_element_appearance", "photo_scanned_PBR"}:
        category, subtype, directory = "appearances", "appearance", family
    elif kind == "physical_reference":
        category, subtype, directory = "physical-materials", "physical-reference", family
    elif kind == "pure_element_reference":
        category, subtype, directory, family = "scientific-references", "element-reference", "chemical-elements", "chemical-elements"
    elif kind in {"lighting", "environment", "quality", "shot"}:
        category = "render"
        subtype, directory = {
            "lighting": ("lighting-rig", "lighting"), "environment": ("environment", "environments"),
            "quality": ("render-preset", "presets"), "shot": ("camera-shot", "shots"),
        }[kind]
        family = str(definition.get("family") or directory)
    elif kind == "setup":
        category = "render"
        f = str(definition.get("family", "")).lower()
        if "studio" in f:
            subtype, directory = "studio", "studios"
        elif f == "environment setup":
            subtype, directory = "environment-setup", "environment-setups"
        else:
            subtype, directory = "scene-setup", "scene-setups"
        family = directory
    else:
        raise ValueError("Unclassified legacy kind: " + kind)
    method = "scanned" if kind == "photo_scanned_PBR" else (
        "published-reference" if kind in {"physical_reference", "pure_element_reference"} else
        "illustrative" if kind == "illustrative_element_appearance" else "authored")
    return {"category": category, "type": subtype, "family": family, "method": method,
            "path": f"assets/{category}/{directory}/{row['id']}"}


def migrate(root: Path, expected_count: int = 2991) -> dict:
    legacy = root / "extras"
    if not (legacy / "INDEX.json").is_file():
        raise ValueError("Original extras/INDEX.json required; migration is not repeatable")
    if (root / "assets").exists():
        raise FileExistsError("Refuse to merge into an existing assets tree")
    rows = read_json(legacy / "INDEX.json")["items"]
    if len(rows) != expected_count or len({r['id'].casefold() for r in rows}) != len(rows):
        raise ValueError("Unexpected or duplicate original identities")
    baseline = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    moves, definitions, paths = [], {}, {}
    # Prepare/validate the entire map before changing directories.
    for row in rows:
        old = confined(legacy, row["folder"])
        definition = read_json(old / "definition.json")
        descriptor = read_json(old / "extra.json")
        destination = classify(row, definition)
        if destination['path'].casefold() in {p.casefold() for p in paths.values()}:
            raise ValueError("Destination collision")
        paths[row['id']] = destination['path']
        descriptor.update({
            "schema": SCHEMA, "type": destination['type'], "category": destination['category'],
            "family": destination['family'], "method": destination['method'],
            "legacy_kind": row['kind'], "legacy_path": 'extras/' + row['folder'],
            "source_namespace": "solidcraft-render-catalog", "maintainer": "0xlillith",
            "attribution": "attribution.json", "credits": "credits.json",
            "facets": {key: definition[key] for key in ("family", "species_id", "cut", "finish_id", "finish", "brand", "manufacturing_process", "atomic_number", "symbol", "group_block", "material_class") if key in definition},
            "relations": [{"role": "element_reference" if dep.startswith('element.') else "physical_reference", "id": dep} for dep in row.get('depends_on', [])],
            "runtime_dependencies": [],
            "dependency_scope": "Legacy depends_on expresses semantic reference links, not package installation requirements. Payload dependency closure remains representation-specific.",
            "compatibility": {"contract": "authoring-data", "installer_format": None, "scope": "Use the declared representations and their source-pinned evidence; no universal importer is claimed."},
        })
        if (old / 'validation/fresh-native-20261027.json').is_file():
            descriptor['evidence_baseline'] = {'definition_sha256': digest(old / 'definition.json')}
            if descriptor.get('active_appearance'):
                descriptor['evidence_baseline']['active_appearance_sha256'] = digest(old / descriptor['active_appearance'])
        definitions[row['id']] = digest(old / 'definition.json')
        moves.append((old, confined(root, destination['path']), descriptor))
    for old, new, descriptor in moves:
        new.parent.mkdir(parents=True, exist_ok=True)
        old.rename(new)
        if (new / 'README.md').is_file():
            (new / 'provenance').mkdir(exist_ok=True)
            (new / 'README.md').rename(new / 'provenance/legacy-readme.md')
        write_text(new / 'asset.json', json_text(descriptor))
    archive = root / 'archive/legacy'
    archive.mkdir(parents=True, exist_ok=True)
    if (root / 'README.md').is_file(): shutil.copyfile(root / 'README.md', archive / 'README.md')
    for name in ('catalog', 'authoring', 'distribution'):
        old = root / name
        if old.exists(): old.rename(archive / name)
    legacy.rename(archive / 'extras')
    # Preserve the exact original notices and make them visible at repository root.
    notices = archive / 'catalog/licenses'
    if notices.is_dir(): shutil.copytree(notices, root / 'LICENSES')
    for category, label, description in CATEGORIES:
        (root / 'assets' / category).mkdir(parents=True, exist_ok=True)
        for subdir in FUTURE_PATHS.get(category, []):
            folder = root / 'assets' / category / subdir
            folder.mkdir(exist_ok=True)
            if not any(folder.iterdir()): write_text(folder / '.gitkeep', '')
    for p in ('schemas', 'collections', 'packages', 'resources', 'provenance'):
        (root / p).mkdir(exist_ok=True)
    write_text(root / 'catalog/paths.json', json_text({'schema': 'solidcraft-library-paths/1', 'assets': dict(sorted(paths.items()))}))
    manifest = {'schema': 'solidcraft-library-layout-migration/1', 'date': '2026-10-30', 'source_commit': baseline,
                'asset_count': len(rows), 'ids_preserved': True, 'definition_sha256': definitions,
                'paths': [{'id': row['id'], 'from': 'extras/' + row['folder'], 'to': paths[row['id']]} for row in rows],
                'archives_changed': False, 'new_packs': 0, 'physical_data_changed': False,
                'scope': 'Published authoring tree reorganization; existing unrelated worktrees remain separate.'}
    write_text(root / 'provenance/layout-migration-20261030.json', json_text(manifest))
    write_text(root / 'assets/.gitignore', '# Restorable original working files are not published by catalog generation.\n**/files/\n')
    write_text(root / 'archive/README.md', '# Historical sources\n\nThe current library starts at [the resource index](../INDEX.md). These records preserve earlier stages, original notices, file receipts and source registries. They are not the current editing authority. Historical links and executable recipes retain the paths used by their recorded revisions; use [the path map](../provenance/layout-migration-20261030.json) to locate current resources.\n')
    write_text(root / 'assets/AGENTS.md', '# Resource editing\n\nThe owner approved this semantic layout on 30 October 2026. Work through stable IDs and the generated path map. Edit asset.json, definition.json, recipes or credits.json; regenerate indexes and attribution pages. Preserve scientific qualifiers, provenance, original receipts and other worktrees. Keep physical references separate from appearances. New assets need attribution and meaningful type/representation metadata. Do not claim native or visual acceptance from index validation. Rebuild one resource at a time; no release packaging or repository transfer is implied. Repository documentation is in English.\n')
    return {'assets': len(rows), 'source_commit': baseline, 'categories': len(CATEGORIES), 'original_definitions': len(definitions)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(migrate(args.root), indent=2))
