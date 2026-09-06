"""Tests for the shared Telegram HITL answer-processing logic."""

from __future__ import annotations

from uuid import uuid4

import pytest

from nightshift.app.persistence.models import ClarificationSession
from nightshift.app.workflow.state import State
from nightshift.integrations.telegram import hitl


class _ScalarResult:
    def __init__(self, value=None) -> None:
        self._value = value

    def scalars(self):
        return self

    def first(self):
        return self._value


class _DbStub:
    def __init__(self, open_session) -> None:
        self.open_session = open_session
        self.flushed = False
        self.committed = False

    def execute(self, _statement):
        return _ScalarResult(self.open_session)

    def flush(self) -> None:
        self.flushed = True

    def commit(self) -> None:
        self.committed = True


class _ExecutionStub:
    def __init__(self) -> None:
        self.id = uuid4()
        self.state = None


class _FakeRepo:
    def __init__(self, execution=None) -> None:
        self.execution = execution or _ExecutionStub()
        self.logged_event = None

    def get(self, execution_id):
        return self.execution

    def log_event(self, execution_id, event, from_state, to_state, payload) -> None:
        self.logged_event = (execution_id, event, from_state, to_state, payload)


def _open_session() -> ClarificationSession:
    return ClarificationSession(
        id=uuid4(),
        task_execution_id=uuid4(),
        question_payload={"questions": [{"question": "Q1"}, {"question": "Q2"}]},
        status="OPEN",
    )


def test_apply_answer_without_open_session_returns_false(monkeypatch) -> None:
    db = _DbStub(open_session=None)

    applied = hitl.apply_telegram_answer(db, "111", "jawaban apa saja")

    assert applied is False
    assert db.committed is False


def test_apply_answer_records_and_resumes_workflow(monkeypatch) -> None:
    session = _open_session()
    db = _DbStub(open_session=session)
    repo = _FakeRepo()
    monkeypatch.setattr(hitl, "TaskExecutionRepository", lambda _db: repo)

    applied = hitl.apply_telegram_answer(db, "111", "1A\n2B")

    assert applied is True
    assert session.raw_answer == "1A\n2B"
    assert session.parsed_answer == {"answers": ["1A", "2B"]}
    assert session.status == "ANSWERED"
    assert db.flushed is True
    assert db.committed is True
    assert repo.execution.state == State.REQUIREMENT_ANALYSIS.value
    assert repo.logged_event[1] == "CLARIFICATION_ANSWERED"
    assert repo.logged_event[2] == State.WAITING_USER.value
    assert repo.logged_event[3] == State.REQUIREMENT_ANALYSIS.value


def test_apply_answer_when_execution_missing_still_commits(monkeypatch) -> None:
    session = _open_session()
    db = _DbStub(open_session=session)
    monkeypatch.setattr(hitl, "TaskExecutionRepository", lambda _db: _FakeRepo(execution=None))

    applied = hitl.apply_telegram_answer(db, "111", "ok")

    assert applied is True
    assert session.status == "ANSWERED"
    assert db.committed is True


@pytest.mark.asyncio
async def test_find_open_session_orders_by_recency() -> None:
    recent = _open_session()
    db = _DbStub(open_session=recent)

    found = hitl._find_open_session(db, "111")

    assert found is recent
