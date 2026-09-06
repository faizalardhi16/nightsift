# 🌙 Night Shift

**Agentic Software Engineering Orchestrator** — mengubah task development menjadi Pull Request tervalidasi, menggunakan AI Coding Assistant sebagai "tangan" eksekusinya.

Night Shift **tidak menulis kode sendiri**. Ia mengorkestrasi: ambil task → pilih task paling mudah → minta klarifikasi ke manusia (Telegram) → nilai readiness dari jawaban user → analisis dampak → rencana implementasi → jalankan coding agent → validasi (build/lint/test) → repair → buat PR/MR.

Spesifikasi lengkap: `Product Requirements Document.md`.

---

## Daftar Isi

1. [Prasyarat](#1-prasyarat)
2. [Instalasi](#2-instalasi)
3. [Konfigurasi (.env)](#3-konfigurasi-env)
4. [Menjalankan Night Shift](#4-menjalankan-night-shift)
5. [Cara Pakai Agent](#5-cara-pakai-agent)
6. [Cara Submit Task](#6-cara-submit-task)
7. [Alur Kerja](#7-alur-kerja)
8. [Konfigurasi Repository (.nightshift.yml)](#8-konfigurasi-repository)
9. [API Reference](#9-api-reference)
10. [Testing](#10-testing)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prasyarat

| Kebutuhan | Versi | Catatan |
|---|---|---|
| Python | 3.12+ | |
| Docker + Docker Compose | terbaru | opsional; hanya diperlukan untuk cara Docker |
| Git | 2.x | wajib, dipakai untuk worktree |
| PostgreSQL | 16 | via Docker Compose atau service PostgreSQL lokal |
| Coding Agent CLI | — | minimal **salah satu**: Codex / Claude Code / OpenCode |

Opsional:
- **Telegram Bot Token** — untuk fitur Human-in-the-Loop (klarifikasi).
- **Token GitLab/GitHub** — untuk membuat PR/MR.
- **Azure OpenAI key** — untuk LLM reasoning internal (readiness, impact, planning, review).

---

## 2. Instalasi

```bash
# Clone project
git clone <nightshift-repo> && cd nightshift

# Buat virtual environment
py -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# Install dependency (termasuk dev)
pip install -e ".[dev]"
```

---

## 3. Konfigurasi (.env)

```bash
cp .env.example .env
```

Isi variabel wajib di `.env`:

```ini
# --- Database ---
DATABASE_URL=postgresql+psycopg://postgres:nightshift@localhost:5432/nightshift

# --- Azure OpenAI (LLM reasoning internal) ---
AZURE_OPENAI_ENDPOINT=https://iu-techpool-production.services.ai.azure.com
AZURE_OPENAI_API_KEY=sk-...
AZURE_OPENAI_MODEL=deepseek-v4-flash

# --- Telegram (opsional, untuk klarifikasi) ---
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=123456789

# --- Git Provider ---
GITLAB_URL=https://git.dexagroup.com
GITLAB_TOKEN=glpat-...
GITHUB_TOKEN=ghp_...

# --- Coding Agent ---
DEFAULT_CODING_AGENT=codex      # codex | claude_code | opencode
CODING_TIMEOUT_SECONDS=3600
```

> `AZURE_OPENAI_API_KEY`, `GITLAB_TOKEN`/`GITHUB_TOKEN`, dan `TELEGRAM_BOT_TOKEN` bersifat rahasia — jangan commit.

---

## 4. Menjalankan Night Shift

### Cara 1: Docker Compose (recommended)

```bash
docker compose up --build

# Jalankan migration (shell terpisah)
docker compose exec nightshift-api alembic upgrade head

# Cek
curl http://localhost:8000/health
```

Ada 3 service: `postgres`, `nightshift-api` (FastAPI), `nightshift-worker` (eksekutor workflow).

### Cara 2: Lokal

Tanpa Docker, jalankan tiga komponen berikut:

| Komponen | Fungsi | Cara menjalankan |
|---|---|---|
| PostgreSQL 16 | Database aplikasi | Windows Service `postgresql-x64-16` |
| Nightshift API | Menerima request HTTP | `uvicorn nightshift.app.main:app` |
| Nightshift worker | Memproses task dan workflow | `python -m nightshift.worker` |

Redis tidak wajib untuk V1 dan tidak perlu dijalankan. Frontend juga tidak disediakan oleh repository ini; gunakan Swagger UI di `http://localhost:8000/docs` untuk pengujian API.

### 4.1 Persiapan PostgreSQL lokal (Windows)

Pastikan service PostgreSQL aktif:

```powershell
Get-Service postgresql*
Start-Service postgresql-x64-16
```

Jika database `nightshift` belum ada, buat sekali menggunakan `psql`:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h localhost -d postgres
```

Kemudian jalankan SQL berikut:

```sql
CREATE DATABASE nightshift;
\q
```

Pastikan `.env` memakai koneksi PostgreSQL lokal dan path Windows yang writable:

```ini
DATABASE_URL=postgresql+psycopg://postgres:nightshift@localhost:5432/nightshift
WORKSPACE_ROOT=D:\fromdoc\Nightshift\workspaces
REPOSITORY_ROOT=D:\fromdoc\Nightshift\repos
```

### 4.2 Install dependency dan migration

Jalankan dari root repository (`D:\fromdoc\Nightshift`):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Repository ini memuat model SQLAlchemy, tetapi jika folder `migrations\versions` masih kosong, buat initial migration satu kali:

```powershell
New-Item -ItemType Directory -Force migrations\versions | Out-Null
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "initial schema"
```

Setelah revision tersedia, apply schema ke database:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

> Jangan menjalankan `revision --autogenerate` setiap kali start. Perintah tersebut hanya untuk membuat revision baru ketika ada perubahan model. Untuk start berikutnya cukup jalankan `alembic upgrade head`.

### 4.3 Jalankan API dan worker

Buka dua terminal PowerShell tambahan, tetap di root repository.

Terminal API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn nightshift.app.main:app --reload
```

Terminal worker:

```powershell
.\.venv\Scripts\python.exe -m nightshift.worker
```

Verifikasi API dari terminal lain:

```powershell
curl.exe http://localhost:8000/health
```

Urutan service yang harus aktif adalah: PostgreSQL → migration selesai → API → worker. Worker harus tetap berjalan karena API hanya menerima request; worker yang mengambil dan memproses task dari database.

Untuk menghentikan aplikasi, tekan `Ctrl+C` pada terminal worker dan API. PostgreSQL dapat tetap berjalan sebagai Windows Service.

### Alternatif: PostgreSQL via Docker, API dan worker lokal

```bash
# 1. Nyalakan PostgreSQL (misal via Docker)
docker run -d -p 5432:5432 -e POSTGRES_USER=nightshift -e POSTGRES_PASSWORD=nightshift -e POSTGRES_DB=nightshift postgres:16-alpine

# 2. Migration
alembic upgrade head

# 3. Jalankan API (terminal 1)
uvicorn nightshift.app.main:app --reload

# 4. Jalankan worker (terminal 2) — inilah yang memproses task
python -m nightshift.worker
```

> **Penting:** API hanya menerima request. Yang benar-benar mengeksekusi workflow adalah **worker** (`python -m nightshift.worker`). Pastikan worker selalu berjalan.

---

## 5. Cara Pakai Agent

Night Shift punya **dua jenis agent**:

| Jenis | Peran | Implementasi |
|---|---|---|
| **Internal LLM Agents** ("otak") | Readiness, impact analysis, planning, review | Azure OpenAI (Deepseek-V4-Flash) |
| **Coding Agents** ("tangan") | Menulis & mengubah kode di worktree | Codex / Claude Code / OpenCode (CLI) |

### 5.1 Internal LLM (otak)

Otomatis aktif ketika `AZURE_OPENAI_API_KEY` terisi. Tanpa key, Night Shift jatuh ke *heuristic* (skor readiness dasar) — tidak disarankan untuk production.

Cek konektivitas:

```bash
curl -X POST http://localhost:8000/api/v1/test/llm
```

### 5.2 Coding Agents (tangan)

Night Shift memanggil coding agent **via CLI (subprocess)** di dalam git worktree. CLI-nya harus terinstall dan bisa dipanggil dari shell.

**Install minimal salah satu:**

```bash
# Codex (OpenAI)
npm install -g @openai/codex

# Claude Code (Anthropic)
npm install -g @anthropic-ai/claude-code

# OpenCode
# ikuti petunjuk instalasi resmi opencode
```

**Memilih agent** — lewat variabel env atau konfigurasi repository:

```ini
# .env
DEFAULT_CODING_AGENT=codex      # codex | claude_code | opencode
```

```yaml
# .nightshift.yml (di root repository target) — override
coding:
  default_agent: claude_code
```

**Cara Night Shift memanggil tiap agent:**

| Agent | Perintah yang dieksekusi |
|---|---|
| `codex` | `codex --worktree <workspace> --prompt-file <file>` |
| `claude_code` | `claude -p --output-format text --allowedTools Bash,Edit,Write,Read -- <prompt>` |
| `opencode` | `opencode run -- <prompt>` |

Prompt dikompilasi otomatis dari Task Context + Impact Analysis + Plan + Skills, lalu ditulis ke `.nightshift-prompt.md` di dalam worktree.

**Menambah agent baru:** buat class turunan `CLICodingAgent` di `nightshift/app/coding/`, daftarkan di `registry.py`.

---

## 6. Cara Submit Task

### 6.1 Manual (tanpa Ace)

Submit task langsung ke queue:

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "external_task_id": "INV-123",
    "title": "Export invoice to XLSX",
    "description": "Add endpoint to export invoice list to XLSX.",
    "priority": 5
  }'
```

Response `201 Created` mengembalikan `id` execution. Simpan nilai `id` tersebut untuk memantau task. Task baru selalu masuk dengan state `QUEUED`, kemudian diambil worker secara otomatis setiap sekitar 5 detik.

Untuk PowerShell Windows, gunakan `curl.exe` atau `Invoke-RestMethod`:

```powershell
$body = @{
    external_task_id = "INV-123"
    title = "Export invoice to XLSX"
    description = "Add endpoint to export invoice list to XLSX."
    priority = 5
} | ConvertTo-Json

$created = Invoke-RestMethod `
    -Method Post `
    -Uri http://localhost:8000/api/v1/tasks `
    -ContentType "application/json" `
    -Body $body

$created | Format-List
$executionId = $created.id
```

Field request:

| Field | Wajib | Keterangan |
|---|---|---|
| `external_task_id` | Ya | ID task dari sistem pemanggil; harus berupa string |
| `title` | Tidak | Judul task |
| `description` | Tidak | Detail requirement task |
| `priority` | Tidak | Prioritas numerik; default `0`, nilai lebih besar diproses lebih dulu |
| `repository_id` | Tidak | UUID repository yang sudah terdaftar |

### 6.2 Via Ace (MCP)

Ketika `ACE_MCP_ENABLED=true` dan kredensial dikonfigurasi (`ACE_BASE_URL`, `ACE_API_KEY`, `ACE_GATEWAY_API_KEY`), worker menjalankan MCP server `@dexagroup/mcp-ace` dan menarik task berstatus `TODO` melalui tools `ace_list_tasks` / `ace_get_task`. Status task di Ace diperbarui ke `IN_PROGRESS` saat readiness ≥ threshold dan ke `IN_REVIEW` saat PR dibuat (lihat `nightshift/integrations/task_provider/ace_mcp.py`).

Scheduler ACE berjalan di dalam process worker, bukan sebagai Windows Service terpisah. Scheduler melakukan sync pertama saat worker berhasil terhubung, lalu memeriksa ACE setiap 300 detik. Setiap sync memasukkan semua task baru yang termasuk scope development ke queue lokal. Saat claim, worker memilih satu task `QUEUED` dengan skor kemudahan judul tertinggi (`TASK_SELECTED`); task lain tetap `QUEUED`. Task terpilih langsung dikirim ke jalur klarifikasi dan menjadi `WAITING_USER`, sehingga pertanyaan Telegram hanya dikirim untuk satu task. Setelah user menjawab, barulah readiness dianalisis untuk menentukan apakah task dapat lanjut ke coding. Sync dilewati jika ada workflow aktif atau task yang masih `QUEUED`. Jika worker menemukan state aktif yang tersisa dari run sebelumnya seperti `REQUIREMENT_ANALYSIS`, dan task tersebut bukan `WAITING_USER` serta tidak sedang `active_coding`, worker akan mencatat `WORKFLOW_RESUMED` lalu menjalankan ulang workflow dari `CLAIMED` agar context dan jawaban Telegram terbaru dibaca kembali. Pantau log `ace_scheduler_started`, `ace_sync_complete`, `ace_sync_skipped_active_task`, `ace_sync_skipped_pending_task`, `task_claim_skipped_active_workflow`, `clarification_first_pass`, dan event timeline `TASK_SELECTED`/`WORKFLOW_RESUMED`. Setelah mengubah `ACE_MCP_ENABLED`, restart worker.

Scheduler hanya menerima task yang terindikasi sebagai development/feature/bugfix/refactor/API/UI/test. Task dengan konteks deployment, release, production, staging, infrastructure, operations, monitoring, backup, CI/CD, Docker, Kubernetes, atau incident akan dilewati dan dicatat sebagai `ace_task_skipped_non_development`; task tersebut tidak diubah statusnya di ACE.

Worker juga melakukan guard saat claim queue lokal. Task non-development yang sudah terlanjur masuk queue lama tidak dijalankan atau dikirim ke Telegram; task tersebut ditandai lokal sebagai `FAILED` dengan alasan `Skipped: non-development task` dan dicatat sebagai event `NON_DEVELOPMENT_SKIPPED`.

#### Mapping project ACE ke directory lokal

Saat membaca task dari ACE, Night Shift mengambil project code dari field `project_code`, `projectCode`, atau `project.code`, lalu mencocokkannya dengan dictionary di `nightshift/app/config/project_directories.py`:

```python
PROJECT_DIRECTORY_MAP = {
    "EXON": Path(r"D:\fromdoc\EXON_V2"),
    "SPBI": Path(r"D:\fromdoc\spbi\dev-spbi"),
}
```

Tambahkan project baru ke dictionary tersebut dan restart worker. Directory harus merupakan local Git repository karena workflow membuat Git worktree dari path tersebut.

### 6.3 Memantau task

```bash
# List semua task
curl http://localhost:8000/api/v1/tasks

# Detail satu task
curl http://localhost:8000/api/v1/tasks/<execution_id>

# Timeline event (audit log)
curl http://localhost:8000/api/v1/tasks/<execution_id>/events

# Retry / cancel
curl -X POST http://localhost:8000/api/v1/tasks/<execution_id>/retry
curl -X POST http://localhost:8000/api/v1/tasks/<execution_id>/cancel
```

#### Ringkasan jumlah task per state

Gunakan endpoint ini untuk melihat berapa task yang sedang antre, berjalan, selesai, atau gagal:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/workflow/status | ConvertTo-Json -Depth 5
```

Contoh response:

```json
{
  "worker_config": {
    "max_active_coding_tasks": 1,
    "readiness_threshold": 90,
    "llm_configured": true
  },
  "task_counts": {
    "QUEUED": 2,
    "CODING": 1,
    "COMPLETED": 4,
    "FAILED": 1
  }
}
```

#### Melihat task yang sedang berjalan

Daftar task lengkap dapat difilter berdasarkan state menggunakan PowerShell:

```powershell
$activeStates = @(
    "QUEUED", "CLAIMED", "CONTEXT_BUILDING", "REQUIREMENT_ANALYSIS",
    "NEED_CLARIFICATION", "WAITING_USER", "READY_TO_PLAN", "IMPACT_ANALYSIS",
    "PLANNING", "READY_TO_CODE", "WORKSPACE_PREPARATION", "CODING",
    "VALIDATING", "REPAIRING", "REVIEWING", "READY_FOR_PR", "PR_CREATING",
    "PR_CREATED"
)

$tasks = Invoke-RestMethod http://localhost:8000/api/v1/tasks
$tasks |
    Where-Object { $_.state -in $activeStates } |
    Select-Object id, external_task_id, state, title, priority, updated_at |
    Format-Table -AutoSize
```

State terminal adalah `COMPLETED`, `FAILED`, dan `BLOCKED`. State `WAITING_USER` berarti workflow menunggu jawaban user, bukan sedang menjalankan coding. Task baru selalu melewati klarifikasi pertama kali; state readiness baru dihitung setelah jawaban Telegram masuk. State aktif lain seperti `REQUIREMENT_ANALYSIS` seharusnya bergerak lagi otomatis; jika terlihat setelah restart worker, cek event `WORKFLOW_RESUMED`. Hanya satu task yang boleh berada di workflow aktif pada satu waktu. Jika sudah ada task `WAITING_USER`, task lain tetap `QUEUED` dan tidak akan mengirim pesan Telegram kedua.

#### Detail dan timeline satu task

```powershell
# Ganti dengan UUID dari response POST atau hasil list
$executionId = "<execution_id>"

# State terkini, branch, readiness, error, dan waktu update
Invoke-RestMethod "http://localhost:8000/api/v1/tasks/$executionId" |
    ConvertTo-Json -Depth 5

# Riwayat perpindahan state dan event workflow
Invoke-RestMethod "http://localhost:8000/api/v1/tasks/$executionId/events" |
    ConvertTo-Json -Depth 10
```

Gunakan `POST /api/v1/tasks/{id}/retry` untuk memasukkan task gagal kembali ke `QUEUED`. Endpoint `POST /api/v1/tasks/{id}/cancel` menandai task sebagai `FAILED` dengan alasan `Cancelled by user`.

---

## 7. Alur Kerja

```
QUEUED → CLAIMED → CONTEXT_BUILDING → REQUIREMENT_ANALYSIS
   ├── NEED_CLARIFICATION → WAITING_USER (Telegram, pertanyaan dibuat LLM) → resume
   └── readiness score ≥ 90 setelah jawaban → READY_TO_PLAN → IMPACT_ANALYSIS → PLANNING
        → READY_TO_CODE → WORKSPACE_PREPARATION → CODING (agent)
        → VALIDATING → (gagal) REPAIRING → VALIDATING (maks 3x)
        → REVIEWING → READY_FOR_PR → PR_CREATED → COMPLETED
```

- **Readiness** dihitung oleh aplikasi dari evidence LLM (bukan self-reported confidence).
- **Repair** maksimal `MAX_REPAIR_ATTEMPTS` (default 3). Habis → `BLOCKED`.
- **PR** hanya dibuat jika semua validasi blocking lolos. **Tidak ada auto-merge.**

---

## 8. Konfigurasi Repository

Taruh file `.nightshift.yml` di root repository target untuk override default:

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

coding:
  default_agent: codex

workflow:
  readiness_threshold: 90
  max_repair_attempts: 3

git:
  branch_prefix: nightshift
```

Contoh untuk target repo Dexagroup:
- `batch-mobile-fe` (Frontend) → sesuaikan `runtime`/`validation` dengan framework mobile.
- `batch-mobile` (Backend) → sesuaikan command build/test.

---

## 9. API Reference

Dokumentasi lengkap request, response, monitoring task, dan contoh PowerShell tersedia di [API.md](API.md).

| Method | Endpoint | Keterangan |
|---|---|---|
| GET | `/health` | Health check (DB + LLM status) |
| POST | `/api/v1/test/llm` | Probe koneksi Azure LLM |
| GET | `/api/v1/tasks` | List task executions |
| POST | `/api/v1/tasks` | Submit task manual |
| GET | `/api/v1/tasks/{id}` | Detail execution |
| POST | `/api/v1/tasks/{id}/retry` | Re-queue task |
| POST | `/api/v1/tasks/retry-all` | Re-queue task FAILED/WAITING_USER development dan reset status ACE ke TODO |
| POST | `/api/v1/tasks/{id}/cancel` | Batalkan task |
| POST | `/api/v1/tasks/cancel-all` | Batalkan semua task non-terminal |
| GET | `/api/v1/tasks/{id}/events` | Timeline event |
| POST | `/api/v1/workflow/start` | Acknowledgement; worker tetap harus dijalankan sebagai process |
| POST | `/api/v1/workflow/stop` | Acknowledgement; hentikan process worker secara manual |
| GET | `/api/v1/workflow/status` | Status & konfigurasi worker |
| POST | `/api/v1/webhooks/telegram` | Webhook jawaban Telegram |

Dokumentasi interaktif: `http://localhost:8000/docs` (Swagger UI).

---

## 10. Testing

```bash
pytest                  # seluruh test
pytest tests/test_transitions.py   # state machine
pytest tests/test_readiness.py     # readiness scoring
pytest tests/test_parser.py        # structured output parser

ruff check nightshift tests        # lint
```

---

## 11. Troubleshooting

| Gejala | Solusi |
|---|---|
| `health` → `database: error` | Pastikan PostgreSQL jalan & `DATABASE_URL` benar. Jalankan `alembic upgrade head`. |
| `UndefinedTable: relation "task_executions" does not exist` | Migration belum dibuat atau belum dijalankan. Jika `migrations\versions` kosong, jalankan `alembic revision --autogenerate -m "initial schema"`, lalu `alembic upgrade head`. |
| Worker tidak memproses task | Pastikan `python -m nightshift.worker` berjalan; cek log. |
| Coding agent "not found" | CLI (`codex`/`claude`/`opencode`) belum terinstall / tidak ada di PATH. |
| Readiness selalu < 90 (terblokir) | Task kurang detail → jawab pertanyaan Telegram, atau lengkapi `description`. |
| `llm_configured: false` | `AZURE_OPENAI_API_KEY` belum diisi di `.env`. |
| Worktree gagal dibuat | Pastikan `REPOSITORY_ROOT`/`WORKSPACE_ROOT` writable dan repository sudah di-clone di `/repos`. |
