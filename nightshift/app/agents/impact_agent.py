"""Impact analysis agent (PRD sections 31-32).

Distinguishes likely vs confirmed vs possible-affected files, and avoids
telling the coding agent that uncertain assumptions are facts.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from nightshift.integrations.llm.base import LLMProvider

SYSTEM_PROMPT = (
    "You are a software architecture analyst. Given a task and repository "
    "context, identify which modules/files are likely affected. Classify "
    "confidence as 'confirmed', 'likely', or 'possible'. Only mark 'confirmed' "
    "when there is direct evidence. Never present guesses as facts."
)


class AffectedFile(BaseModel):
    path: str
    confidence: str = Field(description="confirmed | likely | possible")
    evidence: str = ""


class ImpactAnalysis(BaseModel):
    affected_modules: list[str] = Field(default_factory=list)
    affected_files: list[AffectedFile] = Field(default_factory=list)
    database_change: bool = False
    api_change: bool = False
    dependency_change: bool = False
    risks: list[str] = Field(default_factory=list)
    tests_required: list[str] = Field(default_factory=list)


def build_impact_prompt(task: dict, context: dict | None = None) -> str:
    return (
        "Analyze the impact of this task on the repository.\n\n"
        f"TASK:\nTitle: {task.get('title')}\nDescription: {task.get('description')}\n\n"
        f"CONTEXT:\n{context}\n\n"
        "Return JSON with: affected_modules (list[str]), affected_files "
        '(list of {path, confidence, evidence}), database_change (bool), '
        "api_change (bool), dependency_change (bool), risks (list[str]), "
        "tests_required (list[str])."
    )


class ImpactAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def analyze(self, task: dict, context: dict | None = None) -> ImpactAnalysis:
        result = await self._llm.structured_completion(
            build_impact_prompt(task, context),
            ImpactAnalysis,
            system=SYSTEM_PROMPT,
        )
        return result
