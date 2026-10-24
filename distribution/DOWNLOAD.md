# Restore the complete Render catalog

Repository: 0xlillith/solidcraft-render-catalog (private). Release: catalog-v1-20261024.

Download all seven `catalog-v1-20261024-*.zip` files and extract them into the same empty parent folder. They are independent ZIPs containing disjoint files of `Render-Catalog-Complete-20261024-v1/`. Do not concatenate them. Open `index.html` in the restored folder.

For automatic authenticated download and file-by-file verification, clone the source repository and run:

```text
gh repo clone 0xlillith/solidcraft-render-catalog
cd solidcraft-render-catalog
python distribution/restore_catalog.py --destination restored
```

The helper does not install software, execute authoring scripts or modify SolidCraft. It refuses to overwrite different existing content. Already equal files are preserved. `--offline --archive-dir <folder>` uses previously downloaded ZIPs; `--verify-only` checks without extracting.

`CATALOG-FILES.json` records every original file. `RELEASE-ARTIFACTS.json` records each resource ZIP. `RELEASE-SHA256SUMS.txt` covers all initial release assets other than itself. Native command recipes retain their original explicit Pegasus paths: read the catalog README before replaying them elsewhere. Self-contained native designs and GLB files do not require those original paths to open.

The small `Native-Appearance-Libraries.zip` is optional for standalone uniform-PBR library import; it is not the full texture/scene collection. GitHub's automatic Source code archives are not the complete resource download either.
