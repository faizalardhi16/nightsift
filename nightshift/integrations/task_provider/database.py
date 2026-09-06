"""Database task provider (development fallback).

Used when Ace MCP is not available. Tasks are ingested via the REST API into
a local pending-tasks queue.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from nightshift.app.persistence.models import TaskExecution
from nightshift.app.workflow.state import State
from nightshift.integrations.task_provider.base import ExternalTask, TaskProvider


class DatabaseTaskProvider(TaskProvider):
    name = "database"

    def __init__(self, session: Session) -> None:
        self._session = session

    async def get_candidates(self) -> list[ExternalTask]:
        executions = (
            self._session.query(TaskExecution)
            .filter(TaskExecution.state == State.QUEUED.value)
            .all()
        )
        return [
            ExternalTask(
                id=e.external_task_id,
                title=e.title or e.external_task_id,
                description=e.description or "",
                priority=e.priority,
                metadata={"execution_id": str(e.id)},
            )
            for e in executions
        ]

    async def get_task(self, task_id: str) -> ExternalTask:
        execution = (
            self._session.query(TaskExecution)
            .filter(TaskExecution.external_task_id == task_id)
            .first()
        )
        if execution is None:
            raise ValueError(f"Task not found: {task_id}")
        return ExternalTask(
            id=execution.external_task_id,
            title=execution.title or execution.external_task_id,
            description=execution.description or "",
            priority=execution.priority,
        )

    async def update_status(self, task_id: str, status: str) -> None:
        # Status is reflected in the local execution state; no-op here.
        return None
