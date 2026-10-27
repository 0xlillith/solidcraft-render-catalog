# Pending extras — reviewed and reconciled

Owner request, 27 October 2026: identify outstanding improvements, integrate useful
work with individual extras, and remove obsolete/unhelpful candidates from the
active plan. **No new packs, no final package taxonomy, no SolidCraft core changes.**

## Decisions

| Pending work | Resolution |
|---|---|
| 384 wood finishes | Added actual per-finish maps under each `extras/wood.*/authored/native-1024-r1/`. Color/roughness/normal factors are baked exactly once; clearcoat remains explicit. Original procedural grain still is not a botanical scan. |
| Eight scanned materials | Already-existing `scan.*` identities enriched with source authors/physical qualifications and explicit 1K native profiles. Original 2K/4K files remain intact; this compatibility profile is not a claimed master-resolution upgrade. |
| 168 earth/masonry previews | Corrected physical-height slope scaling, orientation and linear-color math; original source fields unchanged. Labelled software previews, not native screenshots. |
| Eight coarse stone replacements | **Rejected as active replacements.** Inspected native comparisons remain too polygonal/isolated. More visible stones are not necessarily better realism. They are absent from active per-extra pointers. |
| Five wood data recoveries | Exact semantic duplicates of published data; retained in recovery history, not treated as improvements. |
| QA tools and regressions | Useful channel math, local native client, recipe fingerprinting and metric tests integrated; bulk stage builders/collectors replaced with `tools/extras/improve.py --id ...`. |
| PR #7 pack publisher/workflow | Not imported. Valuable source information has been reconciled; the old PR can be closed as superseded, not falsely described as a wholesale merge. |
| Old stage branches | Already behind `main`; nothing additional to integrate. #8's branch has identical trees after squash. |

## Evidence and limits

`integration-inventory.json`, `accepted-binaries.json`, `decisions.json` and
`fresh-workflow-validation.json` contain the source-pinned details. Useful new
maps and previews are ordinary individually tracked Git files, **not** ignored
local-only replacements and **not** new archive releases. Existing `files/` baseline
copies and `FILES.json` restoration receipts remain unchanged.

Five fresh **SolidCraft 0.24.0 / hardware Vulkan** tests were run headlessly through
MCP from the integrated per-extra paths. Each includes flat/curved coupons, 32
samples/pixel, PNG identity verification, native save/reopen, unchanged physical
measurements and exact external-map recapture preflight. Six independent authoring
scenarios reproduced original candidate output hashes. The user's live document
and the separate Drawings agent were not modified.

The previous 607 native receipts are retained separately as historical evidence.
Their corresponding local PNG/model/input hashes were verified. Many earlier
receipts do not contain a whole-recipe fingerprint; these are not current cache
hits, and their `full_optics_supported` text must be read only in their explicitly
bounded coupon scope. Original heavy proof images stay in the evidence workspace;
five fresh proof images/models and selected rejected A/B comparisons are included
here. No blanket premium, measured optical, engineering or full UI acceptance.

## Work on one extra

```sh
python tools/extras/improve.py --id wood.red-alder.plain-sawn.gloss-varnish --out NEW_DIRECTORY
python tools/extras/improve.py --id scan.white_oak_veneer --out NEW_DIRECTORY
python tools/extras/improve.py --id earth.quikrete-concrete-1101.exposed-stones --metric-preview --out NEW_DIRECTORY
python tools/extras/manage.py validate
```

Restore baseline sources first where necessary. Each rebuild reads that extra's
edited definition rather than regenerating the old aggregate catalog; original
source hash mismatches and existing output directories refuse. Newly generated
outputs require their own acceptance; a successful rebuild alone is not a native
rendering or appearance approval. Dependencies are listed in
`tools/extras/quality/requirements.txt`.

The old QA checkout is retained as a tagged source checkpoint, not as another
unexplained set of pending changes. Recovery preserves the rejected trials without
installing them or advertising them as improvements.

## Source checkpoint

The original pending source is now recoverable at tag `archive/native-qa-source-20261027`, commit `ed36f3d427cb203492cb3065ae3e7914a81390fd`. All 17 source file hashes were checked before checkpointing and the remote tag was verified. The former dirty QA checkout is clean and explicitly archived, not an unexplained second line of pending improvements.
