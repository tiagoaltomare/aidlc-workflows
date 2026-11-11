# Cuts from the autonomous-fork plan

Record of work dropped or deferred so a greenfield and a brownfield pilot can
run end to end. Each row is a deliberate cut, not an accidental omission.

| Phase | What was cut                                                                 | Why                                                                                                    |
| ----- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| F0    | `stories` check is a stub (always passes; no INVEST / AC min-max)            | Deadline: keep F0 lean; full story standard is an F3 check                                             |
| F0    | Evaluator tests not added to `.github/workflows/ci.yml`                      | They were never in that workflow on v1; they stay in `codebuild.yml`, which this work does not change  |
