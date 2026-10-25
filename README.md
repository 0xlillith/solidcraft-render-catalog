# SolidCraft Render resource catalog

Personal resource repository maintained by **0xlillith**. **Complete generated assets are stored in this repository's Releases; GitHub's automatic Source code ZIP is not the complete image/mesh library.** Source, numerical inputs, tests and readable inventory remain in Git.

## Published resource deliveries

| Delivery | Coverage | Complete assets | Source and status |
|---|---|---|---|
| Original catalog v1 | 1,386 original resource records | [catalog-v1-20261024](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/catalog-v1-20261024) | [Original guide](catalog/README.md) |
| Stage 01 — woods | 16 species references, 4 grain views, 6 finishes; 384 variants | [wood-stage01-20261025](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/wood-stage01-20261025) | [Wood guide](authoring/stage-01-woods/README.md) · [Status](authoring/stage-01-woods/STATUS.md) |
| Stage 02 — alloys | 24 grade/condition references, 23 distinct grades, 8 finishes; 192 variants | [alloys-stage02-20261025](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/alloys-stage02-20261025) | [Alloy guide](authoring/stage-02-alloys/README.md) · [Status](authoring/stage-02-alloys/STATUS.md) |

**[Global resource index: 2,002 records](authoring/RESOURCE-INDEX.json)**. This count includes appearances, physical references, lights, environments and other resource kinds; it does not mean 2,002 distinct engineering materials.

For each release, download all its resource ZIPs and extract them into the same empty parent directory. No concatenation is necessary. Open `index.html` inside the resulting collection directory. For stage 01/02 the catalog/previews archive is sufficient for browsing; add runtime/master map archives for complete editable material files. Check the attached manifests and `PUBLICATION-VERIFIED.json`.

Original v1 uses seven `catalog-v1-20261024-*.zip` files. Its small optional `Native-Appearance-Libraries.zip` contains only the uniform native appearance libraries, not all maps. Existing restoration helpers remain in `distribution/`.

## Appearance and physical data are distinct, linked records

All new wood/alloy variants link explicit physical substrate references. Source units, SI conversions, grade, condition, temperature and unresolved properties are retained. Visual finish edits do not silently rewrite density, strength or mechanical axes. Missing values are unknown, never zero. The source review excludes inconsistent fields rather than guessing corrections.

New stage 02 exports include 112 map PNGs at 2K/1K, 192 original procedural previews, 192 GLB and 192 editable glTF specimens. All 384 interchange specimens passed the official Khronos validator with zero errors/warnings; data/image regressions and full archive/member download verification also passed. These checks do not imply native SolidCraft or engineering certification.

## Qualification and future integration

**Native SolidCraft acceptance and premium visual qualification of the new wood/alloy stages remain pending.** Proposed native command files are not executed imports or certified materials. Procedural preview images are not native GPU evidence. Finite-patch maps are not claimed seamless. Read each stage's exact boundaries.

The legacy audit still records 345 appearance records with physical-reference candidates requiring selection and 303 without a specific physical reference. New stages do not automatically close those gaps. Further alloy groups, additive manufacturing, soils/masonry/pastes and the 118-element collection remain staged work.

**No plugin, autoinstaller, package compatibility standard or SolidCraft integration API is defined by this repository.** Those decisions remain pending community discussion. Internal resource indexes are not proposals to impose an upstream standard.

## Durable storage, provenance and preservation

[Working policy](authoring/WORKING-POLICY.md): this personal GitHub repository is the required durable destination for source and all generated assets. Local work and conversation attachments are not the final delivery. Publication requires download/hash verification. Earlier releases and original source histories are retained.

The original v1 README/receipt are historical records; their local-only/private wording describes the initial snapshot, not current repository visibility. No original binary was rewritten to update those historical statements.

New original authoring uses MIT OR Apache-2.0 with [the original license notices](catalog/licenses/). Primary factual references, third-party dependencies and their own notices retain their provenance; no blanket relicensing of supplier publications or physical datasets is implied. Complete copyrighted datasheets, commercial textures and font files are not included in the new stages.

Resource-delivery automation is limited to this personal repository. No upstream SolidCraft application code/CI, protection rule or installed application was changed by these publications.
