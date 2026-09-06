"""Tests for readiness scoring."""

from __future__ import annotations

from nightshift.app.agents.requirement_agent import build_readiness_prompt
from nightshift.app.domains.readiness import (
    CriterionAssessment,
    ReadinessAnalysis,
    classify_readiness,
    compute_readiness_score,
)


def _assessment(satisfied_keys: set[str]) -> ReadinessAnalysis:
    criteria = [
        CriterionAssessment(key="objective", satisfied="objective" in satisfied_keys),
        CriterionAssessment(
            key="acceptance_criteria", satisfied="acceptance_criteria" in satisfied_keys
        ),
        CriterionAssessment(key="repository", satisfied="repository" in satisfied_keys),
        CriterionAssessment(key="module_context", satisfied="module_context" in satisfied_keys),
        CriterionAssessment(
            key="expected_behavior", satisfied="expected_behavior" in satisfied_keys
        ),
        CriterionAssessment(key="edge_cases", satisfied="edge_cases" in satisfied_keys),
        CriterionAssessment(
            key="test_expectations", satisfied="test_expectations" in satisfied_keys
        ),
        CriterionAssessment(key="dependencies", satisfied="dependencies" in satisfied_keys),
        CriterionAssessment(key="target_branch", satisfied="target_branch" in satisfied_keys),
    ]
    return ReadinessAnalysis(criteria=criteria)


def test_full_score_is_100() -> None:
    analysis = _assessment(
        {
            "objective",
            "acceptance_criteria",
            "repository",
            "module_context",
            "expected_behavior",
            "edge_cases",
            "test_expectations",
            "dependencies",
            "target_branch",
        }
    )
    assert compute_readiness_score(analysis) == 100


def test_empty_score_is_zero() -> None:
    assert compute_readiness_score(_assessment(set())) == 0


def test_classification() -> None:
    assert classify_readiness(95) == "READY"
    assert classify_readiness(90) == "READY"
    assert classify_readiness(72) == "CLARIFICATION_REQUIRED"
    assert classify_readiness(50) == "INSUFFICIENT_REQUIREMENT"


def test_readiness_prompt_includes_human_clarification_answer() -> None:
    prompt = build_readiness_prompt(
        {
            "title": "Tambah fitur invoice",
            "description": "Detail awal masih kurang.",
            "acceptance_criteria": [],
            "clarification": {
                "raw_answer": "1. Gunakan modul invoice dan target branch develop.",
                "parsed_answer": {"answers": ["Gunakan modul invoice"]},
            },
        }
    )

    assert "Human clarification answer" in prompt
    assert "target branch develop" in prompt
    assert "Parsed clarification answer" in prompt
