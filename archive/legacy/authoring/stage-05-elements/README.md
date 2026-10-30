# Stage 05 — all 118 pure chemical elements

**Scientific-reference collection and original procedural surface studies**, not a periodic-table simulator, chemistry safety manual, SolidCraft plugin, application importer, or engineering grade material catalog.

## Identity and physical sources

The `data/pubchem-reference.json` snapshot stores **all 118 elements**, sorted by atomic number, with names, symbols, group, standard-state labels, reported atomic masses, selected atomic properties, and reported melting/boiling/density summaries. Primary source: [NIH/NLM PubChem Periodic Table JSON](https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/JSON) and its [density units page](https://pubchem.ncbi.nlm.nih.gov/ptable/density/); consulted **26 October 2026**. [NIST atomic-property reference](https://www.nist.gov/pml/periodic-table-elements) is listed for scientific context; NIST is not falsely claimed as the source of every physical datum. The source page and individual element pages contain further citations.

Source-reported **density g/cm³** is converted to kg/m³ by ×1000, retained with its original string and a **missing-condition qualifier**. Density is *reference-only* and **cannot be silently used to assign mass to a CAD body**: temperature, pressure, allotrope, isotope, preparation, purity and physical state are not fully identified in the summary. Likewise, atomic-mass strings for radioactive/synthetic elements are not uncritically treated as measured standard atomic weights. Missing entries stay **null**, not zero.

All **118 elements** are covered by an offline scientific identity card. **77 solid elements** get two original illustrative PBR appearance studies each (**154 appearances**, with six shared finite surface-map patterns). **Eleven gases, two liquids, and 28 rare/short-lived/predicted-state or otherwise limited-sample elements are reference-only**, without invented solid objects. The filtered categories are deliberate authoring policy, not a chemical statement that other elements cannot exist in condensed phases.

Elements are distinct from alloys, oxides, compounds, commercial purities, crystal forms or homogeneous engineering designations. CPK molecular-color conventions are **not** used as macroscopic PBR coloration. An illustrative yellow gold surface or dark graphite-like carbon study is **not measured reflectance**, an identified isotope/allotrope, or a guarantee of current surface condition.

## Generated resources

For the 77 solid study candidates: two finishes chosen from polished/brushed metal, cleaved/matte metalloid, or crystalline/granular nonmetal. Six deterministic **30 × 30 mm**, non-seamless surface maps with **2K masters and 1K runtime versions**: color modulation, GL/DX normals, roughness, metallic, ORM, 16-bit height PNG and signed millimetre EXR. Normal vectors derive from finite physical-height gradients and are recalculated after linear downsampling.

Each appearance contains self-contained **GLB**, editable **glTF/BIN**, an `appearance.json` pointing at its science record, and software-rendered preview with a prominent non-native qualifier. The portable geometry has mapped flat and curved coupons, in metres. Every one of the 118 source elements has a separate labelled scientific card, and `index.html` is an offline gallery.

All sample RGB/roughness/metalness values are original illustrative choices, **not spectroscopic measurements**. Bulk models for gases, liquid transmission, exotic allotropes, crystal optics, radiation or surface oxidation are not faked. No reactions, handling guidance, radioisotope sourcing or safety advice are provided.

## Reproduction

The stage is source-complete and requires no online fetch during generation. From the repository root:

```sh
python -m venv .venv
.venv/bin/pip install -r authoring/stage-05-elements/requirements.txt
.venv/bin/python -m unittest discover -s authoring/stage-05-elements/tests -v
OPENCV_IO_ENABLE_OPENEXR=1 .venv/bin/python authoring/stage-05-elements/tools/build.py --size 2048
npm install --prefix /tmp/element-gltf-validator --ignore-scripts --no-audit --no-fund gltf-validator@2.0.0-dev.3.10
GLTF_VALIDATOR_MODULE=/tmp/element-gltf-validator/node_modules/gltf-validator node authoring/stage-05-elements/tools/validate_gltf.cjs
OPENCV_IO_ENABLE_OPENEXR=1 .venv/bin/python authoring/stage-05-elements/tools/validate.py
```

Only a full 2K/1K generated and validated build is eligible for publication. The personal repository's resource-only publish helper creates a draft release, uploads all ZIPs, re-downloads each, checks archive and each member SHA-256, and only then publishes.

## Acceptance and exclusions

**Native SolidCraft application tests and premium visual calibration are separate, unrun gates.** Generating a valid GLB does not establish CPU/GPU parity, body-local mapping, material picker UX, save/reopen correctness, or measured optical properties. Never mark a scientific reference as engineering certified because it has a color and density number.

No plugin specification, autoinstaller API, version negotiation, native file extension or SolidCraft upstream CI/code change is made by this stage. Existing releases remain unchanged. New code/assets follow the original MIT OR Apache-2.0 source policy; source facts retain their attribution and terms.
