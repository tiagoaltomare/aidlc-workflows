# Autonomous Inception (no per-stage gate)

`core-workflow.md` overrides per-stage "Wait for Explicit Approval" in
Inception. After `vision_scope`, generate artifacts, run the checks in
`automatic-checks.md`, append non-blocking questions to `assumptions.md`,
and continue. The person reviews everything at `inception_end`.

**Still blocking (stop and ask):**

- Extension opt-in, including Operations extensions
- Any question classified blocking in `assumptions.md`
- Validator `blocking` failure the agent cannot fix

User Stories, Application Design, and Units Generation stay **conditional**
exactly as in v1. Do not force a stage the v1 rules would skip.

Apply `stories.*` and `units.*` from `aidlc.config.yaml` (format, INVEST
proxy, min/max acceptance criteria, `max_stories_per_unit`, sequential
units). The dependency table in `unit-of-work-dependency.md` MUST be an
acyclic DAG in the format in `scripts/aidlc-validate/README.md`.
