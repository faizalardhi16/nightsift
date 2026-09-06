"""Skill resolver (PRD section 36).

Maps task classification + repository stack to the minimal set of skills
that should be injected into the coding agent context.
"""

from __future__ import annotations

_BASE_SKILLS = ["task-analysis", "implementation-planning", "code-review", "git-pr"]

_STACK_TO_SKILLS: dict[str, list[str]] = {
    "nestjs": ["backend-nestjs", "unit-testing"],
    "node": ["backend-node", "unit-testing"],
    "python": ["backend-python", "unit-testing"],
    "go": ["backend-go", "unit-testing"],
    "java": ["backend-java", "unit-testing"],
    "react": ["frontend-react", "unit-testing"],
    "flutter": ["mobile-flutter", "unit-testing"],
    "dart": ["mobile-flutter", "unit-testing"],
}

_DB_SKILLS = {
    "postgres": "database-postgresql",
    "postgresql": "database-postgresql",
    "oracle": "database-oracle",
    "mysql": "database-mysql",
}


def resolve_skills(repository: dict, task: dict | None = None) -> list[str]:
    """Return the minimal set of skill names for a task+stack."""
    skills: list[str] = []

    framework = (repository.get("framework") or "").lower()
    language = (repository.get("language") or "").lower()

    for base in _BASE_SKILLS:
        skills.append(base)

    if framework in _STACK_TO_SKILLS:
        skills.extend(_STACK_TO_SKILLS[framework])
    elif language in _STACK_TO_SKILLS:
        skills.extend(_STACK_TO_SKILLS[language])

    if task:
        text = f"{task.get('title','')} {task.get('description','')}".lower()
        for db_key, skill in _DB_SKILLS.items():
            if db_key in text:
                skills.append(skill)

    # de-dup preserving order
    return list(dict.fromkeys(skills))
