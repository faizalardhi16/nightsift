"""Tests for ACE task scope filtering."""

from __future__ import annotations

from nightshift.app.domains.task_scope import is_development_task
from nightshift.integrations.task_provider.base import ExternalTask


def _task(title: str, description: str = "") -> ExternalTask:
    return ExternalTask(id="task-1", title=title, description=description)


def test_development_feature_is_allowed() -> None:
    assert is_development_task(_task("Implement invoice export feature"))


def test_deployment_task_is_skipped_even_when_it_mentions_implementation() -> None:
    task = _task("Implement production deployment pipeline")

    assert not is_development_task(task)


def test_non_development_operations_task_is_skipped() -> None:
    assert not is_development_task(_task("Rotate production backup credentials"))


def test_indonesian_development_task_is_allowed() -> None:
    assert is_development_task(_task("Buat fitur filter invoice di halaman list"))
