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
| F4    | No separate LLM-reviewer harness (process rule only)              | Deadline: hybrid mode is specified in rules; a second model is not spawned by this repo               |
| F5    | F6 documentation polish (`process-overview`, user guides)         | Lowest priority; rules in `core-workflow.md` are enough for a pilot agent                             |
| F5    | Webpack pinned to 5.101.3 in the Docusaurus scaffold              | Newer webpack ProgressPlugin breaks Docusaurus 3.9 `webpackbar` on Node 22                            |
