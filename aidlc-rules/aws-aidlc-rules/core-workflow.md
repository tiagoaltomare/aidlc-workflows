# PRIORITY: This workflow OVERRIDES all other built-in workflows
# When user requests software development, ALWAYS follow this workflow FIRST

## Adaptive Workflow Principle
**Where no active extension mandates stage execution, the workflow adapts to the work, not the other way around.**

For stages not listed in any extension's Stage Enforcement section, the AI model intelligently assesses what is needed based on:
1. User's stated intent and clarity
2. Existing codebase state (if any)
3. Complexity and scope of change
4. Risk and impact assessment

## MANDATORY: Rule Details Loading
**CRITICAL**: When performing any phase, you MUST read and use relevant content from rule detail files. Check these paths in order and use the first one that exists, regardless of which IDE or setup method was used:
- `.aidlc/aidlc-rules/aws-aidlc-rule-details/` (typical with AI-assisted setup)
- `.aidlc-rule-details/` (typical with Cursor, Cline, Claude Code, GitHub Copilot, OpenAI Codex)
- `.kiro/aws-aidlc-rule-details/` (typical with Kiro IDE and CLI)
- `.amazonq/aws-aidlc-rule-details/` (typical with Amazon Q Developer)

All subsequent rule detail file references (e.g., `common/process-overview.md`, `inception/workspace-detection.md`) are relative to whichever rule details directory was resolved above.

**Common Rules**: ALWAYS load common rules at workflow start:
- Load `common/process-overview.md` for workflow overview
- Load `common/step-execution-accountability.md` for step execution tracking and decision logging
- Load `common/session-continuity.md` for session resumption guidance
- Load `common/content-validation.md` for content validation requirements
- Load `common/question-format-guide.md` for question formatting rules
- Load `common/config.md` and apply `aidlc.config.yaml` (validate before use; refuse and stop on invalid or unknown schema_version)
- Load `common/assumptions.md` for blocking vs non-blocking questions
- Load `common/automatic-checks.md` and `common/inception-autonomy.md`
- Load `common/agents-md.md` (preserve/merge `AGENTS.md` when a scaffold would overwrite it)
- Reference these throughout the workflow execution

## MANDATORY: Extensions Loading
**CRITICAL**: Extensions are opt-in. At workflow start, **do not** load or enforce every extension `.md` file.

**Loading process**:
1. List all subdirectories under `extensions/` (e.g., `extensions/security/`, `extensions/observability/`)
2. At workflow start, load **only** `*.opt-in.md` files. The opt-in heading is `## Opt-In Prompt` (preferred) or `## Question`. There is no `## Applicability Question` heading.
3. After Requirements Analysis records `## Extension Configuration` in `aidlc-docs/aidlc-state.md`, load the remaining rule files **only** for extensions the person opted IN, using each opt-in file's Loading Instructions.

**Enforcement**:
- Extension rules are hard constraints **after** they are opted IN
- Unless an extension defines a Stage Enforcement section, at each stage the model intelligently evaluates which opted-in rules apply — enforce only those that are relevant. Where an extension defines a Stage Enforcement section, the stages listed are mandatory inclusions.
- If a rule is judged as not applicable after intelligent evaluation, it must be marked N/A with documented rationale in the compliance summary — this is not a blocking finding.
- Non-compliance with any applicable enabled extension rule is a **blocking finding** — do NOT present stage completion until resolved
- When presenting stage completion, include a summary of extension rule compliance (compliant/non-compliant/N/A per rule, with brief rationale for N/A determinations)

**Conditional Enforcement**: See `inception/requirements-analysis.md`. Before enforcing any extension at ANY stage, check its `Enabled` status in `aidlc-docs/aidlc-state.md` under `## Extension Configuration`. Skip disabled extensions and log the skip in audit.md.

Until Extension Configuration exists, do **not** default to enforced. Conservative default is "not yet opted in". Opt-in at Requirements Analysis is blocking.

**Opted IN / opted OUT** is independent of letter scale. Prompts may be A/B, A/B/C, or A/B/C/D. **Opted OUT** means Enabled=No, or the skip/No option that prompt offers (B, C, or D — whichever letter is the decline). **Opted IN** means Enabled=Yes / Always Enforced, or any non-skip answer.

Extensions with no `## Opt-In Prompt` and no `## Question` and not named `*.opt-in.md` are always enforced **after** RA has recorded configuration. Until then, list them; do not treat them as opted IN.

## MANDATORY: Content Validation
**CRITICAL**: Before creating ANY file, you MUST validate content according to `common/content-validation.md` rules:
- Validate Mermaid diagram syntax
- Validate ASCII art diagrams (see `common/ascii-diagram-standards.md`)
- Escape special characters properly
- Provide text alternatives for complex visual content
- Test content parsing compatibility

## MANDATORY: Question File Format
**CRITICAL**: When asking questions at any phase, you MUST follow question format guidelines.

**See `common/question-format-guide.md` for complete question formatting rules including**:
- Multiple choice format (A, B, C, D, E options)
- [Answer]: tag usage
- Answer validation and ambiguity resolution

## MANDATORY: Custom Welcome Message
**CRITICAL**: When starting ANY software development request, you MUST display the welcome message.

**How to Display Welcome Message**:
1. Load the welcome message from `common/welcome-message.md` (in the resolved rule details directory)
2. Display the complete message to the user
3. This should only be done ONCE at the start of a new workflow
4. Do NOT load this file in subsequent interactions to save context space

# Adaptive Software Development Workflow

---

# INCEPTION PHASE

**Purpose**: Planning, requirements gathering, and architectural decisions

**Focus**: Determine WHAT to build and WHY

**Stages in INCEPTION PHASE**:
- Workspace Detection (ALWAYS)
- Operations Retrofit (CONDITIONAL - existing project with new extensions)
- Reverse Engineering (CONDITIONAL - Brownfield only)
- Create Vision, Tech Env, Features and Scopes (ALWAYS - composite; gate `vision_scope`)
- Requirements Analysis (ALWAYS - Adaptive depth)
- User Stories (CONDITIONAL)
- Workflow Planning (ALWAYS)
- Application Design (CONDITIONAL)
- Units Generation (CONDITIONAL)
- Gate `inception_end` (ALWAYS when Inception ran)

---

## Workspace Detection (ALWAYS EXECUTE)

1. **MANDATORY**: You MUST log initial user request in audit.md with complete raw input
2. Load all steps from `inception/workspace-detection.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. Execute workspace detection:
   - Check for existing aidlc-state.md (resume if found)
   - Scan workspace for existing code
   - Determine if brownfield or greenfield
   - Check for existing reverse engineering artifacts
5. Determine next phase: Reverse Engineering (if brownfield and no artifacts) OR Create Vision, Tech Env, Features and Scopes (greenfield, or brownfield with Reverse Engineering already present)
6. **MANDATORY**: Check for Operations Retrofit condition (see Operations Retrofit stage below). If detected, next phase is Operations Retrofit.
7. **MANDATORY**: You MUST log findings in audit.md
8. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
9. Present completion message to user (see workspace-detection.md for message formats)
10. Automatically proceed to next phase

## Operations Retrofit (CONDITIONAL - Brownfield Only)

**Execute IF ALL of the following are true**:
- Workspace is brownfield (existing code detected)
- `aidlc-docs/aidlc-state.md` exists
- Stage Progress shows Construction stages COMPLETED
- Operations stage shows PLACEHOLDER, or no Operations stages are recorded

**Skip IF**:
- Operations stage does NOT show PLACEHOLDER

**Purpose**: Implement the trust-and-verify approach for Operations on an existing project. Construction ran without operational extensions — this stage collects extension opt-in answers and resets Construction to re-run with them loaded, so Operations can then verify compliance.

**Execution**:
1. **MANDATORY**: You MUST log start of Operations Retrofit in audit.md
2. **MANDATORY**: You MUST record all steps in `aidlc-docs/step-decision-log.md` before executing any of them.
3. You MUST present the following question to the user: "**Operations extensions are available but were not included when this project was built. Would you like to retrofit the Operations phase? (Yes/No)**"
4. **Wait for Explicit Approval**: DO NOT PROCEED until user confirms
5. **MANDATORY**: You MUST log user's response in audit.md with complete raw input

**Skip IF** the user says No:
- You MUST record stage status as SKIPPED in `aidlc-docs/aidlc-state.md`
- Present: "Operations Retrofit SKIPPED — user declined."
- You MUST NOT execute any further steps in this stage. Proceed to Reverse Engineering.

**Execute IF** the user says Yes: Proceed to Step 6.

6. You MUST archive current state:
   - You MUST create `aidlc-docs/operations/retrofit-archive/`
   - You MUST copy `aidlc-docs/aidlc-state.md` to `aidlc-docs/operations/retrofit-archive/aidlc-state.md`
   - You MUST copy `aidlc-docs/audit.md` to `aidlc-docs/operations/retrofit-archive/audit.md`
   - You MUST NOT delete, move, or regenerate `aidlc-docs/vision/`. A retrofit must not wipe a versioned Vision, Tech Env, feature catalog, or scopes.
7. You MUST reset aidlc-state.md:
   - **SET**: Project Type to `Brownfield (Operations Retrofit)`
   - **KEEP**: Project Information (except Project Type), Workspace State, Code Location Rules, Architectural Decisions
   - **CLEAR**: Extension Configuration table. You MUST leave the section header and empty table columns intact.
   - **CLEAR**: Build and Test Results
   - **RESET**: Stage Progress. You MUST mark Requirements Analysis and all subsequent stages as NOT COMPLETED (`[ ]`). You MUST keep Workspace Detection and Operations Retrofit as `[x]`.
   - **SET**: Current Stage to `INCEPTION - Requirements Analysis`
   - **MANDATORY**: You MUST re-read aidlc-state.md and confirm: (1) Extension Configuration table has the header row but NO data rows, (2) Current Stage is `INCEPTION - Requirements Analysis`, (3) Requirements Analysis and all subsequent stages show `[ ]`, (4) `aidlc-docs/operations/retrofit-archive/aidlc-state.md` exists. You MUST NOT proceed to Step 8 until all 4 checks pass.
8. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
9. You MUST automatically proceed to Create Vision, Tech Env, Features and Scopes (reuse_if_present; do not wipe `aidlc-docs/vision/`). Do not enter Requirements Analysis until `vision_scope` is approved.

## Reverse Engineering (CONDITIONAL - Brownfield Only)

**Execute IF**:
- Existing codebase detected
- No previous reverse engineering artifacts found

**Skip IF**:
- Greenfield project
- Previous reverse engineering artifacts exist

**Execution**:
1. **MANDATORY**: You MUST log start of reverse engineering in audit.md
2. Load all steps from `inception/reverse-engineering.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. Execute reverse engineering:
   - Analyze all packages and components
   - Generate a business overview of the whole system covering the business transactions
   - Generate architecture documentation
   - Generate code structure documentation
   - Generate API documentation
   - Generate component inventory
   - Generate Interaction Diagrams depicting how business transactions are implemented across components (`aidlc-docs/inception/reverse-engineering/interaction-diagrams.md`; see reverse-engineering.md)
   - Generate technology stack documentation
   - Generate dependencies documentation
5. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
6. **Wait for Explicit Approval** (gate `reverse_engineering`): Present detailed completion message (see reverse-engineering.md for message format) - DO NOT PROCEED until user confirms
7. **MANDATORY**: You MUST log user's response in audit.md with complete raw input
8. After approval, proceed to Create Vision, Tech Env, Features and Scopes — not to Requirements Analysis

## Create Vision, Tech Env, Features and Scopes (ALWAYS EXECUTE)

**Always executes** after Workspace Detection (when Reverse Engineering is skipped) or after the Reverse Engineering gate. This is one composite stage with four parts and a single human gate `vision_scope`.

**Parts (load and run in this order)**:
1. `inception/create-vision.md`
2. `inception/create-tech-env.md`
3. `inception/feature-catalog.md`
4. `inception/scope-breakdown.md`

**Execution**:
1. **MANDATORY**: You MUST log start of this composite stage in audit.md
2. Load `common/config.md` values already applied at workflow start (`vision.reuse_policy`, paths)
3. Run the four parts. Honor reuse: do not regenerate versioned Vision/Tech Env from scratch when `reuse_if_present` and the files exist under `aidlc-docs/vision/`
4. Run `python3 -m aidlc_validate scope-in-vision --root PRODUCT_REPO` (blocking)
5. Seed `aidlc-docs/assumptions.md` if it does not exist
6. **Wait for Explicit Approval** (gate `vision_scope`): present Vision, Tech Env, catalog, scopes (in/out), low-confidence features, change proposals, and assumptions. DO NOT start Requirements Analysis until the person approves
7. **MANDATORY**: You MUST log the person's response in audit.md with complete raw input

## Requirements Analysis (ALWAYS EXECUTE - Adaptive Depth)

**Always executes** but depth varies based on request clarity and complexity:
- **Minimal**: Simple, clear request - just document intent analysis
- **Standard**: Normal complexity - gather functional and non-functional requirements
- **Comprehensive**: Complex, high-risk - detailed requirements with traceability

**Execution**:
1. **MANDATORY**: You MUST log any user input during this phase in audit.md
2. Load all steps from `inception/requirements-analysis.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. Execute requirements analysis:
   - Load reverse engineering artifacts (if brownfield)
   - Analyze user request (intent analysis)
   - Determine requirements depth needed
   - Assess current requirements
   - Ask clarifying questions (if needed)
   - Generate requirements document
5. Execute at appropriate depth (minimal/standard/comprehensive)
6. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
7. **No stage gate.** Extension opt-in remains a **blocking question** (`common/assumptions.md`). Other questions go to `aidlc-docs/assumptions.md`. Continue to User Stories (if it will run) or Workflow Planning. Human review is at `inception_end`.

## User Stories (CONDITIONAL)

**INTELLIGENT ASSESSMENT**: Use multi-factor analysis to determine if user stories add value:

**ALWAYS Execute IF** (High Priority Indicators):
- New user-facing features or functionality
- Changes affecting user workflows or interactions
- Multiple user types or personas involved
- Complex business requirements with acceptance criteria needs
- Cross-functional team collaboration required
- Customer-facing API or service changes
- New product capabilities or enhancements

**LIKELY Execute IF** (Medium Priority - Assess Complexity):
- Modifications to existing user-facing features
- Backend changes that indirectly affect user experience
- Integration work that impacts user workflows
- Performance improvements with user-visible benefits
- Security enhancements affecting user interactions
- Data model changes affecting user data or reports

**COMPLEXITY-BASED ASSESSMENT**: For medium priority cases, execute user stories if:
- Request involves multiple components or services
- Changes span multiple user touchpoints
- Business logic is complex or has multiple scenarios
- Requirements have ambiguity that stories could clarify
- Implementation affects multiple user journeys
- Change has significant business impact or risk

**SKIP ONLY IF** (Low Priority - Simple Cases):
- Pure internal refactoring with zero user impact
- Simple bug fixes with clear, isolated scope
- Infrastructure changes with no user-facing effects
- Technical debt cleanup with no functional changes
- Developer tooling or build process improvements
- Documentation-only updates

**ASSESSMENT CRITERIA**: When in doubt, favor inclusion of user stories for:
- Requests with business stakeholder involvement
- Changes requiring user acceptance testing
- Features with multiple implementation approaches
- Work that benefits from shared team understanding
- Projects where requirements clarity is valuable

**ASSESSMENT PROCESS**: 
1. Analyze request complexity and scope
2. Identify user impact (direct or indirect)
3. Evaluate business context and stakeholder needs
4. Consider team collaboration benefits
5. Default to inclusion for borderline cases

**Note**: If Requirements Analysis executed, Stories can reference and build upon those requirements.

**User Stories has two parts within one stage**:
1. **Part 1 - Planning**: Create story plan; apply `stories.*` from config (do not wait for a plan gate)
2. **Part 2 - Generation**: Generate stories and personas

**Execution**:
1. **MANDATORY**: You MUST log any user input during this phase in audit.md
2. Load all steps from `inception/user-stories.md` and `common/inception-autonomy.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. **MANDATORY**: Perform intelligent assessment (Step 1 in user-stories.md) to validate user stories are needed. Skip remains allowed exactly as in v1
5. Load reverse engineering artifacts (if brownfield)
6. If Requirements exist, reference them when creating stories. Apply `stories.format`, `invest_required`, `min_acceptance_criteria`, `max_size`
7. Execute at appropriate depth (minimal/standard/comprehensive)
8. **PART 1 - Planning**: Create the story plan from config; non-blocking questions → `assumptions.md`
9. **PART 2 - Generation**: Generate stories and personas
10. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
11. **No stage gate.** Run `python3 -m aidlc_validate stories --root PRODUCT_REPO` and `traceability`. Continue. Human review is at `inception_end`.

## Workflow Planning (ALWAYS EXECUTE)

1. **MANDATORY**: You MUST log any user input during this phase in audit.md
2. Load all steps from `inception/workflow-planning.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. **MANDATORY**: Load content validation rules from `common/content-validation.md`
5. Load all prior context:
   - Reverse engineering artifacts (if brownfield)
   - Intent analysis
   - Requirements (if executed)
   - User stories (if executed)
6. Execute workflow planning:
   - Determine which phases to execute (Inception, Construction, AND Operations — see workflow-planning.md Step 3.6 for Operations determination; Step 3.5 is Infrastructure Design)
   - Determine depth level for each phase
   - Create multi-package change sequence (if brownfield)
   - Generate workflow visualization (VALIDATE Mermaid syntax before writing)
7. **MANDATORY**: Validate all content before file creation per content-validation.md rules
8. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
9. **No stage gate.** Record High/Critical risk; it feeds design validation. Human override is at `inception_end`. Continue.

## Application Design (CONDITIONAL)

**Execute IF**:
- New components or services needed
- Component methods and business rules need definition
- Service layer design required
- Component dependencies need clarification

**Skip IF**:
- Changes within existing component boundaries
- No new components or methods
- Pure implementation changes

**Execution**:
1. **MANDATORY**: You MUST log any user input during this phase in audit.md
2. Load all steps from `inception/application-design.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. Load reverse engineering artifacts (if brownfield)
5. Execute at appropriate depth (minimal/standard/comprehensive)
6. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
7. **No stage gate.** Check consistency with Tech Env and the current scope. Continue. Human review is at `inception_end`.

## Units Generation (CONDITIONAL)

When User Stories ran, this stage **must** produce at least one `UNIT-`
record, `unit-of-work.md`, an acyclic DAG in `unit-of-work-dependency.md`,
and `unit-of-work-story-map.md`. A single simple unit (the whole
application) is valid. Traceability requires the map whenever stories
exist. Do not skip because there is only one unit.

**Execute IF**:
- User Stories executed this cycle (`stories.md` exists), even if there is only one unit
- Multiple services or modules required
- Complex system requiring structured breakdown
- New data models, APIs, or state as in workflow-planning.md Step 3.3

**Skip IF**:
- User Stories was also skipped (no `stories.md`) AND no decomposition is needed

**Execution**:
1. **MANDATORY**: You MUST log any user input during this phase in audit.md
2. Load all steps from `inception/units-generation.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. Load reverse engineering artifacts (if brownfield)
5. Execute at appropriate depth (minimal/standard/comprehensive)
6. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
7. **No stage gate.** Require an acyclic DAG in `unit-of-work-dependency.md` and honor `units.max_stories_per_unit`. Run `python3 -m aidlc_validate units-dag --root PRODUCT_REPO` and `traceability`. Continue to `inception_end`.

## Gate `inception_end` (ALWAYS after Inception)

Not a generation stage. Present the Inception package and **wait for explicit approval** before Construction:

- Diff of the current scope vs stories (in-scope covered, in-scope missing, extras)
- `aidlc-docs/assumptions.md`
- Check results (`traceability`, `stories` if Stories ran, `units-dag` if Units ran, `assumptions`)
- SKIPs and depths from Workflow Planning, including Operations stages
- Unit DAG and story map
- Extensions opted in and refused

Run `python3 -m aidlc_validate assumptions --root PRODUCT_REPO` before presenting
this gate. A non-zero exit (malformed file or unresolved blocking row) is a
blocking check: fix or escalate; do not start Construction until it passes or
the person decides at this gate.

The person may change any Inception artifact. Do not start Construction until they approve. Log the raw reply in `audit.md`.

---

# 🟢 CONSTRUCTION PHASE

**Purpose**: Detailed design, NFR implementation, and code generation

**Focus**: Determine HOW to build it

**Stages in CONSTRUCTION PHASE**:
- Per-Unit Loop (executes for each unit, DAG order):
  - Functional Design (CONDITIONAL, per-unit)
  - NFR Requirements (CONDITIONAL, per-unit)
  - NFR Design (CONDITIONAL, per-unit)
  - Infrastructure Design (CONDITIONAL, per-unit)
  - Design Validation (ALWAYS after that unit's designs; default `hybrid`)
  - Code Generation (ALWAYS, per-unit)
- Build and Test (ALWAYS - after all units complete; gate `build_and_test`)

**Note**: Each unit is completed fully (design + code) before moving to the next unit.

---

## Per-Unit Loop (Executes for Each Unit)

**For each unit of work, execute the following stages in sequence:**

### Functional Design (CONDITIONAL, per-unit)

**Execute IF**:
- New data models or schemas
- Complex business logic
- Business rules need detailed design

**Skip IF**:
- Simple logic changes
- No new business logic

**Execution**:
1. **MANDATORY**: You MUST log any user input during this stage in audit.md
2. Load all steps from `construction/functional-design.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. Execute functional design for this unit
5. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
6. **No stage gate.** Continue to the next design stage of this unit (or Design Validation when designs for the unit are done).

### NFR Requirements (CONDITIONAL, per-unit)

**Execute IF**:
- Performance requirements exist
- Security considerations needed
- Scalability concerns present
- Tech stack selection required

**Skip IF**:
- No NFR requirements
- Tech stack already determined

**Execution**:
1. **MANDATORY**: You MUST log any user input during this stage in audit.md
2. Load all steps from `construction/nfr-requirements.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. Execute NFR assessment for this unit
5. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
6. **No stage gate.** Continue to NFR Design or Design Validation.

### NFR Design (CONDITIONAL, per-unit)

**Execute IF**:
- NFR Requirements was executed
- NFR patterns need to be incorporated

**Skip IF**:
- No NFR requirements
- NFR Requirements was skipped

**Execution**:
1. **MANDATORY**: You MUST log any user input during this stage in audit.md
2. Load all steps from `construction/nfr-design.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. Execute NFR design for this unit
5. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
6. **No stage gate.** Continue to Infrastructure Design or Design Validation.

### Infrastructure Design (CONDITIONAL, per-unit)

**Execute IF**:
- Infrastructure services need mapping
- Deployment architecture required
- Cloud resources need specification

**Skip IF**:
- No infrastructure changes
- Infrastructure already defined

**Execution**:
1. **MANDATORY**: You MUST log any user input during this stage in audit.md
2. Load all steps from `construction/infrastructure-design.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. Execute infrastructure design for this unit
5. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
6. **No stage gate.** If extensions are active, produce the extension plan rule mapping (keep the v1-operations artifact) and feed it into Design Validation. Do not wait here.
7. Continue to Design Validation for this unit.

### Design Validation (ALWAYS, per-unit, after that unit's designs)

1. Load `construction/design-validation.md`
2. Default `design_validation.mode` is `hybrid`
3. Run executable checks. Use a **separate** LLM reviewer; it must not self-approve
4. Escalate to the person (**named gate `design_validation`**) when a hybrid trigger fires (including `public_contract`), mode is `human`, rework limit is exceeded, or the token budget is exceeded (`pause_and_ask_human`). Write the gate question to a file and present it in the assistant turn. Wait.
5. Write `aidlc-docs/construction/{unit}/design-validation.md`
6. On pass, continue to Code Generation for this unit. On rework, return to the design stages of the same unit

### Code Generation (ALWAYS EXECUTE, per-unit)

**Always executes for each unit**

**Code Generation has two parts within one stage**:
1. **Part 1 - Planning**: Create the code generation plan with checkboxes (no human plan approval in autonomous mode)
2. **Part 2 - Generation**: Execute the plan to generate code, tests, and artifacts

**Execution**:
1. **MANDATORY**: You MUST log any user input during this stage in audit.md
2. Load all steps from `construction/code-generation.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. **PART 1 - Planning**: Write the plan with checkboxes. Do not wait for a person
5. **PART 2 - Generation**: Execute the plan for this unit
6. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
7. **No stage gate.** Continue to the next unit in DAG order, or to Build and Test when units are done. Blocking questions still stop the run (`common/assumptions.md`).

---

## Build and Test (ALWAYS EXECUTE)

1. **MANDATORY**: You MUST log any user input during this phase in audit.md
2. Load all steps from `construction/build-and-test.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. Generate comprehensive build and test instructions:
   - Build instructions for all units
   - Unit test execution instructions
   - Integration test instructions (test interactions between units)
   - Performance test instructions (if applicable)
   - Additional test instructions as needed (contract tests, security tests, e2e tests)
5. Create instruction files in build-and-test/ subdirectory: build-instructions.md, unit-test-instructions.md, integration-test-instructions.md, performance-test-instructions.md, build-and-test-summary.md
6. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
7. **Wait for Explicit Approval** (gate `build_and_test`): Ask: "**Build and test instructions complete. Ready to proceed to Operations stage?**" - DO NOT PROCEED until user confirms. This gate is the door into Operations.
8. **MANDATORY**: You MUST log user's response in audit.md with complete raw input

---

# 🟡 OPERATIONS PHASE

**Purpose**: Validate that Construction correctly implemented all applicable operational rules, deploy the workload to a real environment, and execute post-deployment testing to prove operational readiness.

**Focus**: Verify WHAT was built meets the rules, deploy it, and prove it works

**Stages in OPERATIONS PHASE**:
- Rules Validation (CONDITIONAL) — keep the v1-operations checkpoint
- Deployment (CONDITIONAL) — keep opt-in and v1-operations checkpoints
- Post-Deployment Testing (CONDITIONAL) — keep the v1-operations checkpoint
- Docusaurus Export (ALWAYS)
- Gate `operations`

---

## Rules Validation (CONDITIONAL)

**Execute IF**:
- At least one extension is opted IN (Enabled=Yes / Always Enforced, or a non-skip answer on that prompt)

**Skip IF**:
- No operational extensions were opted IN. Opted OUT means Enabled=No, or that prompt's skip/No option (B, C, or D — whichever letter the opt-in file uses). Do not require the skip letter to be D.

**Prerequisites** (evaluated at execution time, not at planning time):
- Build and Test stage must be complete before this stage executes

**Execution**:
1. **MANDATORY**: You MUST log any user input during this phase in audit.md
2. Load all steps from `operations/rules-validation.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. Execute rules validation:
   - Read Extension Configuration from `aidlc-docs/aidlc-state.md`
   - For each opted-in extension with an `extensions/{domain}/` directory, load rules and validate Construction output
   - Process domains in dependency order (observability → recovery → runbooks → deployment)
   - Generate per-domain validation reports and documentation
   - Generate operations summary
5. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
6. **Wait for Explicit Approval**: Present standardized 2-option completion message - DO NOT PROCEED until user confirms
7. **MANDATORY**: You MUST log user's response in audit.md with complete raw input

---

## Deployment (CONDITIONAL)

**Always Execute**: The execution plan always marks this stage EXECUTE. The opt-in check is performed internally by `operations/deployment.md` at runtime — if the deployment extension is not active, the stage asks the customer whether to proceed and may mark itself SKIPPED.

**Prerequisites** (evaluated at execution time, not at planning time):
- Rules Validation stage must be complete before this stage executes

**Execution**:
1. **MANDATORY**: You MUST log any user input during this phase in audit.md
2. Load all steps from `operations/deployment.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. Execute deployment:
   - **First**: the opt-in/skip question in `operations/deployment.md` (before any infrastructure-design artifact check)
   - If skipped, mark SKIPPED and do not require Construction infrastructure artifacts
   - If proceeding: check upstream artifact prerequisites (infra design, extension plan rule mapping, build summary)
   - Verify environment prerequisites (IaC tool, CLI, credentials, bootstrapping)
   - Verify deployment automation covers all components (infrastructure, application artifacts, assets/data)
   - Deploy infrastructure (IaC stacks)
   - Deploy application artifacts (Lambda code, container images, frontend bundles)
   - Deploy assets/data if applicable (migrations, seed data, config)
   - Verify every deployed component is present and observable in the environment
   - Record deployment outputs
5. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
6. **Wait for Explicit Approval**: Present standardized 2-option completion message - DO NOT PROCEED until user confirms
7. **MANDATORY**: You MUST log user's response in audit.md with complete raw input

---

## Post-Deployment Testing (CONDITIONAL)

**Always Execute**: The execution plan always marks this stage EXECUTE. The opt-in check is performed internally by `operations/post-deployment-testing.md` at runtime — if deployment was skipped or blocked, the stage marks itself SKIPPED.

**Prerequisites** (evaluated at execution time, not at planning time):
- Deployment stage must have completed or been explicitly skipped

**Execution**:
1. **MANDATORY**: You MUST log any user input during this phase in audit.md
2. Load all steps from `operations/post-deployment-testing.md`
3. **MANDATORY**: You MUST record all steps identified in the loaded rule file in `aidlc-docs/step-decision-log.md` before executing any of them.
4. Execute post-deployment testing:
   - Discover test assets from Build and Test and active extensions
   - Build test plan using the testing framework phases (per-rule, per-resource)
   - Execute automatable tests against the deployed environment
   - Document customer-staged tests for later execution
   - Generate test report with evidence
5. **MANDATORY**: You MUST verify the step-decision-log entry for this stage is complete and step counts match before presenting completion. For any missing step: re-execute it and all steps that depend on its output. Update the log. You MUST NOT present completion until all steps are logged.
6. **Wait for Explicit Approval**: Present standardized 2-option completion message - DO NOT PROCEED until user confirms
7. **MANDATORY**: You MUST log user's response in audit.md with complete raw input
8. Continue to Docusaurus Export even if this stage was SKIPPED (no deploy)

## Docusaurus Export (ALWAYS EXECUTE)

Runs after Post-Deployment Testing, including when PDT or Deployment was SKIPPED.

1. **MANDATORY**: You MUST log start of Docusaurus export in audit.md
2. Load `operations/docusaurus-export.md`
3. **Generate** the Docusaurus scaffold **in the product repo** at `operations.docusaurus_path` (default `docs-site`) if `package.json` is missing. Write the files from `operations/docusaurus-scaffold-files.md`. Do **not** read `templates/` from the rules fork at runtime.
4. Export included sources; omit `audit.md`, question files, raw plans, `deployment-deploy.md`. Escape `{` `}` in copied markdown so MDX does not treat `{id}` as JavaScript.
5. Set site language from `operations.docs.language` (default `en`)
6. Run `npm install` and `npm run build` in the docs-site folder
7. Run `python3 -m aidlc_validate export --root PRODUCT_REPO`
8. Write `aidlc-docs/operations/docusaurus-export.md`

## Gate `operations` (ALWAYS after export)

Present `operations-summary.md`, the docs-site, SKIPPED deploy/PDT if any, and the proposed delivered-feature marks. **Wait for Explicit Approval.** Only after approval, mark in-scope features delivered on the Vision. Log the raw reply in `audit.md`.

## Key Principles

- **Adaptive Execution**: For stages not listed in any extension's Stage Enforcement section the model only executes stages that add value.
- **Transparent Planning**: Always show execution plan before starting
- **User Control**: User can request stage inclusion/exclusion
- **Progress Tracking**: Update aidlc-state.md with executed and skipped stages
- **Complete Audit Trail**: Log ALL user inputs and AI responses in audit.md with timestamps
  - **CRITICAL**: Capture user's COMPLETE RAW INPUT exactly as provided
  - **CRITICAL**: Never summarize or paraphrase user input in audit log
  - **CRITICAL**: Log every interaction, not just approvals
- **Quality Focus**: Complex changes get full treatment, simple changes stay efficient
- **Content Validation**: Always validate content before file creation per content-validation.md rules
- **NO EMERGENT BEHAVIOR**: Construction design stages have no 2-option stage gate; named gate `design_validation` (when triggered) and `build_and_test` are the control points. Operations keeps the v1-operations checkpoints plus gate `operations`.

## MANDATORY: Plan-Level Checkbox Enforcement

### MANDATORY RULES FOR PLAN EXECUTION
1. **NEVER complete any work without updating plan checkboxes**
2. **IMMEDIATELY after completing ANY step described in a plan file, mark that step [x]**
3. **This must happen in the SAME interaction where the work is completed**
4. **NO EXCEPTIONS**: Every plan step completion MUST be tracked with checkbox updates

### Two-Level Checkbox Tracking System
- **Plan-Level**: Track detailed execution progress within each stage
- **Stage-Level**: Track overall workflow progress in aidlc-state.md
- **Update immediately**: All progress updates in SAME interaction where work is completed

## Prompts Logging Requirements
- **MANDATORY**: You MUST log EVERY user input (prompts, questions, responses) with timestamp in audit.md
- **MANDATORY**: Capture user's COMPLETE RAW INPUT exactly as provided (never summarize)
- **MANDATORY**: You MUST log every approval prompt with timestamp before asking the user
- **MANDATORY**: Record every user response with timestamp after receiving it
- **CRITICAL**: ALWAYS append changes to EDIT audit.md file, NEVER use tools and commands that completely overwrite its contents
- **CRITICAL**: NEVER use file writing tools and commands that overwrite the entire contents of audit.md, as this causes duplication
- Use ISO 8601 format for timestamps (YYYY-MM-DDTHH:MM:SSZ)
- Include stage context for each entry

### Audit Log Format:
```markdown
## [Stage Name or Interaction Type]
**Timestamp**: [ISO timestamp]
**User Input**: "[Complete raw user input - never summarized]"
**AI Response**: "[AI's response or action taken]"
**Context**: [Stage, action, or decision made]

---
```

### Correct Tool Usage for audit.md

✅ CORRECT:

1. Read the audit.md file
2. Append/Edit the file to make changes

❌ WRONG:

1. Read the audit.md file
2. Completely overwrite the audit.md with the contents of what you read, plus the new changes you want to add to it

## Directory Structure

```text
<WORKSPACE-ROOT>/                   # ⚠️ APPLICATION CODE HERE
├── [project-specific structure]    # Varies by project (see code-generation.md)
│
├── aidlc-docs/                     # 📄 DOCUMENTATION ONLY
│   ├── inception/                  # 🔵 INCEPTION PHASE
│   │   ├── plans/
│   │   ├── reverse-engineering/    # Brownfield only
│   │   ├── requirements/
│   │   ├── user-stories/
│   │   └── application-design/
│   ├── construction/               # 🟢 CONSTRUCTION PHASE
│   │   ├── plans/
│   │   ├── {unit-name}/
│   │   │   ├── functional-design/
│   │   │   ├── nfr-requirements/
│   │   │   ├── nfr-design/
│   │   │   ├── infrastructure-design/
│   │   │   └── code/               # Markdown summaries only
│   │   └── build-and-test/
│   ├── operations/                 # 🟡 OPERATIONS PHASE
│   ├── aidlc-state.md
│   └── audit.md
```

**CRITICAL RULE**:
- Application code: Workspace root (NEVER in aidlc-docs/)
- Documentation: aidlc-docs/ only
- Project structure: See code-generation.md for patterns by project type
