"""LLM agent that turns requirement gaps into focused user questions."""

from __future__ import annotations

from nightshift.app.domains.clarification import (
    ClarificationQuestions,
)
from nightshift.integrations.llm.base import LLMProvider

SYSTEM_PROMPT = (
    "You are a senior software requirements analyst. Identify only the missing "
    "information that prevents an engineer from implementing the task safely. "
    "Write concise questions in Indonesian. Do not ask for information already "
    "present in the task. Never mention UUIDs or internal execution identifiers. "
    "For every question, explain why the answer is needed and give a concrete "
    "example answer. Return only the requested JSON structure."
)


def build_clarification_prompt(
    task: dict,
    readiness_analysis: dict | None = None,
    context: dict | None = None,
) -> str:
    """Build an evidence-only prompt for task-specific clarification."""
    return (
        "Generate the smallest useful set of clarification questions for this task. "
        "Ask only about gaps that affect implementation, testing, or review. "
        "If there are no material gaps, return an empty questions array.\n\n"
        f"TASK TITLE:\n{task.get('title', '')}\n\n"
        f"TASK DESCRIPTION:\n{task.get('description', '')}\n\n"
        f"ACCEPTANCE CRITERIA:\n{task.get('acceptance_criteria', [])}\n\n"
        f"READINESS EVIDENCE:\n{readiness_analysis or {}}\n\n"
        f"REPOSITORY CONTEXT:\n{context or {}}\n\n"
        "Return JSON: {\"questions\": [{\"question\": \"...\", "
        "\"reason\": \"...\", \"example\": \"...\", "
        "\"options\": [\"...\"]}]}"
    )


class ClarificationAgent:
    """Generate clarification questions through the model abstraction."""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def generate(
        self,
        task: dict,
        readiness_analysis: dict | None = None,
        context: dict | None = None,
    ) -> list[dict]:
        result = await self._llm.structured_completion(
            build_clarification_prompt(task, readiness_analysis, context),
            ClarificationQuestions,
            system=SYSTEM_PROMPT,
        )
        return [question.model_dump() for question in result.questions]
