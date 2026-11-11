# Automatic checks

Run these with the shipped validator
(`python3 -m aidlc_validate CHECK --root PRODUCT_REPO`). Use **`python3`**.
Do not assume a `python` command exists. An LLM-only review
must not self-approve: if there is no executable check, escalate to the
person.

Write a short result under `aidlc-docs/checks/<check-id>.md` (pass / fail /
advisory, command, exit code).

| id                 | Command           | When                                                | Default severity |
| ------------------ | ----------------- | --------------------------------------------------- | ---------------- |
| `config`           | `config`          | Workflow start, if `aidlc.config.yaml` exists       | blocking         |
| `scope-in-vision`  | `scope-in-vision` | After scope breakdown and at `vision_scope`         | blocking         |
| `traceability`     | `traceability`    | After Requirements, Stories, Units; `inception_end` | blocking         |
| `stories`          | `stories`         | After User Stories (if the stage ran)               | blocking         |
| `units-dag`        | `units-dag`       | After Units Generation (if the stage ran)           | blocking         |
| `assumptions`      | `assumptions`     | At `inception_end` (and whenever the file is asked) | blocking         |
| `export`           | `export`          | After Docusaurus export                             | blocking         |

Stack and allow-list consistency is inspected from the artifacts. It is not a
separate validator subcommand.

`gates.checks` in `aidlc.config.yaml` is a whitelist of these ids. An omitted
id is disabled (`skipped`). `blocking` means do not cross the next stage
boundary (or the phase-end gate) until the check passes or the person decides
at that gate. `advisory` still runs and records findings, and does not fail
the command.
