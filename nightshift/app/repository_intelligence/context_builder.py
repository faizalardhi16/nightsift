"""Context builder (PRD section 21).

Normalizes information from task, repository, documentation, code search and
configuration into a single TaskContext.
"""

from __future__ import annotations

from pathlib import Path

from nightshift.app.repository_intelligence.code_search import search_code
from nightshift.app.repository_intelligence.config_reader import load_repo_config
from nightshift.app.repository_intelligence.scanner import (
    detect_stack,
    find_readme,
    list_source_dirs,
)


def build_task_context(
    task: dict,
    repo_path: Path,
    repository: dict,
) -> dict:
    """Assemble a normalized task context."""
    stack = detect_stack(repo_path)
    config = load_repo_config(repo_path)

    related_code = search_code(repo_path, task.get("title", "") + " " + task.get("description", ""))

    return {
        "task": {
            "id": task.get("id"),
            "title": task.get("title"),
            "description": task.get("description"),
        },
        "repository": {
            "name": repository.get("name"),
            "url": repository.get("url"),
            "default_branch": repository.get("default_branch", "main"),
            "language": stack.get("language"),
            "framework": stack.get("framework"),
        },
        "acceptance_criteria": task.get("acceptance_criteria", []),
        "technical_context": {
            "source_dirs": list_source_dirs(repo_path),
            "readme": find_readme(repo_path),
        },
        "related_code": related_code,
        "constraints": config.get("constraints", []),
        "repo_config": config,
    }
