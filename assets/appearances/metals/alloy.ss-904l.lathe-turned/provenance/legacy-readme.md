# 904L plate reference / Lathe-turned face

**Extra:** `alloy.ss-904l.lathe-turned`
**Kind:** `material_appearance`

Edit `definition.json` and the numerical JSON in `recipes/` for this independent extra. `extra.json` retains identity,
provenance and separate physical-reference dependencies. No density, engineering
condition or qualification is changed by this reorganization.

## Local working files

`files/build/materials/alloy.ss-904l.lathe-turned/material.glb`
`files/build/materials/alloy.ss-904l.lathe-turned/material.gltf`
`files/build/materials/alloy.ss-904l.lathe-turned/preview.png`

These paths are in the independently editable `files/` folder on Pegasus, not
inline GitHub attachments. Restore on another checkout using `FILES.json` and
`tools/extras/manage.py restore --id alloy.ss-904l.lathe-turned --cache-root YOUR_CACHE`.
Existing edited files are never overwritten. The original relative paths are
retained so glTF dependencies stay intact. No hard links are used.

## Provenance and status

Original collection: `stage-02-alloys`. Historical source:
`alloys-stage02-20261025`. Full source record and qualifiers are in the definition.
The original material-stage inputs and releases remain recoverable.

This is a directory migration, not native acceptance or premium visual approval.
Record new improvements and exact-source tests in `CHANGELOG.md` and `validation/`.
Higher-resolution original masters remain in the historical releases where not
present in this runtime workspace. Packaging and final grouping are deferred.
