# Automatic checks

Run these with the shipped validator
(`python3 -m aidlc_validate CHECK --root PRODUCT_REPO`). Use **`python3`**.
Do not assume a `python` command exists. An LLM-only review
must not self-approve: if there is no executable check, escalate to the
person.

Write a short result under `aidlc-docs/checks/<check-id>.md` (pass / fail /
advisory, command, exit code).

| id                     | Command           | When                                                | Default severity |
| ---------------------- | ----------------- | --------------------------------------------------- | ---------------- |
| `scope_in_vision`      | `scope-in-vision` | After scope breakdown and at `vision_scope`         | blocking         |
| `traceability`         | `traceability`    | After Requirements, Stories, Units; `inception_end` | blocking         |
| `story_standard`       | `stories`         | After User Stories (if the stage ran)               | blocking         |
| `units_dag`            | `units-dag`       | After Units Generation (if the stage ran)           | blocking         |
| `assumptions_complete` | `assumptions`     | At `inception_end` (and whenever the file is asked) | blocking         |
| `export`               | `export`          | After Docusaurus export                             | blocking         |
| `config`               | `config`          | Workflow start, if `aidlc.config.yaml` exists       | blocking         |

`vision_tech_consistency` is inspected from the artifacts (stack/allow-lists
respected). It is not a separate validator subcommand in this phase.

Severity comes from `gates.checks` in `aidlc.config.yaml`. `blocking` means
do not cross the next stage boundary (or the phase-end gate) until the check
passes or the person decides at that gate.
