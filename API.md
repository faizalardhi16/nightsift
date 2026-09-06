# Nightshift API

Dokumentasi endpoint HTTP untuk Nightshift.

Base URL lokal:

```text
http://localhost:8000
```

Swagger UI tersedia di `http://localhost:8000/docs` ketika API berjalan.

## 1. Health check

### `GET /health`

Memeriksa API, koneksi database, dan konfigurasi LLM.

```powershell
Invoke-RestMethod http://localhost:8000/health | ConvertTo-Json
```

Contoh response:

```json
{
  "status": "ok",
  "database": "ok",
  "llm_configured": true,
  "version": "0.1.0"
}
```

## 2. Task API

### `POST /api/v1/tasks`

Membuat task baru. Task masuk ke queue dengan state `QUEUED` dan akan diambil oleh worker.

Request:

| Field | Wajib | Tipe | Keterangan |
|---|---:|---|---|
| `external_task_id` | Ya | string | ID task dari sistem pemanggil |
| `title` | Tidak | string/null | Judul task |
| `description` | Tidak | string/null | Requirement atau detail task |
| `priority` | Tidak | integer | Default `0`; nilai lebih besar diproses lebih dulu |
| `repository_id` | Tidak | UUID/null | Repository yang sudah terdaftar |

PowerShell:

```powershell
$body = @{
    external_task_id = "INV-123"
    title = "Export invoice to XLSX"
    description = "Add endpoint to export invoice list to XLSX."
    priority = 5
} | ConvertTo-Json

$task = Invoke-RestMethod `
    -Method Post `
    -Uri http://localhost:8000/api/v1/tasks `
    -ContentType "application/json" `
    -Body $body

$task | ConvertTo-Json -Depth 5
$executionId = $task.id
```

`curl.exe`:

```powershell
curl.exe -X POST http://localhost:8000/api/v1/tasks `
  -H "Content-Type: application/json" `
  -d '{"external_task_id":"INV-123","title":"Export invoice to XLSX","description":"Add endpoint to export invoice list to XLSX.","priority":5}'
```

Response status: `201 Created`.

Contoh response:

```json
{
  "id": "2f4c6e0b-6f8e-4c4f-8d32-123456789abc",
  "external_task_id": "INV-123",
  "state": "QUEUED",
  "title": "Export invoice to XLSX",
  "readiness_score": null,
  "priority": 5,
  "branch_name": null,
  "repair_attempt": 0,
  "failure_reason": null,
  "created_at": "2026-09-06T13:30:00Z",
  "updated_at": "2026-09-06T13:30:00Z"
}
```

Simpan `id` sebagai `execution_id` untuk pemantauan berikutnya.

### `GET /api/v1/tasks`

Mengambil semua task, diurutkan dari yang terbaru.

```powershell
$tasks = Invoke-RestMethod http://localhost:8000/api/v1/tasks
$tasks | Format-Table id, external_task_id, state, title, priority, updated_at
```

### `GET /api/v1/tasks/{execution_id}`

Mengambil detail state terkini satu task.

```powershell
$executionId = "<execution_id>"
Invoke-RestMethod "http://localhost:8000/api/v1/tasks/$executionId" |
    ConvertTo-Json -Depth 5
```

Field penting untuk monitoring:

- `state`: posisi task di workflow
- `readiness_score`: skor readiness jika sudah dianalisis
- `branch_name`: branch/worktree jika sudah dibuat
- `repair_attempt`: jumlah percobaan repair
- `failure_reason`: alasan jika task gagal atau dibatalkan
- `updated_at`: waktu perubahan terakhir

### `GET /api/v1/tasks/{execution_id}/events`

Mengambil timeline event task secara berurutan.

```powershell
Invoke-RestMethod "http://localhost:8000/api/v1/tasks/$executionId/events" |
    ConvertTo-Json -Depth 10
```

Setiap event berisi `event_type`, `from_state`, `to_state`, `payload`, dan `created_at`.

### `POST /api/v1/tasks/{execution_id}/retry`

Memasukkan task kembali ke queue. State diubah menjadi `QUEUED`, `repair_attempt` di-reset ke `0`, dan `failure_reason` dihapus.

```powershell
Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/tasks/$executionId/retry" |
    ConvertTo-Json -Depth 5
```

### `POST /api/v1/tasks/{execution_id}/cancel`

Membatalkan task. Implementasi saat ini menandainya sebagai `FAILED` dengan `failure_reason` `Cancelled by user`.

```powershell
Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8000/api/v1/tasks/$executionId/cancel" |
    ConvertTo-Json -Depth 5
```

### `POST /api/v1/tasks/cancel-all`

Membatalkan semua task non-terminal, termasuk `QUEUED` dan task yang sedang berjalan. Task `COMPLETED`, `FAILED`, dan `BLOCKED` tidak diubah.

> Gunakan endpoint ini dengan hati-hati. Pembatalan dicatat sebagai state `FAILED` dengan alasan `Cancelled by user`.

```powershell
Invoke-RestMethod `
    -Method Post `
    -Uri http://localhost:8000/api/v1/tasks/cancel-all |
    ConvertTo-Json -Depth 5
```

Contoh response:

```json
{
  "cancelled": 2,
  "task_ids": [
    "76f6eda8-8710-43a1-bbc2-e29142eef647",
    "2f4c6e0b-6f8e-4c4f-8d32-123456789abc"
  ]
}
```

### `POST /api/v1/tasks/retry-all`

Memasukkan kembali task `FAILED` dan `WAITING_USER` yang termasuk scope development ke `QUEUED`. Jika ada sesi klarifikasi Telegram yang masih `OPEN`, sesi tersebut ditutup agar jawaban lama tidak dipakai untuk retry baru. Task deployment/non-development tidak diubah dan dikembalikan sebagai `skipped_task_ids`. Jika ACE aktif, status task juga dikembalikan ke `TODO`; kegagalan sinkronisasi ACE tidak membatalkan retry lokal.

```powershell
Invoke-RestMethod `
    -Method Post `
    -Uri http://localhost:8000/api/v1/tasks/retry-all |
    ConvertTo-Json -Depth 5
```

Contoh response:

```json
{
  "retried": 2,
  "task_ids": ["76f6eda8-8710-43a1-bbc2-e29142eef647", "2f4c6e0b-6f8e-4c4f-8d32-123456789abc"],
  "skipped": 1,
  "skipped_task_ids": ["3f4c6e0b-6f8e-4c4f-8d32-123456789abc"],
  "ace_updated": 2,
  "ace_failed": 0,
  "ace_failed_task_ids": []
}
```

## 3. Monitoring workflow

ACE scheduler berjalan di dalam process `nightshift.worker`. Tidak ada endpoint HTTP terpisah untuk menjalankan scheduler. Scheduler melakukan sync awal lalu setiap 300 detik dan memasukkan semua task ACE baru yang termasuk scope development ke queue lokal. Worker memilih satu task `QUEUED` dengan judul yang paling mudah menurut skor seleksi deterministik (`TASK_SELECTED`), lalu langsung menjalankannya ke `WAITING_USER`. Task lain tetap `QUEUED`; worker tidak akan claim task lain saat sudah ada workflow aktif, termasuk `WAITING_USER`, sehingga hanya satu task yang dapat mengirim klarifikasi Telegram.

Jika worker menemukan state aktif yang tersisa dari run sebelumnya seperti `REQUIREMENT_ANALYSIS`, dan task tersebut bukan `WAITING_USER` serta tidak sedang `active_coding`, worker akan mencatat event timeline `WORKFLOW_RESUMED` lalu menjalankan ulang workflow dari `CLAIMED`. Jawaban Telegram terbaru yang sudah berstatus `ANSWERED` ikut dimasukkan ke prompt requirement analysis, sehingga setelah user menjawab, AI menilai ulang confidence sebelum mengubah ACE ke `IN_PROGRESS`.

Log yang relevan adalah `ace_scheduler_started`, `ace_sync_complete`, `ace_sync_skipped_active_task`, `ace_sync_skipped_pending_task`, dan `task_claim_skipped_active_workflow`. Event timeline yang relevan adalah `WORKFLOW_RESUMED`, `CLARIFICATION_ANSWERED`, dan `STATE_TRANSITION`.

Intake ACE hanya menerima task development/feature/bugfix/refactor/API/UI/test. Task deployment, release, production, staging, infrastructure, operations, monitoring, backup, CI/CD, Docker, Kubernetes, atau incident dilewati dengan log `ace_task_skipped_non_development` dan tidak diubah statusnya di ACE.

Task terpilih selalu melewati klarifikasi pertama sebelum readiness dianalisis. Pertanyaan klarifikasi dibuat oleh LLM dari title, description, acceptance criteria, readiness evidence, dan repository context task terpilih. Setiap pertanyaan menjelaskan bagian yang kurang jelas, alasan informasi itu diperlukan, serta contoh jawaban. Setelah Telegram menjawab, AI menghitung readiness dan hanya melanjutkan bila memenuhi threshold. Jika LLM tidak tersedia atau gagal, sistem memakai fallback deterministik.

Worker juga memeriksa queue lokal saat claim. Task non-development yang sudah terlanjur ada akan ditandai `FAILED` dengan alasan `Skipped: non-development task`, tanpa dikirim ke Telegram dan tanpa mengubah status task di ACE.

### `GET /api/v1/workflow/status`

Mengambil jumlah task berdasarkan state dan konfigurasi worker. Ini endpoint utama untuk menjawab “ada berapa task yang sedang berjalan?”.

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/workflow/status |
    ConvertTo-Json -Depth 5
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

Untuk menampilkan task yang belum terminal:

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

State terminal:

- `COMPLETED`: workflow selesai
- `FAILED`: workflow gagal atau dibatalkan
- `BLOCKED`: workflow terblokir dan perlu intervensi

`WAITING_USER` berarti workflow menunggu jawaban user. State aktif lain seperti `REQUIREMENT_ANALYSIS` seharusnya bergerak lagi otomatis; jika terlihat lama setelah restart worker, cek timeline event task untuk `WORKFLOW_RESUMED` dan cek log worker setelah event tersebut.

## 4. Workflow control

### `POST /api/v1/workflow/start`

Mengembalikan acknowledgement. Worker tetap harus dijalankan sebagai process terpisah:

```powershell
.\.venv\Scripts\python.exe -m nightshift.worker
```

### `POST /api/v1/workflow/stop`

Mengembalikan acknowledgement. Untuk benar-benar menghentikan worker, tekan `Ctrl+C` pada terminal worker.

## 5. LLM probe

### `POST /api/v1/test/llm`

Menguji koneksi Azure LLM yang dikonfigurasi di `.env`.

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/v1/test/llm |
    ConvertTo-Json
```

## 6. Telegram webhook

### `POST /api/v1/webhooks/telegram`

Endpoint webhook Telegram untuk menerima jawaban klarifikasi user. Payload mengikuti format update Telegram. Endpoint mengembalikan `{"ok":true}` jika request diterima.

## 7. Urutan pemantauan task

1. `POST /api/v1/tasks` untuk membuat task.
2. Simpan field response `id` sebagai `execution_id`.
3. `GET /api/v1/workflow/status` untuk ringkasan jumlah task per state.
4. `GET /api/v1/tasks/{execution_id}` untuk state dan metadata terbaru.
5. `GET /api/v1/tasks/{execution_id}/events` untuk timeline detail.
6. Gunakan `retry` jika task gagal dan memang boleh dijalankan ulang.
