"""Regression tests for single active Telegram clarification."""

from __future__ import annotations

from uuid import uuid4

import pytest

from nightshift.app.persistence.models import ClarificationSession
from nightshift.app.workflow.nodes import request_clarification as clarification_node
from nightshift.app.workflow.state import State


class _ScalarResult:
    def __init__(self, value=None) -> None:
        self._value = value

    def scalars(self):
        return self

    def first(self):
        return self._value


class _SessionStub:
    def execute(self, _statement):
        return _ScalarResult()


class _ContextStub:
    def __init__(self) -> None:
        self.execution_id = uuid4()
        self.session = _SessionStub()

    def get(self, key, default=None):
        return default

    def set(self, _key, _value) -> None:
        raise AssertionError("clarification state should not be mutated")


@pytest.mark.asyncio
async def test_request_clarification_waits_when_another_task_is_waiting(monkeypatch) -> None:
    async def _generate_questions(_ctx):
        raise AssertionError("questions should not be generated")

    monkeypatch.setattr(clarification_node, "_acquire_clarification_lock", lambda _ctx: None)
    monkeypatch.setattr(clarification_node, "_has_other_waiting_user", lambda _ctx: True)
    monkeypatch.setattr(clarification_node, "_generate_questions", _generate_questions)

    state = await clarification_node.request_clarification(_ContextStub())

    assert state == State.QUEUED


def test_close_stale_clarification_sessions() -> None:
    class _SessionResult:
        def scalars(self):
            return self

        def all(self):
            return [session]

    class _Session:
        def execute(self, _statement):
            return _SessionResult()

        def flush(self):
            self.flushed = True

    session = ClarificationSession(
        id=uuid4(),
        task_execution_id=uuid4(),
        question_payload={"questions": []},
        status="OPEN",
    )
    context = type("Context", (), {"session": _Session()})()

    clarification_node._close_stale_clarifications(context)

    assert session.status == "CANCELLED"
    assert context.session.flushed is True
