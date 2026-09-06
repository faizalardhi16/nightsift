"""Requirement analysis agent (readiness assessment).

Produces criterion-level structured evidence; the application computes the
final score (PRD sections 24-25).
"""

from __future__ import annotations

from nightshift.app.domains.readiness import READINESS_CRITERIA, ReadinessAnalysis
from nightshift.integrations.llm.base import LLMProvider

SYSTEM_PROMPT = (
    "You are a senior software engineering analyst. Evaluate whether a task "
    "description contains enough information for another engineer to implement "
    "it without guessing. Be strict and evidence-based. Never invent facts."
)


def build_readiness_prompt(task: dict, context: dict | None = None) -> str:
    criteria_lines = "\n".join(f"- {c.key}: {c.label}" for c in READINESS_CRITERIA)
    clarification = task.get("clarification") or {}
    return (
        "Analyze this task and decide, for EACH criterion below, whether it is "
        "satisfied based on the evidence provided.\n\n"
        f"TASK:\nTitle: {task.get('title')}\n"
        f"Description: {task.get('description')}\n"
        f"Acceptance criteria: {task.get('acceptance_criteria')}\n"
        f"Human clarification answer: {clarification.get('raw_answer') or 'None'}\n"
        f"Parsed clarification answer: {clarification.get('parsed_answer') or {}}\n\n"
        f"REPOSITORY CONTEXT (if any):\n{context}\n\n"
        "CRITERIA:\n"
        f"{criteria_lines}\n\n"
        "Return a JSON object with a 'criteria' array where each item is "
        '{"key": "<key>", "satisfied": true|false, "reason": "<one sentence>"}.'
    )


class RequirementAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def analyze(self, task: dict, context: dict | None = None) -> ReadinessAnalysis:
        prompt = build_readiness_prompt(task, context)
        result = await self._llm.structured_completion(
            prompt,
            ReadinessAnalysis,
            system=SYSTEM_PROMPT,
        )
        return result
