# Operations Retrofit

Brownfield only. Runs after Workspace Detection when Construction already
completed and Operations is still a placeholder (or unrecorded). Collect
extension opt-in answers and reset Construction so Operations can verify
compliance. Numbered steps here are the steps that
`step-execution-accountability.md` logs.

**Execute IF ALL of the following are true**:

- Workspace is brownfield (existing code detected)
- `aidlc-docs/aidlc-state.md` exists
- Stage Progress shows Construction stages COMPLETED
- Operations stage shows PLACEHOLDER, or no Operations stages are recorded

**Skip IF**:

- Operations stage does NOT show PLACEHOLDER

Do not wipe a versioned Vision. See `inception/create-vision.md`.

## Step 1: Log start

- Log start of Operations Retrofit in `aidlc-docs/audit.md`

## Step 2: Record steps

- Record all steps in this file in `aidlc-docs/step-decision-log.md` before
  executing any of them

## Step 3: Ask retrofit question

Present this question to the person (write it to a file under `aidlc-docs/`
**and** present it in the assistant turn):

**Operations extensions are available but were not included when this
project was built. Would you like to retrofit the Operations phase?
(Yes/No)**

Named gate: Operations Retrofit opt-in. Wait for the answer. Do not proceed
without it. Log the complete raw reply in `audit.md`.

## Step 4: Skip if the person says No

- Record stage status as SKIPPED in `aidlc-docs/aidlc-state.md`
- Present: "Operations Retrofit SKIPPED — user declined."
- Do not execute any further steps in this stage. Proceed to Reverse
  Engineering.

## Step 5: Archive current state (Yes)

- Create `aidlc-docs/operations/retrofit-archive/`
- Copy `aidlc-docs/aidlc-state.md` to
  `aidlc-docs/operations/retrofit-archive/aidlc-state.md`
- Copy `aidlc-docs/audit.md` to
  `aidlc-docs/operations/retrofit-archive/audit.md`
- Do **not** delete, move, or regenerate `aidlc-docs/vision/`. A retrofit
  must not wipe a versioned Vision, Tech Env, feature catalog, or scopes.

## Step 6: Reset `aidlc-state.md`

- **SET**: Project Type to `Brownfield (Operations Retrofit)`
- **KEEP**: Project Information (except Project Type), Workspace State, Code
  Location Rules, Architectural Decisions
- **CLEAR**: Extension Configuration table. Leave the section header and
  empty table columns intact.
- **CLEAR**: Build and Test Results
- **RESET**: Stage Progress. Mark Requirements Analysis and all subsequent
  stages as NOT COMPLETED (`[ ]`). Keep Workspace Detection and Operations
  Retrofit as `[x]`.
- **SET**: Current Stage to `INCEPTION - Requirements Analysis`

Re-read `aidlc-state.md` and confirm all four:

1. Extension Configuration table has the header row but NO data rows
2. Current Stage is `INCEPTION - Requirements Analysis`
3. Requirements Analysis and all subsequent stages show `[ ]`
4. `aidlc-docs/operations/retrofit-archive/aidlc-state.md` exists

Do not proceed to Step 7 until all four pass.

## Step 7: Complete and continue

- Verify the step-decision-log entry for this stage is complete and step
  counts match. For any missing step: re-execute it and all steps that
  depend on its output. Update the log. Do not present completion until all
  steps are logged.
- Continue to Create Vision, Tech Env, Features and Scopes
  (`reuse_if_present`; do not wipe `aidlc-docs/vision/`). Do not enter
  Requirements Analysis until `vision_scope` is approved.
