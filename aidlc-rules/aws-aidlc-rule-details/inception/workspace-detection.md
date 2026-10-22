# Workspace Detection

**Purpose**: Determine workspace state and check for existing AI-DLC projects

## Step 1: Check for Existing AI-DLC Project

Check if `aidlc-docs/aidlc-state.md` exists.

**Memory extension off** (no `aidlc-docs/knowledge/.aidlc-memory`):
- **If exists**: Resume from last phase (load context from previous phases)
- **If not exists**: Continue with new project assessment

**Memory extension on**:
- **State exists and this cycle has no human-approved handoff yet**: Resume the in-progress cycle. Run `aidlc_memory.py check --resume` so a hotfix is still visible. Do not open a new cycle and do not run `inception/cycle-start.md`.
- **Latest `aidlc-docs/knowledge/handoff/cycle-NN.md` is human-approved, or the user asks to start a new cycle**: Run `inception/cycle-start.md` before choosing the next phase.
- **State does not exist**: Continue with new project assessment, then run `inception/cycle-start.md`.

## Step 2: Scan Workspace for Existing Code

**Determine if workspace has existing code:**
- Scan workspace for source code files (.java, .py, .js, .ts, .jsx, .tsx, .kt, .kts, .scala, .groovy, .go, .rs, .rb, .php, .c, .h, .cpp, .hpp, .cc, .cs, .fs, etc.)
- Check for build files (pom.xml, package.json, build.gradle, etc.)
- Look for project structure indicators
- Identify workspace root directory (NOT aidlc-docs/)

**Record findings:**
```markdown
## Workspace State
- **Existing Code**: [Yes/No]
- **Programming Languages**: [List if found]
- **Build System**: [Maven/Gradle/npm/etc. if found]
- **Project Structure**: [Monolith/Microservices/Library/Empty]
- **Workspace Root**: [Absolute path]
```

## Step 3: Determine Next Phase

**IF workspace is empty (no existing code)**:
- Set flag: `brownfield = false`
- Next phase: Requirements Analysis

**IF workspace has existing code**:
- Set flag: `brownfield = true`
- **Memory extension on**: Do not compare timestamps. The next phase comes from the approved cycle-start mode: skip goes to Requirements Analysis, delta and full go to Reverse Engineering. On resume, `check --resume` reports new stale files but does not by itself start a new cycle.
- **Memory extension off**: Check for existing reverse engineering artifacts in `aidlc-docs/inception/reverse-engineering/`
  - **IF reverse engineering artifacts exist**:
    - Check if artifacts are stale (compare artifact timestamps against codebase's last significant modification)
    - **IF artifacts are current**: Load them, skip to Requirements Analysis
    - **IF artifacts are stale**: Next phase is Reverse Engineering (rerun to refresh artifacts)
    - **IF user explicitly requests rerun**: Next phase is Reverse Engineering regardless of staleness
  - **IF no reverse engineering artifacts**: Next phase is Reverse Engineering

## Step 4: Create Initial State File

Create `aidlc-docs/aidlc-state.md`:

```markdown
# AI-DLC State Tracking

## Project Information
- **Project Type**: [Greenfield/Brownfield]
- **Start Date**: [ISO timestamp]
- **Current Stage**: INCEPTION - Workspace Detection

## Workspace State
- **Existing Code**: [Yes/No]
- **Reverse Engineering Needed**: [Yes/No]
- **Workspace Root**: [Absolute path]

## Code Location Rules
- **Application Code**: Workspace root (NEVER in aidlc-docs/)
- **Documentation**: aidlc-docs/ only
- **Structure patterns**: See code-generation.md Critical Rules

When the memory extension is on, also record:
- **Cycle**: [number]
- **RE Mode**: [skip/delta/full]

## Stage Progress
[Will be populated as workflow progresses]
```

## Step 5: Present Completion Message

**For Brownfield Projects:**
```markdown
# 🔍 Workspace Detection Complete

Workspace analysis findings:
• **Project Type**: Brownfield project
• [AI-generated summary of workspace findings in bullet points]
• **Next Step**: Proceeding to **Reverse Engineering** to analyze existing codebase...
```

**For Greenfield Projects:**
```markdown
# 🔍 Workspace Detection Complete

Workspace analysis findings:
• **Project Type**: Greenfield project
• **Next Step**: Proceeding to **Requirements Analysis**...
```

## Step 6: Automatically Proceed

- **Memory off**: No user approval required - this is informational only
- **Memory on**: Cycle start waits for approval of skip, delta, or full before the next phase. Resume of an in-progress cycle does not ask again.
- Automatically proceed to next phase:
  - **Memory off, Brownfield**: Reverse Engineering (if no existing artifacts) or Requirements Analysis (if artifacts exist)
  - **Memory off, Greenfield**: Requirements Analysis
  - **Memory on**: the phase chosen by the approved mode, or Requirements Analysis for greenfield
