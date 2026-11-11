# Getting started — autonomous fork

This branch (`feature/aidlc-autonomo`) is the v1-based autonomous fork.
Inception and Construction generate and continue. Only the **named gates**
stop for a person. Official product docs are a Docusaurus site generated
**in the product repository** (`docs-site/` by default).

English is the language of the new rules, the validator, and this guide.

## How a pilot starts a cycle

1. **Product repo** is the workspace (greenfield empty tree, or brownfield
   codebase). Do not treat the rules fork as the product.
2. **Copy `aidlc.config.yaml`** into the product root from
   [`docs/aidlc.config.example.yaml`](../aidlc.config.example.yaml). Edit
   `project_type`, `depth`, and `scope.current_path` if needed.
3. **Install the rules into the product repo** (Cursor steps in the next
   section; other agents:
   [README Platform-Specific Setup](../../README.md#platform-specific-setup)).
   The first file the agent loads is `core-workflow.md`. That file loads
   `common/welcome-message.md` once, then `common/process-overview.md`,
   `common/config.md`, and the rest from the rule-details directory.
4. **Install the validator** (from this fork, not from the product):

   ```bash
   python3 -m pip install -e /path/to/aidlc-workflows/scripts/aidlc-validate
   ```

   Or set `PYTHONPATH` to `scripts/aidlc-validate`. Always invoke
   **`python3`** (do not assume a `python` command exists):

   ```bash
   python3 -m aidlc_validate config --root /path/to/PRODUCT_REPO
   ```

5. **Give the agent the user request** (what to build this cycle). The
   agent runs Workspace Detection, then the rest of `core-workflow.md`.
6. **Answer only named gates and blocking questions.** Non-blocking
   questions are written to a question file and copied to
   `aidlc-docs/assumptions.md`; the run continues.

### Install into a Cursor product repo

From the **product** repository root, with `RULES` pointing at a checkout
of this fork (`feature/aidlc-autonomo`):

```bash
RULES=/path/to/aidlc-workflows

mkdir -p .cursor/rules
cat > .cursor/rules/ai-dlc-workflow.mdc << 'EOF'
---
description: "AI-DLC (AI-Driven Development Life Cycle) adaptive workflow for software development"
alwaysApply: true
---

EOF
cat "$RULES/aidlc-rules/aws-aidlc-rules/core-workflow.md" >> .cursor/rules/ai-dlc-workflow.mdc

mkdir -p .aidlc-rule-details
cp -R "$RULES/aidlc-rules/aws-aidlc-rule-details/"* .aidlc-rule-details/
```

Commit `.aidlc-rule-details/` with the product. Check the product
`.gitignore` does not ignore that path; if it does, remove the ignore line
so the copied rules are versioned.

- **`.cursor/rules/ai-dlc-workflow.mdc`** — Cursor always-apply rule. It
  is `core-workflow.md` with YAML frontmatter.
- **`.aidlc-rule-details/`** — stage files (`common/`, `inception/`,
  `construction/`, `operations/`, `extensions/`). `core-workflow.md`
  resolves this path. Commit this directory.

**AGENTS.md pointer** (optional, in addition to or instead of the
`.mdc` file). Keep or merge with `common/agents-md.md` if a scaffold
would overwrite it:

```bash
cp "$RULES/aidlc-rules/aws-aidlc-rules/core-workflow.md" ./AGENTS.md
```

Or a short pointer at the top of `AGENTS.md`:

```markdown
# AGENTS.md

This project uses AI-DLC. For software development work, load and follow
`.cursor/rules/ai-dlc-workflow.mdc` (or `core-workflow.md`). Rule details
are in `.aidlc-rule-details/`.
```

Kiro, Amazon Q, Cline, Claude Code, GitHub Copilot, and Codex: same
`aws-aidlc-rule-details/` copy, different host file. Follow
[README Platform-Specific Setup](../../README.md#platform-specific-setup).

### Named gates

| Gate                      | Stops after                                                                         |
| ------------------------- | ----------------------------------------------------------------------------------- |
| `reverse_engineering`     | Reverse Engineering (brownfield)                                                    |
| `vision_scope`            | Vision, Tech Env, feature catalog, scopes                                           |
| Extension opt-in          | Requirements Analysis (blocking question)                                           |
| `inception_end`           | Inception package                                                                   |
| `design_validation`       | Per-unit design, when hybrid triggers fire                                          |
| `build_and_test`          | Build and Test (door into Operations)                                               |
| v1-operations checkpoints | Rules Validation / Deployment / PDT when those stages **run**                       |
| Deployment opt-in         | Asked **before** infrastructure-design artifacts if the deployment extension is off |
| `operations`              | Docusaurus export; then mark delivered features                                     |

### Where files live

| Thing              | Location                                                             |
| ------------------ | -------------------------------------------------------------------- |
| Config             | Product root `aidlc.config.yaml`                                     |
| Cycle artifacts    | Product `aidlc-docs/`                                                |
| Official docs site | Product `docs-site/` (generated; not read from this fork at runtime) |
| Validator          | This fork `scripts/aidlc-validate/`                                  |
| Rules              | This fork `aidlc-rules/`                                             |

### Depth

`depth: minimal` for Vision is a **short section list** (executive
summary, FEAT- list, cycle-cut pointer). `standard` and `comprehensive`
use the full Vision sections. See `create-vision.md`. A strangler
migration uses that same `minimal` / `standard` / `comprehensive` choice;
it does not add a fourth depth. Other stages still create all defined
artifacts; detail inside them follows depth.

### Units

When User Stories ran, Units Generation **must** produce at least one
`UNIT-` record, an acyclic DAG, and a story map. A single simple unit is
valid. Skip Units Generation only when User Stories was also skipped.

### Extensions

At start, load only `*.opt-in.md` (heading `## Opt-In Prompt` or
`## Question`). Do not enforce full extension rules until Requirements
Analysis records opt-in. Opted OUT means that prompt's skip/No option
(B, C, or D — whatever letter the file offers). Do not assume the skip
letter is always D.

### Validator checks

`python3 -m aidlc_validate CHECK --root PRODUCT_REPO` — `CHECK` is one of
`config`, `units-dag`, `traceability`, `scope-in-vision`, `export`,
`stories`, `assumptions`. The `assumptions` check reads
`aidlc-docs/assumptions.md` and fails on a missing or malformed table or
on a blocking row that is not `answered`. It runs at `inception_end`
with the other package checks.

### AGENTS.md

If a framework scaffold (for example `create-next-app`) writes
`AGENTS.md`, merge it with the AI-DLC pointer to `core-workflow.md`.
Never replace the AI-DLC file. See `common/agents-md.md`.
