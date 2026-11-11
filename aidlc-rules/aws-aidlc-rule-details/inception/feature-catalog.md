# Feature catalog

Part 3 of the composite stage **Create Vision, Tech Env, Features and Scopes**.
Run after Tech Env. No stage gate here.

## Definition

A feature is an observable capability for a user or an external system, with
one entry point: route, endpoint, command, job, or event consumer. Derive it
from the end-to-end flow from that entry point, not from the folder tree.
Two entry points that serve the same business goal are one feature.

## Path and ids

Default path: `aidlc-docs/vision/features.md` (`vision.features_path`).

Each record uses a stable `FEAT-` id (see `scripts/aidlc-validate/README.md`).

Required table:

```markdown
| id       | name | entry_points | components | data | tests | confidence |
| -------- | ---- | ------------ | ---------- | ---- | ----- | ---------- |
| FEAT-001 | …    | …            | …          | …    | …     | high       |
```

`confidence` is `high`, `medium`, or `low`.

Do not put unescaped `{identifier}` in table cells (for example
`Book {id, title}`). Spell field names without braces, or wrap them in
backticks (`` `{id}` ``). Docusaurus export also escapes remaining braces
so MDX does not treat `{id}` as JavaScript.

## Greenfield

Build the catalog from the Full Scope Vision feature ids.

## Brownfield

Build from Reverse Engineering: APIs, jobs, consumers, UI routes. Entry
points, components touched, data read/written, existing tests, and
confidence are mandatory. Low-confidence features are listed at
`vision_scope`.

## Completion

Continue to `scope-breakdown.md`.
