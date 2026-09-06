"""Tests for LLM-generated clarification questions."""

from __future__ import annotations

import pytest

from nightshift.app.agents.clarification_agent import (
    ClarificationAgent,
    build_clarification_prompt,
)
from nightshift.app.domains.clarification import (
    ClarificationQuestion,
    ClarificationQuestions,
)


class _FakeLLM:
    def __init__(self) -> None:
        self.prompt = ""
        self.schema = None

    async def structured_completion(self, prompt, schema, system=None):
        self.prompt = prompt
        self.schema = schema
        return ClarificationQuestions(
            questions=[
                ClarificationQuestion(
                    question="Behavior apa yang diharapkan saat filter kosong?",
                    reason="Implementasi perlu aturan default yang eksplisit.",
                    example="Kembalikan semua data saat filter kosong.",
                )
            ]
        )


@pytest.mark.asyncio
async def test_clarification_agent_generates_task_specific_questions() -> None:
    llm = _FakeLLM()
    questions = await ClarificationAgent(llm).generate(
        task={
            "title": "Tambah endpoint invoice",
            "description": "Buat endpoint untuk pencarian invoice.",
        },
        readiness_analysis={"criteria": [{"key": "expected_behavior", "satisfied": False}]},
    )

    assert questions[0]["question"].startswith("Behavior apa")
    assert llm.schema is ClarificationQuestions
    assert "Tambah endpoint invoice" in llm.prompt
    assert "UUID" not in llm.prompt


def test_clarification_prompt_contains_implementation_context() -> None:
    prompt = build_clarification_prompt(
        {"title": "Tambah fitur", "description": "Detail task"},
        {"criteria": []},
        {"repository": "nightshift"},
    )

    assert "TASK TITLE" in prompt
    assert "READINESS EVIDENCE" in prompt
    assert "REPOSITORY CONTEXT" in prompt
