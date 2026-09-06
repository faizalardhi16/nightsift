# Night Shift — Architecture

## Ringkasan

Night Shift adalah **Agentic Software Engineering Orchestrator** (Modular Monolith, Python). Ia tidak langsung menulis kode, melainkan mengorkestrasi alur: mengambil task, memahami requirement, menilai readiness, meminta klarifikasi, menganalisis dampak, merencanakan, menjalankan coding agent, memvalidasi, memperbaiki, lalu membuat PR.

## Komponen

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI (API)                        │
│   /api/v1/tasks  /api/v1/workflow  /api/v1/webhooks      │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Workflow Engine    │   (explicit state machine)
              │   nightshift/app/workflow │
              └──────────┬───────────┘
                         │
   ┌──────────┬──────────┼──────────┬──────────────┐
   ▼          ▼          ▼          ▼              ▼
Task Provider  Telegram   Git Provider  LLM Provider  Coding Agents
(Ace MCP)    (HITL)     (GH/GL)      (Azure Deepseek) (Codex/Claude/OpenCode)
```

## Prinsip Desain

1. **Workflow First** — state machine eksplisit (`workflow/graph.py`), bukan satu agen otonom.
2. **Evidence over Confidence** — readiness dihitung aplikasi dari evidence LLM (`domains/readiness.py`).
3. **Human-in-the-Loop** — ambiguitas = berhenti & tanya via Telegram, bukan menebak.
4. **Isolasi** — tiap task mendapat git worktree terpisah; command runner menolak operasi berbahaya.
5. **Abstraction** — `LLMProvider`, `GitProvider`, `TaskProvider`, `CodingAgent` semua interface.

## State Machine

```
QUEUED → CLAIMED → CONTEXT_BUILDING → REQUIREMENT_ANALYSIS
   → (score < 90) NEED_CLARIFICATION → WAITING_USER → REQUIREMENT_ANALYSIS
   → (score ≥ 90) READY_TO_PLAN → IMPACT_ANALYSIS → PLANNING
   → READY_TO_CODE → WORKSPACE_PREPARATION → CODING → VALIDATING
   → (fail) REPAIRING → VALIDATING | (pass) REVIEWING → READY_FOR_PR
   → PR_CREATED → COMPLETED
```

Transisi divalidasi di `workflow/transitions.py`. Setiap transisi dicatat append-only ke `workflow_events`.

## Struktur Kode

```
nightshift/
├── app/
│   ├── main.py               # FastAPI entrypoint
│   ├── config/               # settings + logging
│   ├── api/routes/           # tasks, workflow, webhooks, health, llm_probe
│   ├── workflow/             # state, graph, transitions, runner, nodes/
│   ├── domains/              # readiness, validation
│   ├── agents/               # requirement, impact, planning, review, prompt_compiler
│   ├── coding/               # base, cli_agent_base, codex, claude_code, opencode, registry
│   ├── repository_intelligence/  # scanner, code_search, config_reader, context_builder
│   ├── sandbox/              # workspace (worktree), command_runner, policies
│   ├── security/             # secret_filter
│   ├── persistence/          # models, database, repositories
│   └── skills/               # loader, resolver
├── integrations/             # task_provider, telegram, git_provider, llm
├── skills/                   # SKILL.md files
└── worker.py                 # polling worker
```

## Decision Records

### DR-1: Explicit State Machine, bukan LangGraph runtime
PRD mengizinkan "LangGraph / Explicit State Machine". Untuk 1 engineer dan reliabilitas, dipilih state machine eksplisit yang deterministik dan mudah di-debug. LangGraph dapat diperkenalkan kemudian tanpa mengubah node handler.

### DR-2: Integrations di level `nightshift/integrations/`
Adapter eksternal (LLM, git, telegram, task provider) diletakkan di package `integrations` agar bisa di-reuse dan di-mock.

### DR-3: Readiness dihitung aplikasi
LLM hanya menilai tiap kriteria (`satisfied: bool + reason`); skor dijumlahkan oleh `compute_readiness_score()`.

### DR-4: Azure Deepseek via OpenAI-compatible client
Endpoint Azure di-normalize menjadi base URL OpenAI (`/openai/v1/`). `structured_completion` memakai bounded parser retry (default 2x).

### DR-5: Git Worktree untuk isolasi
Tiap task dapat worktree di `/workspaces/<task-id>` dengan branch `nightshift/<task-id>`.

## Keamanan

- Command runner menolak pola berbahaya (`rm -rf /`, `sudo`, `shutdown`, `git push --force`, dst).
- Secret redaction sebelum konten dikirim ke LLM.
- Coding agent dibatasi pada workspace.
- V1 tidak mengizinkan auto-merge, force-push, atau akses produksi.

## Observability

- Structured JSON logging (structlog) dengan correlation ID per execution.
- `workflow_events` = audit timeline append-only.
- Metrics (tasks claimed/completed/blocked, repair rate, durasi) di Milestone 7.
