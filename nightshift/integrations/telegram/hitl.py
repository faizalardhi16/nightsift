"""Shared Telegram HITL answer-processing logic.

Used by both the webhook route (public deployments) and the local long-polling
consumer (``poller.py``), so user replies are resolved identically regardless
of which transport delivered them.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from nightshift.app.config.logging import get_logger
from nightshift.app.persistence.models import ClarificationSession
from nightshift.app.persistence.repositories.task_execution_repo import (
    TaskExecutionRepository,
)
from nightshift.app.workflow.state import State
from nightshift.integrations.telegram.webhook_handler import parse_answer

logger = get_logger(__name__)


def apply_telegram_answer(db: Session, chat_id: str, text: str) -> bool:
    """Record a user answer on the most recent OPEN clarification session and
    resume the workflow.

    Returns ``True`` when the answer was applied to a session.
    """
    session = _find_open_session(db, chat_id)
    if session is None:
        logger.info("telegram_message_no_session", chat_id=chat_id)
        return False

    session.raw_answer = text
    question_count = len((session.question_payload or {}).get("questions", []))
    session.parsed_answer = {"answers": parse_answer(text, question_count)}
    session.status = "ANSWERED"
    db.flush()

    # Resume the workflow by re-queuing the execution through requirement analysis.
    repo = TaskExecutionRepository(db)
    execution = repo.get(session.task_execution_id)
    if execution is None:
        logger.warning(
            "telegram_execution_missing",
            execution_id=str(session.task_execution_id),
        )
        db.commit()
        return True

    execution.state = State.REQUIREMENT_ANALYSIS.value
    repo.log_event(
        execution.id,
        "CLARIFICATION_ANSWERED",
        State.WAITING_USER.value,
        State.REQUIREMENT_ANALYSIS.value,
        session.parsed_answer,
    )
    db.commit()
    logger.info(
        "telegram_answer_applied",
        execution_id=str(execution.id),
        clarification_session_id=str(session.id),
    )
    return True


def _find_open_session(db: Session, chat_id: str) -> ClarificationSession | None:
    # In V1, only one active clarification is expected per chat; the chat id
    # match is performed by checking sessions without a stored chat mapping
    # (stored in question_payload by the producer). Here we match the most
    # recently opened OPEN session.
    return (
        db.execute(
            select(ClarificationSession)
            .where(ClarificationSession.status == "OPEN")
            .order_by(ClarificationSession.created_at.desc())
        ).scalars().first()
    )
