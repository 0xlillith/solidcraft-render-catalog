# Stage 02 — metal alloy authoring candidates

**24 grade/condition profiles (23 distinct alloy grades), 192 appearance variants, and 124 source-backed physical records.** Every appearance links to its physical substrate reference. Open `index.html` after extracting all release archives into the same parent directory.

This is resource authoring in `0xlillith/solidcraft-render-catalog`, not a SolidCraft application change. No plugin, installation, integration or packaging standard is defined; those remain for community discussion.

## Included references

304L, 316L, 321, 17-4PH Condition A, 904L, duplex 2205, superduplex 2507; nickel alloys 400, 600, 625, 825, C-276 and Invar 36; aluminum 6061-T651, 7075-T651, 7075-T7351 and 2024-T351; C26000 brass, C93200/C95400 bronzes and C70600/C71500 copper-nickels; Ti-6Al-4V and D2/Sverker 21 hardened and tempered to 62 HRC.

This tranche does **not** complete the list of industrial alloys. Carbon/alloy steels, additional tool steels, cast irons, magnesium, zinc, solders and further aluminum/copper/titanium grades remain later source-reviewed increments.

## Physical data

The source bootstrap is `tools/prepare_alloys.py`; `data/` contains generated, readable numerical exports. Each property retains original units, the explicit SI conversion, primary source, table locator, temperature/interval and qualifier. Mechanical properties are typical supplier references, not guaranteed minima or design allowables. Missing temperatures remain null. Grade and heat-treatment identities are not inferred from the picture.

Titanium modulus ranges stay ranges. Copper density is converted from the table's lb/in3 rather than copied from rounded specific gravity. 7075 T651 and T7351 retain their distinct strength and conductivity values. D2 compressive proof strength does not become tensile yield strength. Online unit errors and conflicting fields are documented and excluded in `reports/source-review.json`.

Selected composition constraints/typical analysis are included where verified. These are not complete purchasing specifications. Elemental remainders, combined Ni+Co/Nb+Ta groups and nominal values are not rewritten as precise measured chemistry.

## Appearance and formats

Eight uncoated finishes: mirror polished, directional brush, cross satin, precision ground, lathe-turned face, overlapping face-milled passes, bead blast and service scuffs. Machining textures are original mathematical fields, not photographs or measured surface reconstructions.

- 2048-square masters and linearly downsampled 1024-square runtime data.
- Shared finish maps: sRGB modulation color; OpenGL/DirectX normal data; perceptual roughness; metallic; ORM; 16-bit height with offset -0.05 mm and range 0.1 mm.
- Finite 40 x 40 mm patch with clamp-to-edge addressing. **No seamless or subpixel manufacturing-detail claim.** Shader roughness, not an undersampled normal map, represents unresolved microstructure.
- Every variant has a self-contained GLB, an editable glTF/BIN referencing shared images, a physical JSON record, appearance JSON and proposed existing-engine commands.
- glTF sphere UVs are illustrative, not a manufacturing/CAD mapping. Its top-left UV/tangent basis uses the explicitly green-converted normal image. Native +V-up maps remain separate.
- Native command files propose `material.create` with the source density/card and a uniform optical fallback. They have **not** been run on SolidCraft; no native container or v2 revision is fabricated. Unsupported extended physics stays in the full reference record.
- Previews are original software-lit sphere/flat coupons using these fields. They are **not** GPU renders from SolidCraft or measured conductor spectra.

Bare metal is deliberate: no rust, anodizing, plating, passivation, coating mass, altered alloy chemistry, residual stress or mechanical-strength change is inferred from a finish. No certified isotropic tensor is synthesized from incomplete or ranged measurements.

## Verification and qualification

Run `python3 tools/prepare_alloys.py`, the Python/Node tests, `node tools/alloy_maps.cjs`, `python3 tools/build_gallery.py`, and `python3 tools/validate_stage.py`. The publication workflow additionally runs the pinned official Khronos glTF validator against every GLB and glTF, then uploads, downloads and SHA-256-verifies every archive/member. The independent image check uses Pillow 11.3.0; the official glTF check uses gltf-validator 2.0.0-dev.3.10.

Independent checks cover property identity/conversions, density coverage, source references, finish determinism, bounded fields, gradient normals, image color roles, PNG CRC/decompression, ORM channels, topology, hashes and file presence.

**Native SolidCraft visual/physical-card acceptance and premium qualification remain pending.** Pegasus was offline for this delivery. A file-complete and source-checked authoring stage is not every material's physically complete implementation.

## Durable storage and ownership

All source and exported data belong in the personal catalog repository; full generated media are release assets. Conversation downloads are not the canonical delivery. The previous v1 and wood releases remain intact. Generated documents and index do not implement a plugin standard.

New source, procedural fields, metadata and original previews are MIT OR Apache-2.0, retaining the repository notices. Factual references keep their primary attribution; complete supplier PDFs, photographs, logos and licensed databases are not redistributed or relicensed. Dependencies retain their own licenses.
