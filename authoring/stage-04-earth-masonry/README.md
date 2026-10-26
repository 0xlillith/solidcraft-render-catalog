# Earth, aggregates, cementitious materials and pastes — Stage 04

Original **resource-authoring candidates** for SolidCraft Render. The current UI/plugin/import contract is **not defined**; none of this changes upstream code, app CI, native document format or installation.

## Coverage and physical integrity

28 condition-specific reference/archetype profiles, across 5 material families; six procedural visual treatments per profile = **168 appearances**, sharing **30 physically scaled map sets**. Every appearance links an explicit physical record and source identity. Some references describe soil-class *ranges* and product-specific curing; others are visual archetypes with unknown numeric density. Unknown means **null**, not zero, and must not be used for automatic volume-to-mass assignment.

- **Soils:** dry bulk density includes pore volume and is dependent on compaction and organic content; not a particle density or an identification of a sample at a particular site.
- **Aggregates:** mineral particle density is not poured loose/granular bulk density. A sample's gradation and compaction are required.
- **Portland cement powder:** ACI typical particle specific gravity 3.15 is not sack bulk density.
- **Concrete and mortar:** selected compressive strengths refer to the named product/mortar class under specified cure/test conditions; visual finishing does not imply those strengths for an arbitrary model.
- **Gypsum:** wet and dry cast densities, plus one-hour and dry strengths, are distinct states. No dry casting strength is assigned to slurry.
- **Pastes/paints:** manufacturer product descriptions may identify a usable visual reference without numerical bulk physical properties. Do not invent them.

Source URLs are written into each property and `data/sources.json`; no copyrighted datasheet images or text have been bundled. Data are informative, not certified engineering design allowables.

## Appearance

Five families × six finish recipes: soil loose/tamped/damp/cracked/wind/raked, aggregate loose/graded/wet/raked/exposed/tumbled, cement as-cast/broomed/form-board/trowelled/exposed/weathered, gypsum smooth/float/scraped/chipped/brushed/sanded, and paste fresh/spatula/swirled/brushed/air-dried/crusted. Colored material references reuse metric topologies: physical profiles are not changed by a visual finish.

Every process map set has PNG color modulation (sRGB), roughness, OpenGL and DirectX normals, ORM (R=255 no synthetic AO, G=roughness, B=0 dielectric metallicity), physical signed-height EXR in millimetres and a 16-bit height PNG; 2048² master and linearly filtered 1024² runtime. Normals are regenerated from filtered height. Finite mapped patches **are not seamless**. 168 external glTF/embedded GLB flat+curved coupons and 168 original software previews. Previews are **not** real SolidCraft GPU output.

## Reproduction and inspection

Install pinned Python dependencies from `requirements.txt`, and install `gltf-validator@2.0.0-dev.3.10` into a separate Node directory. From repository root:

```sh
python -m unittest discover -s authoring/stage-04-earth-masonry/tests -v
python authoring/stage-04-earth-masonry/tools/build.py --size 2048
GLTF_VALIDATOR_MODULE=/path/to/node_modules/gltf-validator node authoring/stage-04-earth-masonry/tools/validate_gltf.cjs
python authoring/stage-04-earth-masonry/tools/validate.py
```

Only the full-resolution source-pinned build is eligible for resource publication. The publication helper uploads and downloads each archive and checks SHA-256 of the archive and each member. Open `stage-04-earth-masonry/index.html` in the expanded release. Its list is an *internal inventory*, not a proposed plugin format.

## Qualification

No claim of manufacturer appearance matching, photometry, real-world grain distributions, measured surface profiles, seamless mapping, built-in CAD body properties, native CPU/GPU equality, or verified save/reopen. **Native acceptance and premium visual qualification are pending.** All original v1–03b releases are immutable and preserved. No new plugin or installer specification is defined.