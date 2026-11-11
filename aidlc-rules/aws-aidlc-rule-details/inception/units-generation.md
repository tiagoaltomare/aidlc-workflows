# Units Generation - Detailed Steps

**Autonomous Inception:** `common/inception-autonomy.md` removes the plan gate and the generation gate. Require an acyclic DAG. Review is at `inception_end`. The stage stays conditional.

## Overview
This stage decomposes the system into manageable units of work through two integrated parts:
- **Part 1 - Planning**: Create decomposition plan with questions; non-blocking answers go to `assumptions.md`
- **Part 2 - Generation**: Generate unit artifacts; run `units-dag`

**DEFINITION**: A unit of work is a logical grouping of stories for development purposes. For microservices, each unit becomes an independently deployable service. For monoliths, the single unit represents the entire application with logical modules.

**Always at least one unit when stories exist.** Do not skip this stage because there is a "single simple unit". Produce `UNIT-001` (or more), the DAG, and the story map so traceability can run. Skip this stage only when User Stories was also skipped.

**Terminology**: Use "Service" for independently deployable components, "Module" for logical groupings within a service, "Unit of Work" for planning context.

## Prerequisites
- Workspace Detection must be complete
- Requirements Analysis recommended (provides functional scope)
- User Stories recommended (stories map to units)
- Application Design stage REQUIRED (determines components, methods, and services)
- Execution plan must indicate Design stage should execute

---

# PART 1: PLANNING

## Step 1: Create Unit of Work Plan
- Generate plan with checkboxes [] for decomposing system into units of work
- Focus on breaking down the system into manageable development units
- Each step and sub-step should have a checkbox []

## Step 2: Include Mandatory Unit Artifacts in Plan
**ALWAYS** include these mandatory artifacts in the unit plan:
- [ ] Generate `aidlc-docs/inception/application-design/unit-of-work.md` with unit definitions and responsibilities
- [ ] Generate `aidlc-docs/inception/application-design/unit-of-work-dependency.md` with dependency matrix
- [ ] Generate `aidlc-docs/inception/application-design/unit-of-work-story-map.md` mapping stories to units
- [ ] **Greenfield only**: Document code organization strategy in `unit-of-work.md` (see code-generation.md for structure patterns)
- [ ] Validate unit boundaries and dependencies
- [ ] Ensure all stories are assigned to units

## Step 3: Generate Context-Appropriate Questions
**DIRECTIVE**: Thoroughly analyze the requirements, stories, and application design to identify ALL areas where clarification would improve unit decomposition quality. Be proactive in asking questions to ensure comprehensive coverage of decomposition concerns.

**CRITICAL**: Default to asking questions when there is ANY ambiguity or missing detail that could affect unit boundaries or decomposition quality. It's better to ask too many questions than to make incorrect assumptions about how the system should be decomposed.

**MANDATORY**: Evaluate ALL of the following categories by asking targeted questions about each. For each category, determine applicability based on evidence from the requirements, stories, and application design -- do not skip categories without explicit justification:

- EMBED questions using [Answer]: tag format
- Focus on ANY ambiguities, missing information, or areas needing clarification
- Generate questions wherever user input would improve decomposition decisions
- **When in doubt, ask the question** - overconfidence leads to poor unit boundaries

**Question categories to evaluate** (consider ALL categories):
- **Story Grouping** - Ask about grouping strategy, story affinity, and logical clustering approaches
- **Dependencies** - Ask about integration approach, shared resources, and inter-unit communication patterns
- **Team Alignment** - Ask about team structure, ownership boundaries, and collaboration models
- **Technical Considerations** - Ask about scalability/deployment requirements that may differ across units
- **Business Domain** - Ask about domain boundaries, bounded contexts, and business capability alignment
- **Code Organization (Greenfield multi-unit only)** - Ask about deployment model and directory structure preferences

## Step 4: Store UOW Plan
- Save as `aidlc-docs/inception/plans/unit-of-work-plan.md`
- Include all [Answer]: tags for user input
- Ensure plan covers all aspects of system decomposition

## Step 5: Request User Input
- Ask user to fill [Answer]: tags directly in the plan document
- Emphasize importance of decomposition decisions
- Provide clear instructions on completing the [Answer]: tags

## Step 6: Collect Answers
- Wait for user to provide answers to all questions using [Answer]: tags in the document
- Do not proceed until ALL [Answer]: tags are completed
- Review the document to ensure no [Answer]: tags are left blank

## Step 7: ANALYZE ANSWERS (MANDATORY)
Before proceeding, you MUST carefully review all user answers for:
- **Vague or ambiguous responses**: "mix of", "somewhere between", "not sure", "depends"
- **Undefined criteria or terms**: References to concepts without clear definitions
- **Contradictory answers**: Responses that conflict with each other
- **Missing generation details**: Answers that lack specific guidance
- **Answers that combine options**: Responses that merge different approaches without clear decision rules

## Step 8: MANDATORY Follow-up Questions
If the analysis in step 7 reveals ANY ambiguous answers, you MUST:
- Add specific follow-up questions to the plan document using [Answer]: tags
- DO NOT proceed to approval until all ambiguities are resolved
- Examples of required follow-ups:
  - "You mentioned 'mix of A and B' - what specific criteria should determine when to use A vs B?"
  - "You said 'somewhere between A and B' - can you define the exact middle ground approach?"
  - "You indicated 'not sure' - what additional information would help you decide?"
  - "You mentioned 'depends on complexity' - how do you define complexity levels?"

## Step 9: No plan gate
- Do not wait. Continue to generation. Honor `units.max_stories_per_unit`.

## Step 10: Log Approval
- Log prompt and response in audit.md with timestamp
- Use ISO 8601 timestamp format
- Include complete approval prompt text

## Step 11: Update Progress
- Mark Units Generation Part 1 (Planning) complete in aidlc-state.md
- Update the "Current Status" section
- Prepare for transition to Units Generation Part 2 (Generation)

---

# PART 2: GENERATION

## Step 12: Load Unit of Work Plan
- [ ] Read the complete plan from `aidlc-docs/inception/plans/unit-of-work-plan.md`
- [ ] Identify the next uncompleted step (first [ ] checkbox)
- [ ] Load the context and requirements for that step

## Step 13: Execute Current Step
- [ ] Perform exactly what the current step describes
- [ ] Generate unit artifacts as specified in the plan
- [ ] Follow the approved decomposition approach from Planning
- [ ] Use the criteria and boundaries specified in the plan

## Step 14: Update Progress
- [ ] Mark the completed step as [x] in the unit of work plan
- [ ] Update `aidlc-docs/aidlc-state.md` current status
- [ ] Save all generated artifacts

## Step 15: Continue or Complete
- [ ] If more steps remain, return to Step 12
- [ ] If all steps complete, verify units are ready for design stages
- [ ] Mark Units Generation stage as complete

## Step 16: Present Completion Message

```markdown
# 🔧 Units Generation Complete

[AI-generated summary of units and decomposition created in bullet points]

**Stage complete (no gate).** Artifacts: `aidlc-docs/inception/application-design/` (`unit-of-work.md`, DAG, story map). Continue to `inception_end`. Do not wait for per-stage approval.
```

## Step 17: No units gate
- Run `python3 -m aidlc_validate units-dag --root PRODUCT_REPO`. Continue to `inception_end`.

## Step 18: Record Approval Response
- Log the user's approval response with timestamp in `aidlc-docs/audit.md`
- Include the exact user response text
- Mark the approval status clearly

## Step 19: Update Progress
- Mark Units Generation stage complete in `aidlc-docs/aidlc-state.md`
- Update the "Current Status" section
- Prepare for transition to CONSTRUCTION PHASE

---

## Critical Rules

### Planning Phase Rules
- Generate ONLY context-relevant questions
- Use [Answer]: tag format for all questions
- Analyze all answers for ambiguities before proceeding
- Resolve ALL ambiguities with follow-up questions
- No plan gate. Non-blocking answers go to `assumptions.md`. Continue. Review is at `inception_end`.

### Generation Phase Rules
- **NO HARDCODED LOGIC**: Only execute what's written in the unit of work plan
- **FOLLOW PLAN EXACTLY**: Do not deviate from the step sequence
- **UPDATE CHECKBOXES**: Mark [x] immediately after completing each step
- **USE APPROVED APPROACH**: Follow the decomposition methodology from Planning
- **VERIFY COMPLETION**: Ensure all unit artifacts are complete before proceeding

## Completion Criteria
- All planning questions answered (blocking) or copied to `assumptions.md` (non-blocking)
- All steps in unit of work plan marked [x]
- At least one `UNIT-` record when stories exist
- All unit artifacts generated according to plan:
  - `unit-of-work.md` with unit definitions
  - `unit-of-work-dependency.md` with dependency matrix
  - `unit-of-work-story-map.md` with story mappings
- Validator `units-dag` and `traceability` run
- Ready for `inception_end`
