"""Prompt compiler (PRD sections 37-38).

Converts structured workflow information into coding-agent instructions.
"""

from __future__ import annotations

from nightshift.app.skills.loader import load_skill


def compile_prompt(
    task: dict,
    context: dict | None,
    impact: dict | None,
    plan: dict | None,
    skills: list[str],
    constraints: dict | None = None,
) -> str:
    """Produce a structured coding prompt."""
    repo = (context or {}).get("repository", {})
    acceptance = task.get("acceptance_criteria") or []

    skill_sections = []
    for skill_name in skills:
        content = load_skill(skill_name)
        if content:
            skill_sections.append(f"## SKILL: {skill_name}\n\n{content}\n")

    ac_lines = "\n".join(f"- {ac}" for ac in acceptance) if acceptance else "- (none provided)"

    sections = [
        "ROLE",
        "You are an expert software engineer implementing a fully-scoped task. "
        "Follow the plan, respect constraints, and verify your work.",
        "",
        "TASK",
        task.get("title", ""),
        "",
        "OBJECTIVE",
        task.get("description", ""),
        "",
        "REPOSITORY CONTEXT",
        f"Name: {repo.get('name')}\n"
        f"Language: {repo.get('language')}\n"
        f"Framework: {repo.get('framework')}\n"
        f"Default branch: {repo.get('default_branch')}",
        "",
        "IMPLEMENTATION PLAN",
        _format_plan(plan),
        "",
        "IMPACT ANALYSIS",
        _format_impact(impact),
        "",
        "ACCEPTANCE CRITERIA",
        ac_lines,
        "",
        "TECHNICAL CONSTRAINTS",
        str(constraints or {}),
        "",
        "REPOSITORY RULES",
        "Read AGENTS.md / CLAUDE.md if present and follow their conventions.",
        "",
        "TEST REQUIREMENTS",
        "Add or update tests covering the changed behavior.",
        "",
        "DEFINITION OF DONE",
        "Implementation is complete, tests pass, and no unrelated changes are made.",
    ]

    body = "\n".join(sections)
    if skill_sections:
        body += "\n\n" + "\n".join(skill_sections)

    body += "\n\nOUTPUT EXPECTATION\nMake the code changes directly. Do not ask questions."

    return body


def _format_plan(plan: dict | None) -> str:
    if not plan:
        return "(none)"
    steps = plan.get("steps", [])
    lines = []
    for step in sorted(steps, key=lambda s: s.get("order", 0)):
        lines.append(f"{step.get('order')}. {step.get('action')}")
    return "\n".join(lines) if lines else "(none)"


def _format_impact(impact: dict | None) -> str:
    if not impact:
        return "(none)"
    files = impact.get("affected_files", [])
    lines = [f"- {f.get('path')} ({f.get('confidence')})" for f in files]
    return "\n".join(lines) if lines else "(none)"
