# SolidCraft complete local render catalog — authoring v1

This is a local resource library, not a software release or a change to the installed application.
Open **index.html** or **Open-Catalog.cmd**. No web server or Internet connection is required.

## Delivered coverage

| Collection | Entries |
|---|---:|
| Original material concepts realized as procedural assets | 600 |
| Conserved SELENE opaque appearances | 48 |
| Authored lighting rig realizations | 280 |
| Finite environment/context realizations | 280 |
| Scene, studio and environment compositions, plus original native studios | 97 |
| Original quality profiles with separate bounded native variants | 10 |
| SELENE shot recipes and saved camera/lighting studies | 12 |
| Existing physical reference profiles retained | 59 |

Every main material has 1024 × 1024 lossless PBR maps, OpenGL and DirectX normals, packed ORM,
16-bit normalized height, signed millimetre-height EXR and linear-color EXR. Role-specific
transmission, coating, emission or masks are supplied where authored. The sphere GLB/glTF is
an interchange material sample; the physical repeat and projection authority is material.json.
The sample UV parameterization is not a global CAD manufacturing/texture-coordinate contract.

Environments include actual GLB/glTF/OBJ geometry, an authored HDR/EXR illumination field, a
separate camera-only background and a native `.solidcraft` document with embedded HDR.
Lighting includes the full numeric rig, layout geometry, a native example and a reference-origin
HDR/EXR projection. Do not combine an analytic emitter with the HDR image of the same emitter.

## Use with the current SolidCraft build

1. **Browse visually** in index.html. Each card links the real files and explains its representation.
2. **Uniform native appearances:** open `libraries/all-600-native-appearances.json` through the
   existing Appearance local-library controls. All 600 entries have native-validated revisions.
   Sixty family libraries and `selene-48-appearances.json` are alternatives.
3. **Richer image maps:** use a material's GLB/glTF in a capable external renderer, or its explicit
   `native-runtime-texture-request.json` against its native Specimen body through SolidCraft's
   GPU image API. Arbitrary new image maps are not magically installed in the application's
   compiled built-in catalog. A v2 appearance library stores uniform PBR, not image textures.
4. **Native scenes/rigs/setups:** open the `.solidcraft` resource in a new document, keeping your
   original project intact. Build scripts construct their own examples; do not run them against
   an unsaved working document. Retained images in the current app are not automatic live preview.
5. **Physical references:** `libraries/physical-references/physical-reference-library.json` contains
   46 supported point-density profiles. All 59 original extended profiles/cards are retained.
   Select the actual material, grade, processing and conditions deliberately; never infer a
   physical material from its appearance. No new mechanical or thermal properties were invented.

The 57 `optical-study.solidcraft` files are smooth closed-slab native studies with explicitly
recorded authored RGB absorption. They are not proof of rough, spectral, thin-film, diffractive,
fluorescent, subsurface or geometry-specific behavior. Rich glTF material intent and the unchanged
original specification remain beside the native variant.

## Coverage is not scientific certification

The full source catalog is covered by generated files. This is a **first complete procedural
realization**, not a claim that every high-level concept now has a measured or physically complete
implementation in SolidCraft. The definitions explicitly distinguish portable material intent,
current-native variants, unresolved external inputs and unsupported phenomena.

Specialized optical phenomena, measured photometry/IES, source-dependent calibration, precise
manufacturing topology, atmosphere/ephemerides, motion studies and semantic SELENE sub-part roles
must not be inferred from a thumbnail. Lunar/vacuum presets contain no invented atmosphere or
undeclared sky fill. The original source constraints and calibration blockers remain unchanged.

Native GPU thumbnails are actual 64-sample denoised images of the recorded variant, not final
convergence tests. Environment model snapshots are actual native viewport images, not saved-HDR
renderings. Mathematical authoring swatches and layout diagrams are explicitly labelled.

## Formats and ownership

- `material.json`, `rig.json`, `environment.json`, `setup.json`, `quality.json`, `shot.json`: editable
  authority for new realizations, with the full unchanged source specification.
- PNG: sRGB color; linear-data normals/scalars/ORM; 16-bit height. ORM R is 1 (no invented AO).
- EXR: linear sRGB color/radiance and signed height in mm; lossless ZIP scanlines.
- HDR: bounded Radiance RGBE, linear sRGB/D65 primaries, Z-up equirectangular source orientation.
- GLB/glTF: metres, Y-up; portable PBR and optional material extensions. Reader support varies.
- OBJ/MTL: millimetres, Z-up, deliberately simpler scalar fallback.
- `.solidcraft`: generated by the real pinned native CLI, not hand-written container guesses.
- `solidcraft-library/2`: native-exported/validated definitions, not a renamed planning JSON file.

External native command paths refer to this output directory. Keep the folder at its current
location, or update those explicit paths before replaying build/request files. GLB is self-contained;
glTF uses adjacent relative images/buffers. The generated native environment files retain HDR bytes
and their imported geometry without needing the original GLB/HDR path at reopen.

## Reproduction and verification

Source application commit: `9e6e0b8df130f342e15ebe988b7211d1482a44c2`.
The authoring scripts are in `tools/`; the unmodified source catalogs and original starter/physical
resources are in `source/`. `reports/` contains native receipts, failures from superseded attempts
and final validation results. `SHA256SUMS.txt` identifies the delivered bytes.

Primary generators: `materials.py`, `lighting.py`, `environments.py`, `setups.py`.
Native writers: `native_materials.py`, `native_environments.py`, `supplements.py`, `selene_shots.py`.
Validation: `validate_assets.py` uses the official offline Khronos glTF validator plus image,
normal, packing, EXR/HDR and native-container checks. Native generation and cold-reopen checks
are separate from photometric correctness and full original-specification acceptance.

The original generators/maps/rigs and reference sources remain archived. New code/assets are
original authoring under MIT OR Apache-2.0. Third-party tool dependencies retain their own licences;
physical-source claims retain their original metadata. No commercial CAD content or font files
were copied. Nothing was published to GitHub and the application source/install was not edited.
