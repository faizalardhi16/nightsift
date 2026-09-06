"""request_clarification node: send focused questions via Telegram.

If Telegram is not configured, the task is blocked (cannot guess per PRD
section 6).
"""

from __future__ import annotations

from sqlalchemy import func, select

from nightshift.app.agents.clarification_agent import ClarificationAgent
from nightshift.app.config.logging import get_logger
from nightshift.app.persistence.models import ClarificationSession, TaskExecution
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State
from nightshift.integrations.telegram.bot import TelegramClient
from nightshift.integrations.telegram.formatter import format_clarification

logger = get_logger(__name__)

_CLARIFICATION_LOCK_KEY = 1314089034

_CLARIFICATION_TEMPLATES = {
    "objective": (
        "Apa tujuan utama task ini dan hasil akhir yang diharapkan?",
        "Tujuannya menambahkan endpoint export invoice untuk menggantikan proses manual.",
    ),
    "acceptance_criteria": (
        "Kriteria apa yang menentukan task ini sudah selesai dan benar?",
        "Endpoint mengembalikan HTTP 200, file XLSX valid, dan total row sesuai filter.",
    ),
    "repository": (
        "Repository atau project mana yang harus diubah?",
        "Repository SPBI, service invoice, branch develop.",
    ),
    "module_context": (
        "File, module, route, atau komponen mana yang terkait?",
        "Backend: nightshift/app/api/routes/tasks.py; frontend: halaman TaskList.",
    ),
    "expected_behavior": (
        "Bagaimana behavior yang diharapkan untuk input dan output normal?",
        "Jika filter kosong, kembalikan semua invoice; jika ada filter status, "
        "hanya status tersebut.",
    ),
    "edge_cases": (
        "Apa edge case yang wajib ditangani?",
        "Invoice kosong, nomor duplikat, tanggal tidak valid, dan request timeout.",
    ),
    "test_expectations": (
        "Test apa yang harus ditambahkan atau diperbarui?",
        "Tambahkan unit test untuk filter status dan integration test untuk response HTTP 200/400.",
    ),
    "dependencies": (
        "Dependency, API eksternal, konfigurasi, atau credential apa yang diperlukan?",
        "Gunakan service Invoice API; tidak ada dependency baru; URL berasal dari environment.",
    ),
    "target_branch": (
        "Branch target untuk perubahan ini apa?",
        "Buat branch dari develop dan targetkan merge request ke develop.",
    ),
}


async def request_clarification(ctx: WorkflowContext) -> State:
    _acquire_clarification_lock(ctx)

    existing_session = ctx.session.execute(
        select(ClarificationSession)
        .where(
            ClarificationSession.task_execution_id == ctx.execution_id,
            ClarificationSession.status == "OPEN",
        )
        .order_by(ClarificationSession.created_at.desc())
        .limit(1)
    ).scalars().first()
    if existing_session is not None:
        logger.info(
            "clarification_already_open",
            execution_id=str(ctx.execution_id),
        )
        return State.WAITING_USER

    if _has_other_waiting_user(ctx):
        logger.info(
            "clarification_skipped_waiting_user",
            execution_id=str(ctx.execution_id),
        )
        return State.QUEUED

    _close_stale_clarifications(ctx)

    questions = ctx.get("clarification_questions")
    if not questions:
        questions = await _generate_questions(ctx)
    ctx.set("clarification_questions", questions)

    task = ctx.get("task", {})
    score = ctx.get("readiness_score", 0)

    telegram = TelegramClient(
        ctx.settings.telegram_bot_token,
        ctx.settings.telegram_chat_id,
    )

    if not telegram.configured:
        logger.warning("telegram_unavailable_blocking_task")
        ctx.set("error", {"type": "REQUIREMENT_FAILURE", "message": "Telegram not configured"})
        return State.BLOCKED

    text = format_clarification(
        title=task.get("title") or "Task tanpa judul",
        score=score,
        questions=questions,
    )
    message_id = await telegram.send_message(text)

    session = ClarificationSession(
        task_execution_id=ctx.execution_id,
        question_payload={"questions": questions},
        message_id=str(message_id) if message_id else None,
        status="OPEN",
    )
    ctx.session.add(session)
    ctx.session.flush()
    ctx.set("clarification_session_id", str(session.id))

    return State.WAITING_USER


def _acquire_clarification_lock(ctx: WorkflowContext) -> None:
    """Serialize clarification checks on PostgreSQL worker deployments."""
    bind = ctx.session.get_bind()
    if bind.dialect.name == "postgresql":
        ctx.session.execute(select(func.pg_advisory_xact_lock(_CLARIFICATION_LOCK_KEY)))


def _has_other_waiting_user(ctx: WorkflowContext) -> bool:
    return (
        ctx.session.execute(
            select(TaskExecution.id)
            .where(
                TaskExecution.state == State.WAITING_USER.value,
                TaskExecution.id != ctx.execution_id,
            )
            .limit(1)
        ).scalar_one_or_none()
        is not None
    )


def _close_stale_clarifications(ctx: WorkflowContext) -> None:
    """Close OPEN sessions whose task is no longer waiting for an answer.

    A failed/cancelled task can leave an old session behind. Treating that
    orphan as active sends the current task back to QUEUED forever.
    """
    stale_sessions = (
        ctx.session.execute(
            select(ClarificationSession)
            .join(
                TaskExecution,
                TaskExecution.id == ClarificationSession.task_execution_id,
            )
            .where(
                ClarificationSession.status == "OPEN",
                TaskExecution.state != State.WAITING_USER.value,
            )
        )
        .scalars()
        .all()
    )
    for session in stale_sessions:
        session.status = "CANCELLED"
        logger.warning(
            "clarification_stale_session_closed",
            execution_id=str(session.task_execution_id),
            clarification_session_id=str(session.id),
        )
    if stale_sessions:
        ctx.session.flush()


async def _generate_questions(ctx: WorkflowContext) -> list[dict]:
    """Prefer LLM-generated gaps, with a deterministic offline fallback."""
    if ctx.llm is not None:
        try:
            questions = await ClarificationAgent(ctx.llm).generate(
                task=ctx.get("task", {}),
                readiness_analysis=ctx.get("readiness_analysis", {}),
                context=ctx.get("context", {}),
            )
            if questions:
                logger.info(
                    "clarification_questions_generated",
                    execution_id=str(ctx.execution_id),
                    question_count=len(questions),
                    source="llm",
                )
                return questions
            logger.info(
                "clarification_questions_empty",
                execution_id=str(ctx.execution_id),
            )
        except Exception as exc:
            logger.error(
                "clarification_agent_failed",
                execution_id=str(ctx.execution_id),
                error=str(exc),
            )

    fallback_questions = _default_questions(ctx)
    logger.info(
        "clarification_questions_generated",
        execution_id=str(ctx.execution_id),
        question_count=len(fallback_questions),
        source="fallback",
    )
    return fallback_questions


def _default_questions(ctx: WorkflowContext) -> list[dict]:
    analysis = ctx.get("readiness_analysis", {})
    questions = []
    criteria = analysis.get("criteria", [])
    for criterion in criteria:
        if not criterion.get("satisfied"):
            key = criterion.get("key", "")
            question, example = _CLARIFICATION_TEMPLATES.get(
                key,
                (
                    f"Mohon jelaskan requirement untuk '{key}'.",
                    "Berikan detail yang dapat diverifikasi oleh developer dan tester.",
                ),
            )
            questions.append(
                {
                    "question": question,
                    "options": [],
                    "reason": criterion.get("reason", ""),
                    "example": example,
                }
            )
    if not questions:
        questions = [
            {
                "question": "Bagian requirement mana yang masih kurang jelas?",
                "options": [],
                "reason": "Task belum memiliki detail yang cukup untuk dilanjutkan tanpa asumsi.",
                "example": (
                    "Jelaskan tujuan, file/module terdampak, expected behavior, "
                    "dan acceptance criteria."
                ),
            }
        ]
    return questions[:5]
