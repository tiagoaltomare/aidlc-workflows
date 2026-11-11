# Preserve `AGENTS.md`

The product repository's `AGENTS.md` (and Cursor/Copilot equivalents such
as `CLAUDE.md` when they point at AI-DLC) is **AI-DLC's entry**. It must
keep a pointer at `core-workflow.md`.

## Rule

When a framework scaffold, generator, or package initializer would
**write or overwrite** `AGENTS.md` (for example `create-next-app`,
`create-vite`, `cdk init`):

1. If `AGENTS.md` already exists, **do not replace it**.
2. **Merge**: keep the AI-DLC block (load `core-workflow.md` first) at the
   top. Append the scaffold's agent notes under a heading such as
   `## Framework notes (from <tool>)`.
3. If `AGENTS.md` does not exist yet, create it with the AI-DLC pointer
   first, then append scaffold notes.
4. Log the merge in `aidlc-docs/audit.md`.

Never leave a scaffold-only `AGENTS.md` that omits AI-DLC.

## Minimum AI-DLC block

```markdown
# AGENTS.md

This project uses AI-DLC. For software development work, load and follow
`aidlc-rules/aws-aidlc-rules/core-workflow.md` (or the installed copy
under `.aidlc-rule-details/` / `.aidlc/`). That workflow overrides other
built-in coding workflows.
```

Adjust the path to however this product installed the rules.
