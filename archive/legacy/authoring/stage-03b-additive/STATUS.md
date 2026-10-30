# Stage 03b status — 25 October 2026

## Resource authoring and GitHub delivery: complete

The previously missing categories are now represented by actual generated and published resources: ABS from additional brands, photopolymer resins, SLS/MJF polymer powders, LPBF metals and bound-metal extrusion/sintering. This closes the missing-category list from stage 03; it is not an exhaustive claim about every commercial formulation or additive process.

| Category | Delivered references | Appearances |
|---|---|---:|
| ABS / additional FFF brands | Bambu Lab ABS V3, PolyLite ABS V5.6, UltiMaker ABS v5.00 | 60 |
| Photopolymer resins | Formlabs Durable V2, Flexible 80A, Elastic V1, Rigid FLRGWH01, Tough 2000 V2, High Temp V2 with separate mechanical cure conditions | 70 |
| Powder-bed polymers | EOS PA2200 Balance, PA1101, PA3200 GF, TPU1301; HP 3D HR TPU01 Balanced MJF | 20 |
| Metal AM | EOS 316L, Ti64, IN718 as-built/heat-treated, AlSi10Mg, MS1; Markforged 17-4PH as-sintered/H900/H1150 | 48 |

**24 condition-specific physical profiles, 208 sourced property records and 198 linked appearances.** Every appearance has both visual resources and a populated physical-reference record; unknown properties are not fabricated. The 40 closed transmission studies are additional representations of existing appearances, not 40 extra material identities.

## Completed verification

- Run [40186384837](https://github.com/0xlillith/solidcraft-render-catalog/actions/runs/40186384837), job `121147952619`: completed successfully.
- 21 numerical/data tests: PASS, with no skipped tests.
- Full generation: 50 map sets, 700 PNG maps at 2K/1K, 100 signed-mm height EXRs, 198 software previews.
- Official Khronos validation: 476 GLB/glTF files, zero errors and zero warnings (396 opaque coupon exports plus 80 closed-transmission exports).
- Independent full-output validation: PASS; includes physical links and snapshots, PNG/EXR, metric height/normal relationships, filtering, channels, preview receipts and coverage.
- Every resource ZIP was uploaded and downloaded by the publication job, then checked at archive and original-member SHA-256 level. The complete log contains `UPLOADED_AND_VERIFIED` for all six ZIPs and both manifests.

## Durable publication

Release: [additive-stage03b-20261025](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/additive-stage03b-20261025), published outside draft on 25 October 2026 at 11:00:00 UTC.

Frozen generated source: `90d05c24cfff31c560721839edefc00a4a9c3670`.

Six ZIPs total **1,816,876,971 bytes**: catalog/sources/previews, runtime maps, and four 2K master groups (FFF, vat resins, powder polymers, metal AM). Extract all ZIPs into the same empty parent directory and open `stage-03b-additive/index.html`. The catalog ZIP alone is sufficient to browse; editable glTF resources also need their adjacent map archives. GLB specimens embed texture bytes.

`PUBLICATION-MANIFEST.json`, `SHA256SUMS.txt` and `PUBLICATION-VERIFIED.json` are attached to the release. [Publication closeout](reports/PUBLICATION-CLOSEOUT.json) records the inspected GitHub run, source pin and archive inventory. This closeout reviews the completed run; it does not claim a second execution of the generator or another full download.

The post-snapshot [source interpretation notes](SOURCE-NOTES.md) take precedence for ambiguous printed supplier dates and describe the density limitations. They are kept in Git without rewriting the verified original archives.

## Separate acceptance gates remain open

Native SolidCraft rendering/mapping/persistence acceptance: **not run**. Premium visual qualification: **pending**. Software previews are not native GPU evidence; closed transmission assets carry authored, unmeasured optics. No exact density is borrowed when the selected source supplies only a bound, relative density or no verified absolute value. There is no automatic engineering-material or mass assignment.

The plugin/installer/integration standard is **undefined**, pending community discussion. The historical 345 candidate-linked / 303 unresolved physical-reference audit is unchanged. Earlier releases, upstream application code/CI and the installed application remain untouched.
