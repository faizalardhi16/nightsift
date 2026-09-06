"""Webhook endpoints (Telegram HITL)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from nightshift.app.config.logging import get_logger
from nightshift.app.persistence.database import get_db
from nightshift.app.persistence.models import ClarificationSession
from nightshift.app.persistence.repositories.task_execution_repo import (
    TaskExecutionRepository,
)
from nightshift.app.workflow.state import State
from nightshift.integrations.telegram.webhook_handler import parse_answer

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/telegram")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    body = await request.json()
    message = body.get("message") or body.get("edited_message") or {}
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not text or not chat_id:
        return {"ok": True}

    session = _find_open_session(db, str(chat_id))
    if session is None:
        logger.info("telegram_message_no_session", chat_id=chat_id)
        return {"ok": True}

    session.raw_answer = text
    question_count = len(session.question_payload.get("questions", []))
    session.parsed_answer = {"answers": parse_answer(text, question_count)}
    session.status = "ANSWERED"
    db.flush()

    # Resume the workflow by re-queuing the execution through requirement analysis.
    repo = TaskExecutionRepository(db)
    execution = repo.get(session.task_execution_id)
    if execution is None:
        return {"ok": True}

    execution.state = State.REQUIREMENT_ANALYSIS.value
    repo.log_event(
        execution.id,
        "CLARIFICATION_ANSWERED",
        State.WAITING_USER.value,
        State.REQUIREMENT_ANALYSIS.value,
        session.parsed_answer,
    )
    db.commit()

    return {"ok": True}


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
