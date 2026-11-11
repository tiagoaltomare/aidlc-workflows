# Autonomous Inception (no per-stage gate)

`core-workflow.md` overrides per-stage "Wait for Explicit Approval" in
Inception. After `vision_scope`, generate artifacts, run the checks in
`automatic-checks.md`, append non-blocking questions to `assumptions.md`,
and continue. The person reviews everything at `inception_end`.

**Still blocking (stop and ask):**

- Extension opt-in, including Operations extensions
- Any question classified blocking in `assumptions.md`
- Validator `blocking` failure the agent cannot fix

User Stories and Application Design stay **conditional** as in v1.

**Units Generation:** when User Stories ran ( `stories.md` exists ), you
MUST produce at least one `UNIT-` record, DAG, and story map — even if
that unit is the whole application. Skip Units Generation only when User
Stories was also skipped. A "single simple unit" is not a skip; it is
one UNIT.

Apply `stories.*` and `units.*` from `aidlc.config.yaml` (format, INVEST
proxy, min/max acceptance criteria, `max_stories_per_unit`, sequential
units). The dependency table in `unit-of-work-dependency.md` MUST be an
acyclic DAG in the format in `scripts/aidlc-validate/README.md`.
