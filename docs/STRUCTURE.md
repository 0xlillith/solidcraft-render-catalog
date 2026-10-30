# Library structure

The library separates editable asset sources, generated navigation, shared
resources, authoring tools and historical evidence. A category describes where a
person can browse; an asset's identity survives changes to that category.

The design context is [the SolidCraft Library discussion in RFC #7558](https://github.com/tangency-labs/solidcraft/issues/7558).
This repository establishes an authoring convention. It does not finalize the
RFC, an installer format, or how the application applies each resource type.

## Repository areas

| Area | Purpose |
| --- | --- |
| `assets/` | Individual asset folders grouped by semantic family |
| `catalog/` | Generated inventory and discovery data |
| `INDEX.md` and category indexes | Complete human-readable navigation |
| `index.html` | Offline browser built from the same inventory |
| `schemas/` | Repository descriptor contracts and validation schemas |
| `resources/` | Explicitly referenced shared source resources |
| `packages/` | Reserved for future pack membership definitions |
| `collections/` | Editable curated selections and their generated browsing pages |
| `tools/` | Source maintenance, restoration and validation tools |
| `provenance/` | Repository-wide origin records and migration evidence |
| `docs/` | Current authoring and storage guidance |
| `LICENSES/` and `ATTRIBUTIONS.md` | Applicable notices and source-credit inventory |
| `archive/legacy/` | Historical catalogs, authoring stages and distribution records |

Current collection definitions select assets across categories without creating
packs or downloading payloads. Their `include` selectors match `category`, `type`,
`family` or `method`: fields within one selector must all match; the selectors are
alternatives. See [wood-studies.json](../collections/wood-studies.json). The builder
produces the collection pages and `catalog/collections.json`. Future pack
definitions can choose a different useful membership without changing the source
folders.

## Asset categories

| Path under `assets/` | Meaning |
| --- | --- |
| `appearances/<family>/<id>/` | Visual surface definitions and their representations |
| `physical-materials/<family>/<id>/` | Physical material records with stated conditions |
| `scientific-references/chemical-elements/<id>/` | Scientific identities and reference facts |
| `render/lighting/<id>/` | Light definitions and rigs |
| `render/environments/<id>/` | Environment resources with declared roles |
| `render/studios/<id>/` | Reusable surroundings for existing model geometry |
| `render/environment-setups/<id>/` | Declared combinations of environment settings |
| `render/scene-setups/<id>/` | Reusable scene arrangements with explicit scope |
| `render/presets/<id>/` | Declared camera, rendering or composition settings |
| `render/shots/<id>/` | Individual shot or presentation references |
| `finishes/`, `parts/`, `drawings/`, `themes/` | Reserved families with category guides |
| `animation/`, `simulation/`, `examples/` | Reserved future domains with category guides |

The category guides identify populated and planned subcategories. Empty folders
reserve editorial space; they do not declare support in the application.

Appearance records can retain method facets such as procedural or scanned.
These describe how the resource was authored, not a separate physical-material
identity. Keep units, material conditions and scientific identity in their own
records. A chemical-element name does not establish a bulk engineering material
or the appearance of every isotope, allotrope or phase.

## Inside an individual folder

`asset.json` is the editable repository descriptor; its contract is documented
in [schemas/asset.schema.json](../schemas/asset.schema.json). Existing entries
also retain editable `definition.json` and numerical `recipes/`, alongside the
preserved original `extra.json`, `FILES.json` and `provenance/` where supplied.
`credits.json` holds explicit attribution additions. Generated `attribution.json`
and `ATTRIBUTIONS.md` combine those additions with preserved sources and explain
credits and terms. See [the credit example](../CONTRIBUTING.md#record-credits)
for the editable fields. Authored revisions and acceptance evidence remain beside
the source they describe.

`FILES.json` records original archive members and hashes. It is a restoration
receipt, not a manifest of every later edit. Restored `files/` preserve original
relative layouts so model, buffer and image references stay together. New
representations carry their own receipts; see [storage](STORAGE.md). The current
catalog derives its representation list from `entrypoints`, `previews` and
`active_appearance` in the descriptor, including maps named by the active profile.
Edit those source references rather than the generated representation list.

## Identity, variants and representations

| Concept | Example | Consequence |
| --- | --- | --- |
| Asset | One reusable surface or physical record | Has a stable identity |
| Variant | A meaningful color, process or dimensional choice | Preserve the choice and its semantics |
| Representation | 2K/4K maps, a model export or a preview | State its role and fidelity explicitly |
| Resource | A particular image, mesh, font or source file | Track exact bytes and usage |
| Pack | Future independently installable selection | Membership is explicit and versioned |
| Collection | A curated choice of assets or future packs | Groups use cases without duplicating sources |

Resolution alone should not create a new physical material. Conversely, different
grades or conditions must not be merged because they have the same visual look.
A preview is evidence of a particular preview process, not an interchangeable
runtime or master representation.

IDs do not contain the current GitHub owner, release URL or folder location as
an implied identity rule. Catalog entries resolve IDs to paths. Keep historical
source IDs and explicit origin mappings when they differ from the stable ID;
use typed mappings for a split into several new records.

## Facets and relationships

Use controlled semantic types for validation, short editorial families for
navigation, and typed facets for meaningful filters such as process, method,
units or supported representation. Tags provide additional search terms. A tag
such as `steel`, `ISO` or `tested` does not establish density, conformity or
consumer acceptance.

Keep semantic relationships distinct from required dependencies. An appearance
may refer to a physical substrate, a scene may demonstrate a studio, and a
resource may derive from another without requiring all of them to be downloaded
together. Required dependencies describe the actual resources needed to use the
chosen representation. In the descriptor, `relations` records links such as
`physical_reference`, `element_reference`, `derived_from`, `related` or `example`.
`runtime_dependencies` is reserved for actual required resource IDs. The
preserved legacy `depends_on` field is not the current install-dependency model.

A studio supplies declared surroundings for a user's model. A preset supplies
settings. A complete example scene may contain demonstration geometry. Their
previews and relationships should make those boundaries visible.

## Generated views and historical records

The catalog builder produces navigation from the individual descriptors and
regenerates attribution outputs from their source records. Change the editable
source first, then run `python tools/library/catalog.py build`. Use `check` to
detect stale generated output. Keep manual classification changes in `asset.json`
and attribution additions in `credits.json`, not in generated indexes or notices.

Historical stages and release groups remain evidence and restoration inputs.
They are not the category system for new work. Keep their exact source and
publication receipts while directing readers to the current per-asset index.
