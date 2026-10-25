# Stage 03 status — 25 October 2026

## Authoring delivery complete and published

- **11 named FFF references**, **194 condition-linked physical-property records**, **280 visual variants**, **73 shared metric process map sets**.
- Generated and independently validated **1,022 PNG maps** (2K masters / 1K runtime), **146 float32 signed-millimetre height EXRs**, **280 GLB + 280 glTF/BIN specimens** and **280 filtered software previews**.
- **19 data/numerical regressions + 5 preview/filtering regressions PASS**. Full output validation PASS. Official Khronos validation: **560 files, zero errors, zero warnings**.
- Previews use the actual runtime map bytes, bilinear filtering and 2x linear-domain pixel integration. Each input/output hash is verified separately; no native-render claim.
- Source checkpoint: `1c53aa136cda376e43487cab15bddafc6ef99197`.
- Complete release: [printing-stage03-20261025](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/printing-stage03-20261025), published 2026-10-25 09:53:21 UTC.
- Resource-only run [40181067606](https://github.com/0xlillith/solidcraft-render-catalog/actions/runs/40181067606): **SUCCESS**. Five resource ZIPs and the manifests were uploaded, downloaded again and checked. Every original member of the **3,509-file** stage snapshot was SHA-256 verified before publication. `PUBLICATION-VERIFIED.json` is attached to the release.
- The five ZIPs total **3,444,469,327 bytes**. Extract together into the same empty parent directory; open `stage-03-printing/index.html`.
- The readable physical summary and supplementary audit are source-only follow-ups; they do not rewrite the original archive bytes. See [REPRODUCE.md](REPRODUCE.md) for the complete final pipeline including filtered previews.

## Remaining qualification

- Native SolidCraft mapping/filtering/CPU/GPU/persistence acceptance: **not run**.
- Premium visual qualification: **not qualified**. The previews are software authoring studies, not measured optics or native GPU acceptance.
- Printed-specimen conditions are not transferred to other layers, infill or postprocessing. Effective printed bulk density remains unknown; no mass model is invented.
- Plugin, autoinstaller and integration standard: **undefined**, pending community discussion.
- This tranche is selected FFF products, not all additive manufacturing. ABS, other suppliers, resins, powder and metal AM remain future work.
- Historical 345 candidate-linked / 303 missing-specific-reference looks remain open. Earlier releases, upstream SolidCraft and the installed application remain unchanged.
