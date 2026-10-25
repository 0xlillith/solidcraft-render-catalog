# Source interpretation notes

These notes supplement the frozen stage03b snapshot at `90d05c24cfff31c560721839edefc00a4a9c3670`. They do not change numerical property values, grade identities, surface maps, portable specimens or validation results.

## Literal publication dates override normalized display labels

Two Formlabs cover dates are ambiguous when converted into ISO dates without an independently established locale. Preserve the **printed strings**, not the inferred ISO date in the original source title:

| Source ID | Exact printed revision date | Inferred label in the frozen snapshot that must not be used as an authoritative date |
|---|---|---|
| `durable-v2` | `10 . 07 . 2020` (Rev. 01; FLDUCL02) | `2020-07-10` |
| `tough2000-v2` | `10/06/2025` (Rev. 01; FLTO2002) | `2025-06-10` |

Both covers were visually rechecked on 25 October 2026. No day/month order is asserted here. Identify the exact numerical source using its source ID, manufacturer URL, resin code, revision number and printed date. The archived generation code reproduces its original title labels; this explicit clarification takes precedence when presenting publication dates. Do not silently overwrite a previously verified release to change metadata.

Primary references:
- Durable: https://formlabs-media.formlabs.com/datasheets/1801084-TDS-ENUS-0P.pdf
- Tough 2000 V2: https://formlabs-media.formlabs.com/datasheets/25011072-TDS-ENUS-0.pdf

## Reference density is not an automatic mass assignment

Every one of the 198 appearances has a populated, sourced physical profile. This is not a claim that every possible property is known. In particular:

- The selected original Rigid FLRGWH01 sheet does not establish an exact density or its equivalence to a subsequently renamed formulation.
- The selected AlSi10Mg and MS1 process sheets contain mechanical data but no verified absolute-density point for that process/condition.
- Markforged supplies relative density; the reference denominator needed for an independent absolute-density conversion is not supplied here.
- EOS 316L and IN718 density bounds remain bounds; they are not converted into point values.
- Resin liquid, cured/solid bulk, loose powder and finished-part densities remain separate quantities. Cure-schedule qualifiers are retained.

No substitute density, fictitious mass, isotropic elasticity tensor or mechanical performance of a visually edited finish is synthesized. This is deliberate data integrity, not an unlinked material record.

## Coverage and acceptance

ABS from three additional brands, photopolymer resins, SLS/MJF polymer powders, LPBF metals and bound-metal extrusion/sintering are all represented with actual generated resources. This closes the previous missing-category list, not every commercial product or manufacturing technology in existence.

Native SolidCraft acceptance, measured optical calibration and premium visual qualification remain separate. The 198 main previews are opaque surface studies. The 40 closed transmission assets have explicitly authored optical parameters and must be inspected in a renderer supporting their glTF material extensions; the opaque thumbnails are not transmission validation.
