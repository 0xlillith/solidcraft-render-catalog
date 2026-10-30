"""Shared identity/path handling for library authoring, independent of folders."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "solidcraft-library-asset/1"

CATEGORIES = [
    ("physical-materials", "Physical material references", "Grades, conditions and source-backed physical properties."),
    ("appearances", "Appearances", "Visual surfaces, with physical references kept separate."),
    ("finishes", "Reusable finishes", "Future reusable coatings, wear, dirt and treatment layers."),
    ("scientific-references", "Scientific references", "Scientific identities and reference facts, not automatically engineering grades."),
    ("parts", "Parts and assemblies", "Reusable components, dimensional families and assembly references."),
    ("render", "Rendering", "Lights, environments, backgrounds, studios, presets and scene studies."),
    ("drawings", "Drawings", "Paper, borders, title blocks, symbols, styles, tables and templates."),
    ("themes", "Interface themes", "Interface appearance and accessibility; separate from printed drawing styles."),
    ("animation", "Animation", "Declarative motion, camera paths and animation configurations."),
    ("simulation", "Simulation and digital twins", "Reusable declarative settings and datasets with explicit consumer requirements."),
    ("examples", "Examples and learning", "Complete demonstrations and educational documents, separate from reusable dependencies."),
]

FUTURE_PATHS = {
    "finishes": ["coatings", "weathering", "decals", "masks"],
    "parts": ["fasteners", "bearings", "profiles", "fittings", "components", "assemblies"],
    "render": ["lighting", "environments", "backgrounds", "studios", "environment-setups", "scene-setups", "presets", "shots", "scene-templates", "post-processing"],
    "drawings": ["paper", "borders", "title-blocks", "symbols", "styles", "tables", "templates"],
    "themes": ["light", "dark", "high-contrast"],
    "animation": ["motion", "camera-paths", "lighting", "presets"],
    "simulation": ["material-models", "boundary-conditions", "sensors", "datasets", "presets"],
    "examples": ["projects", "tutorials", "benchmarks"],
}

def read_json(path: Path):
    def reject(value):
        raise ValueError("Nonfinite JSON number: " + value)
    return json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=reject)

def json_text(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"

def write_text(path: Path, text: str, *, check: bool = False) -> bool:
    content = text.encode("utf-8")
    unchanged = path.is_file() and path.read_bytes() == content
    if check and not unchanged:
        raise ValueError("Generated file is stale or absent: " + str(path))
    if not unchanged and not check:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return not unchanged

def confined(root: Path, relative: str) -> Path:
    p = PurePosixPath(relative)
    if not relative or p.is_absolute() or ".." in p.parts or "\\" in relative or ":" in relative:
        raise ValueError("Unsafe repository-relative path: " + relative)
    result = root.joinpath(*p.parts)
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path escapes library: " + relative)
    return result

def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def asset_records(root: Path = ROOT) -> list[dict]:
    records = []
    seen = set()
    for path in sorted((root / "assets").rglob("asset.json")):
        data = read_json(path)
        identity = data["id"]
        if identity.casefold() in seen:
            raise ValueError("Duplicate case-insensitive asset identity: " + identity)
        seen.add(identity.casefold())
        data["path"] = path.parent.relative_to(root).as_posix()
        records.append(data)
    return sorted(records, key=lambda r: r["id"].casefold())

def path_map(root: Path = ROOT) -> dict[str, str]:
    index = root / "catalog" / "paths.json"
    if index.is_file():
        return read_json(index)["assets"]
    # During initial generation descriptors are authoritative; no ID-to-path concatenation.
    return {row["id"]: row["path"] for row in asset_records(root)}

def asset_directory(identity: str, root: Path = ROOT, *, mapping: dict[str, str] | None = None) -> Path:
    mapping = path_map(root) if mapping is None else mapping
    if identity not in mapping:
        raise ValueError("Unknown asset identity: " + identity)
    folder = confined(root, mapping[identity])
    if not (folder / "definition.json").is_file():
        raise ValueError("Asset definition is absent: " + identity)
    if metadata(folder).get("id") != identity:
        raise ValueError("Asset identity does not match catalog path: " + identity)
    return folder

def archive_sources(root: Path = ROOT) -> Path:
    return root / "archive/legacy/extras/ARCHIVE-SOURCES.json"

def metadata(folder: Path) -> dict:
    path = folder / "asset.json"
    return read_json(path if path.is_file() else folder / "extra.json")

def markdown(value) -> str:
    import html
    text = html.escape(str(value or ""), quote=False).replace("\\", "\\\\")
    for char in "[]`*_~|":
        text = text.replace(char, "\\" + char)
    return text.replace("\n", " ").replace("\r", " ")

def href(path: str) -> str:
    from urllib.parse import quote
    return "/".join(quote(part, safe="@.-_") for part in path.split("/"))
