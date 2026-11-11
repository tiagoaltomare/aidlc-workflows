# Assumptions and blocking questions

During autonomous Inception and Construction, do **not** stop for a stage
gate. Open questions go to `aidlc-docs/assumptions.md` unless they are
**blocking**.

## File

Path: `aidlc-docs/assumptions.md`. Create it in the Vision composite stage if
it is missing. **Append only.**

```markdown
# Assumptions

| id    | stage        | blocking | question | assumption_or_answer | status |
| ----- | ------------ | -------- | -------- | -------------------- | ------ |
| A-001 | requirements | no       | …        | Assumed X            | open   |
```

This table is the required format. `python3 -m aidlc_validate assumptions --root PRODUCT_REPO` checks it.

- `id`: unique, `A-` plus at least three digits (`A-001`)
- `stage`: the stage that recorded the row (non-empty)
- `blocking`: `yes` or `no`
- `question`: the open question (non-empty)
- `assumption_or_answer`: the default taken, or the person's answer (non-empty)
- `status`: `open`, `answered`, or `stopped`

The check **fails** if the file is missing, the table is malformed, a required cell is empty, an `id` is duplicated or not `A-…`, `blocking`/`status` use other values, or any **blocking** row is not `answered` (`open` or `stopped` still waits for the person). An empty table (heading only) is valid.

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
