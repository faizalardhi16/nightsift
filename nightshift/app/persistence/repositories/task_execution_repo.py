"""Task execution repository.

Provides atomic task claiming (PRD section 20) and state persistence.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nightshift.app.domains.task_selection import title_ease_score
from nightshift.app.persistence.models import TaskExecution, WorkflowEvent
from nightshift.app.workflow.state import ACE_SYNC_BLOCKING_STATES, State
from nightshift.app.workflow.transitions import is_valid_transition


class TaskExecutionRepository:
    _CLAIM_LOCK_KEY = 1314089033

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, execution_id: uuid.UUID) -> TaskExecution | None:
        return self._session.get(TaskExecution, execution_id)

    def create(
        self,
        external_task_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: int = 0,
    ) -> TaskExecution:
        execution = TaskExecution(
            external_task_id=external_task_id,
            title=title,
            description=description,
            priority=priority,
            state=State.QUEUED.value,
        )
        self._session.add(execution)
        self._session.flush()
        self.log_event(execution.id, "ENQUEUED", None, State.QUEUED.value)
        return execution

    def claim_next(self) -> TaskExecution | None:
        """Claim one task or recover one interrupted non-waiting workflow."""
        self._acquire_claim_lock()

        execution = self._claim_resumable_execution()
        if execution is not None:
            return execution

        if self.has_blocking_execution():
            return None

        stmt = (
            select(TaskExecution)
            .where(TaskExecution.state == State.QUEUED.value)
            .order_by(TaskExecution.priority.desc(), TaskExecution.created_at.asc())
            .with_for_update(skip_locked=True)
        )
        queued = list(self._session.execute(stmt).scalars().all())
        execution = max(queued, key=lambda item: title_ease_score(item.title), default=None)
        if execution is None:
            return None

        self.log_event(
            execution.id,
            "TASK_SELECTED",
            State.QUEUED.value,
            State.CLAIMED.value,
            {
                "selection": "easiest_title",
                "title_ease_score": title_ease_score(execution.title),
            },
        )
        self.transition(execution, State.CLAIMED)
        execution.started_at = datetime.now(UTC)
        return execution

    def _claim_resumable_execution(self) -> TaskExecution | None:
        """Recover a committed active state left behind by a prior worker pass."""
        if self._has_waiting_user_or_active_coding_execution():
            return None

        stmt = (
            select(TaskExecution)
            .where(
                TaskExecution.state.in_(ACE_SYNC_BLOCKING_STATES),
                TaskExecution.state != State.WAITING_USER.value,
                TaskExecution.active_coding.is_(False),
            )
            .order_by(TaskExecution.updated_at.asc(), TaskExecution.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        execution = self._session.execute(stmt).scalar_one_or_none()
        if execution is None:
            return None

        self._recover_interrupted_execution(execution)
        return execution

    def _has_waiting_user_or_active_coding_execution(self) -> bool:
        return (
            self._session.execute(
                select(TaskExecution.id)
                .where(
                    TaskExecution.state.in_(ACE_SYNC_BLOCKING_STATES),
                    (
                        (TaskExecution.state == State.WAITING_USER.value)
                        | (TaskExecution.active_coding.is_(True))
                    ),
                )
                .limit(1)
            ).scalar_one_or_none()
            is not None
        )

    def _recover_interrupted_execution(self, execution: TaskExecution) -> None:
        from_state = execution.state
        execution.state = State.CLAIMED.value
        execution.started_at = datetime.now(UTC)
        self.log_event(
            execution.id,
            "WORKFLOW_RESUMED",
            from_state,
            State.CLAIMED.value,
            {"reason": "recover_interrupted_active_state"},
        )
        self._session.flush()

    def has_blocking_execution(self) -> bool:
        """Return whether any non-queued, non-terminal workflow is active."""
        return (
            self._session.execute(
                select(TaskExecution.id)
                .where(TaskExecution.state.in_(ACE_SYNC_BLOCKING_STATES))
                .limit(1)
            ).scalar_one_or_none()
            is not None
        )

    def _acquire_claim_lock(self) -> None:
        """Serialize claim checks across worker processes on PostgreSQL."""
        bind = self._session.get_bind()
        if bind.dialect.name == "postgresql":
            self._session.execute(select(func.pg_advisory_xact_lock(self._CLAIM_LOCK_KEY)))

    def transition(self, execution: TaskExecution, new_state: State) -> None:
        from_state = execution.state
        if from_state == new_state.value:
            return
        if not is_valid_transition(from_state, new_state.value):
            raise ValueError(
                f"Invalid transition {from_state} -> {new_state.value}"
            )

        execution.state = new_state.value
        if new_state in (State.COMPLETED, State.FAILED, State.BLOCKED):
            execution.completed_at = datetime.now(UTC)
        self.log_event(execution.id, "STATE_TRANSITION", from_state, new_state.value)
        self._session.flush()

    def set_readiness(self, execution: TaskExecution, score: int) -> None:
        execution.readiness_score = score
        self._session.flush()

    def log_event(
        self,
        execution_id: uuid.UUID,
        event_type: str,
        from_state: str | None,
        to_state: str | None,
        payload: dict | None = None,
    ) -> None:
        self._session.add(
            WorkflowEvent(
                task_execution_id=execution_id,
                event_type=event_type,
                from_state=from_state,
                to_state=to_state,
                payload=payload,
            )
        )
        self._session.flush()

    def list_queued(self) -> list[TaskExecution]:
        stmt = (
            select(TaskExecution)
            .where(TaskExecution.state == State.QUEUED.value)
            .order_by(TaskExecution.priority.desc(), TaskExecution.created_at.asc())
        )
        return list(self._session.execute(stmt).scalars().all())
