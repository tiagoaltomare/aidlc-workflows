# Scope breakdown

Part 4 of the composite stage **Create Vision, Tech Env, Features and Scopes**.
Run after the feature catalog. Ends in the human gate `vision_scope`.

## Path

Write `aidlc-docs/vision/scopes/scope-<id>.md`. Set `scope.current_path` in
`aidlc.config.yaml` to the scope for this cycle (default
`aidlc-docs/vision/scopes/scope-atual.md` may be a copy or a symlink-like
duplicate of the chosen `scope-*.md`; a regular file is enough).

Ids use `SCOPE-` (see `scripts/aidlc-validate/README.md`).

## Required sections

Each scope file MUST contain:

- Scope id and name
- Vision reference (path and a revision/date of `vision-document.md`)
- Covered feature ids
- `## In scope` — `FEAT-` ids this cycle will deliver
- `## Out of scope` — `FEAT-` ids that must not appear in cycle artifacts
- What must not change (especially brownfield)

Example:

```markdown
# SCOPE-001 Cycle 1

Vision: aidlc-docs/vision/vision-document.md

## In scope

- FEAT-001

## Out of scope

- FEAT-099
```

At least one in-scope feature is required for a pilot cycle.

## Check

Run, from this fork, with `PYTHONPATH` including `scripts/aidlc-validate`:

```bash
python -m aidlc_validate scope-in-vision --root PRODUCT_REPO
```

Non-zero exit is blocking. Every in-scope `FEAT-` id MUST resolve in
`features.md`. Do not silently add a feature to the Vision to make the check
pass; use `vision-change-proposals.md`.

## Gate `vision_scope`

Present the package: Vision, Tech Env, feature catalog, scopes (in/out),
low-confidence features, pending Vision change proposals, and
`assumptions.md`.

```markdown
# Vision and scope ready for review

Package: `aidlc-docs/vision/` plus `aidlc-docs/assumptions.md`.
Low-confidence features: [list or "none"].
Validator `scope-in-vision`: [pass/fail].

A) Approve and continue to Inception

B) Request changes (say what to change)

[Answer]:
```

**Wait for Explicit Approval.** Do not start Requirements Analysis until the
person approves. Log the raw reply in `audit.md`. On request for changes,
re-run the composite parts that need it and present `vision_scope` again.
