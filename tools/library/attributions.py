#!/usr/bin/env python3
"""Build traceable credits without assigning source ownership to derived assets.

Editable inputs are credits.json and preserved definition/recipe/provenance JSON.
ATTRIBUTIONS.md, attribution.json and catalog/attributions.json are generated.
This module does not contact the network or alter source files or license texts.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import quote

SCHEMA = "solidcraft-library-attribution/1"
POLICY_LICENSE = "MIT OR Apache-2.0"
POLICY_SCOPE = (
    "The existing repository policy covers original SolidCraft contributions only. "
    "It does not relicense imported payloads, cited publications, datasets or fonts. "
    "A source author is not automatically the author of this derived resource."
)
MAX_JSON_BYTES = 32 * 1024 * 1024
URL_RE = re.compile(r"https?://[^\s<>\"\[\]]+")
SOURCE_ID_KEYS = {"sourceid", "sourceids", "sourcereferenceid", "sourcereferences"}
AUTHOR_KEYS = {"author", "authors", "sourceauthor", "sourceauthors", "creator", "creators"}
LICENSE_KEYS = {"license", "licence", "sourcelicense", "sourceassetlicenses", "licenseexpression", "spdx", "spdxlicenseidentifier", "spdxlicenseexpression"}
URL_KEYS = {"url", "urls", "source", "sources", "reference", "references", "sourceurl", "sourceurls", "providerurl", "providersource", "sourceasset", "homepage", "landingpage", "referenceurl", "documenturl"}


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [s for item in value for s in _strings(item)]
    if isinstance(value, dict):
        for name in ("license_expression", "expression", "spdx", "name", "author", "title", "id"):
            if isinstance(value.get(name), str):
                return _strings(value[name])
    return []


def _unique(values: list[str]) -> list[str]:
    return sorted(set(values), key=lambda value: (value.casefold(), value))


def _pointer(parent: str, key: str | int) -> str:
    return parent + "/" + str(key).replace("~", "~0").replace("/", "~1")


def _walk(value: Any, pointer: str = "", depth: int = 0):
    if depth > 48:
        raise ValueError("Attribution input exceeds the supported nesting depth")
    if isinstance(value, dict):
        yield value, pointer
        for key, item in value.items():
            yield from _walk(item, _pointer(pointer, key), depth + 1)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, _pointer(pointer, index), depth + 1)


def _within(repo: Path, path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(repo)
    except ValueError as exc:
        raise ValueError(f"Path escapes repository: {path}") from exc
    return resolved


def _read_json(path: Path) -> Any:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"Metadata file exceeds {MAX_JSON_BYTES} bytes: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _evidence(path: str, pointer: str = "") -> dict:
    return {"path": path, "pointer": pointer or "/"}


def _normal_urls(values: list[str]) -> list[str]:
    return _unique([value for value in values if value.startswith(("https://", "http://"))])


def _source_from_node(node: dict, path: str, pointer: str, *, source_id: str | None = None,
                      role: str = "reference", explicit: bool = False) -> dict | None:
    fields = {_key(key): value for key, value in node.items()}
    urls = _normal_urls([s for key, value in fields.items() if key in URL_KEYS for s in _strings(value)])
    authors = _unique([s for key, value in fields.items() if key in AUTHOR_KEYS for s in _strings(value)])
    terms = _unique([s for key, value in fields.items() if key in LICENSE_KEYS for s in _strings(value)])
    provider = next((fields[key] for key in ("provider", "visualsource", "publisher", "organization") if isinstance(fields.get(key), str)), None)
    if not (urls or explicit):
        return None
    if explicit and role not in {"payload", "reference", "authoring"}:
        raise ValueError(f"{path}{pointer}: source role must be payload, reference or authoring")
    # Physical bibliographic documents must not be presented as copied payloads.
    if fields.get("redistributeddocument") is False and not explicit:
        role = "reference"
    elif not explicit and (fields.get("sourceassetlicenses") or fields.get("sourceasset")):
        role = "payload"
    title = next((fields[key] for key in ("title", "name", "label") if isinstance(fields.get(key), str)), None)
    sid = source_id or next((fields[key] for key in ("id", "sourceid", "referenceid", "slug") if isinstance(fields.get(key), str)), None)
    result = {
        "role": role, "id": sid, "title": title or sid or (urls[0] if urls else "Unspecified source"),
        "urls": urls, "authors": authors, "provider": provider,
        "license_expression": " OR ".join(terms) if len(terms) == 1 else None,
        "recorded_license_terms": terms,
        "license_status": "recorded" if terms else "not-stated",
        "redistributed_document": fields.get("redistributeddocument"),
        "notice": node.get("notice") or node.get("attribution") or node.get("copyright") or node.get("rights"),
        "evidence": [_evidence(path, pointer)], "via_assets": [], "components": [],
    }
    for key in ("retrieved", "accessed", "dated", "version", "locator", "source_locator", "year", "reviewed_on", "source_kind"):
        if key in node and isinstance(node[key], (str, int, float)):
            result[key] = node[key]
    if isinstance(node.get("extracted_from"), dict):
        result["extracted_from"] = node["extracted_from"]
    return result


def _source_key(source: dict) -> str:
    # The same URL may be a reference and an imported payload; preserve that distinction.
    identity = source["urls"] or [source.get("id") or source["title"]]
    return json.dumps([source["role"], identity], ensure_ascii=False, sort_keys=True)


def _merge_sources(sources: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for source in sources:
        key = _source_key(source)
        if key not in merged:
            merged[key] = json.loads(json.dumps(source))
            continue
        item = merged[key]
        for field in ("authors", "recorded_license_terms", "via_assets"):
            item[field] = _unique(item[field] + source.get(field, []))
        ev = {json.dumps(v, sort_keys=True): v for v in item["evidence"] + source["evidence"]}
        item["evidence"] = [ev[k] for k in sorted(ev)]
        components = {json.dumps(v, sort_keys=True): v for v in item.get("components", []) + source.get("components", [])}
        item["components"] = [components[k] for k in sorted(components)]
        for field in ("id", "provider", "notice", "locator", "source_locator", "retrieved", "accessed", "dated", "version", "extracted_from", "year", "reviewed_on", "source_kind"):
            if not item.get(field) and source.get(field):
                item[field] = source[field]
        if item["title"] in item["urls"] and source["title"] not in source["urls"]:
            item["title"] = source["title"]
        # Different statements are retained for review, never combined into an invented grant.
        terms = item["recorded_license_terms"]
        item["license_expression"] = terms[0] if len(terms) == 1 else None
        item["license_status"] = "multiple-statements" if len(terms) > 1 else "recorded" if terms else "not-stated"
    return sorted(merged.values(), key=lambda value: (value["role"], value["title"].casefold(), _source_key(value)))


def _registry(repo: Path) -> tuple[dict[str, list[dict]], list[dict]]:
    index: dict[str, list[dict]] = defaultdict(list)
    files: list[dict] = []
    roots = [repo / "archive/legacy", repo / "authoring", repo / "catalog/source", repo / "provenance", repo / "sources"]
    seen: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.json")):
            if path in seen or not any(token in path.name.lower() for token in ("source", "provenance", "attribution")):
                continue
            seen.add(path)
            _within(repo, path)
            data = _read_json(path)
            relative = path.relative_to(repo).as_posix()
            files.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            for node, pointer in _walk(data):
                # Some historical registries are keyed dictionaries, not arrays
                # with an `id` member. Retain their actual key as the identifier.
                mapping_key = pointer.rsplit("/", 1)[-1].replace("~1", "/").replace("~0", "~") if pointer else None
                fallback = mapping_key if mapping_key and not mapping_key.isdigit() else None
                source = _source_from_node(node, relative, pointer)
                if source and not source.get("id") and fallback:
                    source["id"] = fallback
                if source and source.get("extracted_from"):
                    origin = source["extracted_from"]
                    if not isinstance(origin.get("path"), str):
                        raise ValueError(f"{relative}: extracted_from needs a source path")
                    original = _within(repo, repo / origin["path"])
                    if not original.is_file():
                        raise ValueError(f"Extracted registry source is missing: {origin['path']}")
                    actual = hashlib.sha256(original.read_bytes()).hexdigest()
                    if origin.get("sha256") and origin["sha256"] != actual:
                        raise ValueError(f"Extracted registry source hash differs: {origin['path']}")
                    ev = _evidence(origin["path"])
                    ev["locator"] = "Preserved literal assignment: " + str(origin.get("assignment", "unspecified"))
                    source["evidence"].append(ev)
                if source and source.get("id"):
                    index[source["id"]].append(source)
    return index, files


def _input_files(repo: Path, folder: Path, record: dict) -> list[Path]:
    # The catalog generator owns README.md; ingesting it would make credits depend
    # on generated output and cause drift after the first catalog build.
    paths = {folder / name for name in ("definition.json", "extra.json", "credits.json") if (folder / name).is_file()}
    for name in ("recipes", "provenance", "authored"):
        directory = folder / name
        if directory.is_dir():
            paths.update(path for path in directory.rglob("*") if path.is_file() and path.suffix.lower() in {".json", ".md", ".txt"})
    for supplied in record.get("attribution_source_paths", []):
        path = _within(repo, repo / supplied)
        if not path.is_file():
            raise ValueError(f"Attribution source does not exist: {supplied}")
        paths.add(path)
    return sorted(_within(repo, path) for path in paths)


def _credits(data: Any, path: str) -> tuple[dict, list[dict]]:
    if not isinstance(data, dict):
        raise ValueError(f"{path}: credits.json must contain an object")
    authoring = data.get("authoring", {})
    if not isinstance(authoring, dict):
        raise ValueError(f"{path}: authoring must be an object")
    if "authors" in authoring and (not isinstance(authoring["authors"], list) or not all(isinstance(x, str) for x in authoring["authors"])):
        raise ValueError(f"{path}: authoring.authors must be a list of names")
    if "license_expression" in authoring and (not isinstance(authoring["license_expression"], str) or not authoring["license_expression"].strip()):
        raise ValueError(f"{path}: authoring.license_expression must be a nonempty string")
    inputs = data.get("sources", [])
    if not isinstance(inputs, list):
        raise ValueError(f"{path}: sources must be a list")
    sources = []
    for position, entry in enumerate(inputs):
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: sources[{position}] must be an object")
        for field in ("urls", "authors"):
            if field in entry and (not isinstance(entry[field], list) or not all(isinstance(x, str) for x in entry[field])):
                raise ValueError(f"{path}: sources[{position}].{field} must be a list of strings")
        if any(not url.startswith(("https://", "http://")) for url in entry.get("urls", [])):
            raise ValueError(f"{path}: source URLs must be HTTP(S)")
        source = _source_from_node(entry, path, f"/sources/{position}", role=entry.get("role", "reference"), explicit=True)
        sources.append(source)
    return authoring, sources


def _asset(repo: Path, record: dict, registry: dict[str, list[dict]], policy_files: list[str]) -> dict:
    aid = str(record["id"])
    folder = _within(repo, repo / record["path"])
    if not folder.is_dir():
        raise ValueError(f"Asset directory does not exist: {record['path']}")
    sources: list[dict] = []
    references: dict[str, list[dict]] = defaultdict(list)
    authors: list[str] = []
    declared_licenses: list[str] = []
    author_evidence: list[dict] = []
    files: list[dict] = []
    explicit_authoring: dict = {}
    for path in _input_files(repo, folder, record):
        relative = path.relative_to(repo).as_posix()
        raw = path.read_bytes()
        files.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest()})
        if path.suffix.lower() != ".json":
            # Prose is evidence, not a reliable machine-readable license assignment.
            continue
        data = _read_json(path)
        if path.name == "credits.json" and path.parent == folder:
            explicit_authoring, explicit_sources = _credits(data, relative)
            sources.extend(explicit_sources)
            if explicit_authoring:
                author_evidence.append(_evidence(relative, "/authoring"))
            continue
        scanned = record.get("method") == "scanned" or record.get("kind") == "photo_scanned_PBR" or record.get("legacy_kind") == "photo_scanned_PBR"
        if isinstance(data, dict) and data.get("kind") == "photo_scanned_PBR":
            scanned = True
        parent_payload = None
        for node, pointer in _walk(data):
            for key, value in node.items():
                norm = _key(key)
                if norm == "authoringlicense":
                    declared_licenses.extend(_strings(value))
                    author_evidence.append(_evidence(relative, _pointer(pointer, key)))
                if norm in {"authoringauthor", "authoringauthors", "originalauthor", "originalauthors"}:
                    authors.extend(_strings(value))
                    author_evidence.append(_evidence(relative, _pointer(pointer, key)))
                if norm in SOURCE_ID_KEYS and not (path.name == "extra.json" and pointer == ""):
                    for sid in _strings(value):
                        if sid != aid:
                            references[sid].append(_evidence(relative, _pointer(pointer, key)))
            role = "payload" if scanned or ("authored" in path.parts and any(_key(key) in {"sourceasset", "sourceassetlicenses"} for key in node)) else "reference"
            source = _source_from_node(node, relative, pointer, role=role)
            if source:
                if parent_payload and pointer and isinstance(node.get("file"), str) and source["urls"]:
                    # Map URLs are components of the explicitly credited scan;
                    # do not invent a new independent owner/license for each channel.
                    parent_payload["components"].append({
                        "role": "payload-component", "title": node.get("role", pointer.rsplit("/", 1)[-1]),
                        "urls": source["urls"], "file": node["file"],
                        "sha256": node.get("sha256"), "evidence": source["evidence"],
                        "credit_scope": "Component of the parent source asset; consult the parent source credits and recorded terms.",
                    })
                else:
                    sources.append(source)
                    if pointer == "" and source["role"] == "payload":
                        parent_payload = source
    unresolved = []
    source_refs = []
    origin = record.get("origin") or {}
    collection = origin.get("collection", "") if isinstance(origin, dict) else ""
    for sid, evidence in sorted(references.items()):
        candidates = registry.get(sid, [])
        scoped = [item for item in candidates if collection and any(collection in ev["path"] for ev in item["evidence"])]
        if scoped:
            candidates = scoped
        if not candidates:
            unresolved.append(sid)
        sources.extend(candidates)
        source_refs.append({"id": sid, "status": "resolved" if candidates else "unresolved", "evidence": evidence, "matches": [entry["evidence"] for entry in candidates]})
    if "authors" in explicit_authoring:
        authors = list(explicit_authoring["authors"])
    explicit_license = explicit_authoring.get("license_expression")
    terms = _unique(declared_licenses)
    license_value = explicit_license or (terms[0] if len(terms) == 1 else POLICY_LICENSE if not terms else None)
    authoring = {
        "license_expression": license_value, "recorded_license_terms": terms,
        "authors": _unique(authors), "evidence": author_evidence,
        "license_basis": "credits.json" if explicit_license else "recorded-authoring-license" if terms else "existing-original-contributions-policy",
        "policy_scope": POLICY_SCOPE, "policy_notice_paths": policy_files,
        "authors_status": "recorded" if authors else "not-individually-stated",
    }
    policy_sources = [p for p in ("archive/legacy/README.md", "archive/legacy/catalog/README.md") if (repo / p).is_file()]
    authoring["policy_source_paths"] = policy_sources
    if authoring["license_basis"] == "existing-original-contributions-policy":
        authoring["evidence"].extend(_evidence(p) for p in policy_sources)
    dependencies = []
    current_relations = []
    if "relations" in record or "runtime_dependencies" in record:
        current_relations = (record.get("relations") or []) + (record.get("runtime_dependencies") or [])
    else:
        current_relations = record.get("depends_on", record.get("dependencies", [])) or []
    for value in current_relations:
        dep_id = value.get("id") if isinstance(value, dict) else value
        if isinstance(dep_id, str) and dep_id != aid:
            dependencies.append(dep_id)
    return {
        "schema": SCHEMA, "asset_id": aid, "name": record.get("name", aid),
        "path": folder.relative_to(repo).as_posix(), "authoring": authoring,
        "sources": _merge_sources(sources), "source_references": source_refs,
        "unresolved_source_ids": unresolved, "dependencies": _unique(dependencies),
        "credit_relations": current_relations,
        "provenance_files": files, "display_authors": authoring["authors"],
    }


def _md(value: Any) -> str:
    return html.escape(str(value or ""), quote=False).replace("|", "\\|").replace("\n", " ").replace("\r", " ").replace("[", "\\[").replace("]", "\\]").replace("`", "\\`")


def _url(value: str) -> str:
    return quote(value, safe=":/?#[]@!$&'*+,;=%")


def _link(repo_path: str, from_path: str = "") -> str:
    target = os.path.relpath(repo_path, from_path or ".").replace(os.sep, "/")
    return quote(target, safe="/._-")


def _asset_markdown(doc: dict) -> str:
    authoring = doc["authoring"]
    lines = [f"# Attributions — {_md(doc['name'])}", "", f"Resource: `{doc['asset_id']}`.", "",
             "Generated from preserved source metadata and optional `credits.json`. Edit those inputs, then run `python tools/library/catalog.py build`; do not hand-edit this file.", "",
             "## Original contributions", "", POLICY_SCOPE, "",
             f"- Recorded original-contribution license: **{_md(authoring['license_expression']) or 'not established'}** ({authoring['license_basis']}).",
             f"- Individually recorded original authors: {_md(', '.join(authoring['authors'])) or 'not stated; no author inferred from maintainership or a source publication'}.", ""]
    if authoring["policy_notice_paths"]:
        lines.append("License texts: " + ", ".join(f"[{_md(Path(p).name)}]({_link(p, doc['path'])})" for p in authoring["policy_notice_paths"]) + ".")
        lines.append("")
    if authoring["policy_source_paths"]:
        lines.append("Original policy statements: " + ", ".join(f"[{_md(p)}]({_link(p, doc['path'])})" for p in authoring["policy_source_paths"]) + ".")
        lines.append("")
    lines += ["## Source credits and references", "", "`payload` describes an imported source asset; `reference` describes a cited publication or linked factual source. A source's terms do not automatically license the derived resource. Unstated terms remain unstated.", ""]
    if not doc["sources"]:
        lines += ["No external source credit was resolved from the available structured metadata. This is not a claim that all provenance has been independently audited.", ""]
    for source in doc["sources"]:
        lines += [f"### {_md(source['title'])}", "", f"- Role: `{source['role']}`."]
        if source.get("provider"):
            lines.append(f"- Published provider: {_md(source['provider'])}.")
        lines.append(f"- Published source authors: {_md(', '.join(source['authors'])) or 'not stated in preserved metadata'}.")
        lines.append(f"- Recorded source terms: {_md('; '.join(source['recorded_license_terms'])) or 'not stated; no redistribution permission inferred'}.")
        if source["redistributed_document"] is False:
            lines.append("- The cited source document is recorded as **not redistributed**.")
        for url in source["urls"]:
            lines.append(f"- Source: <{_url(url)}>.")
        if source.get("components"):
            lines.append(f"- Source components: {len(source['components'])} recorded map/file entries; their original URLs and hashes are retained in `attribution.json` under this source credit.")
        if source.get("notice"):
            lines.append(f"- Preserved notice: {_md(source['notice'])}")
        if source["via_assets"]:
            lines.append("- Linked through resource(s): " + ", ".join(f"`{aid}`" for aid in source["via_assets"]) + ".")
        links = []
        for ev in source["evidence"]:
            links.append(f"[{_md(ev['path'])}]({_link(ev['path'], doc['path'])}) (`{ev['pointer']}`)")
        lines.append("- Evidence: " + "; ".join(links) + ".")
        lines.append("")
    if doc["unresolved_source_ids"]:
        lines += ["## Unresolved source references", "", "These identifiers occur in preserved inputs but could not be matched to a preserved source registry. They need a factual source record; names, authors and permissions have not been guessed.", ""]
        lines.extend(f"- `{sid}`" for sid in doc["unresolved_source_ids"])
        lines.append("")
    if doc["dependencies"]:
        lines += ["## Linked resource credits", ""]
        for entry in doc.get("dependency_attributions", []):
            lines.append(f"- [`{entry['id']}`]({_link(entry['attribution_markdown'], doc['path'])}).")
        lines.append("")
    lines += ["The complete file hashes, source pointers and unresolved references are in [attribution.json](attribution.json).", ""]
    return "\n".join(lines)


def _json_text(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def build_attributions(repo: Path, records: list[dict], *, check: bool = False) -> dict:
    """Generate complete credits. In check mode report drift without writing.

    Records require id and repo-relative path; name, origin and depends_on are
    optional. attribution_source_paths can name additional preserved JSON files.
    """
    repo = Path(repo).resolve()
    ids = [str(record["id"]) for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate asset identity supplied to attribution generator")
    registry, registry_files = _registry(repo)
    policy_files = sorted(path.relative_to(repo).as_posix() for path in (repo / "LICENSES").glob("*") if path.is_file())
    docs = {str(record["id"]): _asset(repo, record, registry, policy_files) for record in records}
    # Resolve links from immutable direct-source snapshots, so ordering cannot affect output.
    direct = {aid: json.loads(json.dumps(doc["sources"])) for aid, doc in docs.items()}
    for aid, doc in sorted(docs.items()):
        inherited = []
        visited = {aid}
        pending = list(doc["dependencies"])
        while pending:
            dep = pending.pop()
            if dep in visited or dep not in docs:
                continue
            visited.add(dep)
            pending.extend(docs[dep]["dependencies"])
            for item in direct[dep]:
                source = json.loads(json.dumps(item))
                source["via_assets"] = _unique(source["via_assets"] + [dep])
                # Citing a material-reference dependency does not import its source document.
                source["role"] = "reference"
                inherited.append(source)
        doc["sources"] = _merge_sources(doc["sources"] + inherited)
        doc["dependency_attributions"] = [{"id": dep, "attribution_markdown": docs[dep]["path"] + "/ATTRIBUTIONS.md"} for dep in doc["dependencies"] if dep in docs]
        doc["unresolved_dependencies"] = [dep for dep in doc["dependencies"] if dep not in docs]
        terms = _unique([term for source in doc["sources"] if source["role"] == "payload" for term in source["recorded_license_terms"]])
        original = doc["authoring"]["license_expression"] or "not established"
        doc["display_license"] = "Original contributions: " + original + ("; imported sources: " + "; ".join(terms) if terms else "")
        unknown_payloads = sum(source["role"] == "payload" and not source["recorded_license_terms"] for source in doc["sources"])
        if unknown_payloads:
            doc["display_license"] += f"; imported sources with unstated terms: {unknown_payloads}"
        doc["attribution_json"] = doc["path"] + "/attribution.json"
        doc["attribution_markdown"] = doc["path"] + "/ATTRIBUTIONS.md"
    source_users: dict[str, list[str]] = defaultdict(list)
    all_sources: list[dict] = []
    for aid, doc in sorted(docs.items()):
        for source in doc["sources"]:
            source_users[_source_key(source)].append(aid)
            all_sources.append(source)
    global_sources = _merge_sources(all_sources)
    for source in global_sources:
        source["asset_ids"] = _unique(source_users[_source_key(source)])
    index = {
        "schema": SCHEMA, "asset_count": len(docs), "policy_scope": POLICY_SCOPE,
        "policy_license": POLICY_LICENSE, "license_notice_paths": policy_files,
        "license_notice_files": [{"path": p, "sha256": hashlib.sha256((repo / p).read_bytes()).hexdigest()} for p in policy_files],
        "source_registry_files": registry_files, "source_count": len(global_sources),
        "sources": global_sources, "assets": [docs[aid] for aid in sorted(docs)],
    }
    lines = ["# Attributions and provenance", "", "This is the generated credit index for SolidCraft Library. Per-resource credits retain the original sources, published authors, recorded licenses and exact evidence pointers.", "",
             "## License scope", "", POLICY_SCOPE, "", "The inherited original-authoring policy is **MIT OR Apache-2.0**. Publisher, maintainer and contributor are separate roles. A cited supplier document is not relicensed under that policy. Unknown terms are explicitly left unresolved.", "",
             "License texts: " + (", ".join(f"[{_md(Path(p).name)}]({p})" for p in policy_files) or "no root notice files found") + ".", "",
             "## Complete indexes", "", f"- **{len(docs):,} resources** with individual `ATTRIBUTIONS.md` and `attribution.json` files.", f"- **{len(global_sources):,} distinct source/role records**, including cited factual references and imported source assets.",
             "- [Complete machine-readable index](catalog/attributions.json), including every resource, source pointer and file hash.",
             "- [Browse the library](INDEX.md).", "",
             "## Published source credits", "", "Terms below are copied from source metadata; empty terms mean **not stated**, not public domain. Counts include resources linking to a physical/reference dependency. A resource may cite the same source in more than one role.", "",
             "| Source | Role | Published authors / provider | Recorded source terms | Resources |", "|---|---|---|---|---:|"]
    for source in global_sources:
        title = _md(source["title"])
        if source["urls"]:
            title = f"[{title}]({_url(source['urls'][0])})"
        credits = ", ".join(source["authors"]) or "Authors not stated"
        if source.get("provider"):
            credits += "; provider: " + source["provider"]
        lines.append(f"| {title} | {source['role']} | {_md(credits)} | {_md('; '.join(source['recorded_license_terms'])) or 'Not stated'} | {len(source['asset_ids'])} |")
    unresolved = [(aid, doc["unresolved_source_ids"]) for aid, doc in sorted(docs.items()) if doc["unresolved_source_ids"]]
    lines += ["", "## Metadata needing clarification", "", f"**{len(unresolved):,} resources** contain source identifiers not resolved by the preserved registries. Exact IDs and evidence remain in each resource's `attribution.json`; no missing author or permission has been invented.", "",
              "## Updating credits", "", "Edit `credits.json` or the preserved source metadata in the resource directory, then run `python tools/library/catalog.py build`. `python tools/library/catalog.py check` verifies generated output. Generated credit files must not be edited by hand. Full source publications are not automatically copied into the library.", ""]
    outputs = {"ATTRIBUTIONS.md": "\n".join(lines), "catalog/attributions.json": _json_text(index)}
    for doc in docs.values():
        outputs[doc["attribution_json"]] = _json_text(doc)
        outputs[doc["attribution_markdown"]] = _asset_markdown(doc)
    changed = []
    for relative, text in sorted(outputs.items()):
        path = _within(repo, repo / relative)
        data = text.encode("utf-8")
        if path.is_file() and path.read_bytes() == data:
            continue
        changed.append(relative)
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    summaries = {aid: {key: doc[key] for key in ("asset_id", "name", "path", "authoring", "sources", "unresolved_source_ids", "display_license", "display_authors", "attribution_json", "attribution_markdown")} for aid, doc in docs.items()}
    return {"asset_count": len(docs), "source_count": len(global_sources), "records": summaries, "changed_files": changed, "errors": ["Generated attribution files differ"] if check and changed else [], "unresolved_asset_count": len(unresolved)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    root = args.root.resolve()
    records = []
    for path in sorted((root / "assets").rglob("asset.json")):
        record = _read_json(path)
        record["path"] = path.parent.relative_to(root).as_posix()
        records.append(record)
    if not records:
        parser.error("No assets/**/asset.json descriptors found")
    result = build_attributions(root, records, check=args.command == "check")
    print(json.dumps({key: value for key, value in result.items() if key != "records"}, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
