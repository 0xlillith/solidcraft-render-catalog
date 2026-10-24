# SolidCraft Render catalog — authoring v1

Private personal resource repository. **The complete binary collection is in the release**, not in Git's automatic Source code ZIP.

## Get the complete catalog

Open [catalog-v1-20261024](https://github.com/0xlillith/solidcraft-render-catalog/releases/tag/catalog-v1-20261024).
Download all `catalog-v1-20261024-*.zip` assets and extract them into the **same empty parent directory**. Each ZIP contains a disjoint part of `Render-Catalog-Complete-20261024-v1/`; no concatenation is needed. Open `index.html` inside that folder.

A restoration helper and release SHA-256 manifest are included in `distribution/`. The repository is private: authenticate with your authorized GitHub account to download.

For only the uniform native appearance libraries, download `Native-Appearance-Libraries.zip` instead. This small optional convenience archive is also preserved inside the complete collection.

## Collection

| Collection | Entries |
|---|---:|
| Main procedural materials | 600 |
| SELENE appearance baselines | 48 |
| Lighting rigs | 280 |
| Environment/context realizations | 280 |
| Scene, studio and environment setups | 97 |
| Quality profiles | 10 |
| SELENE shot studies | 12 |
| Physical reference profiles | 59 |
| **Indexed entries** | **1,386** |

Formats include PNG, EXR, Radiance HDR, glTF/GLB, OBJ/MTL, `.solidcraft`, native version-2 appearance libraries, JSON recipes, HTML and CSV. Full source catalogs, generators, original resources, provenance, diagnostic evidence and local tool dependencies are retained in the resource archives. Editable text is mirrored byte-for-byte in `catalog/` for browsing and review.

## Scope and provenance

This is **complete source-catalog file coverage**, not certification that every optical, physical, spectral, motion or semantic requirement is implemented. Native v2 appearance catalogs hold uniform PBR values; arbitrary maps and richer variants remain separate. Read [the original authoring guide](catalog/README.md) for the exact exclusions.

The original resource README and `PACK-RECEIPT.json` are immutable historical delivery records: their statements about local-only status describe the moment of generation. This separate repository/release records the subsequently authorized publication without rewriting the original bytes or hashes.

Source application: `9e6e0b8df130f342e15ebe988b7211d1482a44c2`. No upstream repository, application installation or CI workflow is modified by this publication. The original catalog on Pegasus is preserved.

New original authoring retains MIT OR Apache-2.0 notices in `catalog/licenses/`. Third-party tool dependencies and physical-source claims retain their own original licences and metadata; no blanket relicensing is implied.
