"""Workflow control endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nightshift.app.config.settings import get_settings
from nightshift.app.persistence.database import get_db
from nightshift.app.persistence.models import TaskExecution

router = APIRouter(prefix="/api/v1/workflow", tags=["workflow"])


@router.post("/start")
def start_workflow() -> dict:
    return {
        "status": "started",
        "note": "Worker polls tasks continuously; nothing to start explicitly.",
    }


@router.post("/stop")
def stop_workflow() -> dict:
    return {"status": "acknowledged", "note": "Stop the worker process to halt processing."}


@router.get("/status")
def workflow_status(db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    counts = {
        row[0]: row[1]
        for row in db.execute(
            select(TaskExecution.state, func.count()).group_by(TaskExecution.state)
        ).all()
    }
    return {
        "worker_config": {
            "max_active_coding_tasks": settings.max_active_coding_tasks,
            "readiness_threshold": settings.readiness_threshold,
            "llm_configured": settings.llm_configured,
        },
        "task_counts": counts,
    }
