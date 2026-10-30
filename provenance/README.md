# Provenance and identity mapping

[The layout migration](layout-migration-20261030.json) maps every original resource
folder to its current location and records the original definition hashes and
source commit. Paths can change while the IDs remain stable.

Each asset retains `extra.json`, `FILES.json`, source recipes and its original
provenance. Generated [attribution records](../ATTRIBUTIONS.md) resolve recorded
sources without rewriting the originals. Historical stage registries remain in
[the archive](../archive/README.md).

The migration record documents a particular reorganization. Its definition hashes
are not a prohibition on later reviewed improvements to the editable definitions.

## Recovered source registries

[Wood Handbook sources](source-registries/wood-handbook-2021-sources.json) preserves
the two source records that existed as a literal dictionary in the original wood
authoring script. They were extracted with `ast.literal_eval` without executing
that script. Each record retains the original script path, assignment, line
location and SHA-256 hash. This makes the published authors, document locators and
rights notes available to the attribution builder without changing the originals.
