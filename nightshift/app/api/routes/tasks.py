"""Task management API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from nightshift.app.api.schemas.task_schemas import (
    TaskCreateRequest,
    TaskResponse,
    WorkflowEventResponse,
)
from nightshift.app.config.logging import get_logger
from nightshift.app.config.settings import get_settings
from nightshift.app.domains.task_scope import is_development_task
from nightshift.app.persistence.database import get_db
from nightshift.app.persistence.models import (
    ClarificationSession,
    TaskExecution,
    WorkflowEvent,
)
from nightshift.app.persistence.repositories.task_execution_repo import (
    TaskExecutionRepository,
)
from nightshift.app.workflow.state import TERMINAL_STATES, State
from nightshift.integrations.task_provider.ace_mcp import (
    AceMcpTaskProvider,
    update_ace_status,
)
from nightshift.integrations.task_provider.base import ExternalTask

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])
logger = get_logger(__name__)


@router.get("", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)) -> list[TaskExecution]:
    stmt = select(TaskExecution).order_by(TaskExecution.created_at.desc())
    return list(db.execute(stmt).scalars().all())


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(payload: TaskCreateRequest, db: Session = Depends(get_db)) -> TaskExecution:
    repo = TaskExecutionRepository(db)
    execution = repo.create(
        external_task_id=payload.external_task_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
    )
    if payload.repository_id is not None:
        execution.repository_id = payload.repository_id
    db.commit()
    db.refresh(execution)
    return execution


@router.get("/{execution_id}", response_model=TaskResponse)
def get_task(execution_id: uuid.UUID, db: Session = Depends(get_db)) -> TaskExecution:
    execution = db.get(TaskExecution, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return execution


@router.post("/cancel-all")
def cancel_all_tasks(db: Session = Depends(get_db)) -> dict:
    """Cancel every non-terminal task execution."""
    terminal_values = {state.value for state in TERMINAL_STATES}
    executions = list(
        db.execute(
            select(TaskExecution).where(~TaskExecution.state.in_(terminal_values))
        ).scalars().all()
    )

    repo = TaskExecutionRepository(db)
    task_ids: list[str] = []
    for execution in executions:
        previous_state = execution.state
        execution.state = State.FAILED.value
        execution.failure_reason = "Cancelled by user"
        execution.active_coding = False
        repo.log_event(
            execution.id,
            "CANCELLED",
            previous_state,
            State.FAILED.value,
        )
        task_ids.append(str(execution.id))

    db.commit()
    return {"cancelled": len(task_ids), "task_ids": task_ids}


@router.post("/retry-all")
async def retry_all_tasks(db: Session = Depends(get_db)) -> dict:
    """Re-queue failed/waiting development tasks and reset ACE to TODO."""
    retryable_states = {State.FAILED.value, State.WAITING_USER.value}
    executions = list(
        db.execute(
            select(TaskExecution).where(TaskExecution.state.in_(retryable_states))
        ).scalars().all()
    )

    repo = TaskExecutionRepository(db)
    retried_ids: list[str] = []
    skipped_ids: list[str] = []
    retried_executions: list[TaskExecution] = []
    for execution in executions:
        if not _is_development_execution(execution):
            skipped_ids.append(str(execution.id))
            continue
        _queue_retry(repo, execution)
        retried_executions.append(execution)
        retried_ids.append(str(execution.id))

    _close_open_clarifications(db, retried_executions)
    db.commit()
    ace_result = await _reset_ace_tasks(retried_executions)
    logger.info(
        "retry_all_completed",
        retried=len(retried_ids),
        skipped=len(skipped_ids),
        ace_updated=ace_result["ace_updated"],
        ace_failed=ace_result["ace_failed"],
    )
    return {
        "retried": len(retried_ids),
        "task_ids": retried_ids,
        "skipped": len(skipped_ids),
        "skipped_task_ids": skipped_ids,
        **ace_result,
    }


@router.post("/{execution_id}/retry", response_model=TaskResponse)
def retry_task(execution_id: uuid.UUID, db: Session = Depends(get_db)) -> TaskExecution:
    execution = db.get(TaskExecution, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if not _is_development_execution(execution):
        raise HTTPException(
            status_code=409,
            detail="Only development tasks can be retried",
        )
    repo = TaskExecutionRepository(db)
    _queue_retry(repo, execution)
    db.commit()
    db.refresh(execution)
    return execution


@router.post("/{execution_id}/cancel", response_model=TaskResponse)
def cancel_task(execution_id: uuid.UUID, db: Session = Depends(get_db)) -> TaskExecution:
    execution = db.get(TaskExecution, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Task not found")
    repo = TaskExecutionRepository(db)
    execution.state = State.FAILED.value
    execution.failure_reason = "Cancelled by user"
    execution.active_coding = False
    repo.log_event(execution.id, "CANCELLED", None, State.FAILED.value)
    db.commit()
    db.refresh(execution)
    return execution


@router.get("/{execution_id}/events", response_model=list[WorkflowEventResponse])
def list_events(execution_id: uuid.UUID, db: Session = Depends(get_db)) -> list[WorkflowEvent]:
    return list(
        db.execute(
            select(WorkflowEvent)
            .where(WorkflowEvent.task_execution_id == execution_id)
            .order_by(WorkflowEvent.created_at.asc())
        ).scalars().all()
    )


def _is_development_execution(execution: TaskExecution) -> bool:
    return is_development_task(
        ExternalTask(
            id=execution.external_task_id,
            title=execution.title or "",
            description=execution.description or "",
        )
    )


def _queue_retry(repo: TaskExecutionRepository, execution: TaskExecution) -> None:
    previous_state = execution.state
    execution.state = State.QUEUED.value
    execution.repair_attempt = 0
    execution.failure_reason = None
    execution.active_coding = False
    execution.started_at = None
    execution.completed_at = None
    repo.log_event(
        execution.id,
        "RETRY_QUEUED",
        previous_state,
        State.QUEUED.value,
    )


def _close_open_clarifications(
    db: Session,
    executions: list[TaskExecution],
) -> None:
    execution_ids = [execution.id for execution in executions]
    if not execution_ids:
        return
    sessions = db.execute(
        select(ClarificationSession).where(
            ClarificationSession.task_execution_id.in_(execution_ids),
            ClarificationSession.status == "OPEN",
        )
    ).scalars().all()
    for session in sessions:
        session.status = "CANCELLED"
        logger.info(
            "clarification_cancelled_for_retry",
            execution_id=str(session.task_execution_id),
            clarification_session_id=str(session.id),
        )


async def _reset_ace_tasks(executions: list[TaskExecution]) -> dict:
    """Best-effort ACE reset; local retry has already been committed."""
    result = {
        "ace_updated": 0,
        "ace_failed": 0,
        "ace_failed_task_ids": [],
    }
    if not executions:
        return result

    settings = get_settings()
    if not settings.ace_mcp_enabled:
        logger.info("retry_all_ace_sync_skipped", reason="ACE_MCP_ENABLED=false")
        return result

    provider = AceMcpTaskProvider(settings)
    try:
        await provider.connect()
        for execution in executions:
            synced = await update_ace_status(
                provider,
                execution.external_task_id,
                "TODO",
            )
            if synced:
                result["ace_updated"] += 1
            else:
                result["ace_failed"] += 1
                result["ace_failed_task_ids"].append(str(execution.id))
    except Exception as exc:  # noqa: BLE001 - local retry must remain successful
        logger.exception("retry_all_ace_sync_failed", error=str(exc))
        result["ace_failed"] = len(executions)
        result["ace_failed_task_ids"] = [str(execution.id) for execution in executions]
    finally:
        await provider.close()
    return result
