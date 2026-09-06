"""Implementation planning agent (PRD sections 33-34)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from nightshift.integrations.llm.base import LLMProvider

SYSTEM_PROMPT = (
    "You are a senior engineer creating an implementation plan. Produce "
    "ordered, concrete steps. Ensure every acceptance criterion is addressed."
)


class PlanStep(BaseModel):
    order: int
    action: str


class ImplementationPlan(BaseModel):
    steps: list[PlanStep] = Field(default_factory=list)
    test_strategy: str = ""
    blockers: list[str] = Field(default_factory=list)


def build_plan_prompt(task: dict, impact: dict | None = None, context: dict | None = None) -> str:
    return (
        "Create an implementation plan for this task.\n\n"
        f"TASK:\nTitle: {task.get('title')}\nDescription: {task.get('description')}\n"
        f"Acceptance criteria: {task.get('acceptance_criteria')}\n\n"
        f"IMPACT ANALYSIS:\n{impact}\n\n"
        f"CONTEXT:\n{context}\n\n"
        "Return JSON with: steps (list of {order, action}), test_strategy "
        "(string), blockers (list[str], empty if none)."
    )


class PlanningAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def plan(
        self,
        task: dict,
        impact: dict | None = None,
        context: dict | None = None,
    ) -> ImplementationPlan:
        return await self._llm.structured_completion(
            build_plan_prompt(task, impact, context),
            ImplementationPlan,
            system=SYSTEM_PROMPT,
        )
