# Authoring metadata schemas

[Asset descriptor](asset.schema.json) documents the common repository metadata.
The typed `definition.json` retains the source format of each resource family.
These schemas do not establish a SolidCraft package, importer or plugin contract.

`python tools/library/validate.py` checks the implemented semantic invariants:
identity, category membership, references, required dependency cycles, file paths,
generated inventory, attribution coverage and active navigation. Run
`python tools/library/catalog.py check` to verify deterministic generated output.
Consumers requiring full JSON Schema validation can use the published schema.

Adding a type requires a documented operation, representation requirements and
appropriate evidence. A future folder alone does not define that behavior.
