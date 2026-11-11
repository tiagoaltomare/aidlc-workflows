# Create Vision

Part 1 of the composite stage **Create Vision, Tech Env, Features and Scopes**.
Always runs after Workspace Detection (greenfield, or brownfield with Reverse
Engineering already present) or after the Reverse Engineering gate when RE ran.
Do not start Requirements Analysis until the `vision_scope` gate is approved.

All new rules in this file are in English. Artifacts are written under
`aidlc-docs/vision/`.

## Paths

Read paths from `aidlc.config.yaml` `vision.*` when present. Defaults:

- Vision: `aidlc-docs/vision/vision-document.md`
- Tech Env: `aidlc-docs/vision/technical-environment.md` (see `create-tech-env.md`)
- Features: `aidlc-docs/vision/features.md`
- Scopes: `aidlc-docs/vision/scopes/scope-<id>.md`
- Change proposals: `aidlc-docs/vision/vision-change-proposals.md`
- Assumptions: `aidlc-docs/assumptions.md` (create if missing; append only)

## Reuse policy

`vision.reuse_policy` (default `reuse_if_present`):

- `reuse_if_present`: if `aidlc-docs/vision/vision-document.md` exists, do **not**
  regenerate it from scratch. If it is missing but `vision-document.md` exists at
  the product root, copy that file into `aidlc-docs/vision/` and treat it as the
  source. Fill only missing required sections when the existing file is clearly
  incomplete.
- `reuse_and_fill_gaps`: keep the file, add missing sections only.
- `regenerate`: rewrite from the current request and (brownfield) Reverse
  Engineering artifacts.

A retrofit or a later cycle MUST NOT delete a versioned Vision.

## Greenfield

Required Vision **sections depend on `depth`** (`aidlc.config.yaml` / Workspace
Detection). Use the wording in `docs/writing-inputs/vision-document-guide.md`
for whichever sections apply. Do not require the full guide at `minimal`.

**`depth: minimal`** — only these sections:

1. Executive Summary (a few sentences: what it is, who it is for)
2. Feature list with a stable `FEAT-` id per feature (the catalog still
   holds the table; see `inception/feature-catalog.md`)
3. Cycle cut — pointer to the versioned scope file(s). Do **not** use a
   single loose "MVP" block

Do not require Business Context subsections, Risks and Dependencies, or
long-form alternatives at `minimal`.

**`depth: standard`** — all of:

1. Executive Summary
2. Business Context (problem, users, success)
3. Full Scope Vision, with a stable `FEAT-` id per feature
4. Cycle cut (versioned scope files)
5. Risks and Dependencies (brief)

**`depth: comprehensive`** — the standard sections with extensive detail
(drivers, constraints, metrics, stakeholders, alternatives).

Long-term vision and the cycle cut stay distinct.

## Brownfield

Generate (or reuse) Vision **from the approved Reverse Engineering artifacts**:

- `business-overview.md` and journeys → business context and Vision
- `api-documentation.md`, jobs, consumers → feature entry points
- `component-inventory.md`, `architecture.md`, `dependencies.md` → components
- `code-quality-assessment.md` → existing tests and confidence

Do not invent a product story that the codebase does not support. Uncertain
features get low confidence in the catalog and are listed at `vision_scope`.

Cycle-requested capabilities that are **not in the codebase yet** go to
`vision-change-proposals.md` **and** the catalog as `FEAT-` rows with
confidence `medium` or `low`. They are not current-state. After
`vision_scope`, those proposed ids may be in-scope for this cycle.

## Change proposals

If this cycle discovers something not in the Vision, append a proposal to
`vision-change-proposals.md`. Do **not** silently edit an approved Vision.
The person accepts or rejects proposals at `vision_scope` (this cycle or the
next).

## Delivered features

Do not mark features delivered here. Marking happens only after the
`operations` gate (see `operations/docusaurus-export.md`).

## Completion

Continue to `create-tech-env.md` in the same composite stage. Do not ask for
a stage gate here.
