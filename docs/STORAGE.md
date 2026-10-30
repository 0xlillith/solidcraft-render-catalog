# Storage and restoration

An asset's editable definition, original bytes, new representations and previews
have different storage needs. The catalog should state which of them exist and
where their exact bytes can be obtained.

## What is stored where

| Content | Storage and responsibility |
| --- | --- |
| Descriptors, definitions, recipes and editable credits | Tracked in Git and reviewed with the asset |
| Authored files already tracked in Git | Available in a normal clone; retain their receipts |
| Original working files under `files/` | Restored separately, normally ignored by Git |
| Original release payloads | Existing immutable releases and member-level restoration receipts |
| New large binaries | A deliberately chosen durable location, with exact hashes and verified availability |
| Generated catalog, indexes, browser and attribution | Rebuildable outputs committed with source changes |
| Temporary downloads and archive caches | Disposable after durable sources and receipts are verified |

A normal clone contains only the tracked files. GitHub's automatically generated
source archive has the same limitation: it is not the complete historical binary
library. Preview availability does not imply that runtime or master files are
present locally. The published catalog reports repository availability separately
from historical restoration. Restoring an ignored `files/` directory on one
workstation does not mark those bytes as shipped in the repository. Read each
representation's role and availability; a single available file does not establish
that all alternate resolutions or exports are present.

Some preserved provenance paths are long. On Windows, prefer a short checkout
location. If Git reports `Filename too long`, enable long-path handling for that
checkout with `git config core.longpaths true` before retrying the operation.
The original nested provenance is retained to preserve its receipts and links.

## Restore one existing asset

Use its stable ID from [the index](../INDEX.md). The resolver finds the current
folder, so the command does not depend on a remembered category path.

From the repository root:

```sh
python tools/extras/manage.py restore --id MAT-001 --cache-root /path/to/archive-cache
python tools/extras/manage.py verify-files --id MAT-001
```

Supply an existing cache location suitable for your system. The tool can search
multiple `--cache-root` locations and accept multiple `--id` arguments. To fetch
missing historical inputs from their recorded release URLs, explicitly permit
downloads:

```sh
python tools/extras/manage.py restore --id MAT-001 --cache-root /path/to/archive-cache --download
```

Selecting one asset limits which members are restored, but may still require
fetching a large historical archive. This is restoration of existing published
content; it does not generate a new pack.

The tool checks archive and member hashes, preserves member layouts, creates
independent working files and refuses to overwrite modified files. An existing
identical file can be reused. Inspect any incomplete download or changed working
file before retrying; do not erase an edit merely to make restoration pass.

`verify-files` compares restored originals with their original receipts. Missing
files in a metadata-only clone are expected until restored. Later authored
representations must be checked against their own receipts.

## Preserve new work

Keep the original `FILES.json` and historical evidence unchanged. Store revised
outputs in a new versioned `authored/<revision>/` location and record the source
revision, transformation, file roles, hashes and sizes. Update the descriptor to
select the new representation explicitly.

Before treating a new large output as preserved, verify the exact bytes in its
durable destination. A receipt without an accessible payload, a workstation-only
file or a conversation attachment is insufficient. When the destination is a
release or other remote store, a download-and-hash check establishes that the
published bytes match the recorded output.

Retain unique historical bytes until an equivalent durable copy and all required
origin mappings are verified. A reorganized folder tree alone does not replace
original archives. Moving or renaming content must also update path resolvers and
references; it must not change an asset's stable ID.

## Keep representations honest

Record whether an output is a runtime map, high-resolution master, model export,
reference image, software preview or native-render evidence. Record texture
resolution, physical scale, color-space and channel conventions where relevant.
Restoring a smaller runtime image does not recreate a missing master.

A representation's acceptance record should identify the input revision or
hashes, consumer and version, tested operation and result. Structural checks,
visual review and engineering-property verification answer different questions.
One accepted representation does not automatically qualify every version of the
asset or every record in its family.

## Future installation

This repository layout describes authoring and preservation. A future installed
library should keep immutable versions separate from editable sources, with
application-specific storage and update behavior defined by its consumer.
Current folder names and restoration receipts are not an installer contract.
