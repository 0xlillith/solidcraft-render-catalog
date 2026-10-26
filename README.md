# SolidCraft Render resource catalog

Personal resource repository maintained by **0xlillith**. **Complete generated assets are stored in this repository's Releases; GitHub's automatic Source code ZIP is not the complete image/mesh library.** Source, numerical inputs, tests and readable inventory remain in Git.

## Published resource deliveries

| Delivery | Coverage | Complete assets | Source and status |
|---|---|---|---|
| Original catalog v1 | 1,386 original resource records | [catalog-v1-20261024](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/catalog-v1-20261024) | [Original guide](catalog/README.md) |
| Stage 01 — woods | 16 species references, 4 grain views, 6 finishes; 384 variants | [wood-stage01-20261025](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/wood-stage01-20261025) | [Wood guide](authoring/stage-01-woods/README.md) · [Status](authoring/stage-01-woods/STATUS.md) |
| Stage 02 — alloys | 24 grade/condition references, 23 distinct grades, 8 finishes; 192 variants | [alloys-stage02-20261025](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/alloys-stage02-20261025) | [Alloy guide](authoring/stage-02-alloys/README.md) · [Status](authoring/stage-02-alloys/STATUS.md) |
| Stage 03 — FFF printing | 11 named references, 194 physical records, 73 metric map sets; 280 variants | [printing-stage03-20261025](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/printing-stage03-20261025) | [FFF guide](authoring/stage-03-printing/README.md) · [Status](authoring/stage-03-printing/STATUS.md) · [Full reproduction](authoring/stage-03-printing/REPRODUCE.md) |
| Stage 03b — additive extension | ABS from three additional brands, resins, SLS/MJF polymers and metal AM; 24 physical profiles and 198 appearances | [additive-stage03b-20261025](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/additive-stage03b-20261025) | [Extension guide](authoring/stage-03b-additive/README.md) · [Status](authoring/stage-03b-additive/STATUS.md) · [Source notes](authoring/stage-03b-additive/SOURCE-NOTES.md) |
| Stage 04 — earth and masonry | 28 physical identity/condition profiles, 30 metric mapsets, 168 illustrated surfaces | [earth-masonry-stage04-20261026](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/earth-masonry-stage04-20261026) | [Earth/masonry guide](authoring/stage-04-earth-masonry/README.md) · [Status](authoring/stage-04-earth-masonry/STATUS.md) |

**[Global resource index: 2,711 records](authoring/RESOURCE-INDEX.json)**. This count includes appearances, physical references, lights, environments and other resource kinds; it does not mean 2,711 distinct engineering materials or individual export files. The 40 additional closed transmission studies in stage 03b are representations of existing appearances and are not double-counted as new material identities.

For each release, download all its resource ZIPs and extract them into the same empty parent directory. No concatenation is necessary. Open `index.html` inside the resulting collection directory. The catalog/sources/previews ZIP is sufficient for browsing; add runtime/master map archives for the complete editable collection. Check the attached manifests and `PUBLICATION-VERIFIED.json`.

Original v1 uses seven `catalog-v1-20261024-*.zip` files. Its small optional `Native-Appearance-Libraries.zip` contains only the uniform native appearance libraries, not all maps. Existing restoration helpers remain in `distribution/`.

Stage 03 uses **five ZIPs**: catalog/sources/previews, runtime maps, and three 2K master groups (smooth, fiber, wood). The complete source-pinned snapshot contains **3,509 files** and the ZIPs total **3,444,469,327 bytes**. Open `stage-03-printing/index.html` after extraction. The source-only physical summary and supplementary documentation follow-ups remain readable in Git without rewriting published resource bytes.

Stage 03b uses **six ZIPs**, totalling **1,816,876,971 bytes**: catalog/sources/previews, runtime maps, and four master groups (FFF, vat, powder-polymer, metal-AM). Open `stage-03b-additive/index.html`. All six archives and their original members passed upload/download SHA-256 verification in run [40186384837](https://github.com/0xlillith/solidcraft-render-catalog/actions/runs/40186384837). Read the later [source interpretation notes](authoring/stage-03b-additive/SOURCE-NOTES.md) alongside the frozen release.

## Appearance and physical data are distinct, linked records

All new wood/alloy/additive/earth-masonry variants link explicit physical substrate references. Source units, SI conversions, grade, condition, temperature and unresolved properties are retained. Visual finish edits do not silently rewrite density, strength or mechanical axes. Missing values are unknown, never zero. The source review excludes inconsistent fields rather than guessing corrections.

FFF physical measurements retain their named product, source version, specimen process and orientation. Selecting another visual layer height, nozzle width, support scar or smoothing does not claim the same mechanical result. Material-reference density is not effective density of an infilled printed part. The [readable physical summary](authoring/stage-03-printing/data/physical-summary.csv) is subordinate to the full conditions and reported spread in each profile.

The [additive-extension physical summary](authoring/stage-03b-additive/data/physical-summary.csv) retains **208** source-backed records. Resin cure schedules, LPBF machine/layer/heat treatment and sintered-metal conditions are kept separate. Liquid resin density, loose-powder density, solid-part density and relative density are not interchangeable. Some references provide mechanical data but no verified exact absolute density; no density is borrowed merely to complete a form. Transmission assets declare their authored, unmeasured optical assumptions rather than implying measured supplier behavior.

Stage 03 exports include **1,022 PNG maps**, **146 physical-height EXRs**, **280 filtered software previews**, **280 GLB** and **280 glTF/BIN specimens** with flat and curved metric coupons. All **560** interchange specimens passed the official Khronos validator with zero errors/warnings. All **24** data/numerical/filtering tests and full resource/archive/member download verification passed.

Stage 03b adds **700 PNG maps**, **100 height EXRs**, **198 previews**, **396 opaque GLB/glTF exports** and **80 closed-transmission GLB/glTF exports**. All **21** numerical/data tests and **476** official glTF validations passed, with zero validator errors/warnings. These checks verify authoring data and files, not native SolidCraft, manufacturing or engineering certification.

Stage 04 adds **420 PBR PNG maps**, **60 millimetre-height EXRs**, **168 software previews** and **336 portable GLB/glTF files**. Its seven ZIPs total **3,235,732,036 compressed bytes**, available in [the verified release](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/earth-masonry-stage04-20261026) with member-level SHA-256 checks. Soil dry bulk, aggregate particle, cement-powder particle, age-conditioned concrete/mortar strength, and wet/dry gypsum reference properties are distinguished. Unknown physical values remain null.

## Qualification and future integration

**Native SolidCraft acceptance and premium visual qualification of the new wood/alloy/additive/earth-masonry stages remain pending.** Proposed native command/appearance files are not executed imports or certified materials. Procedural preview images are not native GPU evidence. Finite-patch maps are not claimed seamless. Read each stage's exact boundaries.

The previously absent ABS/additional-supplier, resin, polymer-powder and metal-AM categories now have generated resources and published assets. This does not claim every commercial product or process. Their native and premium gates are still separate from category delivery.

The legacy audit still records 345 appearance records with physical-reference candidates requiring selection and 303 without a specific physical reference. New stages do not automatically close those gaps. Further alloy groups and the 118-element collection remain staged work. Further earth/masonry fidelity and native acceptance remain separate from published resource generation.

**No plugin, autoinstaller, package compatibility standard or SolidCraft integration API is defined by this repository.** Those decisions remain pending community discussion. Internal resource indexes are not proposals to impose an upstream standard.

## Durable storage, provenance and preservation

[Working policy](authoring/WORKING-POLICY.md): this personal GitHub repository is the required durable destination for source and all generated assets. Local work and conversation attachments are not the final delivery. Publication requires download/hash verification. Earlier releases and original source histories are retained.

The original v1 README/receipt are historical records; their local-only/private wording describes the initial snapshot, not current repository visibility. No original binary was rewritten to update those historical statements.

New original authoring uses MIT OR Apache-2.0 with [the original license notices](catalog/licenses/). Primary factual references, third-party dependencies and their own notices retain their provenance; no blanket relicensing of supplier publications or physical datasets is implied. Complete copyrighted datasheets, commercial textures and font files are not included in the new stages.

Resource-delivery automation is limited to this personal repository. No upstream SolidCraft application code/CI, protection rule or installed application was changed by these publications.
