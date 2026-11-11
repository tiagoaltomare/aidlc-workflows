# aidlc-validate

Deterministic checks for a product repository that follows the AI-DLC
autonomous fork. Stdlib plus PyYAML and jsonschema.

```bash
python3 -m aidlc_validate CHECK --root PRODUCT_REPO
```

Use **`python3`**. Do not assume a `python` command exists.

`CHECK` is one of: `config`, `units-dag`, `traceability`, `scope-in-vision`,
`export`, `stories`, `assumptions`. Non-zero exit prints the failures to stderr.

Install from this directory (`pip install -e .`) or set `PYTHONPATH` to
`scripts/aidlc-validate`.

## Artifact paths

| Check             | Reads                                                                                                                                                                                                                                                 |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config`          | `aidlc.config.yaml`                                                                                                                                                                                                                                   |
| `units-dag`       | `aidlc-docs/inception/application-design/unit-of-work.md`, `unit-of-work-dependency.md`                                                                                                                                                               |
| `traceability`    | Current-cycle scope (`scope.current_path`, else `scope-*.md`), `inception/requirements/requirements.md`, `user-stories/stories.md`, `unit-of-work-story-map.md`                                                                                       |
| `scope-in-vision` | `aidlc-docs/vision/features.md`, current-cycle scope (`scope.current_path`, else `scope-*.md`; alias files with the same `SCOPE-` id count once)                                                                                                      |
| `export`          | `aidlc.config.yaml` `operations.include` / `exclude`, docs-site folder (`operations.docusaurus_path`, default `docs-site`); unescaped `{ident}` and `[Answer]:` lines in exported markdown fail; `node_modules` / `build` / `.docusaurus` are skipped |
| `stories`         | `aidlc-docs/inception/user-stories/stories.md` plus `stories.*` in the config (As a / I want, min/max AC)                                                                                                                                             |
| `assumptions`     | `aidlc-docs/assumptions.md` table (`id`, `stage`, `blocking`, `question`, `assumption_or_answer`, `status`); fails on missing file, malformed rows, or blocking rows that are not `answered`                                                          |

## ID conventions

Stable prefixes. Body is uppercase alphanumeric segments separated by `-`.

| Kind         | Pattern   | Example     |
| ------------ | --------- | ----------- |
| Feature      | `FEAT-…`  | `FEAT-001`  |
| Scope        | `SCOPE-…` | `SCOPE-001` |
| Requirement  | `REQ-…`   | `REQ-001`   |
| User story   | `US-…`    | `US-001`    |
| Unit of work | `UNIT-…`  | `UNIT-001`  |

Put the id in the heading of the record (`### REQ-001 Checkout`). Link records
with a single labelled line:

```markdown
### REQ-001 Checkout
Covers: FEAT-001

### US-001 Checkout a book
Requirement: REQ-001
```

## Scope files

Each file `aidlc-docs/vision/scopes/scope-*.md` must have `## In scope` and
`## Out of scope` sections. List feature ids as list items or in a table with
an `id` column:

```markdown
# SCOPE-001 Cycle 1

## In scope

- FEAT-001

## Out of scope

- FEAT-099
```

`scope-in-vision` requires every in-scope `FEAT-` id to appear in
`aidlc-docs/vision/features.md`.

## Unit dependency table

`unit-of-work-dependency.md` must contain a pipe table with columns `unit` and
`depends_on` (header match is case-insensitive; `depends on` is accepted).
One `UNIT-` id per `unit` cell. Dependencies are comma-separated `UNIT-` ids.
Empty, `None`, `-`, or `n/a` means no dependency.

```markdown
| unit     | depends_on |
| -------- | ---------- |
| UNIT-001 |            |
| UNIT-002 | UNIT-001   |
```

`units-dag` fails on a cycle or on a `UNIT-` id that is not declared in
`unit-of-work.md` (or, if that file has no `UNIT-` ids, in the dependency
table itself).

## Traceability

In-scope features must be covered by a requirement (`Covers: FEAT-…`). If
`stories.md` exists, every `REQ-` heading must be referenced by a story
(`Requirement: REQ-…`), every `US-` heading must appear in
`unit-of-work-story-map.md`, and every declared unit must have at least one
story. Out-of-scope ids must not appear in `aidlc-docs/inception/`,
`construction/`, or `operations/` artifacts.

Story map table:

```markdown
| story  | unit     |
| ------ | -------- |
| US-001 | UNIT-001 |
```

## Export markers

Included sources are present if a file or directory with this name exists
anywhere under the docs-site folder:

| Config include                | Marker                           |
| ----------------------------- | -------------------------------- |
| `vision`                      | `vision-document.md`             |
| `technical_environment`       | `technical-environment.md`       |
| `features`                    | `features.md`                    |
| `scopes`                      | `scopes` (directory)             |
| `requirements`                | `requirements.md`                |
| `user_stories`                | `stories.md`                     |
| `application_design`          | `application-design.md`          |
| `units`                       | `unit-of-work.md`                |
| `construction_designs`        | `construction` (directory)       |
| `build_and_test_summary`      | `build-and-test-summary.md`      |
| `operations_summary`          | `operations-summary.md`          |
| `rules_validation_report`     | `rules-validation-report.md`     |
| `post_deployment_test_report` | `post-deployment-test-report.md` |

Excluded names that must be **absent**: `audit.md`, `deployment-deploy.md`,
any markdown whose name contains `question`, and raw plans (`*plan*.md` or
files under a `plans/` directory).
