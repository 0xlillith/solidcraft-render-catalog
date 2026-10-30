# Stage 04 earth and masonry — published resource authoring

Status date: 2026-10-26. **Resource authoring and binary publication: completed and independently verified.** This does **not** mean native SolidCraft acceptance or premium visual qualification.

## Exact delivered scope
- 28 condition-specific source/identity profiles across soils (10), aggregates (5), cementitious products (5), gypsum (4) and pastes (4).
- 37 referenced physical-property fields: 23 contain documented numerical values/ranges; **14 deliberately remain null**. Absent engineering data are not zero, and do not qualify as measured properties.
- 168 illustrated appearance variants, each linked to a physical profile, with six authored finish studies per reference.
- 30 shared metric mapsets, each with 2K master and 1K runtime maps, for 420 PBR PNG files and 60 signed-height float32 EXR files.
- 168 offline software previews and 336 self-contained GLB/editable glTF files showing flat and curved specimens.

## Reproducibility and release verification
- Resource-only GitHub run [40329658949](https://github.com/0xlillith/solidcraft-render-catalog/actions/runs/40329658949): **success**.
- Nine data/numerical tests: **PASS**.
- Official Khronos glTF validator: **336 files, zero errors, zero warnings** after explicit tangent/vertex-buffer export correction.
- Independent PNG/EXR/dimension/CRC/height/normal/ORM/physical-reference checks: **PASS**.
- Exact frozen generated-source commit: `83618ee2a32b51ba53330ff3129fe4c67470954c`.
- [Release `earth-masonry-stage04-20261026`](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/earth-masonry-stage04-20261026): **published**, seven resource ZIPs, **3,235,732,036 compressed bytes**; the upload/download integrity process verifies each archive and every original ZIP member's SHA-256. Check `PUBLICATION-MANIFEST.json` and `PUBLICATION-VERIFIED.json` in the release.
- Original catalog v1 and prior stages preserved. Index adds 196 records (28 physical profiles plus 168 appearances), bringing the federated inventory to **2,711 records**.

## Unfinished, explicitly separate gates
- Native SolidCraft application acceptance (CPU/GPU, texture scale/placement, save/reopen): **NOT RUN**, because Pegasus was unavailable.
- Premium visual qualification and any measured real-world reflectance/surface roughness: **NOT QUALIFIED**.
- Finite patches are **not seamless**; generated illustrations are **not measured profilometry, mechanical certification or native rendered images**.
- A soil density range does not identify a site specimen; cement particle density is not powder bulk density; a concrete mix's cured compressive strength does not transfer to generic architectural concrete; wet gypsum density differs from cured dry density.
- The historical 345 reference-candidate + 303 missing-reference appearances remain open.
- Plugin, installer and SolidCraft integration standards are **not defined**, pending community discussion.

No changes were made to upstream SolidCraft code/CI or installed applications.
