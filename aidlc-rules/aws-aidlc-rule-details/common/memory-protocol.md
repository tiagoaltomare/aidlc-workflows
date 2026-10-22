# Memory Protocol

**Opt-in.** This file is loaded only when `aidlc-docs/knowledge/.aidlc-memory` exists and is not JSON with `"enabled": false`. When the marker is absent, do not load this file, do not create `aidlc-docs/knowledge/` or `aidlc-docs/openspec/`, and follow every other stage unchanged.

The normative detail is `extensions/memory/memory-spec.md`. Templates are in `templates/`. The model does not calculate hashes.

## Where artifacts live

`knowledge/` and `openspec/` are documentation. They live inside `aidlc-docs/`. Application code stays at the workspace root. The rule that documentation belongs only in `aidlc-docs/` does not change.

## Tool

Run `aidlc_memory.py` with Python 3. Search in this order and use the first file that exists:

1. `.aidlc/aidlc-rules/tools/aidlc_memory.py`
2. `.aidlc/tools/aidlc_memory.py`
3. `aidlc-rules/tools/aidlc_memory.py` under the workspace
4. `tools/aidlc_memory.py` next to the resolved rule-details directory

Commands used by the workflow:

- `check` at cycle start (`--resume` only when resuming an in-progress cycle)
- `stamp ENTRY` after an approved reverse-engineering pass, and again at cycle close for files this cycle changed
- `archive-check` and `archive-apply --approved` at cycle close
- `lint` after a successful archive
- `emit` for archive and handoff events

Exit 0 means skip or disabled. Exit 1 means delta or full, or an archive conflict. Exit 2 means the command could not run. Do not treat exit 2 as a clean workspace.

## Manual fallback

If Python or the script is missing, follow **Manual fallback** in `extensions/memory/memory-spec.md`. That procedure is `git diff --name-only --no-renames`, `git status --porcelain`, and SHA-256 after deleting CR bytes (`tr -d '\r' < file | sha256sum`). Write `aidlc-docs/knowledge/code/.stale.json` with the same fields. Do not invent a hash. Do not skip reverse engineering when the mode is delta or full.

## MANDATORY gates

1. **Cycle start.** The mode in `.stale.json` is the proposal. Ask the human before reverse engineering. Do not offer skip when the mode is delta or full. The human may always ask for full. Record `## Memory RE Decision` in `aidlc-docs/audit.md` with the raw user reply. Append. Never overwrite `audit.md`.
2. **Reverse engineering.** Delta re-reads only `stale_sources`, `uncovered`, and entries whose status is `stale`. It does not analyze packages the check calls current. Stamp only after the human approves step 13.
3. **Archive.** `archive-apply` runs only with `--approved` and only when `archive-check` reports no conflict. A conflict blocks. Do not pick a side. Do not delete conflict markers to force a clean file.
4. **Handoff.** Write `templates/handoff.md` with the six headings in order: `Escopo`, `Changes`, `Stale`, `Dívidas`, `Pendências`, `Commit`. The cycle is closed only after a human `verified` entry (`by` starts with `human:`).

## What to read at the start of a cycle

Read the latest `aidlc-docs/knowledge/handoff/cycle-NN.md` and `aidlc-docs/knowledge/index.md`, plus the check summary. Budget about 2000 tokens (about 8000 characters for those two files). Do not open every codekb entry up front. Open one when a later stage needs that area.

## Force a full scan

Trust `check`. It forces full when any condition in the spec holds, including an unreachable `source_commit`, divergence over 30 percent, a manifest or top-level directory change, three approved delta cycles in a row, a commit missing from `audit.md`, a missing or unapproved handoff on a new cycle, or a user request. `--resume` does not force full just because the in-progress cycle has no handoff yet. A hotfix is still reported.
