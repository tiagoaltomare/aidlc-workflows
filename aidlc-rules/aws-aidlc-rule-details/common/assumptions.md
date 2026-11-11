# Assumptions and blocking questions

During autonomous Inception and Construction, do **not** stop for a stage
gate. Open questions go to `aidlc-docs/assumptions.md` unless they are
**blocking**.

## File

Path: `aidlc-docs/assumptions.md`. Create it in the Vision composite stage if
it is missing. **Append only.**

```markdown
# Assumptions

| id  | stage | blocking | question | assumption_or_answer | status |
| --- | ----- | -------- | -------- | -------------------- | ------ |
| A-001 | requirements | no | … | Assumed X | open |
```

- `blocking`: `yes` or `no`
- `status`: `open`, `answered`, `stopped`

## Blocking vs not

**Blocking** (stop the workflow and ask the person, using A–E from
`question-format-guide.md`):

- Extension opt-in (security, resiliency, testing, and Operations extensions)
- Unknown production target or a forbidden stack required by the Vision
- A validator check with severity `blocking` that the agent cannot fix
- Anything the person must decide and that would be irreversible later

**Not blocking**: record in the table, state the assumption, continue.

A verifier that is only an LLM, with no executable check, must not close a
blocking item. Escalate.

## Escape

When stopping, write the item in `assumptions.md` with `blocking: yes` and
`status: stopped`, show the question once, and wait. After the person
answers, update the row and resume the same stage.
