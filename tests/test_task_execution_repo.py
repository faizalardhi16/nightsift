"""Regression tests for task execution claiming and recovery."""

from __future__ import annotations

from uuid import uuid4

from nightshift.app.persistence.models import TaskExecution
from nightshift.app.persistence.repositories.task_execution_repo import TaskExecutionRepository
from nightshift.app.workflow.state import State


class _SessionStub:
    def __init__(self) -> None:
        self.added = []
        self.flush_count = 0

    def add(self, value) -> None:
        self.added.append(value)

    def flush(self) -> None:
        self.flush_count += 1


def test_recover_interrupted_execution_restarts_from_claimed() -> None:
    session = _SessionStub()
    repo = TaskExecutionRepository(session)
    execution = TaskExecution(
        id=uuid4(),
        external_task_id="ACE-1",
        state=State.REQUIREMENT_ANALYSIS.value,
        active_coding=False,
    )

    repo._recover_interrupted_execution(execution)

    assert execution.state == State.CLAIMED.value
    assert execution.started_at is not None
    assert session.added[0].event_type == "WORKFLOW_RESUMED"
    assert session.added[0].from_state == State.REQUIREMENT_ANALYSIS.value
    assert session.added[0].to_state == State.CLAIMED.value


def test_claim_next_recovers_interrupted_workflow_before_new_queue(monkeypatch) -> None:
    repo = TaskExecutionRepository(_SessionStub())
    execution = TaskExecution(
        id=uuid4(),
        external_task_id="ACE-1",
        state=State.CLAIMED.value,
    )
    calls = []

    monkeypatch.setattr(repo, "_acquire_claim_lock", lambda: calls.append("lock"))
    monkeypatch.setattr(repo, "_claim_resumable_execution", lambda: execution)
    monkeypatch.setattr(
        repo,
        "has_blocking_execution",
        lambda: (_ for _ in ()).throw(AssertionError("should not check queued path")),
    )

    claimed = repo.claim_next()

    assert claimed is execution
    assert calls == ["lock"]
