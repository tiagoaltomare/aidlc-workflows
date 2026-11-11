# Create Technical Environment

Part 2 of the composite stage **Create Vision, Tech Env, Features and Scopes**.
Run after `create-vision.md` in the same stage. No stage gate here.

## Path

Default: `aidlc-docs/vision/technical-environment.md`
(`vision.tech_env_path` in `aidlc.config.yaml` when set).

## Reuse policy

Same `vision.reuse_policy` as Vision. If the versioned file is missing but
`technical-environment.md` exists at the product root, materialize it under
`aidlc-docs/vision/`.

## Greenfield

Write a complete Tech Env from
`docs/writing-inputs/technical-environment-guide.md`: summary, languages,
frameworks, cloud allow/disallow, patterns, security, tests, canonical
examples.

## Brownfield

Derive the Tech Env from Reverse Engineering, especially
`technology-stack.md` and real examples in the repo: what exists, what must
not change, patterns to follow.

## Cross-check with Vision

Before leaving this part:

- Languages and runtimes named in the Vision have a home in the Tech Env
- Allow/disallow lists do not contradict a Vision constraint
- Record leftover mismatches in `aidlc-docs/assumptions.md` (non-blocking) or
  stop if the mismatch is blocking (unknown production target, forbidden
  stack required by the Vision)

Continue to `feature-catalog.md`.
