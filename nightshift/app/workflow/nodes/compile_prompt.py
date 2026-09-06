"""compile_prompt node: produce the coding-agent prompt."""

from __future__ import annotations

from nightshift.app.agents.prompt_compiler import compile_prompt as compile_coding_prompt
from nightshift.app.config.logging import get_logger
from nightshift.app.skills.resolver import resolve_skills
from nightshift.app.workflow.context import WorkflowContext
from nightshift.app.workflow.state import State

logger = get_logger(__name__)


async def compile_prompt(ctx: WorkflowContext) -> State:
    task = ctx.get("task", {})
    context = ctx.get("context", {})
    impact = ctx.get("impact_analysis", {})
    plan = ctx.get("implementation_plan", {})

    repository = context.get("repository", {})
    skills = resolve_skills(repository, task)
    ctx.set("skills", skills)

    prompt = compile_coding_prompt(
        task=task,
        context=context,
        impact=impact,
        plan=plan,
        skills=skills,
        constraints=context.get("constraints"),
    )
    ctx.set("compiled_prompt", prompt)
    return State.READY_TO_CODE
