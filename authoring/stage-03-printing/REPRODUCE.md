# Full production reproduction sequence

This supplements the initial README example with the final filtered-preview steps. It reproduces source checkpoint `1c53aa136cda376e43487cab15bddafc6ef99197`; this documentation does not replace or rewrite its generated archive bytes.

Run in an isolated Python environment with `requirements.txt`, Node and the official `gltf-validator@2.0.0-dev.3.10`. From this stage's directory:

```sh
python tools/data.py
python tests/test_stage.py
python tests/test_previews.py
python tools/build.py --size 2048
python tools/render_previews.py
GLTF_VALIDATOR_MODULE=/path/to/node_modules/gltf-validator node tools/validate_gltf.cjs
python tools/validate_stage.py
python tools/validate_previews.py
```

`build.py` writes initial draft thumbnail studies. **They are not the production gallery until `render_previews.py` has replaced all 280 from the actual 1K runtime map bytes.** The final producer uses bilinear filtering, 2x pixel integration in linear space before tone mapping/sRGB and independently tinted diffuse/untinted dielectric specular. `validate_previews.py` requires all 280 image receipts to match their exact input maps and output bytes.

Only after every step passes may the existing owner-only resource publisher archive, upload and download-verify this stage. Native SolidCraft acceptance, printer process qualification and premium visual review remain separate gates. This is not a plugin or installer specification.

The optional `data/physical-summary.csv` is a readable convenience index added after the generation checkpoint. Every value is subordinate to the full conditions, units, orientation and reported spread in `physical-profiles.json`. Material-reference density must not be used as the effective density of an infilled printed part without an appropriate model or measurement.
