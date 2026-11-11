# Cuts from the autonomous-fork plan

Record of work dropped or deferred so a greenfield and a brownfield
pilot can run end to end. Each row is a deliberate cut, not an
accidental omission.

| Phase | What was cut                                                      | Why                                                                                                                         |
| ----- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| F0    | `stories` check is a stub (always passes; no INVEST / AC min-max) | Deadline: keep F0 lean; full story standard is an F3 check                                                                  |
| F0    | Full evaluator pipeline (Bedrock, docker sandbox) on Actions      | GitHub Actions now runs evaluator **unit tests** only (`uv run python run.py test`); Bedrock/docker stay in `codebuild.yml` |
| F1    | None (full `v1-operations` merge, including evaluator)            | Conflict-free; Actions unit tests are a later add (see F0). `codebuild.yml` is unchanged                                    |
| F2    | Portal skills not copied; writing-inputs guides used as structure | Skills stay interactive and root-file oriented; composite stage replaces that behaviour                                     |
| F3    | Full INVEST scoring and breakdown-strategy enforcement            | Deadline: stories check enforces As a / I want plus min/max AC counts                                                       |
| F3    | No Python subcommand for Vision/Tech consistency                  | Agent inspects Tech Env; `assumptions` is now a validator subcommand                                                        |
| F4    | No separate LLM-reviewer harness (process rule only)              | Deadline: hybrid mode is specified in rules; a second model is not spawned by this repo                                     |
| F5    | Webpack pinned to 5.101.3 in the Docusaurus scaffold              | Newer webpack ProgressPlugin breaks Docusaurus 3.9 `webpackbar` on Node 22                                                  |

F6 documentation polish (README pointer, `getting-started.md`, welcome
and process-overview, named-gate language) is **done** in this change.
Pilot findings F1–F21 and PF-001–PF-015 are addressed in rules,
validator, scaffold generation, and docs. Pilots are not re-run.

Still left out: portal skills, a spawned second-model reviewer, full
INVEST scoring, the full evaluator pipeline with Bedrock on GitHub
Actions, and a Vision/Tech consistency subcommand. Evaluator unit tests
on Actions and the `assumptions` subcommand are **done**.
