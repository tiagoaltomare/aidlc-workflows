# Product configuration (`aidlc.config.yaml`)

Load this file at workflow start, together with the other common rules.
This file does **not** change which stages run or how they run in AI-DLC 1.0.1.
Stage behaviour stays as in `core-workflow.md` (Operations remains a placeholder
until a later phase of this fork).

## Locate

1. Product repository root = the workspace root of the **product** (not this
   rules repository, unless they are the same tree).
2. Config path: `aidlc.config.yaml` in that root.
3. Example and schema live in this fork: `docs/aidlc.config.example.yaml`
   and `scripts/aidlc-validate/schema/aidlc.config.schema.json`.

If the file is absent, continue with built-in 1.0.1 defaults. Do not invent a
config.

## Validate

When the file is present, validate it **before** any stage work by running the
shipped validator (non-zero exit means refuse):

```bash
python -m aidlc_validate config --root PRODUCT_REPO
```

Run that command with `PYTHONPATH` set to this fork's `scripts/aidlc-validate`
directory, or install the `aidlc-validate` package first.

The check proves:

- the file is readable YAML
- `schema_version` is exactly `"1"` (string)
- the document matches the JSON Schema for schema_version 1

**Refusal (workflow stops):**

- YAML cannot be parsed
- JSON Schema validation fails
- `schema_version` is missing or is not `"1"`

On refusal, tell the person the validator's message in one block, name the file
`aidlc.config.yaml`, and **do not start Workspace Detection or any later
stage**. Do not repair the file silently.

Unknown `schema_version` is the same class of refusal: stop, do not guess a
compatibility mode.

## Apply

On a passing check:

1. Read the YAML.
2. Apply schema defaults that the file omitted:
   - `design_validation.mode` = `hybrid`
   - `operations.docs.language` = `en`
3. Keep the values for later stages. In this phase they are recorded only;
   they do not change 1.0.1 stage gates.

Do not treat the config as a reason to skip a 1.0.1 human gate.
