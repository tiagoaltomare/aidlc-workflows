# Cycle Close

**Purpose**: Close a cycle when the memory extension is on. This stage sits after Build and Test and before Operations.

**Skip when**: `aidlc-docs/knowledge/.aidlc-memory` is absent. Build and Test then continues to Operations as before.

**MANDATORY**: Do not overwrite `aidlc-docs/audit.md`. Append every record.

## Step 1: Refresh the codekb for this cycle's edits

Run `aidlc_memory.py check --resume`.

For each path in `stale_sources` and `uncovered` that this cycle changed, update the codekb entry that covers it (or add a narrow entry from `templates/codekb-entry.md`). Do not rescan packages the check calls current.

Run `aidlc_memory.py stamp` on each entry you rewrote. If stamp exits 1, a source file is missing: fix the entry's `sources` list and stamp again. Do not set `source_commit` by hand.

## Step 2: Archive OpenSpec changes

For each directory in `aidlc-docs/openspec/changes/` except `archive/`:

1. Run `aidlc_memory.py archive-check --change <id>`.
2. If the exit code is 1, stop. Show the conflict report. Do not edit the living spec to force a merge. Do not drop conflict markers. Append an audit note and run `aidlc_memory.py emit archive --change-id <id> --result blocked`. Ask the human to resolve the conflict. When they have edited the change and `archive-check` exits 0, continue. A conflict never resolves itself.
3. When check is clean, show the diff and wait for approval.
4. Run `aidlc_memory.py archive-apply --change <id> --approved`. Without `--approved` the command must refuse. The living spec then has one block per requirement id.

If there are no open changes, record that and continue.

## Step 3: Lint

Run `aidlc_memory.py lint`. Fix the reported structure (headings, duplicate requirement ids, conflict markers) and run it again. Do not weaken a requirement to silence the linter.

## Step 4: Index and log

Update `aidlc-docs/knowledge/index.md` so a reader can see the new handoff, codekb entries, and ADRs without opening them.

Append to `aidlc-docs/knowledge/log.md`. Newest date first. Do not rewrite older dates. Use a `## YYYY-MM-DD` heading and bullets such as `**Archive**`, `**RE**`, and `**Handoff**`.

Add an ADR from `templates/adr.md` only when this cycle made an architectural decision. An ADR needs a human `verified` entry before it is `stable`.

## Step 5: Write the handoff

Create `aidlc-docs/knowledge/handoff/cycle-NN.md` from `templates/handoff.md`. `NN` is the cycle number from `aidlc-state.md`, at least two digits.

Keep these headings, in this order: `Escopo`, `Changes`, `Stale`, `Dívidas`, `Pendências`, `Commit`.

- `Changes` lists change ids. It does not copy spec text.
- `Stale` lists what `.stale.json` reported at cycle start and at this refresh.
- `re_mode` in the frontmatter is the mode the human approved at cycle start.
- `source_commit` is the `HEAD` that stamp wrote. Do not add `verified` yet.

## Step 6: Ask the human to approve the handoff

```markdown
> **REVIEW REQUIRED:**
> Please examine `aidlc-docs/knowledge/handoff/cycle-NN.md`.

A) Approve the handoff and close the cycle

B) Request changes to the handoff

[Answer]:
```

Wait. On B, edit and ask again. Do not add `verified` until the answer is approval.

On approval, add:

```yaml
verified:
  - by: human:[name]
    at: [ISO-8601]
```

Run `aidlc_memory.py emit handoff --cycle NN --approved true`.

## Step 7: Audit and state

Append:

```markdown
## Memory Cycle Close
**Timestamp**: [ISO-8601]
**Handoff**: aidlc-docs/knowledge/handoff/cycle-NN.md
**Archive**: [applied change ids, or none, or blocked ids]
**User Input**: "[raw approval]"
**Approved**: yes

---
```

Update `aidlc-docs/aidlc-state.md`: this cycle is closed, and the current stage may move to Operations.

## Step 8: Continue

Operations runs after the handoff is approved. If the user does not want Operations, stop after recording that choice in the audit. The cycle is still closed.
