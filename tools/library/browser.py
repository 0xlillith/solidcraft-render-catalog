"""Render the library's portable, dependency-free resource browser.

The browser reads only its embedded snapshot. It does not fetch files, thumbnails,
scripts or metadata, and works from ``file://`` as well as static hosting.
Availability and evidence are independent, explicit labels; neither is inferred
from a file extension or the existence of a source record.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import quote, urlsplit


_CATEGORY_LABELS = {
    "physical-materials": "Physical materials",
    "appearances": "Appearances",
    "finishes": "Finishes",
    "scientific-references": "Scientific references",
    "parts": "Parts and assemblies",
    "render": "Rendering",
    "drawings": "Drawings",
    "themes": "Interface themes",
    "animation": "Animation",
    "simulation": "Simulation",
    "examples": "Examples",
}

_AVAILABILITY_LABELS = {
    "tracked": "Files tracked in Git",
    "available": "Available files",
    "in_git": "Files tracked in Git",
    "restore_required": "Historical files need restoration",
    "historical_restore_required": "Historical files need restoration",
    "metadata_only": "Metadata only",
    "mixed": "Tracked and restorable files",
    "unknown": "Availability not recorded",
}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Mapping):
        for key in ("label", "name", "title", "expression", "identifier", "id", "status"):
            if value.get(key) is not None:
                return _text(value[key])
        return ""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return "; ".join(filter(None, (_text(item) for item in value)))
    return str(value).strip()


def _items(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _strings(value: Any) -> list[str]:
    return list(dict.fromkeys(filter(None, (_text(item) for item in _items(value)))))


def _title(value: Any) -> str:
    text = _text(value)
    return text.replace("_", " ").replace("-", " ").capitalize() if text else "Not recorded"


def _relative_url(value: Any) -> str | None:
    """Allow repository-relative paths, preserving literal punctuation safely."""
    path = _text(value).replace("\\", "/")
    if not path or path.startswith("/") or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", path):
        return None
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts) or any(ord(c) < 32 for c in path):
        return None
    return "/".join(quote(part, safe="-._~") for part in parts)


def _source_url(value: Any) -> str | None:
    url = _text(value)
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        return None
    if parsed.username is not None or parsed.password is not None or any(ord(c) < 32 for c in url):
        return None
    return url


def _sources(value: Any) -> list[dict[str, str]]:
    if isinstance(value, Mapping) and not any(key in value for key in ("url", "source_url", "href")):
        values = list(value.values())
    else:
        values = _items(value)
    result = []
    seen = set()
    for item in values:
        if isinstance(item, Mapping):
            url = _source_url(item.get("url") or item.get("source_url") or item.get("href"))
            label = _text(item.get("title") or item.get("label") or item.get("name"))
            role = _text(item.get("role") or item.get("kind"))
        else:
            url, label, role = _source_url(item), "", ""
        if url and url not in seen:
            seen.add(url)
            result.append({"url": url, "label": label or url, "role": role})
    return result


def _relations(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        return list(dict.fromkeys(item for values in value.values() for item in _relations(values)))
    return _strings(value)


def _representations(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        values = []
        for key, item in value.items():
            if isinstance(item, Mapping):
                values.append({"label": key, **item})
            else:
                values.append({"label": key, "path": item})
    else:
        values = _items(value)
    result = []
    for item in values:
        if not isinstance(item, Mapping):
            item = {"path": item}
        available = item.get("available") is True or item.get("available_in_git") is True
        declared = _text(item.get("availability"))
        if declared in {"tracked", "in_git", "available"}:
            available = True
        path = _relative_url(item.get("path") or item.get("file"))
        if item.get("available") is False:
            available = False
        result.append({
            "label": _text(item.get("label") or item.get("name") or item.get("role") or item.get("id")) or "Representation",
            "path": path if available else None,
            "declared_path": _text(item.get("path") or item.get("file")),
            "format": _text(item.get("format")),
            "role": _text(item.get("role")),
            "available": available,
            "availability": _AVAILABILITY_LABELS.get(declared, _title(declared)) if declared else ("Available file" if available else "Availability not recorded"),
            "note": _text(item.get("note") or item.get("limitations") or item.get("description")),
            "capabilities": _strings(item.get("capabilities") or item.get("requires")),
        })
    return result


def _evidence(record: Mapping[str, Any]) -> tuple[str, str]:
    explicit = _text(record.get("validation"))
    quality = record.get("quality")
    label = _text(record.get("quality_label"))
    note = ""
    if isinstance(quality, Mapping):
        note = _text(quality.get("scope") or quality.get("note") or quality.get("limitations"))
        label = label or _text(quality.get("label"))
        if not explicit:
            for key in ("status", "native_acceptance", "native_render_validation", "validation"):
                if quality.get(key) is not None:
                    explicit = _text(quality[key])
                    break
    elif quality:
        explicit = explicit or _text(quality)
    if not explicit:
        explicit = _text(record.get("status"))
    return label or explicit or "Not recorded", note


def _record(record: Mapping[str, Any]) -> dict[str, Any]:
    path = _text(record.get("path") or record.get("folder"))
    origin = record.get("origin") if isinstance(record.get("origin"), Mapping) else {}
    parts = path.split("/")
    category = _text(record.get("category")) or (parts[1] if len(parts) > 1 and parts[0] == "assets" else "unclassified")
    attribution = record.get("attribution") if isinstance(record.get("attribution"), Mapping) else {}
    license_text = _text(record.get("license") or record.get("licenses") or attribution.get("license") or attribution.get("licenses")) or "See attribution record"
    authors = _strings(record.get("authors") or attribution.get("authors"))
    evidence, evidence_note = _evidence(record)
    availability = _text(record.get("availability")) or "unknown"
    preview = record.get("preview")
    if isinstance(preview, Mapping):
        preview_url = _relative_url(preview.get("path")) if preview.get("available") is True else None
    else:
        preview_url = _relative_url(preview)
    sources = _sources(record.get("sources") or attribution.get("sources"))
    record_type = _text(record.get("type") or record.get("kind")) or "unclassified"
    family = _text(record.get("family")) or "Unclassified"
    method = _text(record.get("method")) or "Not recorded"
    dependencies = _relations(record.get("dependencies") or record.get("depends_on"))
    related = _relations(record.get("related") or record.get("relations"))
    result = {
        "id": _text(record.get("id")),
        "name": _text(record.get("name")) or _text(record.get("id")),
        "type": record_type,
        "type_label": _text(record.get("type_label")) or _title(record_type),
        "category": category,
        "category_label": _CATEGORY_LABELS.get(category, _title(category)),
        "family": family,
        "method": method,
        "description": _text(record.get("description")),
        "tags": _strings(record.get("tags")),
        "license": license_text,
        "authors": authors,
        "sources": sources,
        "origin_collection": _text(record.get("origin_collection") or origin.get("collection")),
        "legacy_kind": _text(record.get("legacy_kind")),
        "availability": availability,
        "availability_label": _AVAILABILITY_LABELS.get(availability, _title(availability)),
        "validation": evidence,
        "quality_note": evidence_note,
        "representations": _representations(record.get("representations")),
        "dependencies": dependencies,
        "related": related,
        "preview": preview_url,
        "links": {
            "readme": _relative_url(path + "/README.md") if path else None,
            "descriptor": _relative_url(path + "/asset.json") if path else None,
            "attribution": _relative_url(path + "/ATTRIBUTIONS.md") if path else None,
        },
    }
    result["search"] = " ".join(filter(None, [
        result["id"], result["name"], record_type, category, result["category_label"], family,
        method, result["description"], license_text, " ".join(authors), " ".join(result["tags"]),
        result["origin_collection"], result["legacy_kind"], evidence,
        " ".join(source["label"] + " " + source["url"] for source in sources),
        " ".join(dependencies + related),
    ]))
    return result


def _categories(records: list[dict[str, Any]], summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    counts = Counter(record["category"] for record in records)
    declared = summary.get("categories")
    if isinstance(declared, Mapping):
        entries = [{"id": key, **value} if isinstance(value, Mapping) else {"id": key, "count": value} for key, value in declared.items()]
    else:
        entries = _items(declared)
    result = {}
    for item in entries:
        if not isinstance(item, Mapping):
            item = {"id": item}
        identity = _text(item.get("id") or item.get("category"))
        if not identity:
            continue
        path = _text(item.get("path")) or "assets/" + identity
        result[identity] = {
            "id": identity,
            "label": _text(item.get("label") or item.get("name")) or _CATEGORY_LABELS.get(identity, _title(identity)),
            "count": counts[identity],
            "planned": counts[identity] == 0,
            "url": _relative_url(path + "/README.md"),
        }
    for identity, count in counts.items():
        if identity not in result:
            result[identity] = {"id": identity, "label": _CATEGORY_LABELS.get(identity, _title(identity)), "count": count, "planned": False, "url": None}
    return sorted(result.values(), key=lambda category: (category["planned"], category["label"].casefold()))


def _json_script(value: Any) -> str:
    """JSON inside a script element must not be able to end that element."""
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            .replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def render_browser(records: Sequence[Mapping[str, Any]], summary: Mapping[str, Any] | None = None) -> str:
    """Return one deterministic HTML document for the repository-root index."""
    summary = summary or {}
    normalized = sorted((_record(record) for record in records), key=lambda record: (record["name"].casefold(), record["id"]))
    payload = {
        "records": normalized,
        "categories": _categories(normalized, summary),
        "summary": {
            "source_revision": _text(summary.get("source_revision") or summary.get("revision")),
            "updated": _text(summary.get("updated")),
        },
    }
    return _HTML.replace("__CATALOG_DATA__", _json_script(payload))


_HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="description" content="Browse SolidCraft Library resources, representations, sources and attributions. This catalog works offline.">
<title>SolidCraft Library — resource catalog</title>
<style>
:root{--bg:#f5f6f8;--paper:#fff;--ink:#172334;--muted:#5d6a7a;--line:#dbe1e8;--accent:#14695d;--accent-soft:#eaf5f1;--warm:#865412;--warm-bg:#fff5df;--focus:#096fb5;--shadow:0 2px 10px #15253608;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:15px;line-height:1.5;color:var(--ink);background:var(--bg)}
*{box-sizing:border-box}body{margin:0}a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:3px}a:hover{text-decoration-thickness:2px}button,input,select{font:inherit}button,select{cursor:pointer}button{border:1px solid var(--line);border-radius:6px;background:var(--paper);color:var(--ink);padding:.55rem .8rem}button:hover{border-color:var(--accent)}button:disabled{cursor:default;opacity:.45}button:disabled:hover{border-color:var(--line)}:focus-visible{outline:3px solid var(--focus);outline-offset:3px}h1,h2,h3,p{margin-top:0}h1{font-size:clamp(2rem,4vw,3rem);line-height:1.12;letter-spacing:-.045em;margin-bottom:.65rem}h2{font-size:1.15rem;letter-spacing:-.02em}h3{font-size:1.03rem;line-height:1.35;margin-bottom:.2rem}code{font: .82rem ui-monospace,SFMono-Regular,Consolas,monospace;overflow-wrap:anywhere}small,.small{font-size:.84rem}.muted{color:var(--muted)}.skip{position:absolute;left:1rem;top:-5rem;background:var(--paper);padding:.7rem;z-index:4}.skip:focus{top:1rem}.wrap{width:min(1440px,calc(100% - 48px));margin:auto}.masthead{border-bottom:1px solid var(--line);background:var(--paper)}.brand{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:1.05rem 0;border-bottom:1px solid var(--line)}.wordmark{font-weight:700;letter-spacing:.05em;font-size:.83rem;text-transform:uppercase}.mark{display:inline-block;width:12px;height:12px;border:3px solid var(--accent);transform:rotate(45deg);margin-right:.7rem}.nav{display:flex;flex-wrap:wrap;gap:.55rem 1.25rem;font-size:.88rem}.hero{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2rem;align-items:end;padding:2.5rem 0 2rem}.eyebrow{font-size:.73rem;letter-spacing:.13em;text-transform:uppercase;color:var(--accent);font-weight:700;margin:0 0 .65rem}.intro{max-width:750px;color:var(--muted);margin-bottom:0}.offline{font-size:.8rem;color:var(--accent);border:1px solid var(--line);border-radius:20px;padding:.4rem .75rem;white-space:nowrap}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1.25rem;padding:0 0 1.6rem}.stat strong{display:block;font-size:1.45rem;font-weight:650;letter-spacing:-.03em}.stat span{font-size:.82rem;color:var(--muted)}main{padding:1.5rem 0 3rem}.controls{background:var(--paper);border:1px solid var(--line);border-radius:9px;padding:1.2rem;box-shadow:var(--shadow)}.search-row{display:flex;gap:.75rem;align-items:end}.search-field{flex:1}.search-field label,.filter label{display:block;font-size:.78rem;font-weight:650;margin-bottom:.35rem}.search-field input{width:100%;padding:.72rem .85rem;background:var(--bg);border:1px solid var(--line);border-radius:6px;color:var(--ink)}.filters{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:.75rem;margin-top:1rem}.filter select{width:100%;padding:.55rem .45rem;border:1px solid var(--line);border-radius:5px;background:var(--paper);color:var(--ink);min-width:0}.hint{font-size:.79rem;color:var(--muted);margin:.8rem 0 0}.results-bar{display:flex;gap:1rem;align-items:center;justify-content:space-between;padding:1.1rem .1rem}.results-count{font-weight:650;margin:0}.results-settings{display:flex;flex-wrap:wrap;gap:1rem;align-items:center;font-size:.82rem}.results-settings label{margin-right:.3rem}.results-settings select{background:var(--paper);border:1px solid var(--line);border-radius:4px;padding:.35rem;color:var(--ink)}.asset-list{list-style:none;margin:0;padding:0;display:grid;gap:.65rem}.asset{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:1rem 1.2rem;box-shadow:var(--shadow)}.asset-top{display:grid;grid-template-columns:minmax(0,1fr) minmax(240px,.46fr);gap:1.3rem}.asset-heading{display:flex;gap:1rem}.preview{width:76px;height:76px;object-fit:contain;flex:none;border-radius:5px;border:1px solid var(--line);background:var(--bg)}.asset h3 a{color:var(--ink);text-decoration:none}.asset h3 a:hover{text-decoration:underline;text-decoration-color:var(--accent)}.facets{display:flex;gap:.3rem .65rem;flex-wrap:wrap;font-size:.8rem;color:var(--muted);margin:.45rem 0}.facet:first-child{color:var(--accent);font-weight:650}.description{font-size:.86rem;margin:.4rem 0 0;color:var(--muted);max-width:100ch}.asset-meta{border-left:1px solid var(--line);padding-left:1rem;font-size:.8rem}.status{display:inline-block;padding:.18rem .45rem;border-radius:4px;background:var(--bg);font-size:.75rem;font-weight:600;max-width:100%;overflow-wrap:anywhere}.status[data-state="tracked"],.status[data-state="available"],.status[data-state="in_git"]{background:var(--accent-soft);color:var(--accent)}.status[data-state="restore_required"],.status[data-state="historical_restore_required"],.status[data-state="mixed"]{background:var(--warm-bg);color:var(--warm)}.meta-line{margin-top:.4rem;overflow-wrap:anywhere}.meta-label{color:var(--muted)}.asset details{border-top:1px solid var(--line);margin-top:.8rem;padding-top:.55rem;font-size:.83rem}.asset summary{cursor:pointer;color:var(--accent);font-weight:550;width:fit-content}.details-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.3rem;padding-top:.8rem}.details-grid h4{font-size:.79rem;margin:0 0 .4rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}.detail-list{margin:.2rem 0;padding-left:1.1rem}.detail-list li{margin-bottom:.4rem;overflow-wrap:anywhere}.asset-links{display:flex;flex-wrap:wrap;gap:.4rem 1.1rem;padding-top:.8rem}.reference-button{font: .78rem ui-monospace,SFMono-Regular,Consolas,monospace;border:0;padding:.1rem .2rem;color:var(--accent);background:var(--accent-soft);border-radius:3px;margin:.1rem .3rem .1rem 0;text-align:left;overflow-wrap:anywhere}.file-note{display:block;color:var(--muted);font-size:.78rem}.empty{background:var(--paper);border:1px dashed var(--line);border-radius:8px;text-align:center;padding:3rem 1.5rem}.empty p{max-width:60ch;margin:.5rem auto 0;color:var(--muted)}.pagination{display:flex;justify-content:space-between;align-items:center;gap:1rem;margin:1rem 0}.page-buttons{display:flex;gap:.45rem}.page-label{font-size:.85rem;color:var(--muted)}.planned{border-top:1px solid var(--line);margin-top:2rem;padding-top:1.25rem}.planned p{font-size:.87rem;color:var(--muted)}.category-links{display:flex;flex-wrap:wrap;gap:.5rem}.category-link{display:block;border:1px solid var(--line);background:var(--paper);padding:.45rem .7rem;border-radius:5px;font-size:.82rem;text-decoration:none}.category-link span{color:var(--muted);margin-left:.5rem;font-size:.73rem}.footer{border-top:1px solid var(--line);padding:1.2rem 0 2rem;font-size:.8rem;color:var(--muted)}.footer p{margin-bottom:.4rem}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}.noscript{padding:1rem;background:var(--warm-bg);color:var(--ink);border-radius:6px;margin:1rem 0}.error{background:var(--warm-bg);padding:1rem;border-radius:6px}.hidden,[hidden]{display:none!important}
@media(max-width:1050px){.filters{grid-template-columns:repeat(3,minmax(0,1fr))}.asset-top{grid-template-columns:minmax(0,1fr) minmax(210px,.45fr)}}
@media(max-width:700px){.wrap{width:calc(100% - 28px)}.hero{display:block;padding:1.7rem 0}.offline{display:inline-block;margin-top:1rem}.brand{align-items:start;flex-direction:column}.stats{grid-template-columns:repeat(2,minmax(0,1fr));gap:.9rem}.filters{grid-template-columns:repeat(2,minmax(0,1fr))}.search-row{align-items:stretch;flex-direction:column}.search-row button{align-self:flex-start}.asset-top{grid-template-columns:1fr;gap:.65rem}.asset-meta{border-left:0;border-top:1px solid var(--line);padding:.65rem 0 0}.details-grid{grid-template-columns:1fr}.results-bar{align-items:flex-start;flex-direction:column;gap:.55rem}.asset{padding:.9rem}.preview{width:58px;height:58px}.pagination{align-items:flex-start;flex-direction:column}.controls{padding:.9rem}.page-buttons{flex-wrap:wrap}}
@media(prefers-color-scheme:dark){:root{--bg:#12191f;--paper:#1b242c;--ink:#e3e9ee;--muted:#a4b0bd;--line:#34424e;--accent:#77ccba;--accent-soft:#213e39;--warm:#e8c477;--warm-bg:#3b3221;--focus:#79bafa;--shadow:none}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style>
</head>
<body>
<a class="skip" href="#results">Skip to resources</a>
<header class="masthead"><div class="wrap">
<div class="brand"><div class="wordmark"><span class="mark" aria-hidden="true"></span>SolidCraft Library</div><nav class="nav" aria-label="Library documents"><a href="README.md">Readme</a><a href="INDEX.md">Complete index</a><a href="ATTRIBUTIONS.md">Attributions</a><a href="CONTRIBUTING.md">Contribute</a></nav></div>
<div class="hero"><div><p class="eyebrow">Resource catalog</p><h1>Find the right starting point.</h1><p class="intro">Explore individual resources, their sources and available representations. Open a resource's notes or attribution record before using or editing it.</p></div><span class="offline">Works offline · no external services</span></div>
<div class="stats" aria-label="Catalog overview"><div class="stat"><strong id="stat-resources">—</strong><span>individual resources</span></div><div class="stat"><strong id="stat-types">—</strong><span>content types</span></div><div class="stat"><strong id="stat-sources">—</strong><span>source collections</span></div><div class="stat"><strong id="stat-planned">—</strong><span>categories prepared for later</span></div></div>
</div></header>
<main class="wrap">
<noscript><div class="noscript">This interactive browser needs JavaScript. The <a href="INDEX.md">complete Markdown index</a>, <a href="catalog/index.json">machine-readable catalog</a> and individual resource files remain available without it.</div></noscript>
<form id="filters-form" class="controls" role="search" aria-label="Search the resource catalog">
<div class="search-row"><div class="search-field"><label for="search">Search resources, IDs, authors or source references</label><input id="search" type="search" placeholder="For example: white oak, MAT-001, title block…" autocomplete="off" spellcheck="false" aria-describedby="search-hint"></div><button id="clear" type="button">Clear filters</button></div>
<div class="filters">
<div class="filter"><label for="category">Category</label><select id="category"><option value="">All categories</option></select></div>
<div class="filter"><label for="family">Family</label><select id="family"><option value="">All families</option></select></div>
<div class="filter"><label for="method">Production method</label><select id="method"><option value="">All methods</option></select></div>
<div class="filter"><label for="license">License / notice</label><select id="license"><option value="">All notices</option></select></div>
<div class="filter"><label for="availability">File availability</label><select id="availability"><option value="">All availability states</option></select></div>
<div class="filter"><label for="validation">Recorded evidence</label><select id="validation"><option value="">All evidence states</option></select></div>
</div><p id="search-hint" class="hint">All search words must match; use quotes for a phrase. Availability, provenance and validation are separate. A preview or a file-format check does not establish engineering or optical qualification.</p>
</form>
<section id="results" aria-labelledby="results-heading" tabindex="-1">
<div class="results-bar"><h2 id="results-heading" class="results-count" aria-live="polite" aria-atomic="true">Loading resources…</h2><div class="results-settings"><div><label for="sort">Sort</label><select id="sort"><option value="name">Name</option><option value="id">Resource ID</option><option value="type">Content type</option><option value="origin">Source collection</option></select></div><div><label for="page-size">Per page</label><select id="page-size"><option value="25">25</option><option value="50">50</option><option value="100">100</option></select></div></div></div>
<ol id="resource-list" class="asset-list"></ol>
<div id="empty" class="empty" hidden><h3>No matching resources</h3><p id="empty-text">Try a broader search or clear a filter. Prepared categories may not contain resources yet.</p><p id="empty-category"></p></div>
<nav class="pagination" aria-label="Results pages"><span id="page-label" class="page-label" aria-live="polite"></span><div class="page-buttons"><button type="button" id="first-page" aria-label="First page">First</button><button type="button" id="previous-page">Previous</button><button type="button" id="next-page">Next</button><button type="button" id="last-page" aria-label="Last page">Last</button></div></nav>
</section>
<section id="planned" class="planned" aria-labelledby="planned-heading" hidden><h2 id="planned-heading">Prepared for future content</h2><p>These categories have a home in the repository. They do not yet contain cataloged resources.</p><div id="category-links" class="category-links"></div></section>
</main>
<footer class="footer"><div class="wrap"><p>Attribution belongs with every resource. See the <a href="ATTRIBUTIONS.md">attribution directory</a> for authors, providers, source documents and license notices.</p><p>Historical source files may need restoration; tracked derivatives and their limits are identified separately. <a href="docs/STORAGE.md">Storage and restoration</a> · <a href="docs/STRUCTURE.md">Library structure</a></p><p id="snapshot-note"></p></div></footer>
<script type="application/json" id="catalog-data">__CATALOG_DATA__</script>
<script id="catalog-core">
"use strict";
const CatalogCore = (() => {
  const fold = value => String(value || "").normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("en");
  const terms = query => Array.from(fold(query).matchAll(/"([^"]+)"|(\S+)/g), match => match[1] || match[2]);
  const keys = ["category", "family", "method", "license", "availability", "validation"];
  function filter(records, state) {
    const words = terms(state.search);
    return records.filter(record => keys.every(key => !state[key] || record[key] === state[key]) && words.every(word => (record.search_folded || fold(record.search)).includes(word)));
  }
  function sort(records, order) {
    const key = {name:"name",id:"id",type:"type",origin:"origin_collection"}[order] || "name";
    return records.slice().sort((a,b) => a[key].localeCompare(b[key], "en", {numeric:true,sensitivity:"base"}) || a.name.localeCompare(b.name, "en", {numeric:true,sensitivity:"base"}) || a.id.localeCompare(b.id, "en", {numeric:true}));
  }
  function paginate(records, page, pageSize) {
    const pages = Math.max(1, Math.ceil(records.length / pageSize));
    const current = Math.max(1, Math.min(pages, page));
    return {items:records.slice((current-1)*pageSize,current*pageSize),page:current,pages,total:records.length,start:records.length ? (current-1)*pageSize+1 : 0,end:Math.min(current*pageSize,records.length)};
  }
  return {fold,terms,filter,sort,paginate,keys};
})();
</script>
<script>
"use strict";
(() => {
  const byId = id => document.getElementById(id);
  const el = (tag, className, value) => { const node=document.createElement(tag); if(className) node.className=className; if(value !== undefined && value !== null) node.textContent=String(value); return node; };
  const link = (label, href, external=false) => { const node=el("a", "", label); node.href=href; if(external){node.target="_blank";node.rel="noopener noreferrer";} return node; };
  const count = number => number.toLocaleString("en-US");
  let data;
  try { data=JSON.parse(byId("catalog-data").textContent); } catch(error) { byId("results-heading").textContent="The catalog snapshot could not be read."; byId("resource-list").append(el("li","error","Open INDEX.md or catalog/index.json to browse the repository directly.")); return; }
  const records=data.records;
  records.forEach(record => {record.search_folded=CatalogCore.fold(record.search);});
  const lookup=new Map(records.map(record=>[record.id,record]));
  const categories=new Map(data.categories.map(category=>[category.id,category]));
  let currentPage=1, filtered=records;
  byId("stat-resources").textContent=count(records.length);
  byId("stat-types").textContent=count(new Set(records.map(record=>record.type)).size);
  byId("stat-sources").textContent=count(new Set(records.map(record=>record.origin_collection).filter(Boolean)).size);
  const planned=data.categories.filter(category=>category.planned);
  byId("stat-planned").textContent=count(planned.length);
  const snapshots=[];
  if(data.summary.updated) snapshots.push("Catalog snapshot: "+data.summary.updated);
  if(data.summary.source_revision) snapshots.push("Source revision: "+data.summary.source_revision);
  byId("snapshot-note").textContent=snapshots.join(" · ");
  if(planned.length){byId("planned").hidden=false;planned.forEach(category=>{const node=category.url?link(category.label,category.url):el("span","",category.label);node.className="category-link";node.append(el("span","","Prepared"));byId("category-links").append(node);});}

  const optionLabel=(key,value,record)=> key==="category" ? (categories.get(value)?.label || record.category_label) : key==="availability" ? record.availability_label : value;
  CatalogCore.keys.forEach(key=>{
    const values=new Map();
    records.forEach(record=>{const value=record[key];if(!values.has(value)) values.set(value,{label:optionLabel(key,value,record),count:0});values.get(value).count++;});
    if(key==="category") data.categories.forEach(category=>{if(!values.has(category.id))values.set(category.id,{label:category.label,count:0});});
    Array.from(values.entries()).sort((a,b)=>a[1].label.localeCompare(b[1].label,"en",{numeric:true,sensitivity:"base"})).forEach(([value,detail])=>{const option=el("option","",detail.label+" ("+count(detail.count)+")");option.value=value;byId(key).append(option);});
  });

  function readState(){const state={search:byId("search").value};CatalogCore.keys.forEach(key=>state[key]=byId(key).value);return state;}
  function applyHash(){const params=new URLSearchParams(location.hash.replace(/^#/,""));byId("search").value=params.get("q")||"";CatalogCore.keys.forEach(key=>{const value=params.get(key);if(value && Array.from(byId(key).options).some(option=>option.value===value))byId(key).value=value;});}
  function storeHash(){const state=readState(),params=new URLSearchParams();if(state.search)params.set("q",state.search);CatalogCore.keys.forEach(key=>{if(state[key])params.set(key,state[key]);});try{history.replaceState(null,"",location.pathname+location.search+(params.size?"#"+params.toString():""));}catch(error){/* file:// implementations may disallow replaceState; browsing still works. */}}

  function referenceList(ids){
    const container=el("div");
    ids.forEach(id=>{const known=lookup.get(id);if(known){const button=el("button","reference-button",id);button.type="button";button.title=known.name;button.addEventListener("click",()=>{reset(false);byId("search").value='"'+id+'"';refresh();byId("results").focus();});container.append(button);}else{container.append(el("code","",id+" "));}});
    return container;
  }

  function details(record){
    const disclosure=el("details");disclosure.append(el("summary","","Files, sources and evidence"));
    const grid=el("div","details-grid"),files=el("section"),provenance=el("section");
    files.append(el("h4","","Representations"));
    if(!record.representations.length){files.append(el("p","muted","No representation inventory is recorded here. Check the resource notes and descriptor."));}
    else{const list=el("ul","detail-list");record.representations.forEach(rep=>{const item=el("li");if(rep.available && rep.path)item.append(link(rep.label,rep.path));else item.append(el("span","",rep.label));if(rep.format)item.append(document.createTextNode(" · "+rep.format));item.append(el("span","file-note",rep.availability));if(rep.note)item.append(el("span","file-note",rep.note));if(rep.capabilities.length)item.append(el("span","file-note","Requires: "+rep.capabilities.join(", ")));list.append(item);});files.append(list);}
    if(record.dependencies.length){files.append(el("h4","","Declared dependencies"),referenceList(record.dependencies));}
    if(record.related.length){files.append(el("h4","","Related resources"),referenceList(record.related));}
    provenance.append(el("h4","","Attribution and sources"));
    if(record.authors.length)provenance.append(el("p","","Authors / contributors: "+record.authors.join("; ")));
    provenance.append(el("p","","License / notice: "+record.license));
    if(record.sources.length){const list=el("ul","detail-list");record.sources.forEach(source=>{const item=el("li");item.append(link(source.label,source.url,true));if(source.role)item.append(el("span","file-note",source.role));list.append(item);});provenance.append(list);}else{provenance.append(el("p","muted","See the individual attribution record for the complete source notices."));}
    if(record.origin_collection)provenance.append(el("p","muted","Historical origin: "+record.origin_collection));
    provenance.append(el("h4","","Recorded evidence"),el("p","",record.validation));
    if(record.quality_note)provenance.append(el("p","muted",record.quality_note));
    grid.append(files,provenance);disclosure.append(grid);
    const nav=el("nav","asset-links");nav.setAttribute("aria-label","Files for "+record.name);
    if(record.links.readme)nav.append(link("Resource notes",record.links.readme));
    if(record.links.attribution)nav.append(link("Full attributions",record.links.attribution));
    if(record.links.descriptor)nav.append(link("Asset descriptor",record.links.descriptor));
    disclosure.append(nav);return disclosure;
  }

  function resource(record){
    const item=el("li"),article=el("article","asset"),top=el("div","asset-top"),heading=el("div","asset-heading"),main=el("div");
    if(record.preview){const preview=el("img","preview");preview.src=record.preview;preview.alt="Preview of "+record.name;preview.loading="lazy";preview.width=76;preview.height=76;preview.addEventListener("error",()=>preview.remove(),{once:true});heading.append(preview);}
    const title=el("h3");title.append(record.links.readme?link(record.name,record.links.readme):document.createTextNode(record.name));main.append(title,el("code","muted",record.id));
    const facets=el("div","facets");[record.type_label,record.family,record.method].filter(Boolean).forEach(value=>facets.append(el("span","facet",value)));main.append(facets);
    if(record.description)main.append(el("p","description",record.description.length>320?record.description.slice(0,317)+"…":record.description));
    heading.append(main);
    const meta=el("div","asset-meta"),status=el("span","status",record.availability_label);status.dataset.state=record.availability;meta.append(status);
    const evidence=el("div","meta-line");evidence.append(el("span","meta-label","Evidence: "),document.createTextNode(record.validation));meta.append(evidence);
    const license=el("div","meta-line");license.append(el("span","meta-label","Notice: "));if(record.links.attribution)license.append(link(record.license,record.links.attribution));else license.append(document.createTextNode(record.license));meta.append(license);
    if(record.authors.length)meta.append(el("div","meta-line muted",record.authors.join("; ")));
    top.append(heading,meta);article.append(top,details(record));item.append(article);return item;
  }

  function draw(focusResults=false){
    const page=CatalogCore.paginate(filtered,currentPage,Number(byId("page-size").value));currentPage=page.page;
    const fragment=document.createDocumentFragment();page.items.forEach(record=>fragment.append(resource(record)));byId("resource-list").replaceChildren(fragment);
    byId("results-heading").textContent=count(page.total)+" of "+count(records.length)+" resources";
    byId("empty").hidden=page.total>0;
    const category=categories.get(byId("category").value);byId("empty-category").replaceChildren();
    if(!page.total && category?.planned){byId("empty-text").textContent=category.label+" is prepared for future content. It has no cataloged resources yet.";if(category.url)byId("empty-category").append(link("Read the category notes",category.url));}
    else byId("empty-text").textContent="Try a broader search or clear a filter. All search words must match.";
    byId("page-label").textContent=page.total?"Showing "+count(page.start)+"–"+count(page.end)+" · Page "+count(page.page)+" of "+count(page.pages):"No results";
    ["first-page","previous-page"].forEach(id=>byId(id).disabled=page.page<=1);
    ["next-page","last-page"].forEach(id=>byId(id).disabled=page.page>=page.pages);
    if(focusResults)byId("results").focus({preventScroll:false});
  }
  function refresh(){currentPage=1;filtered=CatalogCore.sort(CatalogCore.filter(records,readState()),byId("sort").value);draw();storeHash();}
  function reset(refreshResults=true){byId("search").value="";CatalogCore.keys.forEach(key=>byId(key).value="");if(refreshResults)refresh();}
  let debounce;
  byId("search").addEventListener("input",()=>{clearTimeout(debounce);debounce=setTimeout(refresh,100);});
  CatalogCore.keys.forEach(key=>byId(key).addEventListener("change",refresh));
  byId("sort").addEventListener("change",refresh);byId("page-size").addEventListener("change",refresh);
  byId("clear").addEventListener("click",()=>{reset();byId("search").focus();});
  byId("filters-form").addEventListener("submit",event=>{event.preventDefault();clearTimeout(debounce);refresh();});
  byId("first-page").addEventListener("click",()=>{currentPage=1;draw(true);});
  byId("previous-page").addEventListener("click",()=>{currentPage--;draw(true);});
  byId("next-page").addEventListener("click",()=>{currentPage++;draw(true);});
  byId("last-page").addEventListener("click",()=>{currentPage=Math.max(1,Math.ceil(filtered.length/Number(byId("page-size").value)));draw(true);});
  window.addEventListener("hashchange",()=>{reset(false);applyHash();refresh();});
  applyHash();refresh();
})();
</script>
</body>
</html>
'''
