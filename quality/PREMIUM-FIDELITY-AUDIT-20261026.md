# SolidCraft Render catalog — visual and physical fidelity audit

Date: 2026-10-26. Scope: `catalog-v1`, stages 01/02/03/03b/04/05. This is a **quality audit**, not an assertion that any existing assets are certified or native-ready. No upstream SolidCraft work is in scope.

## Executive decision

**No blanket “premium” status.** Current SHA-256, PNG/EXR and official glTF checks establish *file validity*, not perceptual fidelity, physical optics or correct material application. Keep existing immutable releases as `procedural_authoring`; introduce higher-fidelity scanned, traceable PBR references alongside them. Do not relabel generated imagery as measured photogrammetry.

| Category | Evidence reviewed | Major realism/quality issue | Acceptance status |
|---|---|---|---|
| Wood, stage 01 | Visual inspection of raw samples from the 384-preview original delivery, 4 cuts × four representative species, source `wood_maps.cjs` | Plain/end-grain use over-regular “contour map” growth-ring motifs; figure, early/latewood transitions, pores and rays are too schematic. Every finish in a wood/cut shares the same runtime normal and roughness maps: finish-specific specular response appears only as a simple software-preview multiplier, not a separately exportable clearcoat material | **Not premium** |
| Metal alloys, stage 02 | 8 procedural machining patterns, representative brass sphere/coupon preview, source `alloy_maps.cjs` | Source-linked grades and process-specific finishes exist, but metal F0/base color are original artistic palettes, not grade- and wavelength-specific complex refractive index; anisotropy, oxide layers and abrasion distribution not physically measured | **Not calibrated** |
| FFF, stage 03 | Representative contact sheet: 0.08/0.28 mm ridges, fuzzy skin, top-road, fiber and woodfill | Layer frequency differs by height as intended; process detail risks aliasing at lower mips/oblique angles. Specimen/source physical tests cannot be extrapolated to arbitrary user-selected layers, infill and raster | **Authoring good; application unqualified** |
| Other additive, stage 03b | ABS, resin, SLS/MJF and LPBF representative contact sheet; 198 looks, 40 optics studies | Some resin/machine finish examples have weak distinguishability in the software thumbnails. Translucent optics are explicitly unmeasured. Actual shader response, microfacet normals and scale under camera distance untested | **Not premium** |
| Soil/aggregate/concrete/gypsum/paste, stage 04 | Stage04 preview of `earth.quikrete-concrete-1101.exposed-stones`, source `texture()` and `preview()` | “Exposed stones” shows weak/no resolvable stone outlines in preview. Shapes generated from shared noise and sparse raster ellipses reused across substrate profiles; preview computes gradients after resampling physical height *without mm-per-texel calibration*, flattening the expected normal contrast. Limited aggregate gradation, cracks and pore morphology realism | **Not premium** |
| Pure elements, stage 05 | Six shared mapsets for 154 looks, 118 reference cards | Surface look is generic illustration; not measured complex IOR, alloy purity, crystal phase or isotope. Appropriate omission of fabricated bulk material for 41 reference-only elements should remain. | **Scientific identity coverage; not premium optical reference** |
| Catalog v1 and environments | Original authoring receipts and stage manifests | Existence of 600 concept materials, 280 light and 280 environment concepts does **not** mean premium/physically complete resources, photometric light fields or photographic 3D environments; source catalog explicitly lists approximations | **Mixed fidelity; not blanket premium** |

## Immediate remedy

First create a curated **high-fidelity photographed/scanned PBR benchmark** (this PR, eight original CC0 assets from Poly Haven), with exact provider image hashes, source credits, per-texture dimensions, normals/roughness/height and usable glTF samples. These photographic maps are a higher-quality **visual baseline** than procedurally guessed wood rings or simulated gravel cells; they do **not** turn wood veneers or concrete into a measured structural material.

Source assets are independently published [CC0](https://polyhaven.com/license) by [Poly Haven](https://polyhaven.com). The API and attribution are separate from the original generator licenses. The gallery displays **Powered by Poly Haven**. Original procedural files remain preserved and distinguishable.

## Mandatory quality gates for future promotion

1. **Source audit:** original scans or justified procedural anatomy; full CC0/licensing and data provenance. No falsely inferred engineering grade/physical properties.
2. **PBR channel integrity:** correct color space, normal orientation, roughness and metallic channel semantics, tangent handedness, physical dimensions, bit-depth and hash checks. Avoid JPEG-encoded normals and physically impossible F0 factors.
3. **Macro and microstructure:** credible scale-specific pores/grain/aggregates/roads, stochastic detail without obvious repeats or “contour-map” patterns; compare against real photographed references.
4. **Visual coverage:** physically scaled flat and curved coupons, grazing-light, daylight/studio, dark and bright backgrounds, 1K/2K/4K and variable camera distance/mip behavior. Compare CPU and GPU when the application supports it.
5. **State correctness:** distinguish surface appearance, material substrate and manufacturing/cure/moisture state; never auto-assign reference density to a part with unspecified porosity, mix or coating.
6. **Product acceptance:** through the real SolidCraft UI: select target → apply → preview change → final GPU and CPU where applicable → save/reopen → undo → verify.
7. **Status:** `source_validated`, `asset_validated`, `native_accepted`, `visual_reviewed`, and `premium_qualified` are **independent checkboxes**. Imported scans are not automatically native accepted.
8. **Side-by-side A/B:** keep unchanged original 2K assets for regression; publish improved assets as additive release with provenance and SHA256 rather than overwriting old release bytes.

## Measurements and limits

The original releases have completed their recorded validation. The present inspection is a **representative visual sampling** and source-code review, not exhaustive visual examination of 2,983 entries nor a real native-run acceptance campaign. The latter requires an online, authorized Pegasus GUI/render session and a defined selection of target assets. Missing tests stay open rather than being presumed green.

No plugin/installer/format standard is defined or proposed by this audit. This quality effort is in `0xlillith/solidcraft-render-catalog` only; no upstream SolidCraft CI or code changes.
