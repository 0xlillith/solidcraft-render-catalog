# Library organization verification — 30 October 2026

The library was reorganized from published commit
`740b1f1fba211d7ffcd563bddac187b907b15955` in an isolated worktree. Unrelated
unpublished work was not incorporated or rewritten.

## Verified scope

- All **2,991 resource IDs** and original definitions are preserved.
- All **32,068 moved original Git blobs**, totaling **1,381,239,298 bytes**, match
  the original commit exactly. The check uses Git blob hashes, not filenames alone.
- The original receipts retain **40,383 file records**. The existing authoring
  validator separately verified **2,128 tracked authored files** against their hashes.
- The complete index covers all resources through **98 family pages**, individual
  resource pages, category guides, curated collections and the offline browser.
- All **11 categories** are present in Git; **7** are prepared for future content.
- Every resource has `ATTRIBUTIONS.md` and `attribution.json`. The credit index
  contains **121 source/role records**, with **0 unresolved source identifiers**.
  Missing authors or unstated license terms remain explicitly unspecified.

The [validation report](validation.json) records identity, navigation, advertised
payload digest and migration-preservation checks. Generated output passed the
read-only consistency check after rebuilding. The regression suite passed all
**38 tests** on Linux, covering attribution, restoration, stable path resolution,
search/filter/pagination behavior and catalog completeness. The Windows run
passed its applicable tests; the directory-symlink test requires a privilege not
available there and passed on Linux.

The [browser check](browser-qa.json) also passed in an isolated Chrome instance.
It exercised the real DOM at a 390-pixel viewport, a scanned-resource filter,
clearing filters, pagination, an empty planned category and source-author search.
No horizontal overflow was observed. Desktop and narrow layouts were inspected.

## Reproduce

From the repository root, with Python 3.11 or newer:

```sh
python tools/library/catalog.py check
python tools/library/validate.py
python -m unittest discover -s tools/library -p 'test_*.py'
```

`python tools/library/validate.py --migration` additionally compares the migrated
originals with the recorded baseline. It is a historical preservation check;
later intentional source edits may need their own evidence instead.

## Boundaries

This work checks organization and traceability. It does not add new native
rendering acceptance, engineering-property qualification or an installer
contract. Existing sample evidence retains its original scope.

The six historical release publishers are archived. Existing release payloads
remain available because some unique original bytes still depend on them. No new
pack was built and no release was deleted. The repository remains at its personal
GitHub location; the future Tangency repository was not changed.
