"""Readiness model (PRD sections 24-26).

The readiness score is calculated by the application from criterion-level
LLM evidence, never directly from a self-reported LLM confidence number.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Criterion(BaseModel):
    key: str
    label: str
    weight: int


class CriterionAssessment(BaseModel):
    key: str
    satisfied: bool
    reason: str = ""


class ReadinessAnalysis(BaseModel):
    criteria: list[CriterionAssessment] = Field(default_factory=list)


READINESS_CRITERIA: list[Criterion] = [
    Criterion(key="objective", label="Objective clear", weight=15),
    Criterion(key="acceptance_criteria", label="Acceptance Criteria clear", weight=20),
    Criterion(key="repository", label="Repository identified", weight=10),
    Criterion(key="module_context", label="Relevant module/context found", weight=10),
    Criterion(key="expected_behavior", label="Expected behavior clear", weight=15),
    Criterion(key="edge_cases", label="Edge cases sufficiently understood", weight=10),
    Criterion(key="test_expectations", label="Test expectations known", weight=10),
    Criterion(key="dependencies", label="Dependencies understood", weight=5),
    Criterion(key="target_branch", label="Target branch known", weight=5),
]

CRITERIA_BY_KEY = {c.key: c for c in READINESS_CRITERIA}


def compute_readiness_score(analysis: ReadinessAnalysis) -> int:
    """Sum weights of satisfied criteria (application-owned scoring)."""
    assessments = {a.key: a for a in analysis.criteria}
    score = 0
    for criterion in READINESS_CRITERIA:
        assessment = assessments.get(criterion.key)
        if assessment and assessment.satisfied:
            score += criterion.weight
    return score


def classify_readiness(score: int) -> str:
    if score >= 90:
        return "READY"
    if score >= 70:
        return "CLARIFICATION_REQUIRED"
    return "INSUFFICIENT_REQUIREMENT"
