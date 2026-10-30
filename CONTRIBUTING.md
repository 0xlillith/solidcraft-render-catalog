# Contributing

Work on one resource or one coherent group at a time. Keep source definitions,
representations, attribution and acceptance evidence together so another person
can understand and reproduce the change.

## Find the right place

Start with [the complete index](INDEX.md). Before adding a record, search for an
existing identity or source reference. A new resolution, export format or preview
usually belongs to an existing asset as a representation. A different material
condition, visual treatment or reusable object may need a separate variant or ID.
See [the structure guide](docs/STRUCTURE.md) for the distinctions.

Use the shallowest suitable category under `assets/`. The folder is for browsing;
the stable ID identifies the asset. Preserve existing IDs when moving folders.
Use a new ID for a genuinely new identity and record its relationship to the
original. The catalog validator checks uniqueness and references.

## Improve an existing asset

1. Read `asset.json`, the existing definition, its attribution and any acceptance
   evidence. Identify the exact representation being changed.
2. Edit the individual source definition or recipe. Keep source units,
   conditions, unknown values and physical-reference meaning intact.
3. Write revised payloads under a new versioned location such as
   `authored/<revision>/`. Record their hashes, provenance and available evidence.
   Keep the original restoration receipt unchanged.
4. Update `entrypoints`, `previews` or `active_appearance` in `asset.json` as
   applicable. Maps belong to the selected appearance profile. The catalog
   derives its representation list from these references. A new software preview
   is not evidence that the application rendered the asset.
5. Rebuild the catalog and run the checks below. Review the resulting file list
   before committing.

Existing restoration tools refuse to overwrite changed working files. Do not
work around that check by replacing original hashes with those of an edited file;
retain the edit as a new revision instead.

## Add an asset

Create an individual folder and use an existing descriptor of the same semantic
type as a starting point. Complete each field from evidence rather than copying
another asset's facts. The descriptor and supporting records should identify:

| Information | What to record |
| --- | --- |
| Identity | Stable ID, readable name and semantic type |
| Classification | Useful family, process or creation-method facets and search tags |
| Source | Author or provider, exact source URL or reference, original ID and provenance |
| Rights | Applicable license or terms, required notices and any unresolved status |
| Definition | Editable source and the units or conventions needed to interpret it |
| Representations | File roles, resolution or fidelity, formats and exact availability |
| Relationships | Physical reference, derivation, example usage or other semantic links |
| Required resources | The files and references actually needed to use a representation |
| Evidence | What was checked, on which revision, with what consumer or tool |

Use [the repository descriptor schema](schemas/asset.schema.json) and validator
for field names and required structure. A placeholder category is not a reason
to invent a new runtime contract. Explain a proposed type before adding content that existing tools
cannot interpret.

Add editable attribution information in `credits.json`. Keep provider credits,
license text or links, original identifiers, relevant source conditions and
transformation notes. The attribution builder combines these additions with
preserved source records to generate `attribution.json` and `ATTRIBUTIONS.md`;
do not edit the generated files directly. Unstated third-party terms remain
unstated. A source link or supplier SKU is not permission to redistribute its
model, images or publication. Original contributions and third-party inputs
retain their own applicable terms.

### Record credits

This is a structural example. Replace the example names, URLs and source details
with verified information; use a license expression only when it actually
applies. Omit unknown fields instead of copying the example's claims.

```json
{
  "authoring": {
    "authors": ["Resource creator's credited name"],
    "license_expression": "MIT OR Apache-2.0"
  },
  "sources": [
    {
      "role": "payload",
      "id": "provider-asset-id",
      "title": "Imported texture source",
      "urls": ["https://example.org/texture"],
      "authors": ["Published source creator's name"],
      "license_expression": "CC0-1.0",
      "notice": "Preserve the source's required credit text, if any."
    },
    {
      "role": "reference",
      "id": "property-reference-id",
      "title": "Cited property reference",
      "urls": ["https://example.org/reference"]
    }
  ]
}
```

`authoring.authors` names the original contributors to this resource; source
authors are credited separately. The optional authoring license applies to those
original contributions, with the existing repository policy used when no more
specific original-contribution license is recorded. It does not relicense inputs.

A source's `role` is `payload` for imported content, `reference` for a cited
publication or factual reference, or `authoring` for an explicitly recorded
authoring source. Its `license_expression` and `notice` belong to that source.
Source URLs must use HTTP(S). Names and URLs use arrays, even for one item.
Source terms and original authors are never inferred from who maintains the
repository. Read the generated credits after rebuilding.

## Files and publication

Keep ordinary editable text and appropriate small payloads in Git. For large
originals and derived binaries, follow [STORAGE.md](docs/STORAGE.md): preserve an
exact receipt and verify the durable copy before treating an edit as backed up.
A filename, preview or URL alone does not prove the promised bytes are available.

Keep authoring scripts under `tools/`. Installing or opening content must not be
presented as permission to execute those scripts. Packaging and installer work
are separate from maintaining this source library.

## Regenerate and check

Run from the repository root with Python 3.11 or newer:

```sh
python tools/library/catalog.py build
python tools/library/catalog.py check
python tools/library/validate.py
```

The generated catalog, indexes and browser are navigation outputs. Edit source
records and rebuild them; do not make a correction only in a generated page.
The catalog build also regenerates individual and root attribution outputs.
For an attribution-only check, use `python tools/library/attributions.py check`.
Keep the original `extra.json` and historical evidence as preserved inputs; make
new classification edits in `asset.json`, source edits in `definition.json` or
its recipes, and credit additions in `credits.json`.

Check the index link, source links and selected preview for the affected resource.
Run relevant numerical, file or native acceptance only for the behavior changed,
and retain the exact scope of that evidence. Unknown physical values stay unknown;
a rendering check does not qualify engineering properties.

In a contribution description, state what changed, why, the affected IDs, the
checks performed and any resource still unavailable. Folder moves should also
identify the old and new paths and confirm that all stable references resolve.
