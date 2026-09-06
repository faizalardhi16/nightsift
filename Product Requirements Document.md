# Product Requirements Document
# Night Shift — Agentic Coding Virtual Employee

**Document Version:** 2.0  
**Status:** Draft for Technical Implementation  
**Product Name:** Night Shift  
**Product Type:** Agentic Software Engineering Orchestrator  
**Primary Runtime:** Python  
**Initial Architecture:** Modular Monolith  
**Primary Framework:** FastAPI  
**Workflow Engine:** LangGraph / Explicit State Machine  
**Primary Database:** PostgreSQL  
**Initial Coding Executor:** Codex CLI  
**Default Active Coding Concurrency:** 1  
**Auto Merge:** Disabled

---

# 1. Executive Summary

Night Shift is an Agentic Software Engineering Workflow designed to operate as a **Virtual Software Engineer**.

Its primary responsibility is not directly generating code.

Night Shift acts as an orchestration layer between:

```text
Task Management
Human
Repository
AI Coding Assistant
Validation Environment
Git Provider
```

The system shall autonomously:

```text
Grab Task
    ↓
Understand Requirements
    ↓
Retrieve Repository Context
    ↓
Measure Task Readiness
    ↓
Ask Human if Information is Missing
    ↓
Perform Impact Analysis
    ↓
Create Implementation Plan
    ↓
Generate Coding Prompt
    ↓
Execute AI Coding Assistant
    ↓
Validate Implementation
    ↓
Repair if Required
    ↓
Create Pull Request / Merge Request
    ↓
Continue to Next Task
```

The initial target is not high-volume autonomous coding.

The first product milestone is:

> Night Shift can autonomously convert one sufficiently defined software engineering task into a validated Pull Request requiring minimal human intervention.

---

# 2. Product Vision

The long-term goal is to allow engineering teams to prepare a software backlog before the end of the working day and allow Night Shift to process those tasks autonomously.

Example:

```text
Developer finishes work at 18:00
            ↓
50 Tasks available in backlog
            ↓
Night Shift starts
            ↓
Task #1 processed
            ↓
Task #2 processed
            ↓
Task #3 requires clarification
            ↓
Night Shift asks via Telegram
            ↓
Task #4 continues
            ↓
...
            ↓
Developer returns next day
            ↓
Several Pull Requests ready for review
```

Night Shift should eventually behave more like a software engineering employee than a traditional coding assistant.

---

# 3. Product Positioning

Night Shift is not primarily:

> AI Coding Agent

Night Shift is:

> **An Agentic Software Engineering Orchestrator that transforms development tasks into validated Pull Requests by using AI Coding Assistants as execution tools.**

Examples of coding execution tools:

- Codex CLI
- Claude Code
- OpenCode
- Future internal coding agents

These tools represent the **hands** of Night Shift.

Night Shift itself contains:

```text
Workflow
Reasoning
Context
Memory
Planning
Validation
Control
```

---

# 4. Product Principles

## 4.1 Workflow First

Night Shift must use an explicit workflow/state machine.

The LLM must not control the complete application autonomously.

Correct architecture:

```text
State Machine
   │
   ├── Deterministic Rule
   ├── LLM Reasoning
   ├── Tool Execution
   ├── Validation
   └── State Transition
```

Avoid:

```text
One huge autonomous agent
        ↓
"Figure everything out"
        ↓
Unpredictable execution
```

---

# 5. Evidence Over LLM Confidence

Night Shift shall not trust self-reported confidence such as:

```json
{
  "confidence": 95
}
```

Task readiness shall instead be calculated from identifiable evidence.

LLMs may determine whether individual criteria are satisfied.

The application calculates the final score.

---

# 6. Human-in-the-Loop

Night Shift must stop autonomous implementation whenever significant requirements remain ambiguous.

Instead of guessing, it shall request clarification.

Default communication channel for V1:

```text
Telegram
```

Night Shift shall ask focused questions rather than general questions.

---

# 7. Human Review Before Merge

Night Shift V1 shall be permitted to:

```text
Create branch
Modify code
Run commands
Create commits
Push branch
Create PR/MR
```

Night Shift V1 shall not:

```text
Merge PR automatically
Deploy production
Modify protected main branch directly
```

---

# 8. Primary Goals

Night Shift V1 must support:

- task retrieval;
- sequential task processing;
- workflow persistence;
- requirement analysis;
- Task Readiness scoring;
- Telegram clarification;
- workflow interruption and resume;
- repository context retrieval;
- codebase impact analysis;
- implementation planning;
- coding prompt generation;
- AI coding agent execution;
- build execution;
- lint execution;
- automated testing;
- code diff inspection;
- acceptance criteria validation;
- bounded automated repair;
- Git branch management;
- commit generation;
- PR/MR generation;
- external task status updates;
- audit logging.

---

# 9. Non-Goals

Night Shift V1 shall not support:

- automatic merge;
- automatic production deployment;
- unrestricted shell execution;
- arbitrary infrastructure modification;
- multiple active coding tasks;
- production database access;
- autonomous architecture decisions with high business impact;
- unlimited repair attempts;
- automatic acceptance of ambiguous requirements;
- fully autonomous task decomposition of large epics.

---

# 10. Recommended Technology Stack

Night Shift V1 shall use a Python-first architecture.

## Core

```text
Python 3.12+
FastAPI
Pydantic
SQLAlchemy
Alembic
PostgreSQL
```

## Workflow

```text
LangGraph
```

or an equivalent explicit workflow implementation.

## AI / Agent Integration

Provider adapters should support:

```text
OpenAI
Anthropic
Local/OpenAI-compatible models
```

The orchestration layer shall remain model-independent.

## Coding Executors

Initial:

```text
Codex CLI
```

Future adapters:

```text
Claude Code
OpenCode
Other coding CLIs
```

## Git

Preferred execution approach:

```text
Git CLI
Git worktree
```

GitPython may be used for metadata operations, but raw Git CLI should remain available.

## Communication

```text
Telegram Bot API
```

## Source Control Provider

At least one provider shall be supported in V1:

```text
GitHub
or
GitLab
```

Integration must use an abstraction layer so both can eventually be supported.

---

# 11. Why Python First

Night Shift's primary complexity is centered on:

```text
Agent orchestration
Context retrieval
LLM evaluation
Semantic search
Prompt generation
Human-in-the-loop
Evaluation
Agent testing
```

Python provides strong tooling for these use cases.

V1 should therefore avoid unnecessary cross-language architecture.

Recommended V1:

```text
Python Modular Monolith
```

rather than:

```text
NestJS
+
Python
+
Message Queue
+
Multiple Microservices
```

The architecture may later split into:

```text
NestJS Control Plane
        +
Python Agent Runtime
```

when organizational scale requires it.

---

# 12. High-Level System Architecture

```text
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │    Night Shift API  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Workflow Engine     │
                         │ LangGraph / FSM     │
                         └──────────┬──────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
      Task Provider          Human Gateway           Git Provider
      Jira/GitLab/etc          Telegram              GitHub/GitLab
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Context Engine    │
                         └──────────┬──────────┘
                                    │
                       ┌────────────┼────────────┐
                       │                         │
                       ▼                         ▼
                Repository Search         Codebase Memory
                       │                         │
                       └────────────┬────────────┘
                                    │
                                    ▼
                         Requirement Analyzer
                                    │
                                    ▼
                           Impact Analyzer
                                    │
                                    ▼
                             Task Planner
                                    │
                                    ▼
                           Prompt Compiler
                                    │
                                    ▼
                          Coding Agent Adapter
                       ┌───────────┼────────────┐
                       │           │            │
                     Codex       Claude      OpenCode
                       │
                       ▼
                              Validation
                                    │
                          ┌─────────┴─────────┐
                          │                   │
                         FAIL                PASS
                          │                   │
                          ▼                   ▼
                        Repair            PR Creator
```

---

# 13. V1 Deployment Architecture

V1 may initially run on one machine or VPS.

```text
Docker Compose
│
├── nightshift-api
│     Python + FastAPI
│
├── nightshift-worker
│     Workflow execution
│
├── postgres
│
└── optional redis
```

Redis shall remain optional in initial development.

It may be introduced for:

- distributed locks;
- queues;
- pub/sub;
- caching;
- future concurrency.

---

# 14. Modular Monolith Architecture

The source code should be organized by domain.

Recommended structure:

```text
nightshift/
│
├── app/
│   │
│   ├── main.py
│   │
│   ├── config/
│   │   ├── settings.py
│   │   └── logging.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   └── schemas/
│   │
│   ├── workflow/
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── transitions.py
│   │   └── nodes/
│   │       ├── grab_task.py
│   │       ├── build_context.py
│   │       ├── assess_readiness.py
│   │       ├── request_clarification.py
│   │       ├── analyze_impact.py
│   │       ├── create_plan.py
│   │       ├── compile_prompt.py
│   │       ├── execute_coding.py
│   │       ├── validate.py
│   │       ├── repair.py
│   │       └── create_pr.py
│   │
│   ├── domains/
│   │   ├── tasks/
│   │   ├── repositories/
│   │   ├── executions/
│   │   ├── clarification/
│   │   └── validation/
│   │
│   ├── agents/
│   │   ├── requirement_agent.py
│   │   ├── impact_agent.py
│   │   ├── planning_agent.py
│   │   └── review_agent.py
│   │
│   ├── coding/
│   │   ├── base.py
│   │   ├── codex.py
│   │   ├── claude_code.py
│   │   └── opencode.py
│   │
│   ├── integrations/
│   │   ├── task_provider/
│   │   ├── telegram/
│   │   ├── git_provider/
│   │   └── llm/
│   │
│   ├── repository_intelligence/
│   │   ├── scanner.py
│   │   ├── code_search.py
│   │   ├── git_history.py
│   │   └── context_builder.py
│   │
│   ├── skills/
│   │
│   ├── sandbox/
│   │   ├── workspace.py
│   │   └── command_runner.py
│   │
│   ├── persistence/
│   │   ├── database.py
│   │   └── repositories/
│   │
│   └── security/
│       ├── secret_filter.py
│       ├── command_policy.py
│       └── repository_policy.py
│
├── skills/
│   ├── task-analysis/
│   ├── requirement-readiness/
│   ├── codebase-impact-analysis/
│   ├── implementation-planning/
│   ├── code-review/
│   └── git-pr/
│
├── tests/
│
├── migrations/
│
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

# 15. Workflow State

LangGraph state should represent the complete workflow context.

Conceptual Python model:

```python
class NightShiftState(TypedDict):
    execution_id: str
    task_id: str

    current_state: str

    task: dict
    repository: dict

    context: dict

    readiness_score: int
    readiness_analysis: dict

    clarification: dict | None

    impact_analysis: dict | None

    implementation_plan: dict | None

    compiled_prompt: str | None

    coding_result: dict | None

    validation_result: dict | None

    repair_attempt: int

    branch_name: str | None
    workspace_path: str | None

    pull_request: dict | None

    error: dict | None
```

All significant workflow transitions shall be persisted.

---

# 16. Internal State Machine

Required states:

```text
QUEUED

CLAIMED

CONTEXT_BUILDING

REQUIREMENT_ANALYSIS

NEED_CLARIFICATION

WAITING_USER

READY_TO_PLAN

IMPACT_ANALYSIS

PLANNING

READY_TO_CODE

WORKSPACE_PREPARATION

CODING

VALIDATING

REPAIRING

REVIEWING

READY_FOR_PR

PR_CREATING

PR_CREATED

COMPLETED

FAILED

BLOCKED
```

---

# 17. State Transition Example

```text
QUEUED
   ↓
CLAIMED
   ↓
CONTEXT_BUILDING
   ↓
REQUIREMENT_ANALYSIS
   ↓
Readiness >= 90?
   │
   ├── NO
   │     ↓
   │ NEED_CLARIFICATION
   │     ↓
   │ WAITING_USER
   │     ↓
   │ REQUIREMENT_ANALYSIS
   │
   └── YES
         ↓
    IMPACT_ANALYSIS
         ↓
       PLANNING
         ↓
    READY_TO_CODE
         ↓
WORKSPACE_PREPARATION
         ↓
       CODING
         ↓
     VALIDATING
         │
      Pass?
     /    \
   No      Yes
   │        │
REPAIRING REVIEWING
   │        │
   └────┬───┘
        ↓
   READY_FOR_PR
        ↓
    PR_CREATING
        ↓
     PR_CREATED
        ↓
     COMPLETED
```

---

# 18. Task Queue

Night Shift must support multiple queued tasks but only one active coding task.

Default:

```text
MAX_ACTIVE_CODING_TASKS = 1
```

The task scheduler shall prioritize tasks using configurable rules.

V1 default:

```text
Priority
then
Created Date
```

Equivalent:

```text
ORDER BY priority DESC, created_at ASC
```

---

# 19. Waiting Tasks

A clarification-blocked task must not block all Night Shift activity.

Example:

```text
TASK-101
WAITING_USER

TASK-102
QUEUED
```

Night Shift may process TASK-102.

However only one task may hold:

```text
CODING
VALIDATING
REPAIRING
REVIEWING
```

at any given time.

---

# 20. Task Claiming

To prevent duplicate processing, tasks must be claimed atomically.

Conceptually:

```sql
SELECT *
FROM task_execution
WHERE state = 'QUEUED'
ORDER BY priority DESC, created_at
FOR UPDATE SKIP LOCKED
LIMIT 1;
```

This also prepares the architecture for future multiple workers.

---

# 21. Context Builder

Context Builder shall normalize information from:

```text
Task
Repository
Documentation
Git History
Skills
Code Search
Configuration
Previous Clarification
```

Output:

```python
TaskContext
```

Example:

```json
{
  "task": {
    "id": "INV-123",
    "title": "Export invoice",
    "description": "..."
  },
  "repository": {
    "name": "invoice-api",
    "language": "typescript",
    "framework": "nestjs"
  },
  "acceptance_criteria": [],
  "technical_context": {},
  "related_code": [],
  "constraints": []
}
```

---

# 22. Repository Discovery

Night Shift should inspect the repository before asking humans technical questions.

The system may inspect:

```text
README
package.json
pyproject.toml
pom.xml
go.mod
docker-compose.yml
Dockerfile
CI configuration
source directories
tests
architecture files
AGENTS.md
CLAUDE.md
repository-specific Night Shift config
```

---

# 23. Night Shift Repository Configuration

Repositories may provide:

```text
.nightshift.yml
```

Example:

```yaml
project:
  name: invoice-service

repository:
  default_branch: main

runtime:
  language: node
  version: 22

installation:
  command: npm ci

validation:
  build:
    command: npm run build

  lint:
    command: npm run lint

  unit_test:
    command: npm test

  integration_test:
    command: npm run test:e2e

coding:
  default_agent: codex

workflow:
  readiness_threshold: 90
  max_repair_attempts: 3

git:
  branch_prefix: nightshift

security:
  forbidden_paths:
    - .env
    - secrets/
```

Repository-level configuration overrides platform defaults.

---

# 24. Task Readiness Model

The default readiness score shall be:

| Criteria | Weight |
|---|---:|
| Objective clear | 15 |
| Acceptance Criteria clear | 20 |
| Repository identified | 10 |
| Relevant module/context found | 10 |
| Expected behavior clear | 15 |
| Edge cases sufficiently understood | 10 |
| Test expectations known | 10 |
| Dependencies understood | 5 |
| Target branch known | 5 |
| **Total** | **100** |

---

# 25. Readiness Algorithm

LLM output should be structured.

Example:

```json
{
  "objective": {
    "satisfied": true,
    "reason": "Task explicitly requests XLSX export."
  },
  "acceptance_criteria": {
    "satisfied": false,
    "reason": "Maximum record count is not defined."
  }
}
```

The application then calculates:

```python
score = sum(
    criterion.weight
    for criterion in criteria
    if criterion.satisfied
)
```

LLM must not directly determine the final readiness score.

---

# 26. Readiness Threshold

Default:

```text
90–100
READY

70–89
CLARIFICATION_REQUIRED

0–69
INSUFFICIENT_REQUIREMENT
```

Both ranges below 90 shall enter clarification mode.

The severity may influence question count and task status.

---

# 27. Clarification Engine

Night Shift shall determine missing requirement fields.

Example:

```json
{
  "missing": [
    "export_format",
    "export_scope",
    "maximum_records"
  ]
}
```

The Clarification Agent shall transform these into concise questions.

---

# 28. Telegram Interaction

Example:

```text
🌙 Night Shift — Clarification Required

Task
INV-123 — Export Invoice

Readiness
72 / 100

I need 3 decisions:

1. Export format?
A. XLSX
B. CSV

2. Export source?
A. Current filtered result
B. Selected rows
C. All records

3. Maximum export records?

Reply:
1A
2A
10000
```

---

# 29. Clarification Session

A clarification record shall include:

```text
clarification_session

id
task_execution_id

question_payload
message_id

status

created_at
answered_at

raw_answer
parsed_answer
```

Possible status:

```text
OPEN
ANSWERED
EXPIRED
CANCELLED
```

---

# 30. Human Response Processing

The incoming Telegram message shall:

```text
Receive webhook
      ↓
Identify clarification session
      ↓
Parse response
      ↓
Store raw response
      ↓
Normalize answer
      ↓
Update Task Context
      ↓
Resume workflow
```

---

# 31. Impact Analysis

After readiness passes, Night Shift shall inspect technical impact.

Output model:

```json
{
  "affected_modules": [],
  "affected_files": [],
  "database_change": false,
  "api_change": true,
  "dependency_change": false,
  "risks": [],
  "tests_required": []
}
```

---

# 32. Impact Analysis Safety

Night Shift must distinguish between:

```text
Likely affected
Confirmed affected
Possible regression
```

It should avoid telling the Coding Agent that uncertain assumptions are facts.

Example:

```json
{
  "file": "invoice.service.ts",
  "confidence": "confirmed",
  "evidence": "existing invoice list implementation"
}
```

---

# 33. Implementation Plan

Implementation Planner must create structured steps.

Example:

```json
{
  "steps": [
    {
      "order": 1,
      "action": "Inspect current invoice filtering logic."
    },
    {
      "order": 2,
      "action": "Implement XLSX export service."
    },
    {
      "order": 3,
      "action": "Reuse existing invoice query filters."
    },
    {
      "order": 4,
      "action": "Add tests."
    }
  ]
}
```

---

# 34. Plan Validation

Before coding, Night Shift should verify that:

```text
Every acceptance criterion is addressed
Every significant impacted module has a plan
Test strategy exists
No unresolved blocker remains
```

The workflow shall not transition to READY_TO_CODE if a planning blocker exists.

---

# 35. Skill System

Night Shift shall support task-specific reusable instructions.

Directory:

```text
skills/
│
├── task-analysis/
│   └── SKILL.md
│
├── requirement-readiness/
│   └── SKILL.md
│
├── codebase-impact-analysis/
│   └── SKILL.md
│
├── implementation-planning/
│   └── SKILL.md
│
├── backend-nestjs/
│   └── SKILL.md
│
├── frontend-react/
│   └── SKILL.md
│
├── database-oracle/
│   └── SKILL.md
│
├── database-postgresql/
│   └── SKILL.md
│
├── unit-testing/
│   └── SKILL.md
│
├── code-review/
│   └── SKILL.md
│
└── git-pr/
    └── SKILL.md
```

---

# 36. Skill Resolver

The Skill Resolver shall inspect:

```text
Task classification
Repository stack
Affected components
Database technology
Test strategy
```

Example:

```text
Task:
Implement Oracle repository query in NestJS
```

Resolved skills:

```text
task-analysis
codebase-impact-analysis
backend-nestjs
database-oracle
unit-testing
code-review
git-pr
```

Only required skills should enter the Coding Agent context.

---

# 37. Prompt Compiler

Prompt Compiler converts structured workflow information into Coding Agent instructions.

Inputs:

```text
Task Context
Impact Analysis
Implementation Plan
Skills
Repository Constraints
Acceptance Criteria
Definition of Done
```

Output:

```text
CompiledCodingPrompt
```

---

# 38. Compiled Prompt Format

Recommended:

```text
ROLE

TASK

OBJECTIVE

BUSINESS CONTEXT

REPOSITORY CONTEXT

CURRENT IMPLEMENTATION

AFFECTED MODULES

FILES TO INSPECT

IMPLEMENTATION PLAN

ACCEPTANCE CRITERIA

TECHNICAL CONSTRAINTS

REPOSITORY RULES

SECURITY CONSTRAINTS

TEST REQUIREMENTS

DEFINITION OF DONE

OUTPUT EXPECTATION
```

---

# 39. Coding Agent Abstraction

Python interface:

```python
from abc import ABC, abstractmethod


class CodingAgent(ABC):

    @abstractmethod
    async def execute(
        self,
        request: "CodingRequest",
    ) -> "CodingResult":
        ...
```

Implementations:

```python
class CodexCodingAgent(CodingAgent):
    ...

class ClaudeCodeCodingAgent(CodingAgent):
    ...

class OpenCodeCodingAgent(CodingAgent):
    ...
```

Core workflow must not depend directly on a CLI implementation.

---

# 40. Coding Request

Example:

```python
class CodingRequest(BaseModel):
    task_id: str

    repository_path: str
    workspace_path: str

    prompt: str

    timeout_seconds: int

    allowed_paths: list[str]
```

---

# 41. Coding Result

Example:

```python
class CodingResult(BaseModel):
    success: bool

    exit_code: int | None

    stdout: str
    stderr: str

    modified_files: list[str]

    started_at: datetime
    completed_at: datetime
```

---

# 42. Workspace Isolation

Every coding task shall receive a dedicated Git worktree.

Example:

```text
/repos/invoice-service
```

Night Shift creates:

```text
/workspaces/INV-123
```

using:

```bash
git worktree add \
  /workspaces/INV-123 \
  -b nightshift/INV-123 \
  origin/main
```

The coding assistant shall execute only inside this workspace.

---

# 43. Workspace Lifecycle

```text
Create Worktree
      ↓
Install Dependencies
      ↓
Baseline Validation
      ↓
Coding
      ↓
Validation
      ↓
Commit
      ↓
Push
      ↓
Create PR
      ↓
Archive Logs
      ↓
Clean Workspace
```

Workspaces for BLOCKED tasks may be preserved.

---

# 44. Baseline Validation

Night Shift should validate the repository before making code changes.

Example:

```text
npm ci
npm run build
npm test
```

If the repository already fails before modification, Night Shift shall record:

```text
BASELINE_FAILURE
```

This prevents Night Shift from incorrectly attributing existing failures to generated code.

---

# 45. Command Runner

Night Shift must not use unrestricted shell execution.

All command execution shall pass through:

```python
CommandRunner
```

Conceptual interface:

```python
class CommandRunner:

    async def execute(
        self,
        command: list[str],
        cwd: Path,
        timeout: int,
    ) -> CommandResult:
        ...
```

---

# 46. Command Policies

The runner shall reject commands containing forbidden operations.

Examples:

```text
rm -rf /
sudo
shutdown
reboot
mkfs
force push
direct push main
production database commands
```

Configuration should allow repository-specific commands.

---

# 47. Validation Pipeline

Default:

```text
Baseline Diff Check
      ↓
Build
      ↓
Lint
      ↓
Unit Test
      ↓
Integration Test
      ↓
Static Analysis
      ↓
Git Diff Review
      ↓
Acceptance Criteria Review
```

Validation configuration is repository-specific.

---

# 48. Validation Result

Example:

```json
{
  "build": {
    "status": "PASS"
  },
  "lint": {
    "status": "PASS"
  },
  "unit_tests": {
    "status": "PASS",
    "passed": 34,
    "failed": 0
  },
  "acceptance_criteria": {
    "AC1": "PASS",
    "AC2": "PASS",
    "AC3": "PASS"
  },
  "diff_review": {
    "status": "PASS"
  }
}
```

---

# 49. QA Critic

Night Shift shall have an independent review phase.

The reviewer shall inspect:

```text
Git diff
Task objective
Acceptance criteria
Implementation plan
Test output
Potential regression
Unexpected changes
```

It must not simply trust the Coding Agent statement:

```text
"Task completed successfully."
```

---

# 50. Unrelated Change Detection

Night Shift shall identify files modified outside expected task scope.

Example:

Expected:

```text
invoice.controller.ts
invoice.service.ts
invoice.service.spec.ts
```

Actual:

```text
invoice.controller.ts
invoice.service.ts
invoice.service.spec.ts
auth.service.ts
package-lock.json
```

Night Shift should investigate:

```text
auth.service.ts
```

before creating PR.

---

# 51. Repair Loop

When validation fails:

```text
Validation Failure
      ↓
Failure Analyzer
      ↓
Repair Context
      ↓
Coding Agent
      ↓
Validation
```

Default:

```text
MAX_REPAIR_ATTEMPTS = 3
```

---

# 52. Repair Context

The coding assistant should receive:

```text
Original task
Original implementation plan
Current git diff
Exact failed command
Error output
Previous repair attempts
```

It must not receive only:

```text
"Tests failed, fix it."
```

---

# 53. Repair Termination

After maximum attempts:

```text
state = BLOCKED
```

Night Shift shall preserve:

```text
Branch
Worktree
Agent logs
Failed commands
Git diff
Validation logs
Repair history
```

---

# 54. Pull Request Creation

Night Shift shall create a PR only when all configured blocking checks pass.

Example title:

```text
feat(invoice): add invoice XLSX export
```

PR description:

```text
Task
INV-123

Summary
Implemented invoice export to XLSX.

Implementation
- Added export endpoint
- Added InvoiceExportService
- Reused existing invoice filters
- Added validation
- Added automated tests

Validation
✅ Build
✅ Lint
✅ Unit tests
✅ Integration tests

Acceptance Criteria
✅ AC1
✅ AC2
✅ AC3

Risk
Low

Branch
nightshift/INV-123

Generated by
🌙 Night Shift
```

---

# 55. Commit Policy

Commit messages shall follow repository conventions when known.

Fallback:

```text
<type>(<scope>): <description>
```

Example:

```text
feat(invoice): add xlsx export
```

---

# 56. Git Restrictions

Night Shift V1 shall prohibit:

```text
git push --force
direct push to main
branch deletion of non-Night-Shift branches
rewriting repository history
automatic merge
```

---

# 57. Database Model

Recommended entities:

```text
projects

repositories

task_executions

task_contexts

readiness_assessments

clarification_sessions

impact_analyses

implementation_plans

agent_executions

validation_runs

repair_attempts

git_operations

pull_requests

workflow_events
```

---

# 58. Task Execution Table

Conceptual PostgreSQL schema:

```sql
CREATE TABLE task_executions (
    id UUID PRIMARY KEY,

    external_task_id VARCHAR(255) NOT NULL,

    project_id UUID NOT NULL,
    repository_id UUID NOT NULL,

    state VARCHAR(50) NOT NULL,

    readiness_score INTEGER,

    priority INTEGER DEFAULT 0,

    active_coding BOOLEAN DEFAULT FALSE,

    branch_name VARCHAR(255),
    workspace_path TEXT,

    repair_attempt INTEGER DEFAULT 0,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    failure_reason TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 59. Workflow Event Table

Every transition should produce an append-only event.

```sql
CREATE TABLE workflow_events (
    id UUID PRIMARY KEY,

    task_execution_id UUID NOT NULL,

    event_type VARCHAR(100) NOT NULL,

    from_state VARCHAR(50),
    to_state VARCHAR(50),

    payload JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

This creates an auditable execution timeline.

---

# 60. Agent Execution Table

```sql
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY,

    task_execution_id UUID NOT NULL,

    agent_type VARCHAR(50) NOT NULL,

    model VARCHAR(255),

    prompt TEXT,

    response TEXT,

    success BOOLEAN,

    input_tokens BIGINT,
    output_tokens BIGINT,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
```

Sensitive content must be sanitized before persistence.

---

# 61. REST API

V1 API examples:

```text
GET /api/v1/tasks

GET /api/v1/tasks/{execution_id}

POST /api/v1/tasks/{execution_id}/retry

POST /api/v1/tasks/{execution_id}/cancel

GET /api/v1/tasks/{execution_id}/events

GET /api/v1/tasks/{execution_id}/validation

POST /api/v1/workflow/start

POST /api/v1/workflow/stop

GET /api/v1/workflow/status

POST /api/v1/webhooks/telegram

POST /api/v1/webhooks/git
```

---

# 62. Worker Architecture

Long-running coding operations shall not execute directly inside request handlers.

FastAPI:

```text
HTTP/API
```

Worker:

```text
Workflow Execution
```

V1 may use:

```text
asyncio background worker
```

or a separate process using the same database.

Future:

```text
Temporal worker
```

---

# 63. Locking

To enforce one active coding task, the system shall use:

```text
Database advisory lock
```

or equivalent distributed locking.

Concept:

```text
nightshift-global-coding-lock
```

Only one execution may enter:

```text
WORKSPACE_PREPARATION
CODING
VALIDATING
REPAIRING
REVIEWING
```

at once.

---

# 64. External Task Provider Interface

```python
class TaskProvider(ABC):

    async def get_candidates(self) -> list["ExternalTask"]:
        ...

    async def get_task(self, task_id: str) -> "ExternalTask":
        ...

    async def update_status(
        self,
        task_id: str,
        status: str,
    ) -> None:
        ...
```

Possible implementations:

```text
JiraTaskProvider
GitLabIssueProvider
GitHubIssueProvider
DatabaseTaskProvider
```

---

# 65. Git Provider Interface

```python
class GitProvider(ABC):

    async def create_pull_request(
        self,
        request: "PullRequestRequest",
    ) -> "PullRequestResult":
        ...

    async def add_comment(
        self,
        pull_request_id: str,
        comment: str,
    ) -> None:
        ...
```

Possible implementations:

```text
GitHubProvider
GitLabProvider
```

---

# 66. LLM Provider Abstraction

Night Shift shall avoid tight coupling to one model.

Concept:

```python
class LLMProvider(ABC):

    async def structured_completion(
        self,
        prompt: str,
        schema: type[BaseModel],
    ) -> BaseModel:
        ...
```

Possible implementations:

```text
OpenAIProvider
AnthropicProvider
OpenAICompatibleProvider
```

---

# 67. Structured Output Requirement

Whenever an LLM decision affects state transition, structured responses should be required.

Avoid:

```text
"The task seems ready."
```

Prefer:

```json
{
  "ready": true,
  "missing_requirements": [],
  "blocking_ambiguities": []
}
```

Pydantic shall validate the output.

Invalid responses shall be retried using a bounded parser retry policy.

---

# 68. Observability

Night Shift must expose a timeline such as:

```text
21:00:01 TASK-123 CLAIMED

21:00:02 CONTEXT_BUILDING

21:00:15 REQUIREMENT_ANALYSIS

21:00:19 READINESS = 82

21:00:20 TELEGRAM CLARIFICATION SENT

21:12:03 USER RESPONSE RECEIVED

21:12:08 READINESS = 96

21:12:09 IMPACT_ANALYSIS

21:12:17 PLANNING

21:12:25 WORKSPACE_CREATED

21:12:30 CODEX STARTED

21:20:44 CODEX FINISHED

21:20:45 VALIDATION STARTED

21:21:10 TEST FAILED

21:21:11 REPAIR_ATTEMPT_1

21:24:10 TEST PASS

21:24:40 PR CREATED

21:24:41 COMPLETED
```

---

# 69. Metrics

Important metrics:

```text
Tasks Claimed

Tasks Completed

Tasks Blocked

Readiness Pass Rate

Clarification Rate

Average Clarifications per Task

Coding Success Rate

First-Pass Validation Rate

Repair Rate

Repair Success Rate

PR Creation Rate

PR Acceptance Rate

Human Intervention per PR

Average Cost per Task

Average Tokens per Task

Average Execution Duration
```

---

# 70. Primary Product Metric

The most meaningful initial metric is:

> **Human Interventions per Successful Pull Request**

The target direction is:

```text
Lower is better
```

---

# 71. Logging

Logs shall use structured JSON where possible.

Example:

```json
{
  "event": "VALIDATION_FAILED",
  "execution_id": "abc-123",
  "task_id": "INV-123",
  "command": "npm test",
  "repair_attempt": 0,
  "timestamp": "..."
}
```

---

# 72. Security Model

Night Shift shall follow least privilege.

Separate credentials should be used for:

```text
Task Provider
Git Provider
Telegram
LLM
```

No production infrastructure credentials should be available to the V1 coding runtime.

---

# 73. Secret Protection

Before sending context to any external model, Night Shift shall inspect content for secrets.

Potential secrets:

```text
API keys
Bearer tokens
Passwords
Private keys
Database credentials
.env values
```

Sensitive values should be masked:

```text
sk-abc123
```

becomes:

```text
[REDACTED_OPENAI_KEY]
```

---

# 74. File Access Policy

Coding agents shall be restricted to the worktree.

Forbidden by default:

```text
/home/*
/root/*
~/.ssh
environment secrets
other repositories
host filesystem
```

---

# 75. Prompt Injection Protection

Repository files may contain malicious or irrelevant agent instructions.

Night Shift shall establish instruction priority:

```text
System Security Policy
        ↓
Night Shift Platform Policy
        ↓
Project Configuration
        ↓
Approved Skills
        ↓
Task
        ↓
Repository Content
```

Repository content must be treated as data unless explicitly designated as trusted project instructions.

---

# 76. Retry Policies

Network/API operations:

```text
Maximum retries: configurable
Default: 3
Exponential backoff
```

Coding repair:

```text
Default: 3
```

LLM structured output parser retries:

```text
Default: 2
```

Retry classes must remain separated.

---

# 77. Failure Classification

Failures should be categorized.

```text
REQUIREMENT_FAILURE

TASK_PROVIDER_FAILURE

REPOSITORY_FAILURE

DEPENDENCY_INSTALL_FAILURE

CODING_AGENT_FAILURE

VALIDATION_FAILURE

REPAIR_EXHAUSTED

GIT_FAILURE

PR_CREATION_FAILURE

SECURITY_POLICY_FAILURE

WORKFLOW_INTERNAL_FAILURE
```

---

# 78. Telegram Completion Notification

Success:

```text
🌙 Night Shift completed INV-123

Task
Export Invoice to XLSX

Status
PR Ready for Review

Validation
✅ Build
✅ Lint
✅ 34 Unit Tests
✅ Integration Tests

Pull Request
#482

Repair Attempts
1

Branch
nightshift/INV-123
```

Failure:

```text
🌙 Night Shift blocked INV-124

Reason
Validation failed after 3 repair attempts.

Branch preserved:
nightshift/INV-124

Human review required.
```

---

# 79. V1 Integration Scope

Recommended V1 integrations:

```text
Task source:
One provider only

Human channel:
Telegram

Git:
One provider only

Coding:
Codex

LLM:
One provider

Repository:
One repository at a time
```

Avoid implementing every provider in the first release.

---

# 80. Recommended V1 Product Configuration

A practical first implementation:

```text
Task:
GitLab Issue or Jira

Repository:
GitLab/GitHub

Orchestrator:
Python + LangGraph

API:
FastAPI

Database:
PostgreSQL

Coding Agent:
Codex CLI

Communication:
Telegram

Execution:
Local Docker / VPS

Isolation:
Git Worktree

Concurrency:
1
```

---

# 81. V1 Demo Task

Recommended first end-to-end scenario:

```text
Task:
INV-123

Description:
Add endpoint to export invoice list.
```

Night Shift detects missing requirements.

Telegram:

```text
1. XLSX or CSV?
2. Filtered result or all?
3. Maximum records?
```

Human:

```text
1A
2A
10000
```

Night Shift:

```text
Readiness 72 → 96
```

Then:

```text
Analyze repository
      ↓
Plan
      ↓
Compile Codex prompt
      ↓
Create worktree
      ↓
Run Codex
      ↓
npm build
      ↓
npm test
      ↓
Failure
      ↓
Repair
      ↓
Tests pass
      ↓
Commit
      ↓
Push
      ↓
PR #482
```

Telegram:

```text
🌙 INV-123 completed.
PR #482 is ready for review.
```

---

# 82. Development Phases

## Phase 0 — Foundation

Build:

```text
FastAPI project
PostgreSQL
SQLAlchemy
Alembic
Configuration
Structured logging
Docker Compose
```

Definition of Done:

```text
API can start
Database migration works
Health endpoint available
```

---

# 83. Phase 1 — Workflow Engine

Build:

```text
NightShiftState
State transitions
Task execution persistence
Workflow event log
Single worker
Task locking
```

Initial flow:

```text
QUEUED
↓
CLAIMED
↓
COMPLETED
```

Then progressively expand states.

---

# 84. Phase 2 — Task Provider

Implement:

```text
One task provider adapter
```

Features:

```text
Get tasks
Get task detail
Update status
Add comment if supported
```

---

# 85. Phase 3 — Requirement Intelligence

Implement:

```text
Task Context
Requirement assessment
Readiness scoring
Structured LLM output
```

Target:

```text
Task → readiness score
```

---

# 86. Phase 4 — Telegram HITL

Implement:

```text
Telegram bot
Clarification question generation
Webhook
Clarification session
Workflow resume
```

Target:

```text
Task
↓
Need clarification
↓
Telegram
↓
Human response
↓
Workflow resumes
```

---

# 87. Phase 5 — Repository Intelligence

Implement:

```text
Repository checkout
Repository scanning
Project configuration
Git history
Code search
Impact analysis
```

Target:

```text
Task → affected files/modules
```

---

# 88. Phase 6 — Skill System

Implement:

```text
SKILL.md loader
Skill metadata
Skill resolver
Context injection
```

---

# 89. Phase 7 — Planning and Prompt Compilation

Implement:

```text
ImplementationPlan
Plan validator
Prompt compiler
```

Target:

```text
Task Context
+
Impact Analysis
+
Skills
↓
Codex-ready prompt
```

---

# 90. Phase 8 — Coding Adapter

Implement:

```text
CodingAgent interface
CodexCodingAgent
Process handling
Timeout
Log capture
Modified file detection
```

---

# 91. Phase 9 — Sandbox and Worktree

Implement:

```text
Git worktree
Branch generation
Allowed workspace
Command Runner
Command policies
```

---

# 92. Phase 10 — Validation

Implement:

```text
Build runner
Lint runner
Test runner
Git diff analyzer
Acceptance criteria reviewer
```

---

# 93. Phase 11 — Repair

Implement:

```text
Failure analysis
Repair prompt
Bounded repair execution
Revalidation
```

---

# 94. Phase 12 — Git Delivery

Implement:

```text
Commit
Push
PR creation
External task status update
Telegram completion notification
```

---

# 95. Suggested MVP Cut

The first MVP should not contain every feature described in this PRD.

Recommended MVP:

```text
Task Provider
      ↓
Task Readiness
      ↓
Telegram Clarification
      ↓
Repository Context
      ↓
Implementation Plan
      ↓
Codex
      ↓
Build + Test
      ↓
1 Repair Loop
      ↓
Pull Request
```

Do not initially implement:

```text
Semantic Vector DB
Complex RAG
Multiple coding providers
Multiple Git providers
Multiple task providers
Parallel coding
Web dashboard
Temporal
Auto merge
```

---

# 96. Definition of Done — MVP

MVP is complete when Night Shift can:

1. Retrieve a single software development task.
2. Gather its task details.
3. Analyze missing requirements.
4. Calculate readiness.
5. Ask Telegram clarification.
6. Process the Telegram answer.
7. Reach readiness >= 90.
8. Inspect the repository.
9. Produce an impact analysis.
10. Produce an implementation plan.
11. Create a dedicated Git worktree.
12. Generate a Codex prompt.
13. Execute Codex.
14. Run configured validation.
15. Attempt repair when validation fails.
16. Commit validated code.
17. Push a Night Shift branch.
18. Create a PR/MR.
19. Notify the user.
20. Process the next eligible task.

---

# 97. V1 Acceptance Criteria

## AC-01 Task Retrieval

Given one or more eligible tasks exist,

when Night Shift runs,

then it shall claim one task.

---

## AC-02 Sequential Coding

Given one task is actively coding,

Night Shift shall not allow a second task to enter coding state.

---

## AC-03 Task Readiness

Night Shift shall calculate readiness using configured criteria and weights.

---

## AC-04 Clarification

If readiness is below 90,

Night Shift shall not start coding.

It shall request missing information through Telegram.

---

## AC-05 Resume

After human clarification,

Night Shift shall resume the same execution instead of starting a new execution.

---

## AC-06 Impact Analysis

Night Shift shall identify likely affected modules/files before coding begins.

---

## AC-07 Planning

Night Shift shall create an implementation plan covering all acceptance criteria.

---

## AC-08 Workspace Isolation

Night Shift shall create a dedicated worktree and branch for every coding execution.

---

## AC-09 Coding Adapter

Core workflow shall invoke coding through a CodingAgent abstraction.

---

## AC-10 Validation

Night Shift shall independently run repository validation after code generation.

---

## AC-11 Repair

A failed validation may trigger automated repair.

Repair attempts must not exceed the configured maximum.

---

## AC-12 PR Creation

PR/MR shall only be created when all blocking validation checks pass.

---

## AC-13 No Auto Merge

Night Shift shall never automatically merge V1 Pull Requests.

---

## AC-14 Audit

Every major workflow state transition shall be persisted.

---

# 98. Future V2 Architecture

After V1 becomes reliable:

```text
                     Web Dashboard
                           │
                           ▼
                   NestJS Control Plane
                           │
                           ▼
                  Python Agent Runtime
                           │
                  ┌────────┴────────┐
                  │                 │
               Temporal          Redis
                  │
        ┌─────────┼──────────┐
        │         │          │
     Worker A  Worker B   Worker C
```

Potential worker specialization:

```text
Backend Worker
Frontend Worker
QA Worker
Database Worker
```

---

# 99. Future Capabilities

Future versions may introduce:

- Temporal durable workflows;
- parallel repositories;
- parallel task execution;
- dependency-aware scheduling;
- codebase embeddings;
- long-term codebase memory;
- automatic task decomposition;
- PR review comment handling;
- PR repair after reviewer feedback;
- architecture reviewer;
- security reviewer;
- task complexity estimation;
- task prioritization;
- token/cost optimization;
- local LLM support;
- Engineering Manager dashboard;
- automatic release notes;
- staging deployment;
- CI integration.

---

# 100. Technical Design Principle

Night Shift shall maintain the following separation:

```text
WHAT needs to happen
      ↓
Workflow Engine

WHAT the software means
      ↓
LLM / Agents

HOW code is changed
      ↓
Coding Agent

WHETHER implementation works
      ↓
Validation Engine

HOW result is delivered
      ↓
Git Provider
```

No single component should own all of these responsibilities.

---

# 101. Core Mental Model

```text
                    🌙 NIGHT SHIFT
                  Virtual Engineer

                         │

          ┌──────────────┼──────────────┐
          │              │              │
        Brain          Memory         Hands
          │              │              │
    Requirement      Repository        Codex
      Analysis       Git History       Claude
      Planning         Skills         OpenCode
      Review          Context
          │
          └──────────────┬──────────────┘
                         │
                       Workflow
                         │
                         ▼
                      Evidence
                         │
                         ▼
                      PR / MR
```

---

# 102. Final Development Recommendation

Night Shift V1 should be built as:

```text
Python Modular Monolith

FastAPI
+
LangGraph
+
Pydantic
+
SQLAlchemy
+
PostgreSQL
+
Telegram
+
Git Worktree
+
Codex CLI
```

with:

```text
1 Task Provider
1 Git Provider
1 Coding Agent
1 Active Coding Task
0 Automatic Merge
```

The first engineering objective is not architectural scale.

The first objective is **workflow reliability**.

Success means:

> Night Shift can autonomously receive one software engineering task, understand it, request missing information, inspect the repository, plan the implementation, delegate coding to Codex, independently validate the output, repair reasonable failures, and produce a Pull Request ready for human review.

Only after this lifecycle becomes consistently reliable should Night Shift scale toward autonomous multi-task overnight software development.