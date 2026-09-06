"""QA Critic / review agent (PRD sections 49-50).

Independent review of the git diff against task objective and acceptance
criteria. Detects unrelated changes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from nightshift.integrations.llm.base import LLMProvider

SYSTEM_PROMPT = (
    "You are an independent code reviewer. Inspect a git diff against the task "
    "objective and acceptance criteria. Flag unrelated changes and regressions. "
    "Do not trust the coding agent's self-reported success."
)


class DiffReviewResult(BaseModel):
    passed: bool
    unrelated_changes: list[str] = Field(default_factory=list)
    acceptance_criteria_met: dict[str, bool] = Field(default_factory=dict)
    concerns: list[str] = Field(default_factory=list)


def build_review_prompt(
    task: dict,
    diff: str,
    validation: dict | None = None,
) -> str:
    return (
        "Review the following change.\n\n"
        f"TASK:\nTitle: {task.get('title')}\nDescription: {task.get('description')}\n"
        f"Acceptance criteria: {task.get('acceptance_criteria')}\n\n"
        f"VALIDATION RESULTS:\n{validation}\n\n"
        f"GIT DIFF (may be truncated):\n{diff[:20000]}\n\n"
        "Return JSON with: passed (bool), unrelated_changes (list[str]), "
        "acceptance_criteria_met (map of criterion -> bool), concerns (list[str])."
    )


class ReviewAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def review(
        self,
        task: dict,
        diff: str,
        validation: dict | None = None,
    ) -> DiffReviewResult:
        return await self._llm.structured_completion(
            build_review_prompt(task, diff, validation),
            DiffReviewResult,
            system=SYSTEM_PROMPT,
        )
