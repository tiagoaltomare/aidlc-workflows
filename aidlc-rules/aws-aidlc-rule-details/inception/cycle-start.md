# Cycle Start

**Purpose**: Start a new cycle when the memory extension is on. This file runs from Workspace Detection. It does not run when `aidlc-docs/knowledge/.aidlc-memory` is absent.

**Do not run for an in-progress cycle.** If `aidlc-docs/aidlc-state.md` shows a cycle that has no human-approved handoff yet, resume that cycle and run `check --resume` instead of this file.

## Step 1: Run the check

Run `aidlc_memory.py check` from `common/memory-protocol.md`. If the script cannot run, use the manual fallback in `extensions/memory/memory-spec.md`.

Read `aidlc-docs/knowledge/code/.stale.json`. The `mode` is `skip`, `delta`, or `full`. Do not recompute it.

## Step 2: Read the handoff

Read only:

- the latest `aidlc-docs/knowledge/handoff/cycle-NN.md`, when one exists
- `aidlc-docs/knowledge/index.md`

Stop if those two files together are over about 2000 tokens (about 8000 characters). Do not open codekb entries in this step.

Greenfield (`mode` is `skip` and `reasons` contains `greenfield`) has no code to reverse engineer. Continue to Requirements Analysis after the human accepts that.

## Step 3: Ask the human

**MANDATORY**: Present the mode, the reasons, the stale paths, and the uncovered paths. Then ask, using the options that match the mode.

When the mode is `skip`:

```markdown
A) Approve skip — load the current codekb and continue to Requirements Analysis

B) Run a delta scan anyway

C) Run a full reverse engineering scan

[Answer]:
```

When the mode is `delta`:

```markdown
A) Approve delta — rescan only the stale and uncovered paths

B) Run a full reverse engineering scan

[Answer]:
```

When the mode is `full`:

```markdown
A) Approve full — analyze all packages

[Answer]:
```

Do not offer skip when the mode is `delta` or `full`. The human may always move up to full. A custom reply that asks for full is full. A custom reply that asks to skip a delta or full result is not approval: repeat the question.

Blank lines between options are required. Wait for the answer. Do not start reverse engineering before it.

## Step 4: Record the decision

Append this block to `aidlc-docs/audit.md`. Do not overwrite the file. The user input is the raw reply.

```markdown
## Memory RE Decision
**Timestamp**: [ISO-8601]
**RE Decision**: skip|delta|full
**Reasons**: [reasons from .stale.json]
**User Input**: "[raw user reply]"
**Approved**: yes

---
```

If the human has not approved, `Approved` is `no` and you do not continue.

Update `aidlc-docs/aidlc-state.md` with the cycle number and the approved `RE Mode`. The next cycle number is one greater than the latest handoff, or 1 when there is no handoff.

## Step 5: Continue

- **skip**: Load the codekb index only, then Requirements Analysis.
- **delta** or **full**: Reverse Engineering, using that mode.
