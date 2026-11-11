# AI-DLC Welcome Message

**Purpose**: This file contains the user-facing welcome message that should be displayed ONCE at the start of any AI-DLC workflow.

---

# 👋 Welcome to AI-DLC (AI-Driven Development Life Cycle)! 👋

I'll guide you through an adaptive software development workflow that intelligently tailors itself to your specific needs.

## What is AI-DLC?

AI-DLC is a structured yet flexible software development process that adapts to your project's needs. Think of it as having an experienced software architect who:

- **Analyzes your requirements** and asks clarifying questions when needed
- **Plans the optimal approach** based on complexity and risk
- **Skips unnecessary steps** for simple changes while providing comprehensive coverage for complex projects
- **Documents everything** so you have a complete record of decisions and rationale
- **Guides you through each phase** with clear checkpoints at the **named gates** only

## The Three-Phase Lifecycle

```
                         User Request
                              |
                              v
        +---------------------------------------+
        |     INCEPTION PHASE                   |
        |     Planning & Application Design     |
        +---------------------------------------+
        | * Workspace Detection (ALWAYS)        |
        | * Reverse Engineering (COND, BF)      |
        |   gate reverse_engineering            |
        | * Vision / Tech Env / catalog /       |
        |   scopes (ALWAYS, composite)          |
        |   gate vision_scope                   |
        | * Requirements Analysis (ALWAYS)      |
        | * User Stories (CONDITIONAL)          |
        | * Workflow Planning (ALWAYS)          |
        | * Application Design (CONDITIONAL)    |
        | * Units Generation (when stories)     |
        |   gate inception_end                  |
        +---------------------------------------+
                              |
                              v
        +---------------------------------------+
        |     CONSTRUCTION PHASE                |
        |     Design, Implementation & Test     |
        +---------------------------------------+
        | * Per-Unit Loop (for each unit):      |
        |   - Functional Design (COND)          |
        |   - NFR Requirements Assess (COND)    |
        |   - NFR Design (COND)                 |
        |   - Infrastructure Design (COND)      |
        |   - Design Validation (ALWAYS)        |
        |     gate design_validation            |
        |     (when hybrid triggers fire)       |
        |   - Code Generation (ALWAYS)          |
        | * Build and Test (ALWAYS)             |
        |   gate build_and_test                 |
        +---------------------------------------+
                              |
                              v
        +---------------------------------------+
        |     OPERATIONS PHASE                  |
        |     Validate, deploy, export docs     |
        +---------------------------------------+
        | * Rules Validation (COND)             |
        | * Deployment (COND; opt-in first)     |
        | * Post-Deployment Testing (COND)      |
        | * Docusaurus Export (ALWAYS)          |
        |   gate operations                     |
        +---------------------------------------+
                              |
                              v
                          Complete
```

### Named gates (these stop; other stages do not)

Inception and Construction generate and continue. Only these checkpoints wait for a person:

1. `reverse_engineering` — after Reverse Engineering (brownfield)
2. `vision_scope` — after Vision, Tech Env, feature catalog, and scopes
3. Extension opt-in — blocking question at Requirements Analysis
4. `inception_end` — Inception package before Construction
5. `design_validation` — when hybrid/human triggers fire (or mode is `human`)
6. `build_and_test` — door into Operations
7. v1-operations checkpoints — Rules Validation, Deployment, PDT when those stages run
8. Deployment opt-in — when the deployment extension is not active (asked **before** requiring infrastructure-design artifacts)
9. `operations` — after Docusaurus export; then mark delivered features

### Phase Breakdown:

**INCEPTION PHASE** - *Planning & Application Design*
- **Purpose**: Determines WHAT to build and WHY
- **Activities**: Workspace detection, reverse engineering (brownfield), Vision / Tech Env / catalog / scopes, requirements, stories, plan, application design, units
- **Output**: Approved vision and scope, requirements, stories, unit DAG, execution plan
- **Your Role**: Answer blocking questions, approve the named gates

**CONSTRUCTION PHASE** - *Detailed Design, Implementation & Test*
- **Purpose**: Determines HOW to build it
- **Activities**: Per-unit design, Design Validation, code generation, build and test
- **Output**: Working code, tests, build instructions
- **Your Role**: Approve Design Validation when it escalates, then `build_and_test`

**OPERATIONS PHASE** - *Validate, deploy, and publish docs*
- **Purpose**: Verify what was built, optionally deploy, export official docs
- **Activities**: Rules Validation (if extensions opted in), Deployment (opt-in first), Post-Deployment Testing, Docusaurus Export into the product `docs-site/`
- **Output**: Validation reports, optional deploy evidence, a built docs site
- **Your Role**: Approve the Operations checkpoints and gate `operations`

## Key Principles:

- ⚡ **Fully Adaptive**: Each stage independently evaluated based on your needs
- 🎯 **Efficient**: Simple changes execute only essential stages
- 📋 **Comprehensive**: Complex changes get full treatment with all safeguards
- 🔍 **Transparent**: Named gates show what happened and what you decide
- 📝 **Documented**: Complete audit trail of all decisions and changes
- 🎛️ **User Control**: You can request stages be included or excluded at a named gate

## What Happens Next:

1. **I'll analyze your workspace** to understand if this is a new or existing project
2. **I'll produce Vision, Tech Env, the feature catalog, and this cycle's scope** and wait at `vision_scope`
3. **I'll gather requirements** (extension opt-in is blocking; other questions go to `assumptions.md`)
4. **I'll generate stories, the plan, design, and units** without per-stage approval
5. **You'll review the Inception package** at `inception_end`
6. **We'll build and test**, then Operations and official docs

The AI-DLC process adapts to:
- 📋 Your intent clarity and complexity
- 🔍 Existing codebase state
- 🎯 Scope and impact of changes
- ⚡ Risk and quality requirements

Let's begin!
