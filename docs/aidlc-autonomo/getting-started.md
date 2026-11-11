# Getting started — autonomous fork

This branch (`feature/aidlc-autonomo`) is the v1-based autonomous fork.
Inception and Construction generate and continue. Only the **named gates**
stop for a person. Official product docs are a Docusaurus site generated
**in the product repository** (`docs-site/` by default).

English is the language of the new rules, the validator, and this guide.

## How a pilot starts a cycle

1. **Product repo** is the workspace (greenfield empty tree, or brownfield
   codebase). Do not treat the rules fork as the product.
2. **Copy `aidlc.config.yaml`** into the product root from
   [`docs/aidlc.config.example.yaml`](../aidlc.config.example.yaml). Edit
   `project_type`, `depth`, and `scope.current_path` if needed.
3. **Point the coding agent at the rules** (this fork's `aidlc-rules/`):
   the first file to load is `aidlc-rules/aws-aidlc-rules/core-workflow.md`.
   That file loads `common/welcome-message.md` once, then
   `common/process-overview.md`, `common/config.md`, and the rest.
4. **Install the validator** (from this fork, not from the product):

   ```bash
   python3 -m pip install -e /path/to/aidlc-workflows/scripts/aidlc-validate
   ```

   Or set `PYTHONPATH` to `scripts/aidlc-validate`. Always invoke
   **`python3`** (do not assume a `python` command exists):

   ```bash
   python3 -m aidlc_validate config --root /path/to/PRODUCT_REPO
   ```

5. **Give the agent the user request** (what to build this cycle). The
   agent runs Workspace Detection, then the rest of `core-workflow.md`.
6. **Answer only named gates and blocking questions.** Non-blocking
   questions are written to a question file and copied to
   `aidlc-docs/assumptions.md`; the run continues.

### Named gates

| Gate                      | Stops after                                                                         |
| ------------------------- | ----------------------------------------------------------------------------------- |
| `reverse_engineering`     | Reverse Engineering (brownfield)                                                    |
| `vision_scope`            | Vision, Tech Env, feature catalog, scopes                                           |
| Extension opt-in          | Requirements Analysis (blocking question)                                           |
| `inception_end`           | Inception package                                                                   |
| `design_validation`       | Per-unit design, when hybrid triggers fire                                          |
| `build_and_test`          | Build and Test (door into Operations)                                               |
| v1-operations checkpoints | Rules Validation / Deployment / PDT when those stages **run**                       |
| Deployment opt-in         | Asked **before** infrastructure-design artifacts if the deployment extension is off |
| `operations`              | Docusaurus export; then mark delivered features                                     |

### Where files live

| Thing              | Location                                                             |
| ------------------ | -------------------------------------------------------------------- |
| Config             | Product root `aidlc.config.yaml`                                     |
| Cycle artifacts    | Product `aidlc-docs/`                                                |
| Official docs site | Product `docs-site/` (generated; not read from this fork at runtime) |
| Validator          | This fork `scripts/aidlc-validate/`                                  |
| Rules              | This fork `aidlc-rules/`                                             |

### Depth

`depth: minimal` still requires the **complete Vision structure** (every
required section). Minimal means shorter prose per section, not omitted
sections. Same idea for other stages: all defined artifacts, adaptive
detail.

### Units

When User Stories ran, Units Generation **must** produce at least one
`UNIT-` record, an acyclic DAG, and a story map. A single simple unit is
valid. Skip Units Generation only when User Stories was also skipped.

### Extensions

At start, load only `*.opt-in.md` (heading `## Opt-In Prompt` or
`## Question`). Do not enforce full extension rules until Requirements
Analysis records opt-in. Opted OUT means that prompt's skip/No option
(B, C, or D — whatever letter the file offers). Do not assume the skip
letter is always D.

### AGENTS.md

If a framework scaffold (for example `create-next-app`) writes
`AGENTS.md`, merge it with the AI-DLC pointer to `core-workflow.md`.
Never replace the AI-DLC file. See `common/agents-md.md`.
