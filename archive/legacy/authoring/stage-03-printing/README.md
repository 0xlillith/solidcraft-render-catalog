# Stage 03 — FFF materials and process appearances

Original resource authoring, not a printer profile, plugin, material certification or SolidCraft application release. All source and generated files are delivered in the owner's `0xlillith/solidcraft-render-catalog` repository. The plugin/installer/integration standard remains undecided by the community.

## This tranche

- **11 named Prusament material references**, **194 sourced physical-property records**.
- **280 appearances**, each explicitly linked to a physical reference and a separate visual process recipe.
- **73 shared metric surface map sets**, 2048-square masters and 1024-square runtime variants.
- Seven PNG channels per resolution: sRGB color modulation, OpenGL and DirectX normals, roughness, metallic, ORM, and 16-bit height. **1,022 PNG maps** in total.
- A separate float32 signed millimetre-height EXR at each resolution: **146 EXR files**.
- **280 GLB + 280 glTF/BIN specimens**, each with both flat and curved 12.8 mm coupons, plus **280 original software previews** and an offline searchable gallery.

References: PLA, PETG, ASA, PC Blend, PC Blend Carbon Fiber, PA11 Carbon Fiber, PP Glass Fiber, PP Carbon Fiber, PVB, Woodfill Linden Light and TPU 95A. This does not complete ABS, other manufacturers, resin/SLA, powder processes or metal AM.

## Physical identity and test context

`data/physical-profiles.json` retains the original numerical values, source units, SI conversions, source spread, test method, direction labels, loads, humidity, duration, source version/date and per-property source link. The source PDFs were visually inspected; manufacturer prose, photographs and PDF artwork are not redistributed.

Printed-specimen measurements are separated from filament measurements. The source's 0.20 mm / 100% rectilinear specimen context is not replaced by the selected visual recipe. Horizontal and Vertical xz are preserved as the source labels, not silently reclassified as build-Z tensile loading. The source +/- values have no assumed statistical meaning. Unreported temperature or filler fractions remain null.

Density is the named material reference, not the effective bulk density of a porous/infilled printed part. Effective printed density and a complete constitutive model remain unknown. There is no automatic mass or engineering-material assignment. HDT at a stated load and Vicat are separate tests, not maximum service temperatures.

For TPU 95A, the trade name does not replace the measured Shore A value 92 +/- 0.4. Stresses at 100/200/300% strain are not Young's modulus. The source's suspicious filament elongation row (7264 +/- 76%) is explicitly excluded for review, not silently corrected.

These are versioned reference snapshots, not a claim of the latest product formulation. In particular, PLA uses the accessible dated February 2022 TDS; a newer combined PLA/PLA Blend download exists on the manufacturer's product page and has not been substituted or assumed equivalent. Conditions and properties must be checked against the actual purchased material and manufacturing process before engineering use.

## Visual processes and metric meaning

Smooth-source studies include 0.08, 0.12, 0.16, 0.20 and 0.28 mm wall layers. Filled-source studies use the conservative authored subset 0.16, 0.20 and 0.28 mm; this is not a certified manufacturer's minimum layer range. Wall variants include an aligned seam and fuzzy skin. Top surfaces include monotonic, concentric and ironed roads at authored 0.4/0.6/0.8 mm nozzle sizes with 0.45/0.66/0.88 mm road widths. Bed-contact textures, support marks and sanded walls are separate. Smooth-surface postprocess illustrations are limited to ASA/PVB; no chemical procedure is supplied.

Every patch is **12.8 x 12.8 mm**, finite and **not seamless**. A 0.08 mm layer spans 6.4 texels at 1K. Normals derive from physical height gradients and are regenerated after linear height downsampling. Fine details are illustrative, not measured profilometry, printer simulation or manufacturing geometry. Finite maps clamp at edges. Silhouette displacement is not automatically applied.

The source OpenGL normal uses +U right and +V image-up. Portable coupons use increasing UV-v down and an explicit tangent basis, so their green-flipped normal image is intentional. The glTF units are metres and Y-up. The curved coupon has 12.8 mm arc length. Both coupons are open meshes; neither is a physical mass specimen.

Palettes, scalar IOR 1.5, roughness and local texture variation are original unmeasured authoring choices. All current variants are opaque surface studies. Transparent/translucent polymers, fiber scattering and spectral effects are not inferred or certified. No manufacturer appearance matching or endorsement is claimed.

## Files and browsing

Download all stage release ZIPs into one location and extract them into the same empty parent directory. Open `stage-03-printing/index.html`; it runs locally without a server. Each card exposes its GLB, editable glTF, physical record, recipe and map contract. The GitHub automatic Source code ZIP contains source, not the complete binary resource pack.

`build/maps/` holds shared full-resolution resources and digests. `build/materials/` holds portable specimens, physical snapshots and previews. `data/` and `registry/` retain readable source-linked definitions and indices. `native-appearance-proposal.json` is an unexecuted authoring suggestion, not an installed library, verified API request, mass model or .solidcraft container.

## Reproduction

Use Python 3.11+ and the pinned `requirements.txt` in an isolated environment. Node and the official `gltf-validator@2.0.0-dev.3.10` are needed for portable-file acceptance.

```sh
python tools/data.py
python tests/test_stage.py
python tools/build.py --size 2048
GLTF_VALIDATOR_MODULE=/path/to/node_modules/gltf-validator node tools/validate_gltf.cjs
python tools/validate_stage.py
```

Run from the stage folder. Full production validation refuses partial or reduced-resolution builds. The independent validator checks source conversions, all PNG chunks/CRCs/dimensions/color roles, maps and EXR, height/normal relationships, ORM channels, every profile link and all glTF files. `reports/validation.json` must pass before resource publication. The publisher downloads the uploaded archives again and verifies every original member's SHA-256.

## Acceptance boundaries

Native SolidCraft flat/curved rendering, filtering, body-local mapping, CPU/GPU behavior, persistence and application UI acceptance have **not run**. **Premium qualification is not granted** by a successful generator or glTF validator. Software previews are explicitly not native-render evidence. The earlier 345 candidate-linked / 303 missing-reference legacy material audit remains open.

New original source and assets retain the repository's MIT OR Apache-2.0 license. Manufacturer names identify the source reference; no logos or endorsement are included. Third-party validation dependencies retain their own licenses. Full source documents are linked, not bundled. No upstream application CI, application code, installed app or earlier release is changed.
