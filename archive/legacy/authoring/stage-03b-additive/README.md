# Stage 03b — ABS, additional brands, resins, powder polymers and metal AM

This resource-authoring extension closes the missing **categories** from stage 03. It is not an exhaustive list of every commercial product or manufacturing process. All work and generated assets belong in `0xlillith/solidcraft-render-catalog`. No plugin format, installer, integration API, printer configuration or upstream CI change is defined here.

## Source-linked coverage

| Family | References / conditions | Appearance variants |
|---|---:|---:|
| ABS / additional FFF brands | Bambu Lab ABS V3, Polymaker PolyLite ABS V5.6, UltiMaker ABS v5.00 | 60 |
| Photopolymer resins | Formlabs Durable V2, Flexible 80A, Elastic V1, Rigid FLRGWH01, Tough 2000 V2, High Temp V2 in two mechanical cure conditions | 70 |
| Powder-bed polymers | EOS PA2200 Balance, PA1101, PA3200 GF, TPU1301; HP 3D HR TPU01 Balanced MJF | 20 |
| Metal AM | EOS 316L, Ti64, IN718 as-built/heat-treated, AlSi10Mg, MS1; Markforged 17-4PH as-sintered/H900/H1150 | 48 |
| **Total** | **24 condition-specific physical profiles** | **198** |

There are 208 factual physical-property records. Every appearance has a physical-profile reference, complete copied physical JSON, source locator, original value/unit, explicit SI conversion and manufacturing/test condition. Profile count is not unique formulation count.

Physical data are reference snapshots, not engineering design allowables. Original documents span named historical revisions and current 2026 HTML snapshots; no universal latest-formulation claim is made. Only factual transcriptions and original code/assets are redistributed, not supplier publications, images or logos.

## Important physical distinctions

- Bambu ABS test conditioning is retained; it is not described as unconditioned as-printed ABS.
- PolyLite ABS's pinned PDF conflicts with older/wiki density and contains an implausible XY tensile spread. The conflicting tensile row is excluded, not repaired from another revision. Its flexural method-label conflict is retained explicitly.
- UltiMaker's source XY/YZ/Z labels and the source layer/process remain unchanged when a visual layer is selected.
- Formlabs cure conditions remain per property. High Temp mechanical and HDT tables use different cure schedules: they are explicitly **not** interchangeable.
- Cured, solid bulk, liquid resin, loose-powder and sintered-part densities are distinct quantities. A relative density is not kg/m3; an inequality is not an exact point value.
- EOS 316L/IN718 minimum density values remain lower bounds. Markforged's 96% relative density is not converted into an invented absolute density. Rigid FLRGWH01, the selected AlSi10Mg/MS1 process sheets and Markforged do not have a verified exact absolute-density point here; the absence is explicit. They nevertheless retain their sourced mechanical properties.
- Source sheet temperature, thermal history, machine/process and orientation are not replaced by a rendering finish. No automatic body mass assignment occurs. Postfinish strength and effective density remain unknown.
- Elastic stress-at-strain is not a Young modulus. Unknown mechanical tensors and optical constants are not zero-filled.

See `data/source-audit.json` and `data/physical-summary.csv` for the numerical audit and all exclusions.

## Generated resources

50 original metric map sets, each with 2048-square masters and linearly downsampled 1024-square runtime versions: **700 PNG maps**, **100 float32 signed-mm height EXRs**. PNG roles: color modulation (sRGB), normals OpenGL/DirectX, roughness, metallic, ORM and 16-bit height. ORM R=1 deliberately declares no invented AO. Normal maps are recomputed after height filtering; the 16-bit height mapping is -0.25 to +0.25 mm.

FFF patches are 12.8 mm and show 0.08/0.12/0.16/0.20/0.28 mm layer studies, seam, fuzzy skin, top roads, ironing, bed contact, sanding and polishing. Resin patches are 6.4 mm with 25/50/100 um wall/stair studies, support marks and finishes. The layer examples are authored texture studies, **not claims that each manufacturer's printer supports every combination**.

SLS/MJF include authored as-built grain, bead-blasting, tumbling and smoothing. LPBF differentiates upskin, vertical and downskin patterns at the named source process layer; shot-peening, machining and polishing are distinct. Bound-metal sintered extrusion has a separate road pattern. No visual pattern is measured profilometry, porosity simulation or a guarantee of processing feasibility.

Each appearance has a flat and curved metric coupon in **GLB and editable glTF/BIN**, an opaque software preview and its input hashes. Four translucent-intent resin references/conditions also have **40 closed 2 mm transmission slab studies** (GLB + glTF). These declare unmeasured IOR 1.5, transmission 0.85 and authored volume attenuation; they are not measurements of actual resin scattering or spectral optics. Main gallery images remain clearly labelled opaque surface previews; they do not pretend to show the transmission asset.

Total portable files: **396 standard GLB/glTF + 80 closed-transmission GLB/glTF = 476**. Maps are finite patches, **not seamless**. Heights are data; no automatic silhouette displacement is promised. Shared map sets avoid unnecessary duplication.

## Browse and reproduce

Extract all ZIPs of the stage release into one empty parent directory and open `stage-03b-additive/index.html`. The catalog/source/preview archive is sufficient to browse; all map archives are required for complete editable glTF resources. GLB embeds its texture bytes. GitHub's automatic source ZIP is not the complete binary collection.

Use the pinned requirements in an isolated Python environment and install the official `gltf-validator@2.0.0-dev.3.10` separately. From the stage directory:

```sh
python tools/inputs.py
python tests/test_stage.py
python tools/build.py --size 2048
GLTF_VALIDATOR_MODULE=/path/to/node_modules/gltf-validator node tools/validate_gltf.cjs
python tools/validate_stage.py
```

The publication gate rejects partial builds. It checks all source links, exact physical snapshots, byte hashes, PNG CRCs/color roles/dimensions, float EXR, height/normal agreement, normal handedness, ORM roles, linear downsampling, preview input/output hashes, every portable file and full category coverage. The publisher downloads uploaded archives and verifies each original member before releasing them.

## Qualification boundary

These are original detailed resource-authoring candidates. **Native SolidCraft acceptance and premium visual qualification remain separate, unrun gates.** Software coupon previews and a valid glTF are not proof of native behavior, measured optics or engineering certification. No native format container, unexecuted library revision or certified part density is fabricated. Existing v1/stage releases and the 345 candidate-linked / 303 unresolved historical physical-reference audit are preserved.

Original code and assets use the repository's MIT OR Apache-2.0 licenses; third-party facts and dependencies retain their own provenance. No application installation or upstream SolidCraft repository is modified.
