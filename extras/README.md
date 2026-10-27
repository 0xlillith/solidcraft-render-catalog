# Individual editable extras

**Current owner decision, 27 October 2026: work on individual extras, not packs.**

Each resource has its own folder at `extras/<stable-id>/`. This is deliberately a
flat, provisional editing workspace. We are **not** deciding the final taxonomy,
package format, installer, plugin API or distribution grouping now.

The initial import contains **2,991 extras**: all **2,983** records in the previous
federated inventory plus **8** already published scanned-PBR reference materials.
Records include appearances, physical/scientific references, lights, environments,
setups, shots and quality references. They are not 2,991 distinct certified materials.

## Where to edit

```text
extras/
  MAT-001/
    definition.json     # independently editable source record
    extra.json          # identity, provenance and separate physical links
    FILES.json          # original file-level hashes and restoration locators
    recipes/            # editable numerical JSON recipes, tracked in Git
    provenance/         # historical receipts, not new quality approval
    README.md           # per-extra working notes
    files/              # independently writable original assets on Pegasus
  LUZ-001/
  ENV-001/
  element.029.cu/
  element.029.cu.metal-brushed/
  ...
```

Start with `definition.json`, its `recipes/` JSON and local working files. Keep
new individually versioned assets in `authored/` (not ignored by Git); verify
publication before calling a changed binary backed up. Keep historical evidence
in `provenance/` distinct from new acceptance. Work on one extra at a time; add
actual comparisons and acceptance results in that extra's
`validation/` folder. Unknown physics, source conditions, licences, original
scale/units and reference-only status must survive an appearance edit.

`FILES.json` is the immutable **original** restoration receipt, not a claim that
later hand-edited files still have the original hashes. Record improvements as
new versioned files and changes rather than silently changing an old receipt.
Legacy stage generators and old aggregate indexes remain historical inputs; they
do not automatically consume new per-extra edits. Any new/revised generator must
explicitly load that extra's edited definition, never overwrite it from a pack.

## Git and local files are different layers

**Git tracks individual definitions, references, file-level receipts, tests and
working guidance.** The large binary working copies under `*/files/` are restored
on Pegasus, independently copied (not hardlinked) and excluded from ordinary Git
commits. Their original exact bytes remain durably preserved in the existing
historical GitHub Releases. A new clone does not magically contain these binaries.

No new pack was created or published by this reorganization. Higher-resolution
2K/4K source-master archives that are not in the restored runtime/source deliveries
remain in the original Releases; runtime copies must never be relabelled masters.
Storage/publication of newly edited large binaries must be explicitly verified
before calling those improvements backed up. Conversation attachments and a
single workstation are not the durable destination for new work.

## Work without rebuilding an entire collection

```sh
python tools/extras/manage.py validate
python tools/extras/manage.py verify-files --id element.029.cu.metal-brushed
python tools/extras/manage.py restore --id MAT-001 --cache-root /path/to/archive-cache
```

The restoration tool supports multiple `--cache-root` and `--id` arguments.
`--download` explicitly permits fetching the **old** archive inputs when absent;
it never builds or publishes a ZIP. Existing edited files are refused, not reset.
A resource's historical relative file layout is preserved inside `files/` to keep
its glTF/BIN/image references together. `index.html` is an offline searchable
workbench; the individual JSON records remain usable without JavaScript.

## Provenance and unresolved decisions

`MIGRATION.json` records counts, source hashes and actual materialization scope.
`ARCHIVE-SOURCES.json` records the exact original archive checksums and URLs.
No prior release was modified. The independent native-quality worktree and its
unpublished improvements were not used as disposable input or overwritten.

Two different physical-reference entries used the original ID `c93200`.
The older reference retains that folder name. The alloy-stage record is stored as
`alloy.c93200.reference`, retains `source_id: c93200`, and its appearance links
resolve to that separate record. Their conditions/values were not merged.

The original source/licensing notices remain in `catalog/licenses/` and each
record's provenance. Scanned references retain their separate CC0/provider/source
receipts; supplier publications and scientific facts are not blanket relicensed.
No font files are redistributed. Native SolidCraft acceptance and premium optical
quality remain separate, source-pinned gates. This layout change does not pass them.

## Integrated follow-up

The prepared quality work is resolved in [the reconciliation report](../quality/reconciliation-20261027/README.md). Accepted maps are tracked under each `authored/` folder, with exact receipts; rejected stone candidates are not active. Use `tools/extras/improve.py --id ...` to rebuild one selected extra. This is not blanket premium qualification.
