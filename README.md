# SolidCraft Render resource catalog

Personal resource repository maintained by **0xlillith**. **Complete generated assets are stored in this repository's Releases; GitHub's automatic Source code ZIP is not the complete image/mesh library.** Source, numerical inputs, tests and readable inventory remain in Git.

## Published resource deliveries

| Delivery | Coverage | Complete assets | Source and status |
|---|---|---|---|
| Original catalog v1 | 1,386 original resource records | [catalog-v1-20261024](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/catalog-v1-20261024) | [Original guide](catalog/README.md) |
| Stage 01 — woods | 16 species references, 4 grain views, 6 finishes; 384 variants | [wood-stage01-20261025](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/wood-stage01-20261025) | [Wood guide](authoring/stage-01-woods/README.md) · [Status](authoring/stage-01-woods/STATUS.md) |
| Stage 02 — alloys | 24 grade/condition references, 23 distinct grades, 8 finishes; 192 variants | [alloys-stage02-20261025](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/alloys-stage02-20261025) | [Alloy guide](authoring/stage-02-alloys/README.md) · [Status](authoring/stage-02-alloys/STATUS.md) |
| Stage 03 — FFF printing | 11 named references, 194 physical records, 73 metric map sets; 280 variants | [printing-stage03-20261025](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/printing-stage03-20261025) | [FFF guide](authoring/stage-03-printing/README.md) · [Status](authoring/stage-03-printing/STATUS.md) · [Full reproduction](authoring/stage-03-printing/REPRODUCE.md) |

**[Global resource index: 2,293 records](authoring/RESOURCE-INDEX.json)**. This count includes appearances, physical references, lights, environments and other resource kinds; it does not mean 2,293 distinct engineering materials or individual export files.

For each release, download all its resource ZIPs and extract them into the same empty parent directory. No concatenation is necessary. Open `index.html` inside the resulting collection directory. The catalog/sources/previews ZIP is sufficient for browsing; add runtime/master map archives for the complete editable collection. Check the attached manifests and `PUBLICATION-VERIFIED.json`.

Original v1 uses seven `catalog-v1-20261024-*.zip` files. Its small optional `Native-Appearance-Libraries.zip` contains only the uniform native appearance libraries, not all maps. Existing restoration helpers remain in `distribution/`.

Stage 03 uses **five ZIPs**: catalog/sources/previews, runtime maps, and three 2K master groups (smooth, fiber, wood). The complete source-pinned snapshot contains **3,509 files** and the ZIPs total **3,444,469,327 bytes**. Open `stage-03-printing/index.html` after extraction. The source-only physical summary and supplementary documentation follow-ups remain readable in Git without rewriting published resource bytes.

## Appearance and physical data are distinct, linked records

All new wood/alloy/FFF variants link explicit physical substrate references. Source units, SI conversions, grade, condition, temperature and unresolved properties are retained. Visual finish edits do not silently rewrite density, strength or mechanical axes. Missing values are unknown, never zero. The source review excludes inconsistent fields rather than guessing corrections.

FFF physical measurements retain their named product, source version, specimen process and orientation. Selecting another visual layer height, nozzle width, support scar or smoothing does not claim the same mechanical result. Material-reference density is not effective density of an infilled printed part. The [readable physical summary](authoring/stage-03-printing/data/physical-summary.csv) is subordinate to the full conditions and reported spread in each profile.

Stage 03 exports include **1,022 PNG maps**, **146 physical-height EXRs**, **280 filtered software previews**, **280 GLB** and **280 glTF/BIN specimens** with flat and curved metric coupons. All **560** interchange specimens passed the official Khronos validator with zero errors/warnings. All **24** data/numerical/filtering tests and full resource/archive/member download verification passed. These checks do not imply native SolidCraft, printer or engineering certification.

## Qualification and future integration

**Native SolidCraft acceptance and premium visual qualification of the new wood/alloy/FFF stages remain pending.** Proposed native command/appearance files are not executed imports or certified materials. Procedural preview images are not native GPU evidence. Finite-patch maps are not claimed seamless. Read each stage's exact boundaries.

The legacy audit still records 345 appearance records with physical-reference candidates requiring selection and 303 without a specific physical reference. New stages do not automatically close those gaps. Further alloy groups, other additive materials/processes, soils/masonry/pastes and the 118-element collection remain staged work.

**No plugin, autoinstaller, package compatibility standard or SolidCraft integration API is defined by this repository.** Those decisions remain pending community discussion. Internal resource indexes are not proposals to impose an upstream standard.

## Durable storage, provenance and preservation

[Working policy](authoring/WORKING-POLICY.md): this personal GitHub repository is the required durable destination for source and all generated assets. Local work and conversation attachments are not the final delivery. Publication requires download/hash verification. Earlier releases and original source histories are retained.

The original v1 README/receipt are historical records; their local-only/private wording describes the initial snapshot, not current repository visibility. No original binary was rewritten to update those historical statements.

New original authoring uses MIT OR Apache-2.0 with [the original license notices](catalog/licenses/). Primary factual references, third-party dependencies and their own notices retain their provenance; no blanket relicensing of supplier publications or physical datasets is implied. Complete copyrighted datasheets, commercial textures and font files are not included in the new stages.

Resource-delivery automation is limited to this personal repository. No upstream SolidCraft application code/CI, protection rule or installed application was changed by these publications.
