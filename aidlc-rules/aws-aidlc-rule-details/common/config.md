# Product configuration (`aidlc.config.yaml`)

Load this file at workflow start, together with the other common rules.
This file does **not** by itself change which stages run. Stage order is
owned by `core-workflow.md`. After F1 that includes the Operations stages
from `v1-operations` (Rules Validation, Deployment, Post-Deployment Testing).

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
python3 -m aidlc_validate config --root PRODUCT_REPO
```

Use **`python3`**. Do not assume a `python` command exists.

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
   - `design_validation.human_triggers` = the seven built-in triggers
   - `design_validation.separate_llm_reviewer` = `true`
   - `limits.max_rework_iterations_per_unit` = `3`
   - `limits.token_budget_per_unit` = `200000`
   - `limits.on_token_budget_exceeded` = `pause_and_ask_human`
   - `units.max_stories_per_unit` = `8`
   - `operations.docs.language` = `en`
3. Honor `gates.checks`: each `id` is a validator subcommand (`config`,
   `scope-in-vision`, `traceability`, `stories`, `units-dag`, `assumptions`,
   `export`). If the list is present, omitted ids are disabled. Unknown ids
   fail the config check. `severity: advisory` records findings without
   failing the command.
4. Keep the values for later stages. Do not treat the config as a reason to
   skip a recorded human gate (`reverse_engineering`, `vision_scope`,
   `inception_end`, `design_validation`, `build_and_test`, Operations
   checkpoints, Deployment opt-in, or `operations`).
