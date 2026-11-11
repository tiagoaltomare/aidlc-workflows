# Design validation (per unit)

Runs after the design stages of a unit (Functional Design, NFR Requirements,
NFR Design, Infrastructure Design — whichever executed) and **before** Code
Generation for that unit. Default mode is `hybrid`
(`design_validation.mode` in `aidlc.config.yaml`).

Report path: `aidlc-docs/construction/{unit}/design-validation.md`.

## Modes

- `auto`: executable checks plus a **separate** LLM reviewer. The reviewer is
  not the agent that wrote the design. An LLM-only verdict does **not**
  self-approve.
- `human`: always present the report and wait.
- `hybrid` (default): executable checks plus a separate LLM reviewer. Escalate
  to the person when a trigger fires.

## Executable checks (must run)

- Unit contracts match `component-dependency.md`
- NFRs in the Tech Env are addressed in the unit NFR artifacts
- Lint / type-check of interfaces when the stack has those tools
- `units-dag` still acyclic if dependencies changed

Record command, exit code, and evidence in the report. If none of these can
run, that is trigger `no_executable_check`.

## Human triggers (`hybrid` / `auto`)

Escalate and **wait** when any of these is true (from
`design_validation.human_triggers`, defaults below):

- `persistent_data` — unit writes durable data
- `security` — authn/authz, secrets, threat surface
- `public_contract` — published API or event contract
- `external_integration` — third-party or extra-repo system
- `risk_high_or_critical` — execution-plan risk High or Critical
- `rework_limit_exceeded` — `limits.max_rework_iterations_per_unit` (default 3)
- `no_executable_check` — no command or deterministic inspection proves the result

A separate LLM reviewer **must not** close validation alone.

## Token budget

`limits.token_budget_per_unit` (default 200000). On exceed,
`on_token_budget_exceeded` default `pause_and_ask_human`: stop and ask.
Do not keep spending. Do not abort the unit in silence.

## After a pass

Continue to Code Generation for this unit. Then the next unit in DAG order.
On rework, return to the design stages of the same unit and increment the
rework count in the report.
