# SolidCraft Library

Reusable resources for SolidCraft, organized around individual editable assets.
The current inventory contains **2,991 records**: appearances, physical material
references, scientific references, lights, environments and other rendering
resources. Each record has a stable identity, an editable source folder and its
own provenance. The count includes different kinds of resources, not just materials.

## Find a resource

- **[Complete index](INDEX.md)** — browse every asset by category on GitHub.
- **[Offline browser](index.html)** — after cloning or downloading the repository,
  open this file locally to search and filter the inventory without a server.
- **[Machine-readable catalog](catalog/index.json)** — generated IDs, paths,
  classification, representations and source metadata for tools.
- **[Curated collections](collections/README.md)** — views that bring related
  resources together without duplicating them.
- **[Attributions](ATTRIBUTIONS.md)** — credits, source records and license boundaries.

| Family | Contents |
| --- | --- |
| [Appearances](assets/appearances/) | Visual materials, surface looks and their maps |
| [Physical materials](assets/physical-materials/) | Source-backed physical properties with units and conditions |
| [Scientific references](assets/scientific-references/) | Chemical-element identities and associated reference data |
| [Rendering](assets/render/) | Lighting, environments, studios, presets and shots |
| [Finishes](assets/finishes/), [parts](assets/parts/) | Reserved for reusable treatments and components |
| [Drawings](assets/drawings/), [themes](assets/themes/) | Reserved for drawing resources and interface themes |
| [Animation](assets/animation/), [simulation](assets/simulation/), [examples](assets/examples/) | Reserved for future content with its own supported semantics |

Empty categories are marked as planned in their guides. They do not advertise
available assets or application features.

## Open and edit one asset

Find its stable ID in the index and follow the folder link. Start with
`asset.json` for classification and declared entry points, `definition.json` and
`recipes/` for the existing editable source, and `ATTRIBUTIONS.md` for credits and
source conditions. `extra.json` and `FILES.json` preserve the original metadata
and restoration receipts where present.

An appearance can refer to a physical material without assigning its properties.
A scanned reference identifies how source imagery was obtained; it does not by
itself establish measured optical or mechanical behavior. Check the selected
representation and its evidence before using it.

Git contains metadata, source records and the authored files that are actually
tracked. Some original binary resources are restored separately. See
[storage and restoration](docs/STORAGE.md) before expecting a fresh clone to
contain every texture, model or master file.

## Contribute

Use [CONTRIBUTING.md](CONTRIBUTING.md) to add or improve a resource. The
[structure guide](docs/STRUCTURE.md) explains categories, stable IDs, variants,
representations and relationships.

From the repository root, using Python 3.11 or newer:

```sh
python tools/library/catalog.py build
python tools/library/catalog.py check
python tools/library/validate.py
```

These commands build and check the catalog and its references. Native rendering,
visual acceptance and engineering data review remain specific to each asset and
representation; their evidence belongs with that resource.

## Current scope and history

This repository is an authoring library. Its descriptors and tooling describe the
repository; they do not establish a SolidCraft installer or plugin format.
Individual assets remain the editing unit. Curated collections select them
independently of this folder hierarchy. Future packs can define their own
installable membership without changing those identities.

Historical stage records, release manifests and restoration information are kept
in [archive/legacy](archive/legacy/). Existing release bytes remain available for
resources that have not been replaced by independently preserved equivalents.
Use the current index for navigation and the archive for original evidence.

The working repository remains
[`0xlillith/solidcraft-render-catalog`](https://github.com/0xlillith/solidcraft-render-catalog).
[`tangency-labs/solidcraft-library`](https://github.com/tangency-labs/solidcraft-library)
is the intended future home; this organization does not transfer the repository.
