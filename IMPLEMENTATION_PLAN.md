# 🌙 Night Shift V1 — Implementation Plan

Blueprint implementasi Night Shift berdasarkan PRD (Product Requirements Document) dan klarifikasi kebutuhan.

## Kustomisasi dari PRD

| Aspek | Implementasi |
|---|---|
| **Task Provider** | **Ace** via **MCP (Model Context Protocol)** — `McpTaskProvider` (stub siap, wiring di Milestone 7) |
| **Git Providers** | Dual: **GitHub** + **GitLab** — abstraction layer siap keduanya |
| **LLM Provider** | **Azure OpenAI** — `Deepseek-V4-Flash` via `https://iu-techpool-production.services.ai.azure.com` |
| **Coding Agents** | Triple: **Codex CLI** + **Claude Code** + **OpenCode** — via `CodingAgent` interface |
| **Target Repos** | `batch-mobile-fe` (Frontend), `batch-mobile` (Backend) — di `git.dexagroup.com` |
| **Team** | **1 Engineer** — serial execution, vertical slice per milestone |
| **Reuse Existing** | `cli_agent` → `nightshift/integrations/llm/azure_deepseek.py` |

## Milestone & Status

| Milestone | Cakupan | Status |
|---|---|---|
| **M0 — Foundation** | Scaffolding, config, logging, LLM provider, DB models, health endpoint, Docker Compose | ✅ Selesai |
| **M1 — Workflow Core** | State machine, transitions, task claim (SKIP LOCKED), worker loop, event logging, manual task API | ✅ Selesai |
| **M2 — Requirement Intelligence** | Context builder, readiness scorer, impact agent, planning agent, prompt compiler | ✅ Selesai |
| **M3 — Telegram HITL** | Bot client, formatter, webhook handler, clarification session, resume | ✅ Selesai |
| **M4 — Git Provider** | `GitProvider` abstraction, GitLab + GitHub, repository scanner, `.nightshift.yml` | ✅ Selesai |
| **M5 — Coding Agents + Sandbox** | `CodingAgent` abstraction, Codex/Claude Code/OpenCode, worktree, command runner + policies | ✅ Selesai |
| **M6 — Validation + Repair + PR** | Validation pipeline, repair loop, commit/push/PR, notifikasi | ✅ Selesai |
| **M7 — Ace MCP + Hardening** | MCP client ke Ace, secret redaction, retry policies, observability | 🔜 Berikutnya |

## Definisi Done MVP

Night Shift dapat:
1. Mengambil satu task dari queue.
2. Membangun context dan menilai readiness (evidence-based).
3. Meminta klarifikasi via Telegram jika readiness < threshold.
4. Melakukan impact analysis dan perencanaan.
5. Meng-compile prompt coding.
6. Membuat git worktree terisolasi.
7. Menjalankan coding agent (Codex/Claude Code/OpenCode).
8. Menjalankan validasi (build/lint/test).
9. Melakukan repair (maks 3x).
10. Commit, push, dan buat PR/MR.
11. Notifikasi via Telegram.
12. Melanjutkan ke task berikutnya.

## Langkah Selanjutnya (Milestone 7)

1. Implementasi MCP client untuk Ace (`ace_mcp.py` — ganti stub dengan koneksi nyata).
2. `.nightshift.yml` untuk `batch-mobile` dan `batch-mobile-fe`.
3. E2E test dengan repository target.
4. Observability & metrics.
5. Dokumentasi operasional.

## Menjalankan

```bash
cp .env.example .env            # isi kredensial
docker compose up --build
docker compose exec nightshift-api alembic upgrade head
```

Lihat `README.md` untuk detail.
