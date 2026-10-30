# Stage 01 — wood appearance, physical references and resource inventory

**Private authoring candidate, not a SolidCraft plugin, installer or agreed integration standard.** The community has not yet defined that interface. The historical v1 catalog and release are unchanged.

## Scope

16 source-backed wood references × four grain views × six finishes = **384 authored material variants**, sharing **64 map sets**. These are not 384 independently measured species. Woods: red alder, white ash, American basswood, American beech, yellow birch, black cherry, American elm, shagbark hickory, sugar maple, northern red oak, white oak, black walnut, western redcedar, Douglas-fir (Coast), eastern white pine and loblolly pine. Do not silently substitute European species or an unspecified commercial timber grade for these source names.

Grain views: plain-sawn/cathedral, quarter-sawn/ray flecks, rift-sawn and end grain. Finishes: raw, fine-sanded, oiled, waxed, satin varnish and gloss varnish. Optical values are original illustrative choices, not measured coatings. Each variant links an explicit physical substrate reference; finish changes never invent coated-composite properties.

The completed generation produced **768 maps**: six roles at 2048² and 1024² for each of 64 sets, plus **384 authoring previews**. Roles are sRGB base color, OpenGL and DirectX normals, linear roughness, ORM and 16-bit height. Runtime color is filtered in linear light; normals are derived from physical height after filtering. Metallic is zero; AO is one, not baked lighting. These are finite 100 × 250 mm board patches (100 × 100 mm end grain), **not seamless tiles**. Use clamp-to-edge or an explicit board-placement strategy.

## Physical provenance and limits

Primary source: USDA Forest Products Laboratory, **Wood Handbook (2021), FPL-GTR-282**, Chapter 5, Table 5–3a, metric rows at **12% dry-basis moisture**, printed pages 5–4 through 5–7. The table pages were checked visually. Sources and per-property locators are embedded in `tools/prepare_data.py`; the readable numerical table is `data/wood-reference-summary.csv`.

- Chapter 5: https://research.fs.usda.gov/treesearch/62244
- Chapter 4: https://research.fs.usda.gov/treesearch/62243

The data covers reported specific gravity, bending strength and apparent bending modulus, work to maximum load, impact-bending height, parallel compression, perpendicular proportional-limit compression, parallel shear, perpendicular tension where reported and side hardness. Original units/values remain alongside explicit SI conversions. Two unreported perpendicular-tension values remain null.

These are averages for **clear, straight-grained specimens**, not structural design allowables or product certificates. Bending modulus includes shear deformation; it is not silently used as an isotropic Young modulus. Temperature, uncertainty and a complete orthotropic tensor are not invented.

G12 uses oven-dry mass and volume at 12% moisture. Density including that moisture is separately derived from Chapter 4 Equation (4–14): `rho12 = 1000 kg/m³ × G12 × 1.12`. White oak therefore has a derived reference estimate of 761.6 kg/m³, not 680 kg/m³. Coating mass and mechanical contribution remain unknown. No material is assigned to a CAD body automatically.

## Index and historical gaps

`registry/global-index.json` is a federated inventory of **1,786 records**: the existing 1,386 resources, 384 new variants and 16 new physical profiles. The expanded JSON/CSV/gallery are generated from the versioned sources, not a plugin schema.

The actual audit of all **648 historical material looks** found **345 with candidate physical references requiring selection and 303 without a specific physical reference**. A candidate alloy or substrate is not verified material identity. The summary is preserved in `reports/legacy-coverage-summary.json`; a full checkout can reconstruct the row-by-row audit. Nothing is relabelled complete merely because a reference exists.

## Reproduce

Node.js and Python standard libraries only, with no dependency installer or network access in the generators. From this directory in a repository checkout:

```sh
python3 tools/prepare_data.py
python3 tools/build_registry.py
node --test tests/numerical.cjs
node tools/wood_maps.cjs
python3 tools/validate_stage.py
```

Open `index.html` after generation. `WOOD_SPECIES`, `WOOD_CUT`, `WOOD_SIZE` and `WOOD_OUTPUT` optionally select a bounded subset; the normal full build uses 2048² masters. The gallery images are software authoring swatches, **not SolidCraft GPU renders**.

## Actual validation and publication

The reconstructed complete image set passed source-table/SI/density/identity checks, independent PNG CRC/decompression, file hashes, dimensions, color roles and complete coverage. Eight numerical/image regressions passed. See `reports/validation.json`.

**Native SolidCraft acceptance: NOT RUN. Premium qualification: NOT QUALIFIED.** Pegasus was offline. Flat/curved native renders, instance-attached grain, CPU/GPU agreement, filtering and save/reopen still need testing. There is no new verified glTF/native-material adapter or automatically installed library.

GitHub stores the source, numerical reference table, index definition, tests and validation report. **The new bulk map exports have not been uploaded to a GitHub release in this session**; they are supplied separately in conversation attachments and can be regenerated. The connected source writer supports these repository changes, but an authenticated large-file release uploader was unavailable. Do not confuse this source checkpoint with full binary publication.

Original authoring code and generated media use MIT OR Apache-2.0, as in the repository's `catalog/licenses/`. USDA numerical facts retain cited provenance. No photographs, fonts, proprietary samples or source-table artwork are redistributed.
