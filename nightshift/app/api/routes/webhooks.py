"""Webhook endpoints (Telegram HITL)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from nightshift.app.persistence.database import get_db
from nightshift.integrations.telegram.hitl import apply_telegram_answer

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/telegram")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    body = await request.json()
    message = body.get("message") or body.get("edited_message") or {}
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not text or not chat_id:
        return {"ok": True}

    apply_telegram_answer(db, str(chat_id), text)
    return {"ok": True}
