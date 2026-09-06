"""Scope guard for tasks accepted by the development workflow."""

from __future__ import annotations

import re

from nightshift.integrations.task_provider.base import ExternalTask

_EXCLUDED_TERMS = (
    "deploy",
    "deployment",
    "release",
    "production",
    "staging",
    "rollback",
    "infrastructure",
    "operations",
    "operational",
    "monitoring",
    "backup",
    "incident",
    "hotfix",
    "ci/cd",
    "pipeline",
    "docker",
    "kubernetes",
    "prod",
    "infra",
    "operasional",
)

_DEVELOPMENT_TERMS = (
    "feature",
    "development",
    "develop",
    "implement",
    "tambahkan",
    "menambahkan",
    "buat",
    "membuat",
    "add",
    "create",
    "build",
    "fix",
    "ubah",
    "perbaiki",
    "bug",
    "bugfix",
    "refactor",
    "enhance",
    "improve",
    "endpoint",
    "api",
    "frontend",
    "backend",
    "ui",
    "component",
    "module",
    "test",
    "testing",
    "fitur",
    "pengembangan",
    "perbaikan",
    "implementasi",
    "tampilan",
    "komponen",
    "modul",
)


def is_development_task(task: ExternalTask) -> bool:
    """Return whether an ACE task belongs to the development feature scope."""
    text = _task_text(task)
    if any(_contains_term(text, term) for term in _EXCLUDED_TERMS):
        return False
    return any(_contains_term(text, term) for term in _DEVELOPMENT_TERMS)


def _task_text(task: ExternalTask) -> str:
    metadata = task.metadata or {}
    labels = metadata.get("labels") or metadata.get("tags") or []
    metadata_type = metadata.get("type") or metadata.get("category") or ""
    values = [task.title, task.description, metadata_type, *task.acceptance_criteria, *labels]
    return " ".join(str(value) for value in values if value).lower()


def _contains_term(text: str, term: str) -> bool:
    if "/" in term:
        return term in text
    return re.search(rf"\b{re.escape(term)}\b", text) is not None
