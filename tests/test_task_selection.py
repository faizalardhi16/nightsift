"""Tests for deterministic queue task selection."""

from __future__ import annotations

from nightshift.app.domains.task_selection import title_ease_score


def test_simple_title_scores_higher_than_complex_title() -> None:
    assert title_ease_score("Fix button label") > title_ease_score(
        "Refactor authentication database migration"
    )


def test_empty_title_is_least_preferred() -> None:
    assert title_ease_score("") == 0
