"""Tests for task context assembly."""

from __future__ import annotations

from uuid import uuid4

from nightshift.app.persistence.models import ClarificationSession
from nightshift.app.workflow.nodes.build_context import _apply_latest_clarification_answer


class _ScalarResult:
    def __init__(self, value=None) -> None:
        self._value = value

    def scalars(self):
        return self

    def first(self):
        return self._value


class _SessionStub:
    def __init__(self, clarification) -> None:
        self._clarification = clarification

    def execute(self, _statement):
        return _ScalarResult(self._clarification)


class _ContextStub:
    def __init__(self, clarification) -> None:
        self.execution_id = uuid4()
        self.session = _SessionStub(clarification)
        self.state = {}

    def set(self, key, value) -> None:
        self.state[key] = value


def test_apply_latest_clarification_answer_adds_human_evidence_to_task() -> None:
    clarification = ClarificationSession(
        id=uuid4(),
        task_execution_id=uuid4(),
        question_payload={"questions": []},
        raw_answer="1. Tambahkan filter status invoice.",
        parsed_answer={"answers": ["Tambahkan filter status invoice"]},
        status="ANSWERED",
    )
    ctx = _ContextStub(clarification)
    task = {"title": "Tambah filter"}

    _apply_latest_clarification_answer(ctx, task)

    assert task["clarification"]["raw_answer"] == "1. Tambahkan filter status invoice."
    assert task["clarification"]["parsed_answer"]["answers"] == [
        "Tambahkan filter status invoice"
    ]
    assert ctx.state["clarification"] == task["clarification"]
