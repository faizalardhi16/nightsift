"""Regression tests for retry-all state and ACE reset behavior."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from nightshift.app.api.routes import tasks as task_routes
from nightshift.app.persistence.models import ClarificationSession, TaskExecution
from nightshift.app.workflow.state import State


class _ScalarResult:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return self

    def all(self):
        return self._values


class _DbStub:
    def __init__(self, executions, sessions):
        self._results = [_ScalarResult(executions), _ScalarResult(sessions)]
        self.commits = 0

    def execute(self, _statement):
        return self._results.pop(0)

    def commit(self):
        self.commits += 1


class _RepoStub:
    def __init__(self, _db):
        self.events = []

    def log_event(self, execution_id, event_type, from_state, to_state, payload=None):
        self.events.append((execution_id, event_type, from_state, to_state, payload))


def _execution(state: State, title: str) -> TaskExecution:
    return TaskExecution(
        id=uuid4(),
        external_task_id=f"ACE-{uuid4()}",
        state=state.value,
        title=title,
        description="Implement this feature.",
        repair_attempt=2,
        failure_reason="previous failure",
    )


@pytest.mark.asyncio
async def test_retry_all_requeues_waiting_user_and_closes_open_session(monkeypatch) -> None:
    failed = _execution(State.FAILED, "Implement invoice export feature")
    waiting = _execution(State.WAITING_USER, "Add invoice filter feature")
    skipped = _execution(State.FAILED, "Deploy invoice service to production")
    session = ClarificationSession(
        id=uuid4(),
        task_execution_id=waiting.id,
        question_payload={"questions": []},
        status="OPEN",
    )
    db = _DbStub([failed, waiting, skipped], [session])
    repo = _RepoStub(db)

    monkeypatch.setattr(task_routes, "TaskExecutionRepository", lambda _db: repo)
    monkeypatch.setattr(
        task_routes,
        "get_settings",
        lambda: SimpleNamespace(ace_mcp_enabled=False),
    )

    result = await task_routes.retry_all_tasks(db)

    assert result["retried"] == 2
    assert set(result["task_ids"]) == {str(failed.id), str(waiting.id)}
    assert result["skipped"] == 1
    assert result["skipped_task_ids"] == [str(skipped.id)]
    assert result["ace_updated"] == 0
    assert result["ace_failed"] == 0
    assert failed.state == State.QUEUED.value
    assert waiting.state == State.QUEUED.value
    assert skipped.state == State.FAILED.value
    assert failed.repair_attempt == 0
    assert waiting.failure_reason is None
    assert session.status == "CANCELLED"
    assert db.commits == 1


@pytest.mark.asyncio
async def test_retry_all_reports_ace_updates_without_blocking_local_retry(monkeypatch) -> None:
    execution = _execution(State.WAITING_USER, "Implement task status feature")
    db = _DbStub([execution], [])
    repo = _RepoStub(db)
    calls = []

    class _ProviderStub:
        def __init__(self, _settings):
            pass

        async def connect(self):
            calls.append("connect")

        async def close(self):
            calls.append("close")

    async def _update(provider, task_id, status):
        calls.append((task_id, status))
        return True

    monkeypatch.setattr(task_routes, "TaskExecutionRepository", lambda _db: repo)
    monkeypatch.setattr(
        task_routes,
        "get_settings",
        lambda: SimpleNamespace(ace_mcp_enabled=True),
    )
    monkeypatch.setattr(task_routes, "AceMcpTaskProvider", _ProviderStub)
    monkeypatch.setattr(task_routes, "update_ace_status", _update)

    result = await task_routes.retry_all_tasks(db)

    assert result["retried"] == 1
    assert result["ace_updated"] == 1
    assert result["ace_failed"] == 0
    assert result["ace_failed_task_ids"] == []
    assert calls[0] == "connect"
    assert (execution.external_task_id, "TODO") in calls
    assert calls[-1] == "close"
