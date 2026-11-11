# Cuts from the autonomous-fork plan

Record of work dropped or deferred so a greenfield and a brownfield pilot can
run end to end. Each row is a deliberate cut, not an accidental omission.

| Phase | What was cut                                                      | Why                                                                                                   |
| ----- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| F0    | `stories` check is a stub (always passes; no INVEST / AC min-max) | Deadline: keep F0 lean; full story standard is an F3 check                                            |
| F0    | Evaluator tests not added to `.github/workflows/ci.yml`           | They were never in that workflow on v1; they stay in `codebuild.yml`, which this work does not change |
| F1    | None (full `v1-operations` merge, including evaluator)            | Conflict-free; GitHub Actions CI does not run evaluator tests                                         |
| F2    | Portal skills not copied; writing-inputs guides used as structure | Skills stay interactive and root-file oriented; composite stage replaces that behaviour               |
| F3    | Full INVEST scoring and breakdown-strategy enforcement            | Deadline: stories check enforces As a / I want plus min/max AC counts                                 |
| F3    | No Python subcommand for assumptions or Vision/Tech consistency   | Agent inspects `assumptions.md` and Tech Env; executable checks stay the six CLI subcommands          |
