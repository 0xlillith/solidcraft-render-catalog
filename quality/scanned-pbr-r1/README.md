# Quality Pass 01 — photographed/scanned PBR benchmark surfaces

This is an **additive, manually curated quality-baseline release**. It does not overwrite any historical procedural assets or claim that all 2,983 indexed entries are premium. Source and licensing remain separate from engineering physical-reference records; SolidCraft application import/plugin standards remain **undefined** pending community agreement.

## Eight curated, photographed CC0 references

**Wood:** white oak veneer, black walnut veneer, teak veneer, ash veneer.

**Construction/ground:** gravel concrete, pebble-embedded concrete, dry cracked mud, rocky gravel.

These are **actual photographic/PBR scans published by [Poly Haven](https://polyhaven.com)** under [CC0](https://polyhaven.com/license). Each includes original provider author names, stable slug, pinned **`files_hash`**, four-kilopixel original material maps where available, licensed source URLs, accurate recorded **photographed area in millimetres**, and SHA-256/MD5 integrity receipts. The catalog displays **Powered by Poly Haven**.

The producer's recorded real-world scan dimensions constrain UV scale; the generator does not stretch an arbitrary 30 mm grain texture to a 2.6 m concrete patch. All maps are photometric/photogrammetric source approximations, **not measured complex dielectric IOR or certified structural performance**. No source photographs are silently relicensed as original code.

## PBR exports

- Original high-resolution photographed diffuse and normal/roughness/height (when available) retained in `build/source-4k`.
- Runtime 2K sRGB albedo from **linear-domain** downsampling of 4K photographic data.
- Normal GL from source, renormalized after downsampling; DirectX Y inversion with explicit glTF tangent-basis contract.
- Roughness from source, metallic 0 for dielectric wood/concrete/soil, ORM R=255 (no synthetic AO), G=roughness, B=0.
- **No fake millimetre displacement amplitude**: original displacement map is retained as source data only when available; physical multiplier remains unknown.
- Flat and curved mapped metric coupons in **GLB** and editable **glTF/BIN** with correct documented physical area; paired source/rough/normal previews and offline gallery.
- Physical cards linked to *visual reference IDs*. Candidate USDA oak/walnut clean-wood 12%-moisture references are **not** treated as validated veneer product density; all structural values remain null pending actual grade/condition evidence.

Each source file is checked against Poly Haven's *pinned file-list hash* and its own supplied MD5, then our generated assets and whole release are SHA-256 verified. If upstream files change the job **fails rather than silently incorporating an updated texture**.

## Reproduction

From repository root, in a virtual environment with requirements and Node `gltf-validator@2.0.0-dev.3.10`:

```sh
python -m unittest discover -s quality/scanned-pbr-r1/tests -v
python quality/scanned-pbr-r1/tools/build.py --full
GLTF_VALIDATOR_MODULE=/path/to/node_modules/gltf-validator node quality/scanned-pbr-r1/tools/validate_gltf.cjs
python quality/scanned-pbr-r1/tools/validate.py
```

The source files and 4K assets download via Poly Haven's public **HTTPS API/CDN** from their original provider. External source, licenses and hashes remain in `manifest.json` and `data/appearance-records/`. On success this personal repository's resource-only pipeline publishes all archives with a signed-off verification receipt; never overwrite prior release assets.

## Real acceptance still needed

8 scanned materials are a **premium-reference benchmark for visual comparison**, not a certification of all existing materials. The real SolidCraft application still needs tested GPU/CPU shading, texture sampling, body-local UVs, resizing/mips, live preview and save/reopen; current Pegasus is offline. These native acceptance and visual/art-direction gates remain separate, not implied by glTF format correctness.

Read `../PREMIUM-FIDELITY-AUDIT-20261026.md` for the cross-pack findings and future remediation queue.
