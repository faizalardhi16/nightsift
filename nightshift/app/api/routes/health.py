"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from nightshift.app.config.settings import get_settings
from nightshift.app.persistence.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    database_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_ok = False

    return {
        "status": "ok",
        "database": "ok" if database_ok else "error",
        "llm_configured": settings.llm_configured,
        "version": "0.1.0",
    }
